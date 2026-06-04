"""
Jobs — API URL routes (mounted at /api/jobs/).
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r"", api_views.JobPostViewSet, basename="jobpost")

urlpatterns = [
    path("<int:pk>/status/", api_views.update_job_status, name="job-status-update"),
    path("new/", api_views.new_jobs, name="new-jobs"),
] + router.urls
