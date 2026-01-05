---
executor: bdd
source_feature: ./tests/bdd/task-trigger-matching.feature
---

<objective>
Implement word overlap matching with 60% threshold for Task Trigger Matching.
Users should match tasks when their query contains sufficient overlap with trigger phrases.
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

  # Word Overlap Matching Scenarios

  Scenario: Match task when query contains trigger words
    Given a user query "I want to build a static website for my business"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match task with 60 percent word overlap
    Given a user query "build static website"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: No match when word overlap below threshold
    Given a user query "website"
    When the router processes the query at tier 2
    Then no task trigger match is found
    And the router proceeds to tier 3
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **Word Overlap Scoring Logic**
   - Score = |query_words INTERSECT trigger_words| / |trigger_words|
   - For "build static website" vs "build a static website":
     - Query words: {build, static, website}
     - Trigger words: {build, a, static, website}
     - Overlap: {build, static, website} = 3 words
     - Score: 3/4 = 0.75 (passes 60% threshold)
   - For "website" vs "build a static website":
     - Query words: {website}
     - Overlap: {website} = 1 word
     - Score: 1/4 = 0.25 (fails 60% threshold)

2. **WordOverlapScorer Enhancement**
   - Return 0.0 if score < threshold (default 0.6)
   - Return actual coverage score if >= threshold

3. **TaskTriggerMatcher Enhancement**
   - Check all triggers for each task
   - Track best score across all task/trigger combinations
   - Return TaskMatchResult.no_match() when no trigger meets threshold

Edge Cases to Handle:
- Query with extra words not in trigger (should still match if threshold met)
- Single word queries
- Empty trigger words set
</requirements>

<context>
BDD Specification: specs/DRAFT-task-trigger-matcher.md

Dependencies (from prompts 001-002):
- WordTokenizer (implemented)
- WordOverlapScorer (implemented, enhance threshold logic)
- TaskTriggerMatcher (implemented, ensure threshold behavior)
</context>

<implementation>
Follow TDD approach:
1. Create tests for word overlap scenarios
2. Create tests for threshold behavior
3. Enhance scorer threshold logic if needed
4. Ensure TaskTriggerMatcher returns no_match() correctly
5. All scenarios pass

Test Calculations:
- "build static website" -> trigger "build a static website" -> 3/4 = 0.75 >= 0.6 MATCH
- "website" -> trigger "build a static website" -> 1/4 = 0.25 < 0.6 NO MATCH
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Match task when query contains trigger words
- [ ] Scenario: Match task with 60 percent word overlap
- [ ] Scenario: No match when word overlap below threshold
</verification>

<success_criteria>
- All 3 Gherkin scenarios pass
- Queries with extra words still match if coverage >= 60%
- Queries below 60% coverage return no_match
- Router proceeds to tier 3 when tier 2 fails
- Code follows project coding standards
</success_criteria>
