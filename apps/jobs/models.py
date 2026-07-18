"""
Jobs — Models for Companies, Skills, Job Posts, and User Status.
"""

import re

from django.db import models
from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    """A company that posts jobs across tracked platforms."""

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
    """A job posting collected from LinkedIn, BDJobs, or another source."""

    SOURCE_CHOICES = [
        ("linkedin", "LinkedIn"),
        ("bdjobs", "BDJobs"),
        ("chakri", "Chakri"),
        ("skill_jobs", "Skill.jobs"),
        ("company", "Company Career Page"),
        ("manual", "Manual Import"),
        ("other", "Other"),
    ]

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
        ("shortlisted", "Shortlisted"),
        ("applied", "Applied"),
        ("interview", "Interview"),
        ("rejected", "Rejected"),
        ("offer", "Offer"),
        ("ignored", "Ignored"),
    ]

    source = models.CharField(
        max_length=30, choices=SOURCE_CHOICES, default="linkedin", db_index=True
    )
    source_job_id = models.CharField(max_length=120, blank=True, db_index=True)
    source_url = models.URLField(max_length=1000, blank=True)
    linkedin_job_id = models.CharField(
        max_length=50, unique=True, null=True, blank=True
    )
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
    application_deadline = models.DateField(null=True, blank=True)
    apply_url = models.URLField(max_length=1000, blank=True)
    skills = models.ManyToManyField(Skill, through="JobSkill", blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new"
    )
    match_score = models.PositiveSmallIntegerField(default=0)
    match_reasons = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    application_notes = models.TextField(blank=True)
    resume_version = models.CharField(max_length=120, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    follow_up_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scraped_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_job_id"],
                condition=~models.Q(source_job_id=""),
                name="unique_job_per_source",
            )
        ]
        indexes = [
            models.Index(fields=["source", "source_job_id"]),
            models.Index(fields=["date_posted"]),
            models.Index(fields=["application_deadline"]),
            models.Index(fields=["work_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["match_score"]),
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
            return f"{currency}{self.salary_min:,} - {currency}{self.salary_max:,}"
        elif self.salary_min:
            currency = self.salary_currency or "$"
            return f"From {currency}{self.salary_min:,}"
        return ""

    @property
    def bullet_lines(self):
        """Return job description as readable bullet points for the UI."""
        text = self.description or ""
        lines = []
        for raw in text.splitlines():
            cleaned = re.sub(r"^\s*[-*\u2022]\s*", "", raw).strip()
            if cleaned:
                lines.append(cleaned)

        if lines:
            return lines

        fallback = re.split(r"(?<=[.;])\s+", text)
        return [item.strip(" \u2022-") for item in fallback if item.strip()]

    @property
    def bullet_sections(self):
        """Parse `description` into titled sections with concise bullet points.

        Returns a list of (title, [bullets]) preserving order. Headings detected
        include common labels like 'Responsibilities', 'Qualifications',
        'Educational Requirements', 'Additional Requirements', and 'Preferred Skills'.
        Falls back to a single 'Overview' section.
        """
        text = (self.description or "").strip()
        if not text:
            return []

        # Normalize bullets and separators
        norm = text.replace('\r', '\n')
        norm = norm.replace('\u2022', '\n\u2022')
        # Split into raw lines
        raw_lines = [ln.strip() for ln in norm.splitlines() if ln.strip()]

        # Heading detection regex (case-insensitive)
        heading_re = re.compile(
            r'^(?P<h>about the job|job description|job responsibilities|role responsibilities|responsibilities|qualifications|educational requirements|additional requirements|preferred skills|requirements|skills):?$',
            re.IGNORECASE,
        )

        sections = []
        current_title = 'Overview'
        current_buf = []

        def flush_section():
            nonlocal current_title, current_buf
            if not current_buf:
                return
            # Convert buffer text to bullets by splitting sentences and semicolons
            bullets = []
            for item in current_buf:
                # If item starts with a bullet marker, strip it
                cleaned = re.sub(r'^[-*\u2022]\s*', '', item).strip()
                # Split by semicolon or sentence boundary
                parts = re.split(r'[;\u2022]|(?<=[.?!])\s+', cleaned)
                for p in parts:
                    s = p.strip(' \u2022-:')
                    if not s:
                        continue
                    # Shorten extremely long sentences by breaking on commas
                    if len(s) > 140 and ',' in s:
                        subparts = [sp.strip() for sp in s.split(',') if sp.strip()]
                        for sp in subparts:
                            if sp and len(sp) <= 140:
                                bullets.append(sp)
                    else:
                        bullets.append(s)

            if bullets:
                sections.append((current_title, bullets))
            current_buf = []

        for line in raw_lines:
            m = heading_re.match(line)
            if m:
                # Flush previous
                flush_section()
                current_title = m.group('h').title()
                continue
            # If line looks like a short heading (ends with ':'), treat as heading
            if line.endswith(':') and len(line) < 60:
                flush_section()
                current_title = line.rstrip(':').title()
                continue
            current_buf.append(line)

        # Final flush
        flush_section()

        # If everything ended up in 'Overview' and the single section has long paragraphs,
        # split into shorter bullets by sentences
        if len(sections) == 1 and sections[0][0] == 'Overview':
            title, bullets = sections[0]
            if len(bullets) == 1 and len(bullets[0]) > 180:
                parts = re.split(r'(?<=[.;])\s+', bullets[0])
                sections[0] = (title, [p.strip(' \u2022-') for p in parts if p.strip()])

        return sections
    @property
    def is_new(self):
        """Check if job was posted in the last 24 hours."""
        from django.utils import timezone
        from datetime import timedelta

        return self.scraped_at >= timezone.now() - timedelta(hours=24)

    @property
    def source_label(self):
        """Human-readable platform label for badges and APIs."""
        return dict(self.SOURCE_CHOICES).get(self.source, self.source.title())

    @property
    def canonical_url(self):
        """Best outbound URL for applying or reviewing the original posting."""
        return self.apply_url or self.source_url


class JobSkill(models.Model):
    """Many-to-many through table linking jobs to skills."""

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("job", "skill")

    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"


class UserJobStatus(TimeStampedModel):
    """Tracks user's interaction status with a job post."""

    STATUS_CHOICES = [
        ("new", "New"),
        ("saved", "Saved"),
        ("shortlisted", "Shortlisted"),
        ("applied", "Applied"),
        ("interview", "Interview"),
        ("rejected", "Rejected"),
        ("offer", "Offer"),
        ("ignored", "Ignored"),
    ]

    job = models.OneToOneField(
        JobPost, on_delete=models.CASCADE, related_name="user_status"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True)
    resume_version = models.CharField(max_length=120, blank=True)
    follow_up_on = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "User Job Status"
        verbose_name_plural = "User Job Statuses"

    def __str__(self):
        return f"{self.job.title} - {self.status}"
