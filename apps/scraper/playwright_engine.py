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
from urllib.parse import urlencode

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
    DEFAULT_KEYWORDS = [
        "Data Science",
        "Machine Learning",
        "Data Analyst",
        "Python Developer",
    ]
    DEFAULT_LOCATIONS = ["Bangladesh", "Dhaka"]
    BANGLADESH_LOCATION_TERMS = (
        "bangladesh",
        "dhaka",
        "chattogram",
        "chittagong",
        "sylhet",
        "khulna",
        "rajshahi",
        "barisal",
        "rangpur",
        "mymensingh",
    )
    WORK_TYPE_FILTERS = {
        "On-site": "1",
        "Remote": "2",
        "Hybrid": "3",
    }
    EXPERIENCE_FILTERS = {
        "Internship": "1",
        "Entry": "2",
        "Mid": "3",
        "Senior": "4",
        "Lead": "5",
        "Director": "6",
    }

    def __init__(self, log_id=None):
        self.headless = settings.SCRAPER_HEADLESS
        self.max_jobs = settings.SCRAPER_MAX_JOBS_PER_SEARCH
        self.delay = settings.SCRAPER_REQUEST_DELAY
        self.browser = None
        self.context = None
        self.page = None
        self.log_id = log_id

    async def _update_run_log(self, jobs_found=None, jobs_new=None, progress_message=None):
        if not self.log_id:
            return

        from asgiref.sync import sync_to_async
        from .models import ScrapeLog

        def sync_update():
            log = ScrapeLog.objects.filter(pk=self.log_id).first()
            if not log:
                return

            fields = []
            if jobs_found is not None:
                log.jobs_found = jobs_found
                fields.append("jobs_found")
            if jobs_new is not None:
                log.jobs_new = jobs_new
                fields.append("jobs_new")
            if progress_message is not None:
                log.progress_message = progress_message
                fields.append("progress_message")
            if fields:
                log.save(update_fields=fields)

        await sync_to_async(sync_update)()

    async def run(self):
        """
        Main entry point. Runs the full scraping pipeline.
        Returns dict with stats: {jobs_found, jobs_new, errors}
        """
        from playwright.async_api import async_playwright
        from asgiref.sync import sync_to_async
        from . import session_manager

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
                await self._update_run_log(progress_message="Logging into LinkedIn...")
                logged_in = await self.login()
                if not logged_in:
                    stats["errors"].append("Failed to log in to LinkedIn")
                    await self._update_run_log(progress_message="Login failed. Check credentials or 2FA.")
                    return stats

                await self._update_run_log(progress_message="Login successful. Starting job searches...")

                # Save session after successful login
                await session_manager.save_session(self.context)

                # Get user preferences (using sync_to_async to query Django ORM safely)
                def get_prefs_sync():
                    from .models import UserPreference
                    prefs = UserPreference.objects.first()
                    if not prefs:
                        return {
                            "keywords": self.DEFAULT_KEYWORDS,
                            "locations": self.DEFAULT_LOCATIONS,
                            "work_types": ["Remote", "Hybrid", "On-site"],
                            "experience_levels": ["Entry", "Internship"],
                        }

                    return {
                        "keywords": prefs.keywords or self.DEFAULT_KEYWORDS,
                        "locations": prefs.locations or self.DEFAULT_LOCATIONS,
                        "work_types": prefs.work_types or ["Remote", "Hybrid", "On-site"],
                        "experience_levels": prefs.experience_level or ["Entry", "Internship"],
                    }

                prefs = await sync_to_async(get_prefs_sync)()
                search_plan = self.build_search_plan(prefs)

                # Scrape each preference-aware LinkedIn search.
                for search in search_plan:
                    try:
                        keyword = search["keyword"]
                        location = search["location"]
                        work_type = search.get("work_type", "")
                        await self._update_run_log(
                            progress_message=f"Searching {work_type or 'all'} roles for '{keyword}' in '{location}'...",
                            jobs_found=stats["jobs_found"],
                            jobs_new=stats["jobs_new"],
                        )
                        jobs = await self.search_jobs(
                            keyword,
                            location,
                            work_type=work_type,
                            experience_levels=search.get("experience_levels"),
                        )
                        stats["jobs_found"] += len(jobs)

                        # Save to database (using sync_to_async)
                        new_count = await sync_to_async(self._save_jobs_sync)(jobs)
                        stats["jobs_new"] += new_count
                        await self._update_run_log(
                            progress_message=f"Saved {new_count} new Bangladesh roles for '{keyword}' in '{location}'...",
                            jobs_found=stats["jobs_found"],
                            jobs_new=stats["jobs_new"],
                        )

                    except Exception as e:
                        error_msg = f"Error scraping '{search['keyword']}' in '{search['location']}': {e}"
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)
                        await self._update_run_log(progress_message=error_msg)

                    # Rate limiting between searches
                    await asyncio.sleep(random.uniform(2, 4))

                await self.browser.close()

        except Exception as e:
            logger.error(f"Scraper fatal error: {e}")
            stats["errors"].append(str(e))

        return stats

    def build_search_plan(self, prefs):
        """Build Bangladesh-focused job and internship searches from UI prefs."""
        keywords = self._normalize_keywords(prefs.get("keywords") or [])
        locations = self._normalize_locations(prefs.get("locations") or [])
        work_types = prefs.get("work_types") or ["Remote", "Hybrid", "On-site"]
        experience_levels = self._normalize_experience_levels(
            prefs.get("experience_levels") or []
        )

        plan = []
        seen = set()
        for keyword in keywords:
            for location in locations:
                for work_type in work_types:
                    # Never search worldwide remote jobs. Keep remote searches
                    # anchored to Bangladesh so results stay locally relevant.
                    search_location = "Bangladesh" if work_type == "Remote" else location
                    item = {
                        "keyword": keyword,
                        "location": search_location,
                        "work_type": work_type,
                        "experience_levels": experience_levels,
                    }
                    key = (
                        item["keyword"].lower(),
                        item["location"].lower(),
                        item["work_type"],
                        tuple(item["experience_levels"]),
                    )
                    if key not in seen:
                        seen.add(key)
                        plan.append(item)

        logger.info("Built %s Bangladesh-focused search combinations.", len(plan))
        return plan

    def _normalize_keywords(self, keywords):
        cleaned = []
        for keyword in keywords:
            keyword = str(keyword).strip()
            if keyword:
                cleaned.append(keyword)

        # If the UI still has the original placeholder/default value, broaden it
        # to match the user's profile direction instead of scraping only Python.
        if not cleaned or cleaned == ["Python Developer"]:
            cleaned = self.DEFAULT_KEYWORDS.copy()

        expanded = []
        for keyword in cleaned:
            self._append_unique(expanded, keyword)
            lower_keyword = keyword.lower()
            if "intern" not in lower_keyword and "internship" not in lower_keyword:
                self._append_unique(expanded, f"{keyword} Internship")
                if "developer" in lower_keyword:
                    self._append_unique(expanded, keyword.replace("Developer", "Intern"))

        return expanded

    def _normalize_locations(self, locations):
        normalized = []
        for location in locations:
            location = str(location).strip()
            if not location:
                continue
            if location.lower() == "remote":
                self._append_unique(normalized, "Bangladesh")
                continue
            if location.lower() == "dhaka":
                location = "Dhaka, Bangladesh"
            self._append_unique(normalized, location)

        self._append_unique(normalized, "Bangladesh")
        self._append_unique(normalized, "Dhaka, Bangladesh")
        return normalized

    def _normalize_experience_levels(self, experience_levels):
        normalized = []
        if isinstance(experience_levels, str):
            experience_levels = [experience_levels]

        for level in experience_levels:
            level = str(level).strip()
            if level:
                self._append_unique(normalized, level)

        if not normalized:
            normalized = ["Internship", "Entry"]

        # Entry-level preferences should include internships too.
        if "Entry" in normalized:
            self._append_unique(normalized, "Internship")
        return normalized

    def _append_unique(self, values, value):
        if value and value not in values:
            values.append(value)

    async def login(self):
        """
        Login to LinkedIn.
        Tries saved session first, then credentials, with 2FA fallback.
        """
        try:
            # Check if already logged in
            await self.page.goto(self.LINKEDIN_FEED_URL, wait_until="domcontentloaded")

            if await self.wait_for_logged_in(timeout_ms=15000):
                logger.info("Already logged in via saved session.")
                return True

            # Navigate to login page
            logger.info("Session expired. Logging in with credentials...")
            if "/login" not in self.page.url:
                await self.page.goto(self.LINKEDIN_LOGIN_URL, wait_until="domcontentloaded")

            # LinkedIn sometimes restores the saved session after briefly showing
            # the login redirect URL. Give that redirect a chance before filling
            # credentials, otherwise Playwright can wait for a vanished form.
            if await self.wait_for_logged_in(timeout_ms=5000):
                logger.info("Login completed via delayed session redirect.")
                return True

            try:
                await self.page.wait_for_selector("#username", timeout=15000)
            except Exception:
                if await self.wait_for_logged_in(timeout_ms=5000):
                    logger.info("Login completed before credentials were needed.")
                    return True
                raise

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
            if await self.wait_for_logged_in(timeout_ms=15000):
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

    async def wait_for_logged_in(self, timeout_ms=10000):
        """Poll for LinkedIn's authenticated UI/URL while redirects settle."""
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while asyncio.get_running_loop().time() < deadline:
            if await self.is_logged_in():
                return True
            await self.page.wait_for_timeout(500)
        return await self.is_logged_in()

    async def is_logged_in(self):
        """Check if the current page indicates a logged-in state."""
        try:
            url = self.page.url
            logger.info(f"Checking login status. Current URL: {url}")
            if "/feed" in url or "/jobs" in url or "/mynetwork" in url:
                logger.info("Login confirmed via authenticated URL.")
                return True
            
            nav = await self.page.query_selector('nav, [data-test-global-nav], .global-nav')
            if nav is not None:
                logger.info("Login confirmed via global navigation element.")
                return True
                
            return False
        except Exception as e:
            logger.warning(f"Error checking login status: {e}")
            return False

    async def search_jobs(self, keyword, location="", work_type="", experience_levels=None):
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
        if work_type in self.WORK_TYPE_FILTERS:
            params["f_WT"] = self.WORK_TYPE_FILTERS[work_type]

        experience_filters = [
            self.EXPERIENCE_FILTERS[level]
            for level in (experience_levels or [])
            if level in self.EXPERIENCE_FILTERS
        ]
        if experience_filters:
            params["f_E"] = ",".join(dict.fromkeys(experience_filters))

        query_string = urlencode({k: v for k, v in params.items() if v})
        search_url = f"{self.LINKEDIN_JOBS_URL}?{query_string}"

        logger.info(f"Searching: {keyword} in {location} ({work_type or 'all work types'})")
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
                    if self._is_bangladesh_job(job_data):
                        jobs.append(job_data)
                    else:
                        logger.info(
                            "Skipping non-Bangladesh result: %s | %s",
                            job_data.get("title", ""),
                            job_data.get("location", ""),
                        )
            except Exception as e:
                logger.warning(f"Failed to extract job card {i}: {e}")

            # Rate limiting between cards
            await asyncio.sleep(random.uniform(0.5, self.delay))

        logger.info(f"Found {len(jobs)} jobs for '{keyword}' in '{location}'")
        return jobs

    def _is_bangladesh_job(self, job_data):
        """Only save jobs whose visible LinkedIn location is Bangladesh-based."""
        location = (job_data.get("location") or "").lower()
        return any(term in location for term in self.BANGLADESH_LOCATION_TERMS)

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

    def _save_jobs_sync(self, jobs_data):
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
