"""
CareerBridge — Celery Configuration
"""

import os
from celery import Celery
from celery.schedules import crontab
from decouple import config

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careerbridge.settings.local")

app = Celery("careerbridge")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# ─────────────────────────────────────────────
#  Beat Schedule — Daily Scrape
# ─────────────────────────────────────────────

DAILY_HOUR = config("SCRAPER_DAILY_HOUR", default=8, cast=int)
DAILY_MINUTE = config("SCRAPER_DAILY_MINUTE", default=0, cast=int)

app.conf.beat_schedule = {
    "daily-linkedin-scrape": {
        "task": "scraper.run_scrape",
        "schedule": crontab(hour=DAILY_HOUR, minute=DAILY_MINUTE),
        "kwargs": {"triggered_by": "schedule"},
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f"Request: {self.request!r}")
