"""Tests for skills resolution and tier priority."""
import unittest
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.models import Task


class TestSkillsResolution(unittest.TestCase):
    """Test skills resolution in TaskMatchResult."""

    def setUp(self):
        """Set up matcher and test tasks."""
        tokenizer = WordTokenizer()
        scorer = WordOverlapScorer(threshold=0.6)
        self.matcher = TaskTriggerMatcher(tokenizer, scorer)

        self.tasks = {
            "static-website": Task(
                name="static-website",
                description="Static website hosting",
                triggers=["create a landing page"],
                skills=["nextjs-standards", "aws-static-hosting", "github-actions-cicd"]
            ),
            "no-skills-task": Task(
                name="no-skills-task",
                description="Task without skills",
                triggers=["do something"],
                skills=[]
            )
        }

    def test_return_all_skills_required_by_matched_task(self):
        """Test matched result contains all skills from the task."""
        result = self.matcher.match("create a landing page", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "static-website")
        self.assertEqual(len(result.skills), 3)
        self.assertIn("nextjs-standards", result.skills)
        self.assertIn("aws-static-hosting", result.skills)
        self.assertIn("github-actions-cicd", result.skills)

    def test_skills_list_order_preserved(self):
        """Test skills list preserves order from task definition."""
        result = self.matcher.match("create a landing page", self.tasks)

        self.assertEqual(
            result.skills,
            ["nextjs-standards", "aws-static-hosting", "github-actions-cicd"]
        )

    def test_empty_skills_list_handled(self):
        """Test task with empty skills list returns empty skills."""
        result = self.matcher.match("do something", self.tasks)

        self.assertTrue(result.is_match())
        self.assertEqual(result.task_name, "no-skills-task")
        self.assertEqual(result.skills, [])

    def test_no_match_has_empty_skills(self):
        """Test no match result has empty skills list."""
        result = self.matcher.match("unrelated query", self.tasks)

        self.assertFalse(result.is_match())
        self.assertEqual(result.skills, [])


class TestTierPriorityConcept(unittest.TestCase):
    """Test tier priority concept for integration.

    Note: This tests the concept that Tier 1 (DirectSkillMatcher) should
    take priority over Tier 2 (TaskTriggerMatcher) in router orchestration.
    The actual router integration will be implemented separately.
    """

    def test_task_matcher_returns_skills_list(self):
        """Test TaskTriggerMatcher result includes skills for tier routing."""
        tokenizer = WordTokenizer()
        scorer = WordOverlapScorer(threshold=0.6)
        matcher = TaskTriggerMatcher(tokenizer, scorer)

        tasks = {
            "static-website": Task(
                name="static-website",
                description="Static website hosting",
                triggers=["build a static website"],
                skills=["nextjs-standards", "aws-static-hosting"]
            )
        }

        result = matcher.match("build a static website", tasks)

        # Result should have skills that can be used by router
        self.assertTrue(result.is_match())
        self.assertIsNotNone(result.skills)
        self.assertGreater(len(result.skills), 0)

    def test_concept_tier_1_direct_skill_match_would_return_different_type(self):
        """Test conceptual difference between Tier 1 (skill) and Tier 2 (task) results.

        In router orchestration:
        - Tier 1 (DirectSkillMatcher) returns MatchResult with single skill_name
        - Tier 2 (TaskTriggerMatcher) returns TaskMatchResult with task_name and skills list
        - Router should check Tier 1 first, only use Tier 2 if Tier 1 fails
        """
        # This is a conceptual test - actual router integration tested separately
        from lib.skill_router.matching.result import MatchResult, TaskMatchResult

        # Tier 1 result: single skill
        tier1_result = MatchResult.exact_match("terraform-base")
        self.assertIsNotNone(tier1_result.skill_name)
        self.assertIsNone(getattr(tier1_result, 'task_name', None))

        # Tier 2 result: task with multiple skills
        tier2_result = TaskMatchResult.from_task(
            task_name="static-website",
            score=1.0,
            matched_trigger="build a static website",
            skills=["nextjs-standards", "aws-static-hosting"]
        )
        self.assertIsNotNone(tier2_result.task_name)
        self.assertIsNone(getattr(tier2_result, 'skill_name', None))

        # Router logic would be: if tier1_result.skill_name, use it; else use tier2


if __name__ == '__main__':
    unittest.main()
