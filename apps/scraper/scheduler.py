"""
Scraper — Startup scrape scheduler.

Called from ScraperConfig.ready() to check if we need to scrape today.
"""

import logging

logger = logging.getLogger(__name__)


def startup_scrape_check():
    """
    Check if a scrape already ran today.
    If not, trigger a background scrape task.

    On PythonAnywhere (no Celery), this just logs a message.
    Use the run_scrape management command or scheduled task instead.
    """
    try:
        from .models import ScrapeLog
        from datetime import date

        already_ran = ScrapeLog.objects.filter(
            started_at__date=date.today(),
            status__in=["success", "running"],
        ).exists()

        if not already_ran:
            logger.info("No scrape today — scheduling startup scrape...")
            try:
                from .tasks import run_scrape_task
                run_scrape_task.delay(triggered_by="startup")
            except Exception:
                # Celery not available (e.g., PythonAnywhere)
                logger.info(
                    "Celery not available. Use 'python manage.py run_scrape' "
                    "or set up a scheduled task on PythonAnywhere."
                )
        else:
            logger.info("Scrape already ran/running today. Skipping.")

    except Exception as e:
        # Don't crash Django startup if Celery/Redis isn't available
        logger.warning(f"Startup scrape check skipped: {e}")
