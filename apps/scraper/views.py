"""
Scraper — Template views for the scraper control panel.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ScrapeLog, UserPreference


def scraper_status(request):
    """Scraper control panel page."""
    # Latest scrape logs
    logs = ScrapeLog.objects.all()[:20]

    # Current status
    running_scrape = ScrapeLog.objects.filter(status="running").first()
    last_success = ScrapeLog.objects.filter(status="success").first()

    # User preferences
    preferences = UserPreference.objects.first()

    context = {
        "logs": logs,
        "running_scrape": running_scrape,
        "last_success": last_success,
        "preferences": preferences,
        "is_running": running_scrape is not None,
    }
    return render(request, "scraper/status.html", context)
