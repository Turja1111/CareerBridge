"""
Jobs — Template views for the job board pages.
"""

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from .models import JobPost, Company, Skill
from .utils import is_relevant_job, relevance_score


def _relevant_jobs_queryset():
    return (
        JobPost.objects.filter(is_active=True)
        .exclude(status="ignored")
        .select_related("company")
        .prefetch_related("skills")
    )


def job_list(request):
    """Main job board page with Bangladesh-safe, high-quality recommendations."""
    queryset = _relevant_jobs_queryset()

    # --- Search ---
    search_query = request.GET.get("search", "").strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query)
            | Q(company__name__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # --- Filters ---
    work_type = request.GET.get("work_type", "")
    if work_type:
        queryset = queryset.filter(work_type=work_type)

    status_filter = request.GET.get("status", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    source_filter = request.GET.get("source", "")
    if source_filter:
        queryset = queryset.filter(source=source_filter)

    skill_filter = request.GET.get("skill", "")
    if skill_filter:
        queryset = queryset.filter(skills__name__iexact=skill_filter)

    company_filter = request.GET.get("company", "")
    if company_filter:
        queryset = queryset.filter(company__name__iexact=company_filter)

    experience_filter = request.GET.get("experience", "")
    if experience_filter:
        queryset = queryset.filter(experience_level=experience_filter)

    # --- Sorting ---
    sort_by = request.GET.get("sort", "-scraped_at")
    if sort_by in ("-match_score", "-scraped_at", "-date_posted", "title", "company__name"):
        queryset = queryset.order_by(sort_by)

    # --- Distinct (needed after M2M filter) ---
    queryset = queryset.distinct()

    jobs = [job for job in queryset if is_relevant_job(job)]
    jobs = sorted(
        jobs,
        key=lambda job: (
            relevance_score(job.title, job.description, job.location, " ".join(skill.name for skill in job.skills.all())),
            job.scraped_at,
        ),
        reverse=True,
    )

    # --- Pagination ---
    paginator = Paginator(jobs, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # --- Sidebar data ---
    skills_list = (
        Skill.objects.annotate(job_count=Count("jobpost"))
        .filter(job_count__gt=0)
        .order_by("-job_count")[:15]
    )
    companies_list = (
        Company.objects.annotate(job_count=Count("job_posts"))
        .filter(job_count__gt=0)
        .order_by("-job_count")[:10]
    )
    source_counts = (
        JobPost.objects.filter(is_active=True)
        .exclude(status="ignored")
        .values("source")
        .annotate(job_count=Count("id"))
        .order_by("-job_count")
    )
    source_labels = dict(JobPost.SOURCE_CHOICES)
    sources_list = [
        {
            "value": item["source"],
            "label": source_labels.get(item["source"], item["source"].title()),
            "job_count": item["job_count"],
        }
        for item in source_counts
    ]

    # --- Counts ---
    total_jobs = len(jobs)
    new_today = sum(1 for job in jobs if job.scraped_at >= timezone.now() - timedelta(hours=24))

    # --- Status counts ---
    saved_count = JobPost.objects.filter(status="saved", is_active=True).count()
    applied_count = JobPost.objects.filter(status="applied", is_active=True).count()
    ignored_count = JobPost.objects.filter(status="ignored", is_active=True).count()

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "work_type": work_type,
        "status_filter": status_filter,
        "source_filter": source_filter,
        "skill_filter": skill_filter,
        "company_filter": company_filter,
        "experience_filter": experience_filter,
        "sort_by": sort_by,
        "skills_list": skills_list,
        "companies_list": companies_list,
        "sources_list": sources_list,
        "total_jobs": total_jobs,
        "new_today": new_today,
        "saved_count": saved_count,
        "applied_count": applied_count,
        "ignored_count": ignored_count,
    }
    return render(request, "jobs/list.html", context)


def manage_ignored_jobs(request):
    """Restore ignored jobs manually from a dedicated management page."""
    ignored_jobs = (
        JobPost.objects.filter(status="ignored", is_active=True)
        .select_related("company")
        .prefetch_related("skills")
        .order_by("-updated_at")
    )

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        if job_id:
            JobPost.objects.filter(pk=job_id, status="ignored").update(status="new")
        return render(request, "jobs/ignored_jobs.html", {"ignored_jobs": ignored_jobs, "restored": True})

    return render(request, "jobs/ignored_jobs.html", {"ignored_jobs": ignored_jobs, "restored": False})


def job_detail(request, pk):
    """Single job post detail page."""
    job = get_object_or_404(
        JobPost.objects.select_related("company").prefetch_related("skills"),
        pk=pk,
    )
    if job.status == "ignored" or not is_relevant_job(job):
        raise get_object_or_404(JobPost, pk=pk)
    # Get similar jobs (same company or same skills)
    similar_jobs = (
        JobPost.objects.filter(is_active=True)
        .filter(
            Q(company=job.company) | Q(skills__in=job.skills.all())
        )
        .exclude(pk=job.pk)
        .distinct()[:4]
    )
    context = {
        "job": job,
        "similar_jobs": similar_jobs,
    }
    return render(request, "jobs/detail.html", context)
