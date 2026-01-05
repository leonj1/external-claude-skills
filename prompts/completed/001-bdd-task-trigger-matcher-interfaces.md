---
executor: bdd
source_feature: ./tests/bdd/task-trigger-matching.feature
---

<objective>
Implement the foundational interfaces and data models for Task Trigger Matching (Tier 2 routing).
These components enable word-overlap-based matching of user queries to predefined task triggers.
</objective>

<gherkin>
Feature: Task Trigger Matching (Tier 2 Routing)
  As a user
  I want my high-level requests to match predefined tasks
  So that I get the right combination of skills for my goal

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains tasks
      | name             | description                  | triggers                                                              |
      | static-website   | Static website hosting       | build a static website, create a landing page, make a marketing site  |
      | admin-panel      | Internal admin dashboard     | build an admin panel, create a dashboard, create an internal tool     |
      | rest-api         | RESTful API service          | build an API, create a REST API, build a backend service              |
      | serverless-api   | Serverless Lambda API        | build a serverless API, create a Lambda function                      |
</gherkin>

<requirements>
Based on the spec, implement foundational components:

1. **ITaskMatcher Interface** (`lib/skill_router/interfaces/matching.py`)
   - Method: `match(query: str, tasks: Dict[str, Task]) -> TaskMatchResult`
   - Abstract base class for task matching strategies

2. **IWordOverlapScorer Interface** (`lib/skill_router/interfaces/matching.py`)
   - Method: `score(query_words: Set[str], trigger_words: Set[str]) -> float`
   - Computes overlap score between query and trigger words

3. **IWordTokenizer Interface** (`lib/skill_router/interfaces/matching.py`)
   - Method: `tokenize(text: str) -> Set[str]`
   - Tokenizes strings into word sets

4. **TaskMatchResult Model** (`lib/skill_router/matching/result.py`)
   - Fields: task_name, score, matched_trigger, skills
   - Factory methods: `no_match()`, `from_task()`
   - Method: `is_match()` returns bool

Edge Cases:
- Empty query handling
- Empty task dictionary
- Tasks with no triggers
</requirements>

<context>
BDD Specification: specs/DRAFT-task-trigger-matcher.md

Reuse Opportunities (existing code):
- `lib/skill_router/interfaces/matching.py` - Has ISkillMatcher, IQueryNormalizer, IPatternRegistry
- `lib/skill_router/matching/result.py` - Has MatchResult for skill matching
- `lib/skill_router/matching/normalizer.py` - DefaultQueryNormalizer can inform tokenizer
- `lib/skill_router/models.py` - Task model already exists with triggers and skills fields

New Components Needed:
- ITaskMatcher, IWordOverlapScorer, IWordTokenizer interfaces
- TaskMatchResult dataclass (separate from MatchResult)
</context>

<implementation>
Follow TDD approach:
1. Tests will be created for each interface and model
2. Implement interfaces and TaskMatchResult model
3. Ensure all tests pass

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Add new interfaces to existing `lib/skill_router/interfaces/matching.py`
- Add TaskMatchResult to existing `lib/skill_router/matching/result.py`
- Use typing for all method signatures
</implementation>

<verification>
Foundational components must be implemented:
- [ ] ITaskMatcher interface defined
- [ ] IWordOverlapScorer interface defined
- [ ] IWordTokenizer interface defined
- [ ] TaskMatchResult dataclass with all fields
- [ ] TaskMatchResult.no_match() factory method
- [ ] TaskMatchResult.from_task() factory method
- [ ] TaskMatchResult.is_match() method
</verification>

<success_criteria>
- All interface contracts defined with proper type hints
- TaskMatchResult model complete with factory methods
- Tests verify interface contracts
- Code follows project coding standards
</success_criteria>
