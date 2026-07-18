"""
Scraper — Template views for the scraper control panel.
"""

from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import logging

from .models import ScrapeLog, UserPreference

logger = logging.getLogger(__name__)


def _cleanup_stale_running():
    """Mark any 'running' logs older than 1 hour as failed (stale/crashed)."""
    stale_threshold = timezone.now() - timedelta(hours=1)
    stale = ScrapeLog.objects.filter(status="running", started_at__lt=stale_threshold)
    if stale.exists():
        count = stale.count()
        stale.update(
            status="failed",
            finished_at=timezone.now(),
            error_message="Timed out — marked as failed after 1 hour without update.",
            progress_message="Timed out.",
        )
        logger.warning("Cleaned up %d stale running scrape log(s) on page load.", count)


def scraper_status(request):
    """Scraper control panel page."""
    _cleanup_stale_running()

    logs = ScrapeLog.objects.all()[:20]
    running_scrape = ScrapeLog.objects.filter(status="running").first()
    last_success = ScrapeLog.objects.filter(status="success").first()
    preferences = UserPreference.objects.first()

    context = {
        "logs": logs,
        "running_scrape": running_scrape,
        "last_success": last_success,
        "preferences": preferences,
        "is_running": running_scrape is not None,
    }
    return render(request, "scraper/status.html", context)
