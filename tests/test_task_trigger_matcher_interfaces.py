"""Tests for Task Trigger Matching interfaces and TaskMatchResult model."""
import unittest
from lib.skill_router.matching.result import TaskMatchResult
from lib.skill_router.interfaces.matching import (
    ITaskMatcher,
    IWordOverlapScorer,
    IWordTokenizer
)


class TestTaskMatchResult(unittest.TestCase):
    """Test TaskMatchResult dataclass and factory methods."""

    def test_no_match_factory(self):
        """Test no_match() factory method creates empty result."""
        result = TaskMatchResult.no_match()

        self.assertIsNone(result.task_name)
        self.assertEqual(result.score, 0.0)
        self.assertIsNone(result.matched_trigger)
        self.assertEqual(result.skills, [])
        self.assertFalse(result.is_match())

    def test_from_task_factory(self):
        """Test from_task() factory method populates all fields."""
        skills = ["skill1", "skill2", "skill3"]
        result = TaskMatchResult.from_task(
            task_name="test-task",
            score=0.95,
            matched_trigger="build a test",
            skills=skills
        )

        self.assertEqual(result.task_name, "test-task")
        self.assertEqual(result.score, 0.95)
        self.assertEqual(result.matched_trigger, "build a test")
        self.assertEqual(result.skills, ["skill1", "skill2", "skill3"])
        self.assertTrue(result.is_match())

    def test_from_task_copies_skills_list(self):
        """Test from_task() creates a copy of skills list to avoid reference issues."""
        original_skills = ["skill1", "skill2"]
        result = TaskMatchResult.from_task(
            task_name="test-task",
            score=1.0,
            matched_trigger="trigger",
            skills=original_skills
        )

        # Modify original list
        original_skills.append("skill3")

        # Result should not be affected
        self.assertEqual(result.skills, ["skill1", "skill2"])

    def test_is_match_returns_true_when_task_matched(self):
        """Test is_match() returns True when task_name is set."""
        result = TaskMatchResult.from_task(
            task_name="my-task",
            score=0.8,
            matched_trigger="trigger phrase",
            skills=[]
        )

        self.assertTrue(result.is_match())

    def test_is_match_returns_false_when_no_match(self):
        """Test is_match() returns False when task_name is None."""
        result = TaskMatchResult.no_match()

        self.assertFalse(result.is_match())

    def test_task_match_result_with_empty_skills(self):
        """Test TaskMatchResult works with empty skills list."""
        result = TaskMatchResult.from_task(
            task_name="no-skills-task",
            score=1.0,
            matched_trigger="exact trigger",
            skills=[]
        )

        self.assertEqual(result.skills, [])
        self.assertTrue(result.is_match())


class TestIWordTokenizerInterface(unittest.TestCase):
    """Test IWordTokenizer interface contract."""

    def test_interface_has_tokenize_method(self):
        """Test IWordTokenizer defines tokenize method."""
        self.assertTrue(hasattr(IWordTokenizer, 'tokenize'))

    def test_tokenize_method_is_abstract(self):
        """Test tokenize method is abstract (cannot instantiate)."""
        with self.assertRaises(TypeError):
            IWordTokenizer()


class TestIWordOverlapScorerInterface(unittest.TestCase):
    """Test IWordOverlapScorer interface contract."""

    def test_interface_has_score_method(self):
        """Test IWordOverlapScorer defines score method."""
        self.assertTrue(hasattr(IWordOverlapScorer, 'score'))

    def test_score_method_is_abstract(self):
        """Test score method is abstract (cannot instantiate)."""
        with self.assertRaises(TypeError):
            IWordOverlapScorer()


class TestITaskMatcherInterface(unittest.TestCase):
    """Test ITaskMatcher interface contract."""

    def test_interface_has_match_method(self):
        """Test ITaskMatcher defines match method."""
        self.assertTrue(hasattr(ITaskMatcher, 'match'))

    def test_match_method_is_abstract(self):
        """Test match method is abstract (cannot instantiate)."""
        with self.assertRaises(TypeError):
            ITaskMatcher()


if __name__ == '__main__':
    unittest.main()
