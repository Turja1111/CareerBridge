"""
Scraper — Template URL routes.
"""

from django.urls import path
from . import views

app_name = "scraper"

urlpatterns = [
    path("", views.scraper_status, name="status"),
]
