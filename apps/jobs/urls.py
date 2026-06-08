"""
Jobs — Template URL routes.
"""

from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("ignored/", views.manage_ignored_jobs, name="ignored"),
    path("<int:pk>/", views.job_detail, name="detail"),
]
