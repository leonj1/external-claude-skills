"""Tests for exact trigger matching with case and whitespace normalization."""
import unittest
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.models import Task


class TestWordTokenizer(unittest.TestCase):
    """Test WordTokenizer normalization and tokenization."""

    def setUp(self):
        """Set up tokenizer for tests."""
        self.tokenizer = WordTokenizer()

    def test_tokenize_lowercase_normalization(self):
        """Test tokenizer converts to lowercase."""
        result = self.tokenizer.tokenize("BUILD A STATIC WEBSITE")
        self.assertEqual(result, {"build", "a", "static", "website"})

    def test_tokenize_strips_whitespace(self):
        """Test tokenizer strips leading/trailing whitespace."""
        result = self.tokenizer.tokenize("  build a website  ")
        self.assertEqual(result, {"build", "a", "website"})

    def test_tokenize_handles_multiple_spaces(self):
        """Test tokenizer handles multiple consecutive spaces."""
        result = self.tokenizer.tokenize("build   a   static   website")
        self.assertEqual(result, {"build", "a", "static", "website"})

    def test_tokenize_empty_string(self):
        """Test tokenizer returns empty set for empty string."""
        result = self.tokenizer.tokenize("")
        self.assertEqual(result, set())

    def test_tokenize_whitespace_only(self):
        """Test tokenizer returns empty set for whitespace-only string."""
        result = self.tokenizer.tokenize("    ")
        self.assertEqual(result, set())

    def test_tokenize_mixed_case(self):
        """Test tokenizer normalizes mixed case."""
        result = self.tokenizer.tokenize("BuIlD a StAtIc WeBsItE")
        self.assertEqual(result, {"build", "a", "static", "website"})


class TestWordOverlapScorer(unittest.TestCase):
    """Test WordOverlapScorer overlap calculation."""

    def setUp(self):
        """Set up scorer with default 60% threshold."""
        self.scorer = WordOverlapScorer(threshold=0.6)

    def test_exact_match_returns_1_0(self):
        """Test exact match returns score of 1.0."""
        query_words = {"build", "a", "static", "website"}
        trigger_words = {"build", "a", "static", "website"}

        score = self.scorer.score(query_words, trigger_words)
        self.assertEqual(score, 1.0)

    def test_partial_match_above_threshold(self):
        """Test partial match above 60% threshold returns coverage score."""
        # Query has all trigger words plus extras
        query_words = {"build", "static", "website"}  # 3 words
        trigger_words = {"build", "a", "static", "website"}  # 4 words
        # Coverage: 3/4 = 0.75 >= 0.6

        score = self.scorer.score(query_words, trigger_words)
        self.assertEqual(score, 0.75)

    def test_partial_match_below_threshold_returns_zero(self):
        """Test partial match below 60% threshold returns 0.0."""
        query_words = {"website"}  # 1 word
        trigger_words = {"build", "a", "static", "website"}  # 4 words
        # Coverage: 1/4 = 0.25 < 0.6

        score = self.scorer.score(query_words, trigger_words)
        self.assertEqual(score, 0.0)

    def test_empty_trigger_words_returns_zero(self):
        """Test empty trigger words returns 0.0."""
        query_words = {"build", "website"}
        trigger_words = set()

        score = self.scorer.score(query_words, trigger_words)
        self.assertEqual(score, 0.0)

    def test_empty_query_words_returns_zero(self):
        """Test empty query words returns 0.0."""
        query_words = set()
        trigger_words = {"build", "a", "website"}

        score = self.scorer.score(query_words, trigger_words)
        self.assertEqual(score, 0.0)


class TestTaskTriggerMatcherExact(unittest.TestCase):
    """Test TaskTriggerMatcher with exact trigger matching scenarios."""

    def setUp(self):
        """Set up matcher and test tasks."""
        tokenizer = WordTokenizer()
        scorer = WordOverlapScorer(threshold=0.6)
        self.matcher = TaskTriggerMatcher(tokenizer, scorer)

        # Create test tasks matching BDD background
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
                    "create a dashboard",
                    "create an internal tool"
                ],
                skills=["react-admin", "auth-service"]
            ),
            "rest-api": Task(
                name="rest-api",
                description="RESTful API service",
                triggers=[
                    "build an API",
                    "create a REST API",
                    "build a backend service"
                ],
                skills=["fastapi-standards", "db-integration"]
            )
        }

    def test_match_task_with_exact_trigger_phrase(self):
        """Test matching task with exact trigger phrase."""
        result = self.matcher.match("build a static website", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.matched_trigger, "build a static website")

    def test_match_different_task_with_exact_trigger(self):
        """Test matching different task with exact trigger."""
        result = self.matcher.match("create a dashboard", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "admin-panel")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.matched_trigger, "create a dashboard")

    def test_match_triggers_case_insensitively(self):
        """Test matching triggers case-insensitively."""
        result = self.matcher.match("BUILD A STATIC WEBSITE", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.score, 1.0)

    def test_match_with_extra_whitespace_in_query(self):
        """Test matching with extra whitespace in query."""
        result = self.matcher.match("  build   a   static   website  ", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(result.score, 1.0)

    def test_no_match_for_empty_query(self):
        """Test empty query returns no match."""
        result = self.matcher.match("", self.tasks)

        self.assertFalse(result.is_match())
        self.assertIsNone(result.task_name)
        self.assertEqual(result.score, 0.0)

    def test_no_match_for_empty_tasks(self):
        """Test empty tasks dictionary returns no match."""
        result = self.matcher.match("build a website", {})

        self.assertFalse(result.is_match())
        self.assertIsNone(result.task_name)


if __name__ == '__main__':
    unittest.main()
