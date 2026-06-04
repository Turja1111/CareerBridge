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
        "location",
        "work_type",
        "status",
        "experience_level",
        "date_posted",
        "is_active",
    )
    list_filter = ("work_type", "status", "experience_level", "is_active")
    search_fields = ("title", "company__name", "location", "description")
    date_hierarchy = "date_posted"
    inlines = [JobSkillInline]
    readonly_fields = ("scraped_at", "created_at", "updated_at")


@admin.register(UserJobStatus)
class UserJobStatusAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "updated_at")
    list_filter = ("status",)
