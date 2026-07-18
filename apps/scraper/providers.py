"""Provider abstractions for collecting jobs from multiple platforms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
import re
from typing import Protocol
from urllib.parse import urljoin, urlencode, urlparse

from django.conf import settings

from .parser import extract_skills_from_text, parse_experience_level, parse_salary, parse_work_type

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchRequest:
    keyword: str
    location: str = "Bangladesh"
    work_type: str = ""
    experience_levels: tuple[str, ...] = ()


class JobProvider(Protocol):
    source: str
    label: str

    def build_search_url(self, request: SearchRequest) -> str:
        """Return a platform search URL for a request."""


class BDJobsProvider:
    """Playwright-backed BDJobs collection provider.

    Scrapes both logged-in and anonymous job listings from BDJobs.com.
    Data is normalized into CareerBridge's common job schema before saving.
    """

    source = "bdjobs"
    label = "BDJobs"

    # BDJobs has two domains — jobs.bdjobs.com for search, bdjobs.com for home
    # All detail URLs are on jobs.bdjobs.com, so we use that as our base.
    jobs_base_url = "https://jobs.bdjobs.com"
    home_base_url = "https://bdjobs.com"
    search_url = "https://jobs.bdjobs.com/jobsearch.asp"
    login_url = "https://mybdjobs.bdjobs.com/mybdjobs/signin.asp"

    # Job detail URL patterns used by BDJobs (match any of these hrefs)
    DETAIL_LINK_SELECTORS = (
        'a[href*="jobdetails.asp"]',
        'a[href*="jobdetail.asp"]',
        'a[href*="job-detail"]',
        'a[href*="jobsearch-detail"]',
        'a[href*="/job/"]',
        'a[href*="jobdetails"]',
    )

    def build_search_url(self, request: SearchRequest) -> str:
        params = {
            "fcatId": "",
            "icatId": "",
            "txtsearch": request.keyword,
            "location": request.location,
        }
        return f"{self.search_url}?{urlencode({k: v for k, v in params.items() if v})}"

    def _resolve_url(self, href: str) -> str:
        """Resolve a BDJobs href to an absolute URL on the correct domain."""
        if not href:
            return ""
        # Already absolute
        if href.startswith("http://") or href.startswith("https://"):
            return href
        # Relative path — attach the jobs subdomain as that's where details live
        return urljoin(self.jobs_base_url, href)

    async def login(self, page) -> bool:
        """Log in when credentials are configured; continue anonymously otherwise."""
        email = getattr(settings, "BDJOBS_EMAIL", "")
        password = getattr(settings, "BDJOBS_PASSWORD", "")
        if not email or not password:
            logger.info("BDJobs credentials not configured. Scraping public listings only.")
            return True

        try:
            await page.goto(self.login_url, wait_until="domcontentloaded", timeout=45_000)
            await page.wait_for_timeout(2000)

            # Try BDJobs-specific selectors first, then generic fallbacks
            email_selector = await self._first_visible_selector(
                page,
                [
                    '#txtUserName',
                    'input[name="txtUserName"]',
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[name*="user" i]',
                    'input[type="text"]',
                ],
            )
            password_selector = await self._first_visible_selector(
                page,
                [
                    '#txtPassword',
                    'input[name="txtPassword"]',
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[name*="pass" i]',
                ],
            )

            if not email_selector or not password_selector:
                logger.warning("BDJobs login form not detected. Continuing without login.")
                return True

            await page.fill(email_selector, email)
            await page.fill(password_selector, password)

            submit_selector = await self._first_visible_selector(
                page,
                [
                    '#btnLogin',
                    'input[name="btnLogin"]',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Sign in")',
                    'button:has-text("Login")',
                ],
            )
            if submit_selector:
                await page.click(submit_selector)
                await page.wait_for_timeout(3000)

            # Verify login by looking for authenticated UI elements
            logged_in = await self._first_visible_selector(
                page,
                [
                    '.loggedin',
                    '#divMyBDJobs',
                    'a[href*="logout"]',
                    'a[href*="signout"]',
                    '.user-profile',
                    'a[href*="mybdjobs"]',
                ],
            )
            if logged_in:
                logger.info("BDJobs login successful.")
            else:
                logger.warning(
                    "BDJobs login could not be verified — continuing as public user."
                )
            return True

        except Exception as exc:
            logger.warning("BDJobs login failed, continuing public scrape: %s", exc)
            return True

    async def search_jobs(self, page, request: SearchRequest, max_jobs: int = 30) -> list[dict]:
        """Search BDJobs and return a list of normalized job dicts."""
        search_url = self.build_search_url(request)
        logger.info("BDJobs: searching %s", search_url)

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as exc:
            logger.error("BDJobs: failed to load search page: %s", exc)
            return []

        await page.wait_for_timeout(2500)

        # Wait for any job-related content to load
        try:
            await page.wait_for_selector(
                'a[href*="job"], .job-list-item, .sout-jobs-wrapper, .job-card, [class*="job"]',
                timeout=10_000,
            )
        except Exception:
            logger.debug("BDJobs: no job elements detected within 10s, proceeding with scroll.")

        # Scroll to trigger lazy-loaded results
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)

        # Build a combined CSS selector for all known detail link patterns
        combined_selector = ", ".join(self.DETAIL_LINK_SELECTORS)
        links = await page.query_selector_all(combined_selector)

        if not links:
            # Debug: log page title and URL to understand what's happening
            try:
                page_title = await page.title()
                page_url = page.url
                body_text = await page.evaluate("document.body?.innerText?.substring(0, 500) || ''")
                logger.warning(
                    "BDJobs: no job links found for '%s'. "
                    "Page title: '%s', URL: '%s'. Body preview: '%s'",
                    request.keyword, page_title, page_url, body_text[:200],
                )
            except Exception:
                logger.warning(
                    "BDJobs: no job links found for '%s'. Page structure may have changed.",
                    request.keyword,
                )
            return []

        seen_urls: set[str] = set()
        jobs: list[dict] = []

        for link in links:
            if len(jobs) >= max_jobs:
                break
            try:
                href = (await link.get_attribute("href") or "").strip()
                url = self._resolve_url(href)

                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Walk up the DOM to find the enclosing card
                card = await link.evaluate_handle(
                    """node => node.closest(
                        '.sout-jobs-wrapper, .job-list-item, .job-card,
                         .job-item, .job-wrapper, .job_list, tr, li, div'
                    ) || node"""
                )
                card_text = (await card.evaluate("node => node.innerText || ''")).strip()

                # Prefer link inner text as title; fall back to first card line
                title = (await link.inner_text()).strip()
                if not title or len(title) < 3:
                    title = self._title_from_text(card_text)

                if not title:
                    continue  # Skip cards without a recognisable title

                company = self._company_from_text(card_text, title)
                deadline = self._deadline_from_text(card_text)
                salary = parse_salary(card_text)
                skills = extract_skills_from_text(f"{title} {card_text}")
                job_id = self._job_id_from_url(url)

                jobs.append(
                    self._normalize_card(
                        {
                            "id": job_id,
                            "url": url,
                            "title": title,
                            "company": company,
                            "location": self._location_from_text(card_text),
                            "description": card_text,
                            "salary_min": salary["min"],
                            "salary_max": salary["max"],
                            # BDJobs is a Bangladeshi portal — override USD default
                            "salary_currency": salary["currency"] if salary["currency"] != "USD" else "BDT",
                            "deadline": deadline,
                            "skills": skills,
                            "experience_level": parse_experience_level(f"{title} {card_text}"),
                            "work_type": parse_work_type(card_text),
                        }
                    )
                )

            except Exception as exc:
                logger.warning("BDJobs: failed to parse job card: %s", exc)

        logger.info(
            "BDJobs: found %d jobs for keyword '%s'", len(jobs), request.keyword
        )
        return jobs

    # ──────────────────────────────────────────
    #  Private helpers
    # ──────────────────────────────────────────

    def _normalize_card(self, card: dict) -> dict:
        """Normalise a parsed BDJobs card into CareerBridge's common schema."""
        return {
            "source": self.source,
            "source_job_id": str(card.get("id") or card.get("url") or ""),
            "source_url": card.get("url", ""),
            "title": card.get("title", ""),
            "company_name": card.get("company", ""),
            "location": card.get("location", ""),
            "description": card.get("description", ""),
            "salary_min": card.get("salary_min"),
            "salary_max": card.get("salary_max"),
            "salary_currency": card.get("salary_currency", "BDT"),
            "application_deadline": card.get("deadline"),
            "apply_url": card.get("url", ""),
            "skills": card.get("skills", []),
            "date_posted": date.today(),
            "experience_level": card.get("experience_level", ""),
            "work_type": card.get("work_type", "On-site"),
        }

    async def _first_visible_selector(self, page, selectors: list[str]) -> str:
        """Return the first selector that matches a *visible* element."""
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    return selector
            except Exception:
                continue
        return ""

    def _job_id_from_url(self, url: str) -> str:
        """Extract a numeric BDJobs job ID from a URL, or fall back to the URL itself."""
        # BDJobs URLs look like: jobdetails.asp?id=1234567&fcatId=...
        id_match = re.search(r"[?&]id=(\d+)", url, re.IGNORECASE)
        if id_match:
            return id_match.group(1)
        # Generic fallback: take any 5+ digit number
        fallback = re.search(r"(\d{5,})", url)
        return fallback.group(1) if fallback else url

    def _title_from_text(self, text: str) -> str:
        """Pick the first non-empty line as a candidate job title."""
        for line in text.splitlines():
            line = line.strip()
            if line and len(line) >= 5:
                return line
        return ""

    def _company_from_text(self, text: str, title: str) -> str:
        """
        Heuristically extract the company name.
        Skips the title line and lines that look like metadata.
        """
        SKIP_TERMS = (
            "deadline", "salary", "vacancy", "vacancies",
            "location", "experience", "apply", "job type",
            "category", "published", "view", "days left",
        )
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            if line == title:
                continue
            lower = line.lower()
            if any(term in lower for term in SKIP_TERMS):
                continue
            # Skip very short lines (likely icons/numbers) and very long ones (descriptions)
            if 3 <= len(line) <= 80:
                return line
        return ""

    def _location_from_text(self, text: str) -> str:
        """
        Extract a Bangladesh location from card text.
        Prefers an explicit 'Location:' label; otherwise scans for city names.
        """
        for line in text.splitlines():
            if re.search(r"location\s*:", line, re.IGNORECASE):
                return line.split(":", 1)[-1].strip()

        CITY_TERMS = (
            "dhaka", "chattogram", "chittagong", "sylhet",
            "khulna", "rajshahi", "barisal", "rangpur",
            "mymensingh", "comilla", "narayanganj", "bangladesh",
        )
        lower = text.lower()
        found = [t.title() for t in CITY_TERMS if t in lower]
        return ", ".join(dict.fromkeys(found)) or "Bangladesh"

    def _deadline_from_text(self, text: str):
        """
        Parse an application deadline date from card text.
        Returns a date object or None.
        """
        patterns = [
            r"(?:deadline|last date|apply before|application deadline)\s*:?\s*"
            r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
            r"(\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).replace(",", "").strip()
            for fmt in (
                "%B %d %Y", "%b %d %Y",
                "%d %B %Y", "%d %b %Y",
                "%d/%m/%Y", "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None


AVAILABLE_PROVIDERS = {
    "bdjobs": BDJobsProvider(),
}
