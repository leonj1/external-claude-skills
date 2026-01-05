---
executor: bdd
source_feature: ./tests/bdd/task-trigger-matching.feature
---

<objective>
Implement exact trigger matching with case and whitespace normalization for Task Trigger Matching.
Users should be able to match tasks using exact trigger phrases regardless of case or formatting.
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

  # Exact Trigger Match Scenarios

  Scenario: Match task with exact trigger phrase
    Given a user query "build a static website"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match different task with exact trigger
    Given a user query "create a dashboard"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "admin-panel"

  # Case and Formatting Scenarios

  Scenario: Match triggers case-insensitively
    Given a user query "BUILD A STATIC WEBSITE"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match with extra whitespace in query
    Given a user query "  build   a   static   website  "
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **WordTokenizer** (`lib/skill_router/matching/tokenizer.py`)
   - Implements IWordTokenizer interface
   - Normalizes to lowercase
   - Strips leading/trailing whitespace
   - Splits on whitespace (handles multiple spaces)
   - Returns Set[str] of words

2. **WordOverlapScorer** (`lib/skill_router/matching/scorer.py`)
   - Implements IWordOverlapScorer interface
   - Computes: overlap = |query_words INTERSECT trigger_words| / |trigger_words|
   - Returns 1.0 for exact match (all trigger words present)
   - Default threshold: 0.6 (60%)

3. **TaskTriggerMatcher** (`lib/skill_router/matching/task_matcher.py`)
   - Implements ITaskMatcher interface
   - Uses WordTokenizer and WordOverlapScorer via dependency injection
   - For exact matches, score should be 1.0

Edge Cases to Handle:
- Empty query string
- Query with only whitespace
- Mixed case input
- Multiple consecutive spaces
</requirements>

<context>
BDD Specification: specs/DRAFT-task-trigger-matcher.md

Reuse Opportunities:
- `lib/skill_router/matching/normalizer.py` - DefaultQueryNormalizer logic can be reused
- `lib/skill_router/models.py` - Task.triggers is List[str]

Dependencies (from prompt 001):
- ITaskMatcher, IWordOverlapScorer, IWordTokenizer interfaces
- TaskMatchResult model
</context>

<implementation>
Follow TDD approach:
1. Create tests for exact trigger matching scenarios
2. Create tests for case and whitespace normalization
3. Implement WordTokenizer
4. Implement WordOverlapScorer
5. Implement TaskTriggerMatcher
6. Ensure all scenarios pass

Architecture Guidelines:
- Each class in its own file (tokenizer.py, scorer.py, task_matcher.py)
- Use dependency injection for tokenizer and scorer
- Follow 500 lines max per file
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Match task with exact trigger phrase
- [ ] Scenario: Match different task with exact trigger
- [ ] Scenario: Match triggers case-insensitively
- [ ] Scenario: Match with extra whitespace in query
</verification>

<success_criteria>
- All 4 Gherkin scenarios pass
- Exact trigger matches return score 1.0
- Case insensitive matching works
- Whitespace normalization works
- Code follows project coding standards
</success_criteria>
