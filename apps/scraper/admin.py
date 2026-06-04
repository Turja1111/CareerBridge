"""
Scraper — Django Admin configuration.
"""

from django.contrib import admin
from .models import LinkedInCredential, ScrapeLog, UserPreference


@admin.register(LinkedInCredential)
class LinkedInCredentialAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "last_login", "created_at")
    readonly_fields = ("encrypted_password", "session_data", "created_at", "updated_at")


@admin.register(ScrapeLog)
class ScrapeLogAdmin(admin.ModelAdmin):
    list_display = (
        "started_at",
        "finished_at",
        "status",
        "jobs_found",
        "jobs_new",
        "triggered_by",
    )
    list_filter = ("status", "triggered_by")
    readonly_fields = ("started_at",)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("keywords", "locations", "work_types", "experience_level", "updated_at")
