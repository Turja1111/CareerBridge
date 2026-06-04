"""
Jobs — DRF API views for job data.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import JobPost
from .serializers import JobPostListSerializer, JobPostDetailSerializer, JobStatusUpdateSerializer
from .filters import JobPostFilter


class JobPostViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for job posts with filtering and search."""

    queryset = (
        JobPost.objects.filter(is_active=True)
        .select_related("company")
        .prefetch_related("skills")
    )
    filterset_class = JobPostFilter
    search_fields = ["title", "company__name", "location", "description"]
    ordering_fields = ["scraped_at", "date_posted", "title"]
    ordering = ["-scraped_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobPostDetailSerializer
        return JobPostListSerializer


@api_view(["PATCH"])
def update_job_status(request, pk):
    """Update job status (saved/applied/ignored)."""
    try:
        job = JobPost.objects.get(pk=pk)
    except JobPost.DoesNotExist:
        return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = JobStatusUpdateSerializer(data=request.data)
    if serializer.is_valid():
        job.status = serializer.validated_data["status"]
        job.save(update_fields=["status", "updated_at"])
        return Response({"status": job.status, "id": job.id})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def new_jobs(request):
    """Return jobs added in the last 24 hours."""
    cutoff = timezone.now() - timedelta(hours=24)
    jobs = (
        JobPost.objects.filter(is_active=True, scraped_at__gte=cutoff)
        .select_related("company")
        .prefetch_related("skills")
    )
    serializer = JobPostListSerializer(jobs, many=True)
    return Response(serializer.data)
