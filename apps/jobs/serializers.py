"""
Jobs — DRF Serializers for API endpoints.
"""

from rest_framework import serializers
from .models import Company, Skill, JobPost, UserJobStatus


class CompanySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Company
        fields = ["id", "name", "linkedin_id", "logo_url", "website", "industry", "job_count"]


class SkillSerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Skill
        fields = ["id", "name", "category", "job_count"]


class JobPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job listing."""

    company_name = serializers.CharField(source="company.name", read_only=True, default="")
    company_logo = serializers.CharField(source="company.logo_url", read_only=True, default="")
    skills = SkillSerializer(many=True, read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    salary_display = serializers.CharField(read_only=True)

    class Meta:
        model = JobPost
        fields = [
            "id",
            "source",
            "source_label",
            "source_job_id",
            "linkedin_job_id",
            "title",
            "company_name",
            "company_logo",
            "location",
            "work_type",
            "salary_display",
            "experience_level",
            "date_posted",
            "application_deadline",
            "apply_url",
            "canonical_url",
            "skills",
            "status",
            "match_score",
            "match_reasons",
            "missing_skills",
            "is_active",
            "is_new",
            "scraped_at",
        ]


class JobPostDetailSerializer(serializers.ModelSerializer):
    """Full serializer with description for job detail view."""

    company = CompanySerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    salary_display = serializers.CharField(read_only=True)

    class Meta:
        model = JobPost
        fields = [
            "id",
            "source",
            "source_label",
            "source_job_id",
            "source_url",
            "linkedin_job_id",
            "title",
            "company",
            "location",
            "work_type",
            "description",
            "salary_min",
            "salary_max",
            "salary_currency",
            "salary_display",
            "experience_level",
            "date_posted",
            "application_deadline",
            "apply_url",
            "canonical_url",
            "skills",
            "status",
            "match_score",
            "match_reasons",
            "missing_skills",
            "application_notes",
            "resume_version",
            "applied_at",
            "follow_up_on",
            "is_active",
            "is_new",
            "scraped_at",
            "updated_at",
        ]


class JobStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating job status."""

    status = serializers.ChoiceField(choices=JobPost.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    resume_version = serializers.CharField(required=False, allow_blank=True, default="")
    follow_up_on = serializers.DateField(required=False, allow_null=True)
