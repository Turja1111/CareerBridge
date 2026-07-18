"""Application services for source-aware job persistence."""

from __future__ import annotations

from django.db import transaction

from .matching import calculate_job_match
from .models import Company, JobPost, JobSkill, Skill
from apps.scraper.parser import get_skill_category


@transaction.atomic
def upsert_job_from_source(job_data: dict) -> tuple[JobPost, bool]:
    """Create or update a job using the common multi-source schema."""
    source = job_data.get("source") or "linkedin"
    source_job_id = str(
        job_data.get("source_job_id")
        or job_data.get("linkedin_job_id")
        or job_data.get("apply_url")
        or job_data.get("source_url")
        or ""
    ).strip()

    company = None
    company_name = (job_data.get("company_name") or "").strip()
    if company_name:
        company, _ = Company.objects.get_or_create(name=company_name)

    skills = list(dict.fromkeys(job_data.get("skills") or []))
    match = calculate_job_match(
        job_data.get("title", ""),
        job_data.get("description", ""),
        job_data.get("location", ""),
        skills=skills,
    )

    defaults = {
        "source_url": job_data.get("source_url", ""),
        "linkedin_job_id": job_data.get("linkedin_job_id") or None,
        "title": job_data.get("title", ""),
        "company": company,
        "location": job_data.get("location", ""),
        "work_type": job_data.get("work_type", "On-site"),
        "description": job_data.get("description", ""),
        "salary_min": job_data.get("salary_min"),
        "salary_max": job_data.get("salary_max"),
        "salary_currency": job_data.get("salary_currency", "USD"),
        "experience_level": job_data.get("experience_level", ""),
        "date_posted": job_data.get("date_posted"),
        "application_deadline": job_data.get("application_deadline"),
        "apply_url": job_data.get("apply_url", ""),
        "match_score": match.score,
        "match_reasons": match.reasons,
        "missing_skills": match.missing_skills,
    }

    lookup = {"source": source, "source_job_id": source_job_id}
    job, created = JobPost.objects.update_or_create(defaults=defaults, **lookup)

    if skills:
        for skill_name in skills:
            skill, _ = Skill.objects.get_or_create(
                name=skill_name,
                defaults={"category": get_skill_category(skill_name)},
            )
            JobSkill.objects.get_or_create(job=job, skill=skill)

    return job, created
