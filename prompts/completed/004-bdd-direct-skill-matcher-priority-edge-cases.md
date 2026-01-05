---
executor: bdd
source_feature: ./tests/bdd/direct-skill-matching.feature
scenario_filter: priority and edge cases
---

<objective>
Implement priority handling and edge cases for Tier 1 Direct Skill Matcher.
Handle ambiguous matches, no-match scenarios, and edge cases like punctuation.
</objective>

<gherkin>
Feature: Direct Skill Matching (Tier 1 Routing) - Priority and Edge Cases
  As a power user
  I want predictable matching behavior
  So that I get consistent results for ambiguous or edge case queries

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains skills
      | name                  | description                     |
      | terraform-base        | Terraform state backend setup   |
      | aws-ecs-deployment    | ECS Fargate deployment          |
      | auth-cognito          | AWS Cognito authentication      |
      | nextjs-standards      | Next.js project conventions     |

  Scenario: Prioritize longer skill name when multiple match
    Given the manifest also contains skill "terraform"
    And a user query "use terraform-base for infrastructure"
    When the router processes the query
    Then the matched item is "terraform-base"

  Scenario: No match when skill name not in query
    Given a user query "build a website for my company"
    When the router processes the query at tier 1
    Then no direct skill match is found
    And the router proceeds to tier 2

  Scenario: Handle query with only skill name
    Given a user query "terraform-base"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "terraform-base"

  Scenario: Handle skill name with surrounding punctuation
    Given a user query "Can you apply 'aws-ecs-deployment'?"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "aws-ecs-deployment"
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Priority: Longer skill names match first
   - Sort skill names by length descending before matching
   - "terraform-base" matches before "terraform" for query containing both
   - First match wins (no backtracking)

2. No-match handling
   - Return MatchResult.no_match() when no skill name found in query
   - MatchResult.no_match() has skill_name=None, match_type=None, confidence=0.0
   - Router should proceed to Tier 2 when no match

3. Minimal query handling
   - Query containing only skill name should match
   - "terraform-base" (just the name) matches terraform-base skill

4. Punctuation handling in normalizer
   - Remove single quotes: 'aws-ecs-deployment' -> aws-ecs-deployment
   - Remove double quotes: "aws-ecs-deployment" -> aws-ecs-deployment
   - Handle question marks around names

Edge Cases to Handle:
- Substring matches (terraform vs terraform-base)
- Empty or whitespace-only queries
- Queries with no recognizable skill names
- Skill names wrapped in quotes or other punctuation
</requirements>

<context>
BDD Specification: specs/DRAFT-direct-skill-matcher.md
Source Feature: tests/bdd/direct-skill-matching.feature

Existing Code (from prompts 001-003):
- lib/skill_router/matching/normalizer.py: Enhance punctuation handling
- lib/skill_router/matching/direct_matcher.py: Verify length-based priority
- lib/skill_router/matching/result.py: MatchResult.no_match() factory
</context>

<implementation>
Follow TDD approach:
1. Write tests for priority and edge case scenarios
2. Verify skill names sorted by length descending
3. Enhance normalizer to handle quotes and punctuation
4. Verify no_match() factory returns correct values
5. Test minimal query (just skill name) matching

Architecture Guidelines:
- Length-based sorting happens once per match() call
- Normalizer handles punctuation removal
- No special case code for "no match" - natural fallthrough
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Prioritize longer skill name when multiple match
- [ ] Scenario: No match when skill name not in query
- [ ] Scenario: Handle query with only skill name
- [ ] Scenario: Handle skill name with surrounding punctuation
</verification>

<success_criteria>
- Longer skill names take priority over shorter substrings
- No-match returns MatchResult with skill_name=None
- Single-word queries (just skill name) match correctly
- Quotes and punctuation around skill names handled
- All edge case scenarios pass
</success_criteria>
Archived: 2026-01-05 00:07:11
