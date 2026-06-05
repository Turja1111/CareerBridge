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
    Main Celery task. Runs the Playwright scraper and saves results to PostgreSQL.
    - Creates a ScrapeLog entry
    - Runs the playwright_engine
    - Updates log with results
    - Handles errors gracefully
    """
    from .models import ScrapeLog
    from .playwright_engine import LinkedInScraper

    # Create log entry
    log = ScrapeLog.objects.create(
        status="running",
        triggered_by=triggered_by,
        progress_message="Queued and starting...",
    )

    try:
        logger.info(f"Starting scrape (triggered by: {triggered_by})")

        # Run the async scraper in a new event loop
        scraper = LinkedInScraper(log_id=log.id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats = loop.run_until_complete(scraper.run())
        finally:
            loop.close()

        # Update log
        log.status = "failed" if stats["errors"] else "success"
        log.jobs_found = stats["jobs_found"]
        log.jobs_new = stats["jobs_new"]
        log.finished_at = timezone.now()

        if stats["errors"]:
            log.error_message = "\n".join(stats["errors"])
            log.progress_message = stats["errors"][-1]
        else:
            log.progress_message = (
                f"Scrape complete: {stats['jobs_found']} found, "
                f"{stats['jobs_new']} new."
            )

        log.save()

        logger.info(
            f"Scrape complete: {stats['jobs_found']} found, "
            f"{stats['jobs_new']} new, {len(stats['errors'])} errors"
        )
        return {
            "status": log.status,
            "jobs_found": stats["jobs_found"],
            "jobs_new": stats["jobs_new"],
            "errors": stats["errors"],
        }

    except Exception as e:
        logger.error(f"Scrape task failed: {e}")
        log.status = "failed"
        log.error_message = str(e)
        log.finished_at = timezone.now()
        log.save()
        raise


@shared_task(name="scraper.startup_check")
def startup_scrape_if_needed():
    """
    Called on Django app startup.
    Checks if a scrape already ran today. If not, triggers run_scrape_task.
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
        logger.info("Scrape already ran today. Skipping startup scrape.")
