"""
Scraper — API views for scraper control.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import ScrapeLog, UserPreference


@api_view(["POST"])
def trigger_scrape(request):
    """Manually trigger a scrape task."""
    try:
        from .tasks import run_scrape_task
        # Check if already running
        running = ScrapeLog.objects.filter(status="running").exists()
        if running:
            return Response(
                {"error": "A scrape is already running"},
                status=status.HTTP_409_CONFLICT,
            )
        run_scrape_task.delay(triggered_by="manual")
        return Response({"message": "Scrape triggered successfully"})
    except Exception as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def scraper_status_api(request):
    """Return current scraper status."""
    running = ScrapeLog.objects.filter(status="running").first()
    last_success = ScrapeLog.objects.filter(status="success").first()

    data = {
        "is_running": running is not None,
        "current_run": None,
        "last_success": None,
    }

    if running:
        data["current_run"] = {
            "id": running.id,
            "started_at": running.started_at.isoformat(),
            "jobs_found": running.jobs_found,
        }

    if last_success:
        data["last_success"] = {
            "id": last_success.id,
            "started_at": last_success.started_at.isoformat(),
            "finished_at": last_success.finished_at.isoformat() if last_success.finished_at else None,
            "jobs_found": last_success.jobs_found,
            "jobs_new": last_success.jobs_new,
        }

    return Response(data)


@api_view(["GET"])
def scraper_logs(request):
    """Return last 20 scrape log entries."""
    logs = ScrapeLog.objects.all()[:20]
    data = [
        {
            "id": log.id,
            "started_at": log.started_at.isoformat(),
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
            "status": log.status,
            "jobs_found": log.jobs_found,
            "jobs_new": log.jobs_new,
            "triggered_by": log.triggered_by,
            "error_message": log.error_message,
            "duration": log.duration,
        }
        for log in logs
    ]
    return Response(data)


@api_view(["GET", "POST"])
def preferences_api(request):
    """Get or update scraping preferences."""
    prefs, created = UserPreference.objects.get_or_create(pk=1)

    if request.method == "GET":
        return Response({
            "keywords": prefs.keywords,
            "locations": prefs.locations,
            "work_types": prefs.work_types,
            "experience_level": prefs.experience_level,
        })

    # POST — update preferences
    prefs.keywords = request.data.get("keywords", prefs.keywords)
    prefs.locations = request.data.get("locations", prefs.locations)
    prefs.work_types = request.data.get("work_types", prefs.work_types)
    prefs.experience_level = request.data.get("experience_level", prefs.experience_level)
    prefs.save()
    return Response({"message": "Preferences updated"})
