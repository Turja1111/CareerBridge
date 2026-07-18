"""
Scraper — Celery tasks for background scraping.
"""

import asyncio
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="scraper.run_scrape")
def run_scrape_task(self, triggered_by="schedule"):
    """
    Main Celery task. Runs the Playwright scrapers and saves results to PostgreSQL.

    Pipeline:
    1. Creates a ScrapeLog entry (status=running)
    2. Runs LinkedIn scraper (playwright_engine)
    3. Runs BDJobs scraper (providers.py) if SCRAPER_ENABLE_BDJOBS is True
    4. Merges combined stats and updates the log entry
    5. Handles all errors gracefully — partial success is still recorded
    """
    from .models import ScrapeLog
    from .playwright_engine import LinkedInScraper

    log = ScrapeLog.objects.create(
        status="running",
        triggered_by=triggered_by,
        progress_message="Queued and starting...",
        celery_task_id=self.request.id,
    )

    # Initialise an empty stats dict so we always have a safe object to merge into
    stats = {"jobs_found": 0, "jobs_new": 0, "errors": []}

    from .playwright_engine import ScrapeCancelledException

    try:
        logger.info("Starting scrape (triggered by: %s)", triggered_by)

        # ── LinkedIn ────────────────────────────────────────────────────────────
        try:
            scraper = LinkedInScraper(log_id=log.id)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                linkedin_stats = loop.run_until_complete(scraper.run())
            finally:
                loop.close()

            stats["jobs_found"] += linkedin_stats.get("jobs_found", 0)
            stats["jobs_new"] += linkedin_stats.get("jobs_new", 0)
            stats["errors"].extend(linkedin_stats.get("errors", []))

        except ScrapeCancelledException as exc:
            raise exc
        except Exception as exc:
            error_msg = f"LinkedIn scraper error: {exc}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        # ── BDJobs ──────────────────────────────────────────────────────────────
        from django.conf import settings
        if getattr(settings, "SCRAPER_ENABLE_BDJOBS", True):
            try:
                bdjobs_stats = _run_bdjobs_sync(log)
                stats["jobs_found"] += bdjobs_stats.get("jobs_found", 0)
                stats["jobs_new"] += bdjobs_stats.get("jobs_new", 0)
                stats["errors"].extend(bdjobs_stats.get("errors", []))
            except ScrapeCancelledException as exc:
                raise exc
            except Exception as exc:
                error_msg = f"BDJobs scraper error: {exc}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)

        # ── Check if Cancelled ──────────────────────────────────────────────────
        log.refresh_from_db()
        if log.status == "failed" and "stopped" in (log.error_message or "").lower():
            logger.info("Scrape task was cancelled. Skipping final status save.")
            return {
                "status": "failed",
                "jobs_found": stats["jobs_found"],
                "jobs_new": stats["jobs_new"],
                "errors": len(stats["errors"]),
            }

        # ── Finalise log ────────────────────────────────────────────────────────
        # Mark as "failed" only when EVERY error is fatal (no jobs at all)
        # so that partial successes are correctly recorded.
        has_errors = bool(stats["errors"])
        has_results = stats["jobs_found"] > 0

        if has_errors and not has_results:
            log.status = "failed"
        elif has_errors and has_results:
            log.status = "success"   # Partial success — errors logged in message
        else:
            log.status = "success"

        log.jobs_found = stats["jobs_found"]
        log.jobs_new = stats["jobs_new"]
        log.finished_at = timezone.now()

        if has_errors:
            log.error_message = "\n".join(stats["errors"])
            log.progress_message = (
                f"Completed with {len(stats['errors'])} warning(s). "
                f"{stats['jobs_found']} found, {stats['jobs_new']} new."
            )
        else:
            log.progress_message = (
                f"Done — {stats['jobs_found']} found, {stats['jobs_new']} new."
            )

        log.save()

        logger.info(
            "Scrape complete: %d found, %d new, %d error(s)",
            stats["jobs_found"],
            stats["jobs_new"],
            len(stats["errors"]),
        )
        return {
            "status": log.status,
            "jobs_found": stats["jobs_found"],
            "jobs_new": stats["jobs_new"],
            "errors": len(stats["errors"]),
        }

    except ScrapeCancelledException:
        logger.info("Scrape task was cancelled by user. Terminating gracefully.")
        return {
            "status": "failed",
            "jobs_found": stats["jobs_found"],
            "jobs_new": stats["jobs_new"],
            "errors": len(stats["errors"]),
        }
    except Exception as exc:
        logger.error("Scrape task failed catastrophically: %s", exc)
        log.status = "failed"
        log.error_message = str(exc)
        log.progress_message = f"Fatal error: {exc}"
        log.finished_at = timezone.now()
        log.save()
        raise


# ──────────────────────────────────────────────────────────────────────────────
#  BDJobs async pipeline (called from both Celery task and management command)
# ──────────────────────────────────────────────────────────────────────────────

def _run_bdjobs_sync(log):
    """
    Run the BDJobs async scraper inside a fresh event loop.
    Returns the same stats dict structure as the LinkedIn scraper.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_bdjobs_async(log))
    finally:
        loop.close()


async def _bdjobs_async(log):
    """
    Async BDJobs scraping pipeline:
    - Launches Chromium (respects SCRAPER_HEADLESS)
    - Logs in with BDJobs credentials (if provided)
    - Iterates over user keywords and scrapes job listings
    - Saves new jobs to the DB
    """
    from playwright.async_api import async_playwright
    from asgiref.sync import sync_to_async
    from django.conf import settings
    from .providers import BDJobsProvider, SearchRequest
    from .models import UserPreference

    stats = {"jobs_found": 0, "jobs_new": 0, "errors": []}

    def _update_log(msg: str):
        from .models import ScrapeLog
        # Check if the user manually cancelled the scraper session
        log_obj = ScrapeLog.objects.filter(pk=log.id).first()
        if log_obj and log_obj.status != "running":
            raise ScrapeCancelledException("Scrape task cancelled by user.")
        ScrapeLog.objects.filter(pk=log.id).update(progress_message=msg)

    def _get_keywords() -> list[str]:
        prefs = UserPreference.objects.first()
        if prefs and prefs.keywords:
            return prefs.keywords
        return ["Data Science", "Machine Learning", "Data Analyst", "Python Developer"]

    def _save_jobs(jobs: list[dict]) -> int:
        from apps.jobs.services import upsert_job_from_source
        count = 0
        for job in jobs:
            try:
                _, created = upsert_job_from_source(job)
                if created:
                    count += 1
            except Exception as exc:
                logger.error("Failed to save BDJobs job '%s': %s", job.get("title"), exc)
        return count

    provider = BDJobsProvider()
    max_jobs = getattr(settings, "SCRAPER_MAX_JOBS_PER_SEARCH", 30)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.SCRAPER_HEADLESS,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="Asia/Dhaka",
            )
            # Remove the `navigator.webdriver` flag
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            page = await context.new_page()

            # Login (gracefully falls back to anonymous if credentials missing)
            await sync_to_async(_update_log)("BDJobs: Logging in...")
            await provider.login(page)

            keywords = await sync_to_async(_get_keywords)()
            logger.info("BDJobs: searching %d keyword(s)", len(keywords))

            for idx, keyword in enumerate(keywords, 1):
                try:
                    await sync_to_async(_update_log)(
                        f"BDJobs [{idx}/{len(keywords)}]: Searching '{keyword}'..."
                    )
                    request = SearchRequest(keyword=keyword, location="Bangladesh")
                    jobs = await provider.search_jobs(page, request, max_jobs=max_jobs)

                    stats["jobs_found"] += len(jobs)
                    new_count = await sync_to_async(_save_jobs)(jobs)
                    stats["jobs_new"] += new_count

                    logger.info(
                        "BDJobs '%s': %d found, %d new", keyword, len(jobs), new_count
                    )
                    await sync_to_async(_update_log)(
                        f"BDJobs: '{keyword}' — {new_count} new job(s) saved"
                    )

                except Exception as exc:
                    err = f"BDJobs error for '{keyword}': {exc}"
                    logger.warning(err)
                    stats["errors"].append(err)

                import asyncio as _asyncio
                import random as _random
                await _asyncio.sleep(_random.uniform(2, 4))

            await browser.close()

    except Exception as exc:
        err = f"BDJobs fatal error: {exc}"
        logger.error(err)
        stats["errors"].append(err)

    return stats


# ──────────────────────────────────────────────────────────────────────────────
#  Startup task
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="scraper.startup_check")
def startup_scrape_if_needed():
    """
    Called on Django app startup.
    Checks if a successful scrape already ran today.  If not, triggers one.
    """
    from .models import ScrapeLog
    from datetime import date

    already_ran = ScrapeLog.objects.filter(
        started_at__date=date.today(),
        status="success",
    ).exists()

    if not already_ran:
        logger.info("No successful scrape today. Triggering startup scrape...")
        run_scrape_task.delay(triggered_by="startup")
    else:
        logger.info("Scrape already ran successfully today. Skipping.")
