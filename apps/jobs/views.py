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


def job_list(request):
    """Main job board page with filters, search, and pagination."""
    queryset = JobPost.objects.filter(is_active=True).select_related("company").prefetch_related("skills")

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
    if sort_by in ("-scraped_at", "-date_posted", "title", "company__name"):
        queryset = queryset.order_by(sort_by)

    # --- Distinct (needed after M2M filter) ---
    queryset = queryset.distinct()

    # --- Pagination ---
    paginator = Paginator(queryset, 12)
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

    # --- Counts ---
    total_jobs = JobPost.objects.filter(is_active=True).count()
    new_today = JobPost.objects.filter(
        is_active=True,
        scraped_at__gte=timezone.now() - timedelta(hours=24),
    ).count()

    # --- Status counts ---
    saved_count = JobPost.objects.filter(status="saved", is_active=True).count()
    applied_count = JobPost.objects.filter(status="applied", is_active=True).count()
    ignored_count = JobPost.objects.filter(status="ignored", is_active=True).count()

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "work_type": work_type,
        "status_filter": status_filter,
        "skill_filter": skill_filter,
        "company_filter": company_filter,
        "experience_filter": experience_filter,
        "sort_by": sort_by,
        "skills_list": skills_list,
        "companies_list": companies_list,
        "total_jobs": total_jobs,
        "new_today": new_today,
        "saved_count": saved_count,
        "applied_count": applied_count,
        "ignored_count": ignored_count,
    }
    return render(request, "jobs/list.html", context)


def job_detail(request, pk):
    """Single job post detail page."""
    job = get_object_or_404(
        JobPost.objects.select_related("company").prefetch_related("skills"),
        pk=pk,
    )
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
