"""Utility helpers for Bangladesh-safe job filtering and recommendation quality."""

import re
from typing import Iterable

BANGLADESH_TERMS = (
    "bangladesh", "dhaka", "chattogram", "chittagong", "khulna", "rajshahi",
    "rangpur", "sylhet", "barisal", "cumilla", "gazipur", "narayanganj", "bogura",
)

ALLOWED_DEGREE_TERMS = (
    "computer science", "computer engineering", "software engineering", "information technology",
    "cyber security", "data science", "artificial intelligence", "machine learning",
    "devops", "cloud computing", "networking", "database administration", "qa", "testing",
    "ui/ux", "technology internship", "internship", "graduate trainee", "bank", "bba",
    "business analyst", "business intelligence", "it-related", "it related", "cse", "cs", "it",
)

EXCLUDED_DEGREE_TERMS = (
    "mechanical engineering", "industrial engineering", "civil engineering", "electrical",
    "architecture", "diploma", "hsc", "ssc", "office assistant", "office staff",
    "support staff", "receptionist", "call center", "video editor", "graphic designer",
    "data entry", "sales representative", "field officer", "labor", "general labor",
)

EXPIRED_TERMS = (
    "closed", "expired", "no longer accepting", "application deadline", "deadline passed",
    "removed", "unavailable", "not accepting applications", "position filled", "inactive",
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).lower().strip()


def is_bangladesh_eligible(location: str, description: str, company_name: str) -> bool:
    """Keep Bangladesh-relevant roles and Bangladesh-friendly remote roles only."""
    text = _normalize_text(" ".join([location or "", description or "", company_name or ""]))

    if any(term in text for term in BANGLADESH_TERMS):
        return True

    if "remote" in text and any(term in text for term in ("bangladeshi", "bangladesh")):
        return True

    return False


def is_degree_relevant(title: str, description: str) -> bool:
    """Allow only technology, business, and graduate-trainee style paths."""
    text = _normalize_text(" ".join([title or "", description or ""]))

    if any(term in text for term in EXCLUDED_DEGREE_TERMS):
        return False

    if any(term in text for term in ALLOWED_DEGREE_TERMS):
        return True

    # The dashboard should stay focused on professional roles; fall back to tech-safe keywords.
    return any(term in text for term in ("software", "developer", "analyst", "trainee", "intern", "it", "technology"))


def seems_expired(title: str, description: str, location: str) -> bool:
    """Filter out obviously closed, expired, or removed listings."""
    text = _normalize_text(" ".join([title or "", description or "", location or ""]))
    return any(term in text for term in EXPIRED_TERMS)


def relevance_score(title: str, description: str, location: str, skills_text: str) -> int:
    """Approximate relevance score for ranking recommendations."""
    text = _normalize_text(" ".join([title or "", description or "", location or "", skills_text or ""]))
    score = 40

    if is_bangladesh_eligible(location, description, ""):
        score += 20
    if is_degree_relevant(title, description):
        score += 20
    if any(term in text for term in ("python", "django", "sql", "aws", "docker", "react", "javascript", "devops", "cloud")):
        score += 10
    if any(term in text for term in ("intern", "graduate trainee", "bank", "bba", "business analyst", "business intelligence")):
        score += 10

    return min(100, score)


def is_relevant_job(job) -> bool:
    """Return True when the job should be recommended to the dashboard."""
    if not job.is_active:
        return False
    if seems_expired(job.title, job.description, job.location):
        return False
    if job.status == "ignored":
        return False
    if not is_bangladesh_eligible(job.location, job.description, job.company.name if job.company else ""):
        return False
    if not is_degree_relevant(job.title, job.description):
        return False
    return relevance_score(job.title, job.description, job.location, " ".join(skill.name for skill in job.skills.all())) >= 70
