"""
Scraper — Management command to run the full scraping pipeline.

Usage:
    python manage.py run_scrape
    python manage.py run_scrape --triggered-by schedule

Can be used as a Celery alternative on platforms like PythonAnywhere
where Celery is not available. Schedule via the host's task runner.
"""

import asyncio
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the LinkedIn + BDJobs job scrapers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--triggered-by",
            type=str,
            default="manual",
            choices=["manual", "schedule", "startup"],
            help="What triggered this scrape (default: manual)",
        )

    def handle(self, *args, **options):
        triggered_by = options["triggered_by"]
        self.stdout.write(
            self.style.NOTICE(f"Starting scrape (triggered by: {triggered_by})")
        )

        from apps.scraper.models import ScrapeLog
        from apps.scraper.playwright_engine import LinkedInScraper, ScrapeCancelledException
        from django.conf import settings
        from apps.scraper.tasks import _run_bdjobs_sync

        log = ScrapeLog.objects.create(
            status="running",
            triggered_by=triggered_by,
            progress_message="Starting...",
        )

        # Initialise safe defaults — errors are isolated per platform
        stats = {"jobs_found": 0, "jobs_new": 0, "errors": []}

        try:
            # ── LinkedIn ─────────────────────────────────────────────────────────
            self.stdout.write(self.style.NOTICE("  → Running LinkedIn scraper..."))
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

                self.stdout.write(
                    self.style.SUCCESS(
                        f"     LinkedIn: {linkedin_stats.get('jobs_found', 0)} found, "
                        f"{linkedin_stats.get('jobs_new', 0)} new"
                    )
                )
            except ScrapeCancelledException as exc:
                raise exc
            except Exception as exc:
                error_msg = f"LinkedIn scraper error: {exc}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                self.stdout.write(self.style.ERROR(f"     LinkedIn FAILED: {exc}"))

            # ── BDJobs ───────────────────────────────────────────────────────────
            if getattr(settings, "SCRAPER_ENABLE_BDJOBS", True):
                self.stdout.write(self.style.NOTICE("  → Running BDJobs scraper..."))
                try:
                    bdjobs_stats = _run_bdjobs_sync(log)
                    stats["jobs_found"] += bdjobs_stats.get("jobs_found", 0)
                    stats["jobs_new"] += bdjobs_stats.get("jobs_new", 0)
                    stats["errors"].extend(bdjobs_stats.get("errors", []))

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"     BDJobs: {bdjobs_stats.get('jobs_found', 0)} found, "
                            f"{bdjobs_stats.get('jobs_new', 0)} new"
                        )
                    )
                except ScrapeCancelledException as exc:
                    raise exc
                except Exception as exc:
                    error_msg = f"BDJobs scraper error: {exc}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    self.stdout.write(self.style.ERROR(f"     BDJobs FAILED: {exc}"))
            else:
                self.stdout.write(
                    self.style.WARNING("  → BDJobs scraper disabled (SCRAPER_ENABLE_BDJOBS=False)")
                )

            # ── Check if Cancelled ───────────────────────────────────────────────
            log.refresh_from_db()
            if log.status == "failed" and "stopped" in (log.error_message or "").lower():
                self.stdout.write(self.style.WARNING("\n⛔  Scrape was cancelled by user. Terminating gracefully."))
                return

            # ── Finalise log ─────────────────────────────────────────────────────
            has_errors = bool(stats["errors"])
            has_results = stats["jobs_found"] > 0

            if has_errors and not has_results:
                log.status = "failed"
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

            # ── Console summary ──────────────────────────────────────────────────
            if stats["errors"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠  Completed with {len(stats['errors'])} warning(s):"
                    )
                )
                for err in stats["errors"]:
                    self.stdout.write(self.style.ERROR(f"   • {err}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓  Scrape complete: "
                    f"{stats['jobs_found']} found, {stats['jobs_new']} new"
                )
            )

        except ScrapeCancelledException:
            self.stdout.write(self.style.WARNING("\n⛔  Scrape was cancelled by user. Terminating gracefully."))
        except Exception as exc:
            logger.error("Scrape command failed: %s", exc)
            log.status = "failed"
            log.error_message = str(exc)
            log.progress_message = f"Fatal error: {exc}"
            log.finished_at = timezone.now()
            log.save()
            self.stdout.write(self.style.ERROR(f"Fatal error: {exc}"))
            raise
