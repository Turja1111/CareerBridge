"""
Scraper — Models for LinkedIn credentials, scrape logs, and user preferences.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import TimeStampedModel


class LinkedInCredential(TimeStampedModel):
    """Stores encrypted LinkedIn login credentials."""

    email = models.EmailField(max_length=255)
    encrypted_password = models.TextField(help_text="AES-encrypted password")
    session_data = models.TextField(
        blank=True, help_text="JSON browser cookies for session persistence"
    )
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "LinkedIn Credential"

    def __str__(self):
        return f"LinkedIn: {self.email}"

    def set_password(self, raw_password):
        """Encrypt and store the password."""
        from apps.core.utils import encrypt_value
        self.encrypted_password = encrypt_value(raw_password)

    def get_password(self):
        """Decrypt and return the password."""
        from apps.core.utils import decrypt_value
        return decrypt_value(self.encrypted_password)


class ScrapeLog(models.Model):
    """Log entry for each scraping run."""

    STATUS_CHOICES = [
        ("running", "Running"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    TRIGGER_CHOICES = [
        ("schedule", "Scheduled"),
        ("manual", "Manual"),
        ("startup", "Startup"),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    jobs_found = models.IntegerField(default=0)
    jobs_new = models.IntegerField(default=0)
    progress_message = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    triggered_by = models.CharField(
        max_length=20, choices=TRIGGER_CHOICES, default="manual"
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Scrape {self.started_at:%Y-%m-%d %H:%M} — {self.status}"

    @property
    def duration(self):
        """Return scrape duration in seconds."""
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class UserPreference(TimeStampedModel):
    """User's job search preferences for the scraper."""

    keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text='Search keywords, e.g. ["Python Developer", "Django"]',
    )
    locations = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text='Preferred locations, e.g. ["Remote", "Dhaka"]',
    )
    work_types = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text='Work type filters, e.g. ["Remote", "Hybrid"]',
    )
    experience_level = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text='Experience filters, e.g. ["Entry", "Mid", "Internship"]',
    )

    class Meta:
        verbose_name = "User Preference"

    def __str__(self):
        kw = ", ".join(self.keywords[:3]) if self.keywords else "No keywords"
        return f"Preferences: {kw}"
