"""
Jobs — Models for Companies, Skills, Job Posts, and User Status.
"""

from django.db import models
from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    """A company that posts jobs on LinkedIn."""

    name = models.CharField(max_length=255)
    linkedin_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    logo_url = models.URLField(max_length=1000, blank=True)
    website = models.URLField(max_length=500, blank=True)
    industry = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Skill(TimeStampedModel):
    """A skill that can be required by job postings."""

    CATEGORY_CHOICES = [
        ("Programming", "Programming"),
        ("Framework", "Framework"),
        ("Database", "Database"),
        ("DevOps", "DevOps"),
        ("Cloud", "Cloud"),
        ("Data Science", "Data Science"),
        ("Design", "Design"),
        ("Soft Skill", "Soft Skill"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default="Other")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobPost(TimeStampedModel):
    """A LinkedIn job posting."""

    WORK_TYPE_CHOICES = [
        ("Remote", "Remote"),
        ("Hybrid", "Hybrid"),
        ("On-site", "On-site"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("Entry", "Entry Level"),
        ("Mid", "Mid Level"),
        ("Senior", "Senior Level"),
        ("Lead", "Lead"),
        ("Director", "Director"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("ignored", "Ignored"),
    ]

    linkedin_job_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_posts",
    )
    location = models.CharField(max_length=255, blank=True)
    work_type = models.CharField(
        max_length=20, choices=WORK_TYPE_CHOICES, default="On-site"
    )
    description = models.TextField(blank=True)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, default="USD")
    experience_level = models.CharField(
        max_length=50,
        choices=EXPERIENCE_LEVEL_CHOICES,
        blank=True,
    )
    date_posted = models.DateField(null=True, blank=True)
    apply_url = models.URLField(max_length=1000, blank=True)
    skills = models.ManyToManyField(Skill, through="JobSkill", blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new"
    )
    is_active = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["date_posted"]),
            models.Index(fields=["work_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        company_name = self.company.name if self.company else "Unknown"
        return f"{self.title} at {company_name}"

    @property
    def salary_display(self):
        """Formatted salary range string."""
        if self.salary_min and self.salary_max:
            currency = self.salary_currency or "$"
            return f"{currency}{self.salary_min:,} – {currency}{self.salary_max:,}"
        elif self.salary_min:
            currency = self.salary_currency or "$"
            return f"From {currency}{self.salary_min:,}"
        return ""

    @property
    def is_new(self):
        """Check if job was posted in the last 24 hours."""
        from django.utils import timezone
        from datetime import timedelta

        return self.scraped_at >= timezone.now() - timedelta(hours=24)


class JobSkill(models.Model):
    """Many-to-many through table linking jobs to skills."""

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("job", "skill")

    def __str__(self):
        return f"{self.job.title} — {self.skill.name}"


class UserJobStatus(TimeStampedModel):
    """Tracks user's interaction status with a job post."""

    STATUS_CHOICES = [
        ("new", "New"),
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("ignored", "Ignored"),
    ]

    job = models.OneToOneField(
        JobPost, on_delete=models.CASCADE, related_name="user_status"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "User Job Status"
        verbose_name_plural = "User Job Statuses"

    def __str__(self):
        return f"{self.job.title} — {self.status}"
