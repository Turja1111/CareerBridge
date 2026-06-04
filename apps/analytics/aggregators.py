"""
Analytics — Aggregation functions for dashboard charts.
All queries run against the Jobs app models.
"""

from django.db.models import Count, Avg, Min, Max, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import JobPost, Skill, Company


def top_skills(limit=15):
    """Returns skills ranked by frequency across all active job posts."""
    return list(
        Skill.objects.annotate(
            job_count=Count("jobpost", filter=Q(jobpost__is_active=True))
        )
        .filter(job_count__gt=0)
        .order_by("-job_count")
        .values("name", "category", "job_count")[:limit]
    )


def jobs_over_time(days=30):
    """Returns daily job count for the last N days."""
    cutoff = timezone.now() - timedelta(days=days)
    return list(
        JobPost.objects.filter(is_active=True, scraped_at__gte=cutoff)
        .annotate(date=TruncDate("scraped_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )


def salary_ranges_by_title(limit=10):
    """Returns avg/min/max salary grouped by job title."""
    return list(
        JobPost.objects.filter(
            is_active=True, salary_min__isnull=False, salary_max__isnull=False
        )
        .values("title")
        .annotate(
            avg_min=Avg("salary_min"),
            avg_max=Avg("salary_max"),
            lowest=Min("salary_min"),
            highest=Max("salary_max"),
            count=Count("id"),
        )
        .filter(count__gte=1)
        .order_by("-avg_max")[:limit]
    )


def work_type_distribution():
    """Returns count per work type (Remote/Hybrid/On-site)."""
    return list(
        JobPost.objects.filter(is_active=True)
        .values("work_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


def top_companies(limit=10):
    """Returns companies with the most active postings."""
    return list(
        Company.objects.annotate(
            job_count=Count("job_posts", filter=Q(job_posts__is_active=True))
        )
        .filter(job_count__gt=0)
        .order_by("-job_count")
        .values("name", "industry", "logo_url", "job_count")[:limit]
    )


def skills_by_experience_level():
    """Returns which skills appear most for each experience level."""
    levels = ["Entry", "Mid", "Senior"]
    result = {}
    for level in levels:
        skills = list(
            Skill.objects.annotate(
                job_count=Count(
                    "jobpost",
                    filter=Q(
                        jobpost__is_active=True,
                        jobpost__experience_level=level,
                    ),
                )
            )
            .filter(job_count__gt=0)
            .order_by("-job_count")
            .values("name", "job_count")[:8]
        )
        result[level] = skills
    return result


def top_locations(limit=10):
    """Returns most common job locations."""
    return list(
        JobPost.objects.filter(is_active=True)
        .exclude(location="")
        .values("location")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )


def summary_stats():
    """Returns KPI summary numbers for the dashboard."""
    now = timezone.now()
    today_cutoff = now - timedelta(hours=24)

    total_jobs = JobPost.objects.filter(is_active=True).count()
    new_today = JobPost.objects.filter(
        is_active=True, scraped_at__gte=today_cutoff
    ).count()
    total_companies = Company.objects.annotate(
        job_count=Count("job_posts", filter=Q(job_posts__is_active=True))
    ).filter(job_count__gt=0).count()

    top_skill = (
        Skill.objects.annotate(
            job_count=Count("jobpost", filter=Q(jobpost__is_active=True))
        )
        .filter(job_count__gt=0)
        .order_by("-job_count")
        .values_list("name", flat=True)
        .first()
    ) or "—"

    avg_skills = 0
    jobs_with_skills = JobPost.objects.filter(is_active=True).annotate(
        skill_count=Count("skills")
    )
    if jobs_with_skills.exists():
        total_skill_count = sum(j.skill_count for j in jobs_with_skills)
        avg_skills = round(total_skill_count / jobs_with_skills.count(), 1)

    return {
        "total_jobs": total_jobs,
        "new_today": new_today,
        "total_companies": total_companies,
        "top_skill": top_skill,
        "avg_skills_per_job": avg_skills,
    }
