"""
Scraper — Playwright engine for LinkedIn job scraping.

Core responsibilities:
- Auto-login to LinkedIn (with 2FA headed-mode fallback)
- Search for jobs based on user preferences
- Extract full job details from each listing
- Deduplicate and save to database
"""

import asyncio
import logging
import random
from datetime import datetime, date

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    Playwright-based LinkedIn scraper.

    Usage:
        scraper = LinkedInScraper()
        results = await scraper.run()
    """

    LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
    LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
    LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(self):
        self.headless = settings.SCRAPER_HEADLESS
        self.max_jobs = settings.SCRAPER_MAX_JOBS_PER_SEARCH
        self.delay = settings.SCRAPER_REQUEST_DELAY
        self.browser = None
        self.context = None
        self.page = None

    async def run(self):
        """
        Main entry point. Runs the full scraping pipeline.
        Returns dict with stats: {jobs_found, jobs_new, errors}
        """
        from playwright.async_api import async_playwright
        from . import session_manager
        from .models import UserPreference

        stats = {"jobs_found": 0, "jobs_new": 0, "errors": []}

        try:
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(headless=self.headless)

                # Try loading saved session
                self.context = await session_manager.load_session(self.browser)
                if self.context is None:
                    self.context = await self.browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    )

                self.page = await self.context.new_page()

                # Login
                logged_in = await self.login()
                if not logged_in:
                    stats["errors"].append("Failed to log in to LinkedIn")
                    return stats

                # Save session after successful login
                await session_manager.save_session(self.context)

                # Get user preferences
                prefs = UserPreference.objects.first()
                if not prefs or not prefs.keywords:
                    keywords = ["Python Developer"]
                    locations = ["Remote"]
                else:
                    keywords = prefs.keywords
                    locations = prefs.locations or [""]

                # Scrape for each keyword+location combination
                for keyword in keywords:
                    for location in locations:
                        try:
                            jobs = await self.search_jobs(keyword, location)
                            stats["jobs_found"] += len(jobs)

                            # Save to database
                            new_count = await self._save_jobs(jobs)
                            stats["jobs_new"] += new_count

                        except Exception as e:
                            error_msg = f"Error scraping '{keyword}' in '{location}': {e}"
                            logger.error(error_msg)
                            stats["errors"].append(error_msg)

                        # Rate limiting between searches
                        await asyncio.sleep(random.uniform(2, 4))

                await self.browser.close()

        except Exception as e:
            logger.error(f"Scraper fatal error: {e}")
            stats["errors"].append(str(e))

        return stats

    async def login(self):
        """
        Login to LinkedIn.
        Tries saved session first, then credentials, with 2FA fallback.
        """
        try:
            # Check if already logged in
            await self.page.goto(self.LINKEDIN_FEED_URL, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)

            if await self.is_logged_in():
                logger.info("Already logged in via saved session.")
                return True

            # Navigate to login page
            logger.info("Session expired. Logging in with credentials...")
            await self.page.goto(self.LINKEDIN_LOGIN_URL, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(1000)

            # Fill credentials
            email = settings.LINKEDIN_EMAIL
            password = settings.LINKEDIN_PASSWORD

            if not email or not password:
                logger.error("LinkedIn credentials not configured in .env")
                return False

            await self.page.fill("#username", email)
            await self.page.fill("#password", password)
            await self.page.click('button[type="submit"]')

            # Wait for redirect
            await self.page.wait_for_timeout(3000)

            # Check for 2FA / CAPTCHA
            if await self.is_logged_in():
                logger.info("Login successful!")
                return True

            # 2FA or CAPTCHA detected — switch to headed mode
            logger.warning("2FA/CAPTCHA detected. Manual intervention may be needed.")
            logger.warning("If running headless, set SCRAPER_HEADLESS=False and try again.")

            # Wait up to 60 seconds for manual completion
            for _ in range(12):
                await self.page.wait_for_timeout(5000)
                if await self.is_logged_in():
                    logger.info("Login completed after manual intervention.")
                    return True

            logger.error("Login timed out after 60 seconds.")
            return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def is_logged_in(self):
        """Check if the current page indicates a logged-in state."""
        try:
            url = self.page.url
            # Check if we're on the feed or any authenticated page
            if "/feed" in url or "/jobs" in url or "/mynetwork" in url:
                # Also verify there's a nav element
                nav = await self.page.query_selector('nav, [data-test-global-nav]')
                return nav is not None
            return False
        except Exception:
            return False

    async def search_jobs(self, keyword, location=""):
        """
        Search LinkedIn Jobs with given keyword and location.
        Returns list of raw job data dicts.
        """
        # Build search URL
        params = {
            "keywords": keyword,
            "location": location,
            "f_TPR": "r86400",  # Last 24 hours
            "sortBy": "DD",  # Newest first
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v)
        search_url = f"{self.LINKEDIN_JOBS_URL}?{query_string}"

        logger.info(f"Searching: {keyword} in {location}")
        await self.page.goto(search_url, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(2000)

        # Scroll to load more job cards
        for _ in range(3):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1500)

        # Extract job cards
        job_cards = await self.page.query_selector_all(
            ".jobs-search-results__list-item, .scaffold-layout__list-item"
        )

        jobs = []
        for i, card in enumerate(job_cards[: self.max_jobs]):
            try:
                job_data = await self.extract_job_detail(card)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Failed to extract job card {i}: {e}")

            # Rate limiting between cards
            await asyncio.sleep(random.uniform(0.5, self.delay))

        logger.info(f"Found {len(jobs)} jobs for '{keyword}' in '{location}'")
        return jobs

    async def extract_job_detail(self, card):
        """
        Extract all fields from a single job card.
        Clicks the card to load the detail panel, then scrapes it.
        """
        from .parser import extract_skills_from_text, parse_salary, parse_experience_level, parse_work_type

        try:
            # Click card to load detail
            await card.click()
            await self.page.wait_for_timeout(1500)

            # Extract basic info from card
            title_el = await card.query_selector(".job-card-list__title, .artdeco-entity-lockup__title")
            company_el = await card.query_selector(".job-card-container__primary-description, .artdeco-entity-lockup__subtitle")
            location_el = await card.query_selector(".job-card-container__metadata-item, .artdeco-entity-lockup__caption")

            title = await title_el.inner_text() if title_el else ""
            company_name = await company_el.inner_text() if company_el else ""
            location_text = await location_el.inner_text() if location_el else ""

            # Extract detail panel info
            detail_panel = await self.page.query_selector(
                ".jobs-search__job-details, .jobs-details"
            )

            description = ""
            apply_url = ""
            salary_text = ""

            if detail_panel:
                desc_el = await detail_panel.query_selector(
                    ".jobs-description__content, .jobs-box__html-content"
                )
                if desc_el:
                    description = await desc_el.inner_text()

                # Try to get apply URL
                apply_el = await detail_panel.query_selector(
                    'a[href*="apply"], .jobs-apply-button'
                )
                if apply_el:
                    apply_url = await apply_el.get_attribute("href") or ""

                # Try to get salary
                salary_el = await detail_panel.query_selector(
                    ".job-details-jobs-unified-top-card__job-insight--highlight, .salary-main-rail__data-value"
                )
                if salary_el:
                    salary_text = await salary_el.inner_text()

            # Extract LinkedIn job ID from URL or card
            job_id = ""
            link_el = await card.query_selector("a[href*='/jobs/view/']")
            if link_el:
                href = await link_el.get_attribute("href") or ""
                # Extract numeric ID from URL
                import re
                id_match = re.search(r'/jobs/view/(\d+)', href)
                if id_match:
                    job_id = id_match.group(1)
                if not apply_url:
                    apply_url = f"https://www.linkedin.com{href}" if href.startswith("/") else href

            if not job_id or not title:
                return None

            # Parse enriched data
            skills = extract_skills_from_text(f"{title} {description}")
            salary = parse_salary(salary_text)
            experience = parse_experience_level(f"{title} {description}")
            work_type = parse_work_type(f"{location_text} {description}")

            return {
                "linkedin_job_id": job_id,
                "title": title.strip(),
                "company_name": company_name.strip(),
                "location": location_text.strip(),
                "work_type": work_type,
                "description": description.strip(),
                "salary_min": salary["min"],
                "salary_max": salary["max"],
                "salary_currency": salary["currency"],
                "experience_level": experience,
                "apply_url": apply_url,
                "skills": skills,
                "date_posted": date.today(),
            }

        except Exception as e:
            logger.warning(f"Error extracting job detail: {e}")
            return None

    async def _save_jobs(self, jobs_data):
        """Save scraped jobs to the database, deduplicating by linkedin_job_id."""
        from apps.jobs.models import JobPost, Company, Skill, JobSkill
        from .parser import get_skill_category

        new_count = 0

        for job_data in jobs_data:
            # Check for duplicate
            if JobPost.objects.filter(linkedin_job_id=job_data["linkedin_job_id"]).exists():
                continue

            # Get or create company
            company = None
            if job_data["company_name"]:
                company, _ = Company.objects.get_or_create(
                    name=job_data["company_name"],
                    defaults={"linkedin_id": None},
                )

            # Create job post
            job = JobPost.objects.create(
                linkedin_job_id=job_data["linkedin_job_id"],
                title=job_data["title"],
                company=company,
                location=job_data["location"],
                work_type=job_data["work_type"],
                description=job_data["description"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                salary_currency=job_data["salary_currency"],
                experience_level=job_data["experience_level"],
                date_posted=job_data["date_posted"],
                apply_url=job_data["apply_url"],
            )

            # Create skill associations
            for skill_name in job_data["skills"]:
                skill, _ = Skill.objects.get_or_create(
                    name=skill_name,
                    defaults={"category": get_skill_category(skill_name)},
                )
                JobSkill.objects.get_or_create(job=job, skill=skill)

            new_count += 1

        return new_count
