---
executor: bdd
source_feature: ./tests/bdd/task-trigger-matching.feature
---

<objective>
Implement skills resolution and tier priority handling for Task Trigger Matching.
Matched tasks should return their full skills list, and Tier 1 (direct skill match) takes priority over Tier 2 (task trigger match).
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

  # Skills Resolution Scenarios

  Scenario: Return all skills required by matched task
    Given task "static-website" requires skills
      | skill               |
      | nextjs-standards    |
      | aws-static-hosting  |
      | github-actions-cicd |
    And a user query "create a landing page"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"
    And the primary skills list contains "nextjs-standards"
    And the primary skills list contains "aws-static-hosting"
    And the primary skills list contains "github-actions-cicd"

  # Tier Priority Scenarios

  Scenario: Tier 1 takes priority over Tier 2
    Given a user query "use terraform-base to build a static website"
    And the manifest contains skill "terraform-base"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "terraform-base"
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **Skills Resolution in TaskMatchResult**
   - TaskMatchResult.skills populated from Task.skills
   - TaskMatchResult.from_task() copies task.skills list
   - Skills returned in order defined in task

2. **Skills List Assertion Support**
   - RouteResult (or equivalent) must expose skills list
   - Tests can verify specific skills are present

3. **Tier Priority in Router (Integration)**
   - Router checks Tier 1 (DirectSkillMatcher) FIRST
   - If Tier 1 matches, return immediately (route_type="skill")
   - Only if Tier 1 fails, proceed to Tier 2 (TaskTriggerMatcher)
   - If Tier 2 matches, return route_type="task" with skills list

Edge Cases:
- Task with empty skills list
- Query that matches both skill and task trigger
- Skills list with duplicates (should preserve or dedupe?)
</requirements>

<context>
BDD Specification: specs/DRAFT-task-trigger-matcher.md

Reuse Opportunities:
- `lib/skill_router/matching/direct_matcher.py` - DirectSkillMatcher for Tier 1
- `lib/skill_router/models.py` - Task.skills is List[str]
- `lib/skill_router/matching/result.py` - MatchResult for Tier 1 results

Dependencies (from prompts 001-004):
- TaskTriggerMatcher (implemented)
- TaskMatchResult with skills field (implemented)

Integration Point:
- Router orchestration (may be in Task 1.6) will use both matchers
- This prompt focuses on TaskMatchResult.skills and tier priority concept
</context>

<implementation>
Follow TDD approach:
1. Create tests for skills resolution
2. Create tests for tier priority
3. Ensure TaskMatchResult properly copies skills
4. Ensure router (or test harness) checks Tier 1 before Tier 2
5. All scenarios pass

Test Setup for Skills Resolution:
- Create Task with skills: ["nextjs-standards", "aws-static-hosting", "github-actions-cicd"]
- Match query "create a landing page"
- Verify result.skills contains all three

Test Setup for Tier Priority:
- Create Skill "terraform-base"
- Create Task "static-website" with trigger "build a static website"
- Query: "use terraform-base to build a static website"
- Tier 1 (DirectSkillMatcher) finds "terraform-base" -> return immediately
- Tier 2 never executed
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Return all skills required by matched task
- [ ] Scenario: Tier 1 takes priority over Tier 2
</verification>

<success_criteria>
- All 2 Gherkin scenarios pass
- TaskMatchResult.skills properly populated
- Tier 1 results take priority over Tier 2
- Skills list contains all required skills
- Code follows project coding standards
</success_criteria>
