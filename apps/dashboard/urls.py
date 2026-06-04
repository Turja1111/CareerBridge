"""
Dashboard — URL routes (root of the site).
"""

from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
]
