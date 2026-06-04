"""
Analytics — API URL routes (mounted at /api/analytics/).
"""

from django.urls import path
from . import api_views

urlpatterns = [
    path("top-skills/", api_views.top_skills_api, name="api-top-skills"),
    path("jobs-over-time/", api_views.jobs_over_time_api, name="api-jobs-over-time"),
    path("work-type-distribution/", api_views.work_type_api, name="api-work-type"),
    path("salary-ranges/", api_views.salary_ranges_api, name="api-salary-ranges"),
    path("top-companies/", api_views.top_companies_api, name="api-top-companies"),
    path("top-locations/", api_views.top_locations_api, name="api-top-locations"),
    path("skills-by-experience/", api_views.skills_by_experience_api, name="api-skills-exp"),
    path("summary/", api_views.summary_api, name="api-summary"),
]
