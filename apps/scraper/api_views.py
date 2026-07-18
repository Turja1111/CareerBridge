"""
Scraper — API views for scraper control.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import logging

from .models import ScrapeLog, UserPreference

logger = logging.getLogger(__name__)


def _as_clean_list(value):
    """Normalize preference API values to a clean list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split(",")
    return [str(item).strip() for item in value if str(item).strip()]


@api_view(["POST"])
def trigger_scrape(request):
    """Manually trigger a scrape task."""
    try:
        from .tasks import run_scrape_task

        # Clean up any stale running logs (>1 hour) before checking
        stale_threshold = timezone.now() - timedelta(hours=1)
        stale = ScrapeLog.objects.filter(status="running", started_at__lt=stale_threshold)
        if stale.exists():
            stale.update(
                status="failed",
                finished_at=timezone.now(),
                error_message="Timed out — cleaned up before new trigger.",
                progress_message="Timed out.",
            )

        running = ScrapeLog.objects.filter(status="running").exists()
        if running:
            return Response(
                {"error": "A scrape is already running. Use Force Stop first."},
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
    # Clean up stale running logs (>1 hour) so UI doesn't get stuck
    stale_threshold = timezone.now() - timedelta(hours=1)
    stale = ScrapeLog.objects.filter(status="running", started_at__lt=stale_threshold)
    if stale.exists():
        stale.update(
            status="failed",
            finished_at=timezone.now(),
            error_message="Timed out — marked as failed after 1 hour without update.",
            progress_message="Timed out.",
        )

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
            "jobs_new": running.jobs_new,
            "progress_message": running.progress_message,
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
            "progress_message": log.progress_message,
            "error_message": log.error_message,
            "duration": log.duration,
        }
        for log in logs
    ]
    return Response(data)


@api_view(["POST"])
def force_stop_scrape(request):
    """
    Force-stop all currently 'running' scrape logs.

    Marks every stuck ScrapeLog(status='running') as 'failed' with a clear
    error message so the UI unblocks and a new scrape can be triggered.

    Automatically revokes any associated Celery tasks found in the DB.
    Also cleans up stale 'running' logs older than 1 hour.
    Always safe to call — it is idempotent when nothing is running.
    """
    now = timezone.now()

    # Also clean up stale running logs older than 1 hour
    stale_threshold = now - timedelta(hours=1)
    stale_logs = ScrapeLog.objects.filter(
        status="running", started_at__lt=stale_threshold
    )
    if stale_logs.exists():
        logger.warning("Cleaning up %d stale running log(s) older than 1 hour.", stale_logs.count())
        stale_logs.update(
            status="failed",
            finished_at=now,
            error_message="Timed out — marked as failed after 1 hour.",
            progress_message="Timed out.",
        )

    running_logs = ScrapeLog.objects.filter(status="running")
    count = running_logs.count()

    if count == 0:
        return Response({"message": "No running scrape found. Nothing to stop."})

    # Collect all Celery task IDs from running logs and revoke them
    task_ids = list(
        running_logs.exclude(celery_task_id__isnull=True)
        .exclude(celery_task_id="")
        .values_list("celery_task_id", flat=True)
    )

    revoked = 0
    for task_id in task_ids:
        try:
            from celery.app.control import Control
            from careerbridge.celery import app as celery_app
            Control(celery_app).revoke(task_id, terminate=True, signal="SIGKILL")
            revoked += 1
            logger.info("Revoked Celery task %s.", task_id)
        except Exception as exc:
            logger.warning("Could not revoke Celery task %s: %s", task_id, exc)

    # Also try to revoke via request body (for backwards compatibility)
    task_id = request.data.get("task_id")
    if task_id and task_id not in task_ids:
        try:
            from celery.app.control import Control
            from careerbridge.celery import app as celery_app
            Control(celery_app).revoke(task_id, terminate=True, signal="SIGKILL")
            revoked += 1
            logger.info("Revoked Celery task %s (from request body).", task_id)
        except Exception as exc:
            logger.warning("Could not revoke Celery task %s: %s", task_id, exc)

    # Mark all running logs as failed
    running_logs.update(
        status="failed",
        finished_at=now,
        error_message="Manually stopped by user via Force Stop.",
        progress_message="Stopped by user.",
    )

    logger.info("Force-stopped %d running scrape log(s), revoked %d task(s).", count, revoked)
    return Response({
        "message": f"Stopped {count} running scrape session(s). Revoked {revoked} background task(s). You can now start a fresh scrape.",
        "stopped": count,
        "revoked": revoked,
    })


@api_view(["GET"])
def scraper_health(request):
    """
    Health check — returns whether the scraper appears to be 'stuck'.

    A run is considered stuck if it has been in 'running' state for
    more than STUCK_THRESHOLD_MINUTES without updating its progress_message.
    The frontend can use this to prompt the user to force-stop.
    """
    STUCK_THRESHOLD_MINUTES = 30

    running = ScrapeLog.objects.filter(status="running").order_by("started_at")
    stuck = []

    threshold = timezone.now() - timedelta(minutes=STUCK_THRESHOLD_MINUTES)
    for log in running:
        if log.started_at < threshold:
            stuck.append({
                "id": log.id,
                "started_at": log.started_at.isoformat(),
                "jobs_found": log.jobs_found,
                "progress_message": log.progress_message,
                "running_minutes": int((timezone.now() - log.started_at).total_seconds() / 60),
            })

    return Response({
        "total_running": running.count(),
        "stuck_count": len(stuck),
        "is_stuck": len(stuck) > 0,
        "stuck_runs": stuck,
        "threshold_minutes": STUCK_THRESHOLD_MINUTES,
    })


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
    if "keywords" in request.data:
        prefs.keywords = _as_clean_list(request.data.get("keywords"))
    if "locations" in request.data:
        prefs.locations = _as_clean_list(request.data.get("locations"))
    if "work_types" in request.data:
        prefs.work_types = _as_clean_list(request.data.get("work_types"))
    if "experience_level" in request.data:
        prefs.experience_level = _as_clean_list(request.data.get("experience_level"))
    prefs.save()
    return Response({"message": "Preferences updated"})
