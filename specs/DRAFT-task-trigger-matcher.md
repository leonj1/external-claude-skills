# DRAFT: Task Trigger Matcher (Tier 2 Routing)

## Overview

The Task Trigger Matcher implements Tier 2 of the 3-tier routing system. It matches user queries against predefined task triggers using word overlap scoring with a 60% threshold. When multiple tasks match, the one with the highest overlap score wins.

## Traces to Root Request

- **Root**: "Read specs.md and implement the Skill Router system with YAML manifest, **3-tier routing**, dependency resolution, and hook integration"
- **This sub-task**: Implements Tier 2 of the "3-tier routing" requirement

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 3 (~150 lines) |
| New code to write | ~120 lines |
| Test code to write | ~200 lines |
| Estimated context usage | ~15% |

**Verdict**: APPROVED (under 60% threshold)

---

## Interfaces Needed

### ITaskMatcher (New)

```python
from abc import ABC, abstractmethod
from typing import Dict
from lib.skill_router.models import Task


class ITaskMatcher(ABC):
    """Interface for task matching strategies."""

    @abstractmethod
    def match(self, query: str, tasks: Dict[str, Task]) -> "TaskMatchResult":
        """Match a query against available tasks.

        Args:
            query: User query string
            tasks: Dictionary mapping task names to Task objects

        Returns:
            TaskMatchResult containing matched task name, score, and skills
        """
        pass
```

### IWordOverlapScorer (New)

```python
from abc import ABC, abstractmethod
from typing import Set


class IWordOverlapScorer(ABC):
    """Interface for computing word overlap scores."""

    @abstractmethod
    def score(self, query_words: Set[str], trigger_words: Set[str]) -> float:
        """Compute overlap score between query and trigger.

        Args:
            query_words: Set of words from user query
            trigger_words: Set of words from task trigger

        Returns:
            Score from 0.0 to 1.0 representing coverage
        """
        pass
```

### IWordTokenizer (New)

```python
from abc import ABC, abstractmethod
from typing import Set


class IWordTokenizer(ABC):
    """Interface for tokenizing strings into words."""

    @abstractmethod
    def tokenize(self, text: str) -> Set[str]:
        """Tokenize text into a set of words.

        Args:
            text: Input string

        Returns:
            Set of lowercase words
        """
        pass
```

---

## Data Models

### TaskMatchResult (New)

```python
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class TaskMatchResult:
    """Represents the result of a task matching operation.

    Attributes:
        task_name: Name of matched task, or None if no match
        score: Word overlap score (0.0-1.0)
        matched_trigger: The trigger phrase that matched
        skills: List of skill names required by the matched task
    """
    task_name: Optional[str]
    score: float
    matched_trigger: Optional[str]
    skills: List[str]

    @classmethod
    def no_match(cls) -> "TaskMatchResult":
        """Factory method for no match result."""
        return cls(task_name=None, score=0.0, matched_trigger=None, skills=[])

    @classmethod
    def from_task(cls, task_name: str, score: float, trigger: str, skills: List[str]) -> "TaskMatchResult":
        """Factory method for successful match."""
        return cls(task_name=task_name, score=score, matched_trigger=trigger, skills=skills)

    def is_match(self) -> bool:
        """Check if this result represents a valid match."""
        return self.task_name is not None
```

---

## Implementation Classes

### WordTokenizer

```python
class WordTokenizer(IWordTokenizer):
    """Simple word tokenizer that splits on whitespace."""

    def tokenize(self, text: str) -> Set[str]:
        """Tokenize text into lowercase words.

        Handles:
        - Case normalization (lowercase)
        - Whitespace normalization (multiple spaces, leading/trailing)
        - Empty strings
        """
        normalized = text.lower().strip()
        if not normalized:
            return set()
        return set(normalized.split())
```

### WordOverlapScorer

```python
class WordOverlapScorer(IWordOverlapScorer):
    """Computes word overlap as coverage of trigger words."""

    def __init__(self, threshold: float = 0.6):
        """Initialize with overlap threshold.

        Args:
            threshold: Minimum coverage required (default 0.6 = 60%)
        """
        self.threshold = threshold

    def score(self, query_words: Set[str], trigger_words: Set[str]) -> float:
        """Compute overlap score.

        Score = |query_words INTERSECT trigger_words| / |trigger_words|

        Returns 0.0 if trigger_words is empty or if score < threshold.
        """
        if not trigger_words:
            return 0.0

        overlap = len(query_words & trigger_words)
        coverage = overlap / len(trigger_words)

        return coverage if coverage >= self.threshold else 0.0
```

### TaskTriggerMatcher

```python
class TaskTriggerMatcher(ITaskMatcher):
    """Matches user queries to tasks via trigger phrase word overlap."""

    def __init__(self, tokenizer: IWordTokenizer, scorer: IWordOverlapScorer):
        """Initialize with dependencies.

        Args:
            tokenizer: Word tokenizer for splitting strings
            scorer: Word overlap scorer for computing coverage
        """
        self.tokenizer = tokenizer
        self.scorer = scorer

    def match(self, query: str, tasks: Dict[str, Task]) -> TaskMatchResult:
        """Match query against all task triggers, return best match.

        Algorithm:
        1. Tokenize query into words
        2. For each task, for each trigger:
           a. Tokenize trigger into words
           b. Compute overlap score
           c. Track best score and corresponding task
        3. Return task with highest score (if any meets threshold)
        """
        query_words = self.tokenizer.tokenize(query)
        if not query_words:
            return TaskMatchResult.no_match()

        best_result = TaskMatchResult.no_match()
        best_score = 0.0

        for task_name, task in tasks.items():
            for trigger in task.triggers:
                trigger_words = self.tokenizer.tokenize(trigger)
                score = self.scorer.score(query_words, trigger_words)

                if score > best_score:
                    best_score = score
                    best_result = TaskMatchResult.from_task(
                        task_name=task_name,
                        score=score,
                        trigger=trigger,
                        skills=task.skills
                    )

        return best_result
```

---

## Logic Flow (Pseudocode)

```
FUNCTION match_task(query, tasks):
    query_words = tokenize(query)
    IF query_words is empty:
        RETURN no_match

    best = no_match
    best_score = 0

    FOR each task in tasks:
        FOR each trigger in task.triggers:
            trigger_words = tokenize(trigger)
            overlap = count(query_words INTERSECT trigger_words)
            coverage = overlap / len(trigger_words)

            IF coverage >= 0.60 AND coverage > best_score:
                best_score = coverage
                best = TaskMatchResult(task, coverage, trigger, task.skills)

    RETURN best
```

---

## Integration Points

### With Router Orchestration (Task 1.6)

The router will call the task matcher in Tier 2:

```python
# In SkillRouter.route():
if tier1_result.is_match():
    return tier1_result

tier2_result = self.task_matcher.match(query, manifest.tasks)
if tier2_result.is_match():
    execution_order = self.dependency_resolver.resolve(tier2_result.skills)
    return RouteResult(
        route_type="task",
        matched=tier2_result.task_name,
        skills=tier2_result.skills,
        execution_order=execution_order
    )

return self.llm_discovery(query, manifest)
```

### With Dependency Resolver (Task 1.2)

Once a task matches, its skills list is passed to the dependency resolver to compute execution order.

---

## File Structure

```
lib/skill_router/
  interfaces/
    matching.py          # Add ITaskMatcher, IWordOverlapScorer, IWordTokenizer
  matching/
    result.py            # Add TaskMatchResult
    task_matcher.py      # TaskTriggerMatcher implementation
    tokenizer.py         # WordTokenizer implementation
    scorer.py            # WordOverlapScorer implementation
```

---

## Test Scenarios (from BDD)

| Scenario | Query | Expected Task | Expected Score |
|----------|-------|---------------|----------------|
| Exact trigger | "build a static website" | static-website | 1.0 |
| Word overlap | "build static website" | static-website | 0.75 (3/4 words) |
| Below threshold | "website" | None | 0.0 |
| Best match | "build a REST API backend service" | rest-api | highest |
| Case insensitive | "BUILD A STATIC WEBSITE" | static-website | 1.0 |
| Extra whitespace | "  build   a   static   website  " | static-website | 1.0 |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| 60% threshold | Balances precision vs recall; prevents weak matches |
| Coverage = trigger coverage | Measures how much of the trigger is present in query |
| Best match wins | When multiple tasks match, highest score is selected |
| Tokenizer as interface | Enables future improvements (stemming, stop words) |
| Scorer as interface | Enables alternative scoring strategies |
