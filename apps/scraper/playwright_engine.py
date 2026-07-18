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
import re
from datetime import datetime, date
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ScrapeCancelledException(Exception):
    """Raised when a scrape job is manually cancelled by the user."""
    pass


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

    # ── Selectors (multiple fallbacks for each — LinkedIn updates its DOM often)
    CARD_SELECTORS = [
        ".jobs-search-results__list-item",
        ".scaffold-layout__list-item",
        '[data-occludable-job-id]',
        ".job-card-container",
        "li.jobs-search-results__list-item",
    ]
    TITLE_SELECTORS = [
        ".job-card-list__title",
        ".artdeco-entity-lockup__title",
        ".job-card-container__link",
        '[class*="job-card"] a[class*="title"]',
        "a.job-card-list__title--link",
        "strong",
    ]
    COMPANY_SELECTORS = [
        ".job-card-container__primary-description",
        ".artdeco-entity-lockup__subtitle",
        ".job-card-container__company-name",
        '[class*="job-card"] [class*="company"]',
        ".job-card-container__metadata-item:first-child",
    ]
    LOCATION_SELECTORS = [
        ".job-card-container__metadata-item",
        ".artdeco-entity-lockup__caption",
        '[class*="job-card"] [class*="location"]',
        ".job-card-container__metadata-wrapper li:first-child",
    ]
    DETAIL_PANEL_SELECTORS = [
        ".jobs-search__job-details",
        ".jobs-details",
        ".job-view-layout",
        "[class*='jobs-details']",
        ".scaffold-layout__detail",
    ]
    DESCRIPTION_SELECTORS = [
        ".jobs-description__content",
        ".jobs-box__html-content",
        "[class*='jobs-description']",
        ".jobs-description-content__text",
        "#job-details",
    ]
    SALARY_SELECTORS = [
        ".job-details-jobs-unified-top-card__job-insight--highlight",
        ".salary-main-rail__data-value",
        "[class*='salary']",
        "[class*='compensation']",
        ".jobs-unified-top-card__job-insight",
    ]

    def __init__(self, log_id=None):
        self.headless = settings.SCRAPER_HEADLESS
        self.max_jobs = settings.SCRAPER_MAX_JOBS_PER_SEARCH
        self.delay = settings.SCRAPER_REQUEST_DELAY
        self.browser = None
        self.context = None
        self.page = None
        self.log_id = log_id

    # ──────────────────────────────────────────────────────────────────────────
    #  Log helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _check_cancellation(self):
        """Query the database to check if the current scrape session has been cancelled."""
        if not self.log_id:
            return

        from asgiref.sync import sync_to_async
        from .models import ScrapeLog

        def check():
            log = ScrapeLog.objects.filter(pk=self.log_id).first()
            if log and log.status != "running":
                return True
            return False

        cancelled = await sync_to_async(check)()
        if cancelled:
            raise ScrapeCancelledException("Scrape task cancelled by user.")

    async def _update_run_log(self, jobs_found=None, jobs_new=None, progress_message=None):
        if not self.log_id:
            return

        # First, ensure we haven't been cancelled
        await self._check_cancellation()

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

    # ──────────────────────────────────────────────────────────────────────────
    #  Main pipeline
    # ──────────────────────────────────────────────────────────────────────────

    async def run(self):
        """
        Main entry point.  Runs the full LinkedIn scraping pipeline.
        Returns: dict with {jobs_found, jobs_new, errors}
        """
        from playwright.async_api import async_playwright
        from asgiref.sync import sync_to_async
        from . import session_manager

        stats = {"jobs_found": 0, "jobs_new": 0, "errors": []}

        try:
            async with async_playwright() as p:
                # Always launch with a realistic viewport + UA
                launch_args = [
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ]
                self.browser = await p.chromium.launch(
                    headless=self.headless,
                    args=launch_args,
                )

                # Try loading a saved Playwright session first
                self.context = await session_manager.load_session(self.browser)
                if self.context is not None:
                    # Test if saved session still works
                    test_page = await self.context.new_page()
                    try:
                        await test_page.goto(
                            self.LINKEDIN_FEED_URL,
                            wait_until="domcontentloaded",
                            timeout=30_000,
                        )
                        logged_in = await self.wait_for_logged_in_on_page(test_page, timeout_ms=10_000)
                        if not logged_in:
                            logger.warning("Saved LinkedIn session is expired or blocked. Deleting and trying fresh login.")
                            session_manager.delete_session()
                            await self.context.close()
                            self.context = None
                        else:
                            logger.info("Saved LinkedIn session is still valid.")
                    except Exception as e:
                        logger.warning("Saved LinkedIn session failed (%s). Deleting and trying fresh login.", e)
                        session_manager.delete_session()
                        await self.context.close()
                        self.context = None
                    finally:
                        try:
                            await test_page.close()
                        except Exception:
                            pass

                if self.context is None:
                    self.context = await self.browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        ),
                        # Mimic a real browser — hide automation signals
                        java_script_enabled=True,
                        locale="en-US",
                        timezone_id="Asia/Dhaka",
                    )

                self.page = await self.context.new_page()

                # Remove the `navigator.webdriver` flag that LinkedIn checks
                await self.page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                # Login
                await self._update_run_log(progress_message="Logging into LinkedIn...")
                logged_in = await self.login()
                if not logged_in:
                    stats["errors"].append("Failed to log in to LinkedIn")
                    await self._update_run_log(
                        progress_message="Login failed. Check credentials or 2FA."
                    )
                    return stats

                await self._update_run_log(
                    progress_message="Login successful. Starting job searches..."
                )

                # Persist session so next run can skip login
                await session_manager.save_session(self.context)

                # Fetch user preferences
                prefs = await sync_to_async(self._get_prefs_sync)()
                search_plan = self.build_search_plan(prefs)

                # Limit total searches so we don't burn too much time
                max_combos = getattr(
                    settings, "SCRAPER_MAX_SEARCH_COMBINATIONS", 18
                )
                search_plan = search_plan[:max_combos]

                for idx, search in enumerate(search_plan, 1):
                    keyword = search["keyword"]
                    location = search["location"]
                    work_type = search.get("work_type", "")

                    await self._update_run_log(
                        progress_message=(
                            f"[{idx}/{len(search_plan)}] Searching "
                            f"'{keyword}' in '{location}' ({work_type or 'all types'})..."
                        ),
                        jobs_found=stats["jobs_found"],
                        jobs_new=stats["jobs_new"],
                    )

                    try:
                        jobs = await self.search_jobs(
                            keyword,
                            location,
                            work_type=work_type,
                            experience_levels=search.get("experience_levels"),
                        )
                        stats["jobs_found"] += len(jobs)

                        new_count = await sync_to_async(self._save_jobs_sync)(jobs)
                        stats["jobs_new"] += new_count

                        await self._update_run_log(
                            progress_message=(
                                f"Saved {new_count} new jobs for '{keyword}' in '{location}'"
                            ),
                            jobs_found=stats["jobs_found"],
                            jobs_new=stats["jobs_new"],
                        )

                    except Exception as e:
                        error_msg = (
                            f"Error scraping '{keyword}' in '{location}': {e}"
                        )
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)
                        await self._update_run_log(progress_message=error_msg)

                    # Polite rate-limiting between searches
                    await asyncio.sleep(random.uniform(2, 4))

                await self.browser.close()

        except Exception as e:
            logger.error("LinkedIn scraper fatal error: %s", e)
            stats["errors"].append(str(e))

        return stats

    def _get_prefs_sync(self):
        """Read user preferences from the DB (synchronous, used via sync_to_async)."""
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

    # ──────────────────────────────────────────────────────────────────────────
    #  Search plan builder
    # ──────────────────────────────────────────────────────────────────────────

    def build_search_plan(self, prefs):
        """Build Bangladesh-focused job and internship searches from UI prefs."""
        keywords = self._normalize_keywords(prefs.get("keywords") or [])
        locations = self._normalize_locations(prefs.get("locations") or [])
        work_types = prefs.get("work_types") or ["Remote", "Hybrid", "On-site"]
        experience_levels = self._normalize_experience_levels(
            prefs.get("experience_levels") or []
        )

        plan = []
        seen: set[tuple] = set()

        for keyword in keywords:
            for location in locations:
                for work_type in work_types:
                    # Keep remote searches anchored to Bangladesh for relevance
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

        logger.info("Built %d Bangladesh-focused search combinations.", len(plan))
        return plan

    def _normalize_keywords(self, keywords):
        cleaned = [str(k).strip() for k in keywords if str(k).strip()]
        if not cleaned or cleaned == ["Python Developer"]:
            cleaned = self.DEFAULT_KEYWORDS.copy()

        expanded = []
        for keyword in cleaned:
            self._append_unique(expanded, keyword)
            lower = keyword.lower()
            if "intern" not in lower and "internship" not in lower:
                self._append_unique(expanded, f"{keyword} Internship")
                if "developer" in lower:
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
        if isinstance(experience_levels, str):
            experience_levels = [experience_levels]
        normalized = [str(l).strip() for l in experience_levels if str(l).strip()]
        if not normalized:
            normalized = ["Internship", "Entry"]
        if "Entry" in normalized:
            self._append_unique(normalized, "Internship")
        return normalized

    def _append_unique(self, values, value):
        if value and value not in values:
            values.append(value)

    # ──────────────────────────────────────────────────────────────────────────
    #  Login
    # ──────────────────────────────────────────────────────────────────────────

    async def login(self):
        """
        Attempt to log in to LinkedIn.
        Order: saved session -> credentials -> 2FA/manual fallback.
        """
        try:
            # Try navigating to feed first (tests saved session)
            try:
                await self.page.goto(
                    self.LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=30_000
                )
            except Exception as nav_err:
                logger.warning("Initial feed navigation failed (%s). Trying login page directly.", nav_err)
                await self.page.goto(
                    self.LINKEDIN_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000
                )

            if await self.wait_for_logged_in(timeout_ms=15_000):
                logger.info("Already logged in via saved session.")
                return True

            # Navigate to login page if not already there
            if "/login" not in self.page.url and "/authwall" not in self.page.url:
                try:
                    await self.page.goto(
                        self.LINKEDIN_LOGIN_URL,
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )
                except Exception as nav_err:
                    logger.error("Failed to navigate to login page: %s", nav_err)
                    return False

            # LinkedIn sometimes restores a session after a brief redirect
            if await self.wait_for_logged_in(timeout_ms=6_000):
                logger.info("Login completed via delayed session redirect.")
                return True

            email = settings.LINKEDIN_EMAIL
            password = settings.LINKEDIN_PASSWORD

            if not email or not password:
                logger.error("LinkedIn credentials not configured in .env")
                return False

            # Wait for the username field to appear (LinkedIn uses various selectors)
            email_selectors = [
                "#username",
                'input[name="session_key"]',
                'input[type="email"]',
                'input[name="email"]',
                'input[aria-label*="email" i]',
                'input[aria-label*="username" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]',
            ]
            email_field = None
            for sel in email_selectors:
                try:
                    el = await self.page.wait_for_selector(sel, timeout=5_000)
                    if el:
                        email_field = sel
                        break
                except Exception:
                    continue

            if not email_field:
                if await self.wait_for_logged_in(timeout_ms=5_000):
                    return True
                # Debug: capture page content to understand what's happening
                page_title = await self.page.title()
                page_url = self.page.url
                logger.error(
                    "LinkedIn login page did not load (no email field found). "
                    "Page title: '%s', URL: '%s'",
                    page_title, page_url,
                )
                return False

            await self.page.fill(email_field, email)
            await asyncio.sleep(random.uniform(0.5, 1.2))  # human-like pause

            # LinkedIn may have a two-step flow (email first, then password)
            # Try to find password field directly
            password_selectors = [
                "#password",
                'input[name="session_password"]',
                'input[type="password"]',
                'input[name="password"]',
            ]
            password_field = None
            for sel in password_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        password_field = sel
                        break
                except Exception:
                    continue

            if not password_field:
                # Two-step flow: click "Continue" after entering email
                continue_selectors = [
                    'button[type="submit"]',
                    'button[type="button"]',
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'button:has-text("Sign in")',
                    'button:has-text("Log in")',
                ]
                for sel in continue_selectors:
                    try:
                        el = await self.page.query_selector(sel)
                        if el and await el.is_visible():
                            await el.click()
                            await asyncio.sleep(random.uniform(1.5, 3.0))
                            break
                    except Exception:
                        continue

                # Now wait for password field
                for sel in password_selectors:
                    try:
                        el = await self.page.wait_for_selector(sel, timeout=10_000)
                        if el:
                            password_field = sel
                            break
                    except Exception:
                        continue

            if password_field:
                await self.page.fill(password_field, password)
                await asyncio.sleep(random.uniform(0.3, 0.8))

            # Click submit/continue button
            submit_selectors = [
                'button[type="submit"]',
                'button[type="button"]',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'button:has-text("Continue")',
            ]
            for sel in submit_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        break
                except Exception:
                    continue

            if await self.wait_for_logged_in(timeout_ms=20_000):
                logger.info("LinkedIn login successful.")
                return True

            # 2FA / CAPTCHA path
            logger.warning(
                "2FA or CAPTCHA detected on LinkedIn. "
                "If running headless, set SCRAPER_HEADLESS=False and complete it manually."
            )
            for _ in range(12):
                await self.page.wait_for_timeout(5_000)
                if await self.is_logged_in():
                    logger.info("Login completed after manual 2FA intervention.")
                    return True

            logger.error("LinkedIn login timed out after 60 seconds.")
            return False

        except Exception as e:
            logger.error("LinkedIn login error: %s", e)
            return False

    async def wait_for_logged_in(self, timeout_ms: int = 10_000) -> bool:
        """Poll for LinkedIn's authenticated UI while page redirects settle."""
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while asyncio.get_running_loop().time() < deadline:
            if await self.is_logged_in():
                return True
            await self.page.wait_for_timeout(500)
        return await self.is_logged_in()

    async def wait_for_logged_in_on_page(self, page, timeout_ms: int = 10_000) -> bool:
        """Poll for LinkedIn's authenticated UI on a specific page."""
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while asyncio.get_running_loop().time() < deadline:
            if await self._is_logged_in_on_page(page):
                return True
            await page.wait_for_timeout(500)
        return await self._is_logged_in_on_page(page)

    async def _is_logged_in_on_page(self, page) -> bool:
        """Return True if the given page indicates an authenticated LinkedIn session."""
        try:
            url = page.url
            if any(p in url for p in ("/feed", "/jobs", "/mynetwork", "/messaging")):
                return True

            selectors = [
                "nav.global-nav",
                "[data-test-global-nav]",
                ".global-nav",
                "#global-nav",
                "[class*='global-nav']",
            ]
            for sel in selectors:
                el = await page.query_selector(sel)
                if el:
                    return True

            return False
        except Exception as e:
            logger.debug("_is_logged_in_on_page check error: %s", e)
            return False

    async def is_logged_in(self) -> bool:
        """Return True if the current page indicates an authenticated LinkedIn session."""
        try:
            url = self.page.url
            if any(p in url for p in ("/feed", "/jobs", "/mynetwork", "/messaging")):
                return True

            # Check for global nav (present only when logged in)
            selectors = [
                "nav.global-nav",
                "[data-test-global-nav]",
                ".global-nav",
                "#global-nav",
                "[class*='global-nav']",
            ]
            for sel in selectors:
                el = await self.page.query_selector(sel)
                if el:
                    return True

            return False
        except Exception as e:
            logger.debug("is_logged_in check error: %s", e)
            return False

    # ──────────────────────────────────────────────────────────────────────────
    #  Job searching
    # ──────────────────────────────────────────────────────────────────────────

    async def search_jobs(
        self,
        keyword: str,
        location: str = "",
        work_type: str = "",
        experience_levels=None,
    ) -> list[dict]:
        """
        Run a LinkedIn Jobs search and return normalised job dicts.
        Applies last-30-day recency, work-type and experience-level filters.
        """
        params = {
            "keywords": keyword,
            "location": location,
            # Last 30 days instead of 24 h so we catch more BD postings
            "f_TPR": "r2592000",
            "sortBy": "DD",  # Newest first
        }
        if work_type in self.WORK_TYPE_FILTERS:
            params["f_WT"] = self.WORK_TYPE_FILTERS[work_type]

        exp_codes = [
            self.EXPERIENCE_FILTERS[lvl]
            for lvl in (experience_levels or [])
            if lvl in self.EXPERIENCE_FILTERS
        ]
        if exp_codes:
            params["f_E"] = ",".join(dict.fromkeys(exp_codes))

        query_string = urlencode({k: v for k, v in params.items() if v})
        search_url = f"{self.LINKEDIN_JOBS_URL}?{query_string}"

        logger.info(
            "LinkedIn: searching '%s' in '%s' (%s)",
            keyword,
            location,
            work_type or "all types",
        )

        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            logger.error("LinkedIn: failed to load search page: %s", exc)
            return []

        await self.page.wait_for_timeout(2500)

        # Scroll to trigger lazy-loaded cards
        for _ in range(4):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1200)

        # Find job cards with multiple selector fallbacks
        job_cards = await self._find_job_cards()
        if not job_cards:
            logger.warning(
                "LinkedIn: no job cards found for '%s'. "
                "Selectors may be outdated or LinkedIn returned no results.",
                keyword,
            )
            return []

        logger.info("LinkedIn: found %d cards for '%s'", len(job_cards), keyword)

        jobs: list[dict] = []
        for i, card in enumerate(job_cards[: self.max_jobs]):
            await self._check_cancellation()
            try:
                job_data = await self.extract_job_detail(card)
                if job_data:
                    if self._is_bangladesh_job(job_data):
                        jobs.append(job_data)
                    else:
                        logger.debug(
                            "Skipping non-BD job: %s | %s",
                            job_data.get("title", ""),
                            job_data.get("location", ""),
                        )
            except Exception as e:
                logger.warning("LinkedIn: failed to extract card %d: %s", i, e)

            await asyncio.sleep(random.uniform(0.5, self.delay))

        logger.info(
            "LinkedIn: '%s' → %d Bangladesh jobs found", keyword, len(jobs)
        )
        return jobs

    async def _find_job_cards(self):
        """Try each card selector in order and return the first non-empty result."""
        for selector in self.CARD_SELECTORS:
            try:
                cards = await self.page.query_selector_all(selector)
                if cards:
                    logger.debug(
                        "LinkedIn: using card selector '%s' (%d cards)", selector, len(cards)
                    )
                    return cards
            except Exception:
                continue
        return []

    # ──────────────────────────────────────────────────────────────────────────
    #  Job detail extraction
    # ──────────────────────────────────────────────────────────────────────────

    async def extract_job_detail(self, card) -> dict | None:
        """
        Click a job card to load the detail panel, then scrape all fields.
        Returns a normalised job dict or None if extraction fails.
        """
        from .parser import extract_skills_from_text, parse_salary, parse_experience_level, parse_work_type

        try:
            await card.click()
            await self.page.wait_for_timeout(2000)

            # ── Title ──────────────────────────────────────────────────────────
            title = await self._extract_text_from_card(card, self.TITLE_SELECTORS)

            # ── Company ────────────────────────────────────────────────────────
            company_name = await self._extract_text_from_card(card, self.COMPANY_SELECTORS)

            # ── Location ───────────────────────────────────────────────────────
            location_text = await self._extract_text_from_card(card, self.LOCATION_SELECTORS)

            # ── LinkedIn job ID from card link ─────────────────────────────────
            job_id = ""
            apply_url = ""
            link_el = await card.query_selector(
                "a[href*='/jobs/view/'], a[href*='jobs/view']"
            )
            if link_el:
                href = (await link_el.get_attribute("href") or "").strip()
                id_match = re.search(r"/jobs/view/(\d+)", href)
                if id_match:
                    job_id = id_match.group(1)
                if href:
                    apply_url = (
                        f"https://www.linkedin.com{href}"
                        if href.startswith("/")
                        else href
                    )

            # Also try data attribute as fallback for job ID
            if not job_id:
                job_id = (await card.get_attribute("data-occludable-job-id") or "").strip()
                if job_id and not apply_url:
                    apply_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

            if not job_id or not title:
                return None

            # ── Detail panel ───────────────────────────────────────────────────
            description = ""
            salary_text = ""

            detail_panel = await self._find_element(self.DETAIL_PANEL_SELECTORS)
            if detail_panel:
                desc_el = await self._find_element_within(
                    detail_panel, self.DESCRIPTION_SELECTORS
                )
                if desc_el:
                    description = (await desc_el.inner_text()).strip()

                if not apply_url:
                    apply_el = await detail_panel.query_selector(
                        'a[href*="apply"], .jobs-apply-button'
                    )
                    if apply_el:
                        apply_url = (await apply_el.get_attribute("href") or "").strip()

                salary_el = await self._find_element_within(
                    detail_panel, self.SALARY_SELECTORS
                )
                if salary_el:
                    salary_text = (await salary_el.inner_text()).strip()

            # ── Parse enriched fields ──────────────────────────────────────────
            skills = extract_skills_from_text(f"{title} {description}")
            salary = parse_salary(salary_text)
            experience = parse_experience_level(f"{title} {description}")
            work_type = parse_work_type(f"{location_text} {description}")

            return {
                "source": "linkedin",
                "source_job_id": job_id,
                "source_url": apply_url,
                "linkedin_job_id": job_id,
                "title": title.strip(),
                "company_name": company_name.strip(),
                "location": location_text.strip(),
                "work_type": work_type,
                "description": description,
                "salary_min": salary["min"],
                "salary_max": salary["max"],
                "salary_currency": salary["currency"],
                "experience_level": experience,
                "apply_url": apply_url,
                "skills": skills,
                "date_posted": date.today(),
            }

        except Exception as e:
            logger.warning("LinkedIn: error extracting job detail: %s", e)
            return None

    # ──────────────────────────────────────────────────────────────────────────
    #  Selector helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _extract_text_from_card(self, card, selectors: list[str]) -> str:
        """Try each selector within a card element and return the first found text."""
        for selector in selectors:
            try:
                el = await card.query_selector(selector)
                if el:
                    text = (await el.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                continue
        return ""

    async def _find_element(self, selectors: list[str]):
        """Try each page-level selector and return the first matching element."""
        for selector in selectors:
            try:
                el = await self.page.query_selector(selector)
                if el:
                    return el
            except Exception:
                continue
        return None

    async def _find_element_within(self, parent, selectors: list[str]):
        """Try each selector within a parent element and return first match."""
        for selector in selectors:
            try:
                el = await parent.query_selector(selector)
                if el:
                    return el
            except Exception:
                continue
        return None

    def _is_bangladesh_job(self, job_data: dict) -> bool:
        """Return True only for jobs whose LinkedIn location is Bangladesh-based."""
        location = (job_data.get("location") or "").lower()
        return any(term in location for term in self.BANGLADESH_LOCATION_TERMS)

    # ──────────────────────────────────────────────────────────────────────────
    #  DB persistence
    # ──────────────────────────────────────────────────────────────────────────

    def _save_jobs_sync(self, jobs_data: list[dict]) -> int:
        """Save scraped jobs to the database, deduplicating by source + job ID."""
        from apps.jobs.services import upsert_job_from_source

        new_count = 0
        for job_data in jobs_data:
            try:
                _, created = upsert_job_from_source(job_data)
                if created:
                    new_count += 1
            except Exception as exc:
                logger.error("Failed to save LinkedIn job '%s': %s", job_data.get("title"), exc)

        return new_count
