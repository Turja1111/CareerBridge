"""
Scraper — Management command to run LinkedIn scraper.

Usage:
    python manage.py run_scrape

This replaces the Celery task for PythonAnywhere where Celery is not available.
Can be scheduled via PythonAnywhere's "Tasks" tab.
"""

import asyncio
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the LinkedIn job scraper"

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
        self.stdout.write(self.style.NOTICE(f"Starting scrape (triggered by: {triggered_by})"))

        from apps.scraper.models import ScrapeLog
        from apps.scraper.playwright_engine import LinkedInScraper

        # Create log entry
        log = ScrapeLog.objects.create(
            status="running",
            triggered_by=triggered_by,
            progress_message="Queued and starting...",
        )

        try:
            # Run the async scraper
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

            log.save()

            # Print results
            if stats["errors"]:
                self.stdout.write(self.style.WARNING(
                    f"Scrape finished with errors: {len(stats['errors'])}"
                ))
                for err in stats["errors"]:
                    self.stdout.write(self.style.ERROR(f"  - {err}"))

            self.stdout.write(self.style.SUCCESS(
                f"Scrape complete: {stats['jobs_found']} found, "
                f"{stats['jobs_new']} new"
            ))

        except Exception as e:
            logger.error(f"Scrape task failed: {e}")
            log.status = "failed"
            log.error_message = str(e)
            log.finished_at = timezone.now()
            log.save()
            self.stdout.write(self.style.ERROR(f"Scrape failed: {e}"))
