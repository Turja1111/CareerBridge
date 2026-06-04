"""
Analytics — API views returning JSON data for charts.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import aggregators


@api_view(["GET"])
def top_skills_api(request):
    """Top 15 in-demand skills."""
    limit = int(request.GET.get("limit", 15))
    return Response(aggregators.top_skills(limit=limit))


@api_view(["GET"])
def jobs_over_time_api(request):
    """Daily job counts for the last N days."""
    days = int(request.GET.get("days", 30))
    data = aggregators.jobs_over_time(days=days)
    # Convert date objects to strings for JSON
    for item in data:
        item["date"] = item["date"].isoformat() if item["date"] else None
    return Response(data)


@api_view(["GET"])
def work_type_api(request):
    """Remote/Hybrid/On-site distribution."""
    return Response(aggregators.work_type_distribution())


@api_view(["GET"])
def salary_ranges_api(request):
    """Salary data by job title."""
    limit = int(request.GET.get("limit", 10))
    return Response(aggregators.salary_ranges_by_title(limit=limit))


@api_view(["GET"])
def top_companies_api(request):
    """Most active hiring companies."""
    limit = int(request.GET.get("limit", 10))
    return Response(aggregators.top_companies(limit=limit))


@api_view(["GET"])
def top_locations_api(request):
    """Top job locations."""
    limit = int(request.GET.get("limit", 10))
    return Response(aggregators.top_locations(limit=limit))


@api_view(["GET"])
def skills_by_experience_api(request):
    """Skills breakdown per experience level."""
    return Response(aggregators.skills_by_experience_level())


@api_view(["GET"])
def summary_api(request):
    """Summary KPI stats."""
    return Response(aggregators.summary_stats())
