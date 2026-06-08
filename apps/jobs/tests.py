from django.test import SimpleTestCase

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
