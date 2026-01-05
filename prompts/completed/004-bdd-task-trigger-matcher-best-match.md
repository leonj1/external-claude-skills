---
executor: bdd
source_feature: ./tests/bdd/task-trigger-matching.feature
---

<objective>
Implement best match selection logic for Task Trigger Matching.
When multiple tasks match, the one with the highest word overlap score should win.
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

  # Best Match Selection Scenarios

  Scenario: Select task with highest word overlap score
    Given a user query "build a REST API backend service"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "rest-api"

  Scenario: Distinguish between similar tasks
    Given a user query "build a serverless API"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "serverless-api"

  Scenario: Match admin panel over generic dashboard
    Given a user query "create an internal tool for admin"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "admin-panel"

  # No Match Scenarios

  Scenario: No match for ambiguous request
    Given a user query "help me with authentication"
    When the router processes the query at tier 2
    Then no task trigger match is found
    And the router proceeds to tier 3

  Scenario: No match for unrelated query
    Given a user query "what is the weather today"
    When the router processes the query at tier 2
    Then no task trigger match is found
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **Best Match Selection in TaskTriggerMatcher**
   - For each task, check ALL triggers
   - Track best score AND best task across ALL combinations
   - Only update best if new score > current best score
   - Return task with highest overall score

2. **Score Comparison Logic**
   - "build a REST API backend service" should match "rest-api":
     - Trigger "build a backend service": 4/4 words match = 1.0
     - This beats any partial matches from other tasks
   - "build a serverless API" should match "serverless-api":
     - Trigger "build a serverless API": 4/4 = 1.0 (exact)
     - vs "build an API" on rest-api: 3/3 = 1.0 but "serverless" distinguishes

3. **No Match Handling**
   - Queries with no overlapping words return no_match()
   - Ambiguous queries that don't meet threshold return no_match()

Edge Cases:
- Multiple tasks with same score (first wins or deterministic selection)
- Queries that partially match multiple tasks
- Completely unrelated queries
</requirements>

<context>
BDD Specification: specs/DRAFT-task-trigger-matcher.md

Dependencies (from prompts 001-003):
- WordTokenizer (implemented)
- WordOverlapScorer (implemented)
- TaskTriggerMatcher (implemented, verify best-match logic)

Score Calculations for "build a serverless API":
- serverless-api trigger "build a serverless API": {build, a, serverless, api} vs {build, a, serverless, api} = 4/4 = 1.0
- rest-api trigger "build an API": {build, a, serverless, api} vs {build, an, api} = {build, api}/3 = 0.67
- Best: serverless-api with 1.0
</context>

<implementation>
Follow TDD approach:
1. Create tests for best match selection
2. Create tests for similar task disambiguation
3. Create tests for no match scenarios
4. Verify TaskTriggerMatcher selects highest score
5. All scenarios pass

Key Test Cases:
- Query matches multiple tasks -> highest score wins
- Query exactly matches one trigger -> that task wins
- Query matches nothing -> no_match returned
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Select task with highest word overlap score
- [ ] Scenario: Distinguish between similar tasks
- [ ] Scenario: Match admin panel over generic dashboard
- [ ] Scenario: No match for ambiguous request
- [ ] Scenario: No match for unrelated query
</verification>

<success_criteria>
- All 5 Gherkin scenarios pass
- Best match selection is deterministic
- Similar tasks correctly distinguished
- Unrelated queries return no_match
- Code follows project coding standards
</success_criteria>
