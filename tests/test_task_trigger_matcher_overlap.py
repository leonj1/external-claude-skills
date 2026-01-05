"""Tests for word overlap matching with 60% threshold."""
import unittest
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.models import Task


class TestWordOverlapMatching(unittest.TestCase):
    """Test word overlap matching scenarios."""

    def setUp(self):
        """Set up matcher and test tasks."""
        tokenizer = WordTokenizer()
        scorer = WordOverlapScorer(threshold=0.6)
        self.matcher = TaskTriggerMatcher(tokenizer, scorer)

        self.tasks = {
            "static-website": Task(
                name="static-website",
                description="Static website hosting",
                triggers=[
                    "build a static website",
                    "create a landing page",
                    "make a marketing site"
                ],
                skills=["nextjs-standards", "aws-static-hosting"]
            ),
            "admin-panel": Task(
                name="admin-panel",
                description="Internal admin dashboard",
                triggers=[
                    "build an admin panel",
                    "create a dashboard"
                ],
                skills=["react-admin"]
            )
        }

    def test_match_task_when_query_contains_trigger_words(self):
        """Test match when query contains trigger words plus extras."""
        # Query: "I want to build a static website for my business"
        # Contains all words from trigger "build a static website"
        result = self.matcher.match(
            "I want to build a static website for my business",
            self.tasks
        )

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.matched_trigger, "build a static website")
        # Score should be 1.0 since all trigger words are present
        self.assertEqual(result.score, 1.0)

    def test_match_task_with_60_percent_word_overlap(self):
        """Test match with exactly 60% word overlap."""
        # Query: "build static website" = {build, static, website}
        # Trigger: "build a static website" = {build, a, static, website}
        # Overlap: {build, static, website} = 3 words
        # Coverage: 3/4 = 0.75 >= 0.6 PASS
        result = self.matcher.match("build static website", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.score, 0.75)

    def test_no_match_when_word_overlap_below_threshold(self):
        """Test no match when word overlap is below 60% threshold."""
        # Query: "website" = {website}
        # Trigger: "build a static website" = {build, a, static, website}
        # Overlap: {website} = 1 word
        # Coverage: 1/4 = 0.25 < 0.6 FAIL
        result = self.matcher.match("website", self.tasks)

        self.assertFalse(result.is_match())
        self.assertIsNone(result.task_name)
        self.assertEqual(result.score, 0.0)

    def test_query_with_extra_words_still_matches_if_threshold_met(self):
        """Test query with extra words still matches if coverage >= 60%."""
        # Query has all trigger words plus many extras
        result = self.matcher.match(
            "I really need to create a dashboard for monitoring",
            self.tasks
        )

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "admin-panel")
        self.assertEqual(result.matched_trigger, "create a dashboard")
        # All 3 trigger words present: coverage = 3/3 = 1.0
        self.assertEqual(result.score, 1.0)

    def test_single_word_query_below_threshold(self):
        """Test single word query that doesn't meet threshold."""
        # Single word queries will typically be below 60% for multi-word triggers
        result = self.matcher.match("dashboard", self.tasks)

        # "dashboard" vs "create a dashboard" = 1/3 = 0.33 < 0.6
        self.assertFalse(result.is_match())

    def test_multiple_trigger_phrases_select_best(self):
        """Test matcher selects best score across multiple trigger phrases."""
        # Query matches "create a landing page" better than other triggers
        result = self.matcher.match("create a landing page", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.matched_trigger, "create a landing page")
        self.assertEqual(result.score, 1.0)


if __name__ == '__main__':
    unittest.main()
