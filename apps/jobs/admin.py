"""
Jobs — Django Admin configuration.
"""

from django.contrib import admin
from .models import Company, Skill, JobPost, JobSkill, UserJobStatus


class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "website", "created_at")
    search_fields = ("name", "industry")
    list_filter = ("industry",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "created_at")
    search_fields = ("name",)
    list_filter = ("category",)


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "source",
        "match_score",
        "location",
        "work_type",
        "status",
        "experience_level",
        "date_posted",
        "is_active",
    )
    list_filter = ("source", "work_type", "status", "experience_level", "is_active")
    search_fields = (
        "title",
        "company__name",
        "location",
        "description",
        "source_job_id",
        "linkedin_job_id",
    )
    date_hierarchy = "date_posted"
    inlines = [JobSkillInline]
    readonly_fields = ("scraped_at", "created_at", "updated_at")


@admin.register(UserJobStatus)
class UserJobStatusAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "follow_up_on", "updated_at")
    list_filter = ("status",)
