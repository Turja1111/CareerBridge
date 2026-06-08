"""
Dashboard — Main home page view.
"""

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import JobPost
from apps.jobs.utils import is_relevant_job
from apps.scraper.models import ScrapeLog
from apps.analytics.aggregators import summary_stats, top_skills, work_type_distribution


def index(request):
    """Home dashboard with KPI summary and quick stats."""
    stats = summary_stats()

    # Recent jobs
    recent_jobs = [
        job for job in JobPost.objects.filter(is_active=True)
        .exclude(status="ignored")
        .select_related("company")
        .prefetch_related("skills")
        if is_relevant_job(job)
    ][:6]

    # Last scrape info
    last_scrape = ScrapeLog.objects.first()

    # Quick chart data
    top_skills_data = top_skills(limit=5)
    work_types = work_type_distribution()

    context = {
        "stats": stats,
        "recent_jobs": recent_jobs,
        "last_scrape": last_scrape,
        "top_skills_data": top_skills_data,
        "work_types": work_types,
    }
    return render(request, "dashboard/index.html", context)
