"""Tests for best match selection logic."""
import unittest
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.models import Task


class TestBestMatchSelection(unittest.TestCase):
    """Test best match selection scenarios."""

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
                    "create a landing page"
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
            ),
            "serverless-api": Task(
                name="serverless-api",
                description="Serverless Lambda API",
                triggers=[
                    "build a serverless API",
                    "create a Lambda function"
                ],
                skills=["lambda-deployment", "api-gateway"]
            )
        }

    def test_select_task_with_highest_word_overlap_score(self):
        """Test selecting task with highest word overlap score."""
        # Query: "build a REST API backend service"
        # Should match "rest-api" with trigger "build a backend service"
        # {build, a, rest, api, backend, service} vs {build, a, backend, service} = 4/4 = 1.0
        # "build an API" would be {build, an, api} = 2/3 = 0.67
        result = self.matcher.match("build a REST API backend service", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "rest-api")
        # Should match "build a backend service" with perfect score
        self.assertEqual(result.score, 1.0)

    def test_distinguish_between_similar_tasks(self):
        """Test distinguishing between similar API tasks."""
        # Query: "build a serverless API"
        # "serverless-api" trigger "build a serverless API" = 4/4 = 1.0 (exact)
        # "rest-api" trigger "build an API" = 2/3 = 0.67
        result = self.matcher.match("build a serverless API", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "serverless-api")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.matched_trigger, "build a serverless API")

    def test_match_admin_panel_over_generic_dashboard(self):
        """Test matching admin panel with specific internal tool query."""
        # Query: "create an internal tool for admin"
        # Should match "admin-panel" trigger "create an internal tool"
        # {create, an, internal, tool, for, admin} vs {create, an, internal, tool} = 4/4 = 1.0
        result = self.matcher.match("create an internal tool for admin", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "admin-panel")
        self.assertEqual(result.score, 1.0)

    def test_no_match_for_ambiguous_request(self):
        """Test no match for ambiguous query that doesn't meet threshold."""
        # Query: "help me with authentication"
        # No task has triggers that overlap >= 60% with this
        result = self.matcher.match("help me with authentication", self.tasks)

        self.assertFalse(result.is_match())
        self.assertIsNone(result.task_name)
        self.assertEqual(result.score, 0.0)

    def test_no_match_for_unrelated_query(self):
        """Test no match for completely unrelated query."""
        result = self.matcher.match("what is the weather today", self.tasks)

        self.assertFalse(result.is_match())
        self.assertIsNone(result.task_name)
        self.assertEqual(result.score, 0.0)

    def test_best_match_across_multiple_tasks(self):
        """Test best match is selected when multiple tasks partially match."""
        # Query should match "rest-api" better than others
        result = self.matcher.match("create a REST API", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "rest-api")
        self.assertEqual(result.matched_trigger, "create a REST API")
        self.assertEqual(result.score, 1.0)

    def test_task_with_no_triggers_never_matches(self):
        """Test task with empty triggers list never matches."""
        tasks_with_empty = self.tasks.copy()
        tasks_with_empty["no-triggers"] = Task(
            name="no-triggers",
            description="Task without triggers",
            triggers=[],
            skills=["some-skill"]
        )

        result = self.matcher.match("build something", tasks_with_empty)

        # Should match another task, not the one without triggers
        if result.is_match():
            self.assertNotEqual(result.task_name, "no-triggers")


if __name__ == '__main__':
    unittest.main()
