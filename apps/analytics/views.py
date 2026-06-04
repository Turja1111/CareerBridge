"""
Analytics — Template and API views for charts and data.
"""

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import aggregators


def analytics_dashboard(request):
    """Analytics dashboard page with all charts."""
    stats = aggregators.summary_stats()
    context = {
        "stats": stats,
    }
    return render(request, "analytics/index.html", context)
