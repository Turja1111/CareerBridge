"""
Jobs — django-filter configuration for job filtering.
"""

import django_filters
from .models import JobPost


class JobPostFilter(django_filters.FilterSet):
    """Filter jobs by work type, status, skill, company, date range, and search."""

    search = django_filters.CharFilter(method="filter_search", label="Search")
    work_type = django_filters.ChoiceFilter(choices=JobPost.WORK_TYPE_CHOICES)
    status = django_filters.ChoiceFilter(choices=JobPost.STATUS_CHOICES)
    skill = django_filters.CharFilter(method="filter_skill", label="Skill")
    company = django_filters.CharFilter(
        field_name="company__name", lookup_expr="icontains"
    )
    experience_level = django_filters.ChoiceFilter(
        choices=JobPost.EXPERIENCE_LEVEL_CHOICES
    )
    date_from = django_filters.DateFilter(field_name="date_posted", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date_posted", lookup_expr="lte")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = JobPost
        fields = [
            "work_type",
            "status",
            "experience_level",
            "is_active",
        ]

    def filter_search(self, queryset, name, value):
        """Search across title, company name, location, and description."""
        return queryset.filter(
            models.Q(title__icontains=value)
            | models.Q(company__name__icontains=value)
            | models.Q(location__icontains=value)
            | models.Q(description__icontains=value)
        )

    def filter_skill(self, queryset, name, value):
        """Filter jobs that require a specific skill."""
        return queryset.filter(skills__name__iexact=value)


# Need to import models for Q lookups
from django.db import models
