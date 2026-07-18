"""Job matching helpers for ranking roles against the user's search profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from apps.scraper.parser import extract_skills_from_text


DEFAULT_TARGET_SKILLS = {
    "Python",
    "Django",
    "SQL",
    "PostgreSQL",
    "JavaScript",
    "React",
    "Machine Learning",
    "Data Analysis",
    "Pandas",
    "Docker",
    "Git",
}

ENTRY_TERMS = ("intern", "internship", "entry", "junior", "trainee", "graduate")


@dataclass(frozen=True)
class MatchResult:
    score: int
    reasons: list[str]
    missing_skills: list[str]


def calculate_job_match(
    title: str,
    description: str,
    location: str = "",
    skills: Iterable[str] | None = None,
    target_skills: Iterable[str] | None = None,
) -> MatchResult:
    """Return a simple, explainable fit score for a job."""
    text = " ".join([title or "", description or "", location or ""]).lower()
    detected_skills = set(skills or extract_skills_from_text(f"{title} {description}"))
    desired_skills = set(target_skills or DEFAULT_TARGET_SKILLS)
    matched_skills = sorted(detected_skills & desired_skills)
    missing_skills = sorted(desired_skills - detected_skills)[:6]

    score = 35
    reasons: list[str] = []

    if matched_skills:
        skill_score = min(35, len(matched_skills) * 6)
        score += skill_score
        reasons.append(f"Matches {len(matched_skills)} target skills")

    if any(term in text for term in ("bangladesh", "dhaka", "remote", "hybrid")):
        score += 15
        reasons.append("Location matches Bangladesh or remote preference")

    if any(term in text for term in ENTRY_TERMS):
        score += 10
        reasons.append("Good fit for internship or early-career search")

    if any(term in text for term in ("data", "python", "developer", "software", "analyst")):
        score += 5
        reasons.append("Role direction matches your target career path")

    return MatchResult(score=min(score, 100), reasons=reasons[:4], missing_skills=missing_skills)
