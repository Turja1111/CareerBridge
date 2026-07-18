from datetime import date

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.analytics.aggregators import summary_stats
from apps.scraper.models import ScrapeLog
from .matching import calculate_job_match
from .models import Company, JobPost
from .services import upsert_job_from_source
from .utils import is_bangladesh_eligible, is_degree_relevant, relevance_score, seems_expired


class JobFilteringTests(SimpleTestCase):
    def test_bangladesh_remote_role_is_kept(self):
        self.assertTrue(
            is_bangladesh_eligible("Remote", "Remote role for Bangladeshi applicants", "Acme Bangladesh")
        )

    def test_irrelevant_role_is_filtered(self):
        self.assertFalse(is_degree_relevant("Office Assistant", "Support desk and reception duties"))

    def test_expired_role_is_detected(self):
        self.assertTrue(seems_expired("Software Engineer", "This posting is expired and closed", "Dhaka"))

    def test_relevance_score_stays_above_threshold_for_tech_role(self):
        score = relevance_score("Software Engineer", "Python and Django role in Dhaka", "Dhaka, Bangladesh", "Python Django SQL")
        self.assertGreaterEqual(score, 70)


class JobSourceAndMatchingTests(TestCase):
    def test_upsert_job_from_source_deduplicates_by_source_id(self):
        payload = {
            "source": "bdjobs",
            "source_job_id": "bd-100",
            "source_url": "https://jobs.bdjobs.com/jobdetails.asp?id=bd-100",
            "title": "Junior Python Developer",
            "company_name": "Acme Bangladesh",
            "location": "Dhaka, Bangladesh",
            "description": "Entry-level Python and Django role for Bangladeshi applicants.",
            "date_posted": date.today(),
            "skills": ["Python", "Django"],
        }

        job, created = upsert_job_from_source(payload)
        same_job, created_again = upsert_job_from_source({**payload, "title": "Junior Python Developer Updated"})

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(job.pk, same_job.pk)
        self.assertEqual(JobPost.objects.count(), 1)
        self.assertEqual(same_job.title, "Junior Python Developer Updated")
        self.assertGreaterEqual(same_job.match_score, 70)

    def test_calculate_job_match_returns_reasons_and_missing_skills(self):
        match = calculate_job_match(
            "Data Analyst Intern",
            "Python, SQL, Pandas and dashboard reporting in Dhaka.",
            "Dhaka, Bangladesh",
        )

        self.assertGreaterEqual(match.score, 70)
        self.assertTrue(match.reasons)
        self.assertIn("Django", match.missing_skills)


class AnalyticsAndDashboardTests(TestCase):
    def test_summary_stats_includes_status_and_source_counts(self):
        company = Company.objects.create(name="Acme Bangladesh")
        JobPost.objects.create(
            source="linkedin",
            source_job_id="li-1",
            linkedin_job_id="li-1",
            title="Python Developer",
            company=company,
            location="Dhaka, Bangladesh",
            description="Python and Django role in Bangladesh.",
            status="saved",
            is_active=True,
        )
        JobPost.objects.create(
            source="bdjobs",
            source_job_id="bd-1",
            title="Data Analyst Intern",
            company=company,
            location="Dhaka, Bangladesh",
            description="SQL and Python internship in Bangladesh.",
            status="applied",
            is_active=True,
        )

        stats = summary_stats()

        self.assertEqual(stats["total_jobs_by_status"]["saved"], 1)
        self.assertEqual(stats["total_jobs_by_status"]["applied"], 1)
        self.assertEqual(stats["total_jobs_by_source"]["linkedin"], 1)
        self.assertEqual(stats["total_jobs_by_source"]["bdjobs"], 1)

    def test_dashboard_uses_scrape_log_fields_without_errors(self):
        ScrapeLog.objects.create(status="success", jobs_found=5, jobs_new=2)
        response = Client().get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 new / 5 total")
