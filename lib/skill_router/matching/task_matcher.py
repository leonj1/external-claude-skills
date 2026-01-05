"""Task trigger matching implementation."""
from typing import Dict
from lib.skill_router.interfaces.matching import ITaskMatcher, IWordTokenizer, IWordOverlapScorer
from lib.skill_router.models import Task
from lib.skill_router.matching.result import TaskMatchResult


class TaskTriggerMatcher(ITaskMatcher):
    """Matches user queries to tasks using word overlap scoring.

    Uses dependency injection for tokenizer and scorer to enable
    flexible matching strategies.
    """

    def __init__(self, tokenizer: IWordTokenizer, scorer: IWordOverlapScorer):
        """Initialize matcher with tokenizer and scorer.

        Args:
            tokenizer: Word tokenization strategy
            scorer: Word overlap scoring strategy
        """
        self.tokenizer = tokenizer
        self.scorer = scorer

    def match(self, query: str, tasks: Dict[str, Task]) -> TaskMatchResult:
        """Match a query against available tasks.

        Args:
            query: User query string
            tasks: Dictionary mapping task names to Task objects

        Returns:
            TaskMatchResult containing best matched task and score,
            or no_match() if no task meets the threshold.
        """
        if not query or not tasks:
            return TaskMatchResult.no_match()

        # Tokenize query once
        query_words = self.tokenizer.tokenize(query)

        if not query_words:
            return TaskMatchResult.no_match()

        best_score = 0.0
        best_task_name = None
        best_trigger = None
        best_skills = []

        # Check all tasks and their triggers
        for task_name, task in tasks.items():
            if not task.triggers:
                continue

            # Check each trigger for this task
            for trigger in task.triggers:
                trigger_words = self.tokenizer.tokenize(trigger)

                if not trigger_words:
                    continue

                # Score this trigger
                score = self.scorer.score(query_words, trigger_words)

                # Update best if this is better
                if score > best_score:
                    best_score = score
                    best_task_name = task_name
                    best_trigger = trigger
                    best_skills = task.skills

        # Return no match if nothing scored above threshold (scorer returns 0.0)
        if best_score == 0.0 or best_task_name is None:
            return TaskMatchResult.no_match()

        return TaskMatchResult.from_task(
            task_name=best_task_name,
            score=best_score,
            matched_trigger=best_trigger,
            skills=best_skills
        )
