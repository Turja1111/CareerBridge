"""
Scraper — API URL routes (mounted at /api/scraper/).
"""

from django.urls import path
from . import api_views

urlpatterns = [
    path("trigger/",    api_views.trigger_scrape,    name="scraper-trigger"),
    path("stop/",       api_views.force_stop_scrape,  name="scraper-force-stop"),
    path("health/",     api_views.scraper_health,     name="scraper-health"),
    path("status/",     api_views.scraper_status_api, name="scraper-status"),
    path("logs/",       api_views.scraper_logs,       name="scraper-logs"),
    path("preferences/",api_views.preferences_api,    name="scraper-preferences"),
]
