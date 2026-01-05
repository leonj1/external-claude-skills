---
executor: bdd
source_feature: ./tests/bdd/direct-skill-matching.feature
scenario_filter: case sensitivity
---

<objective>
Implement case-insensitive matching for Tier 1 Direct Skill Matcher.
Ensure skill names match regardless of case in user queries.
</objective>

<gherkin>
Feature: Direct Skill Matching (Tier 1 Routing) - Case Sensitivity
  As a power user
  I want skill matching to ignore case
  So that I can type naturally without worrying about capitalization

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains skills
      | name                  | description                     |
      | terraform-base        | Terraform state backend setup   |
      | aws-ecs-deployment    | ECS Fargate deployment          |
      | auth-cognito          | AWS Cognito authentication      |
      | nextjs-standards      | Next.js project conventions     |

  Scenario: Match skill name case-insensitively
    Given a user query "USE TERRAFORM-BASE"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "terraform-base"

  Scenario: Match mixed case skill request
    Given a user query "Apply Aws-Ecs-Deployment to my service"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "aws-ecs-deployment"
</gherkin>

<requirements>
Based on the Gherkin scenarios, verify/implement:

1. Verify DefaultQueryNormalizer converts to lowercase
   - "USE TERRAFORM-BASE" -> "use terraform-base"
   - "Apply Aws-Ecs-Deployment" -> "apply aws-ecs-deployment"

2. Verify DirectSkillMatcher compares normalized query with lowercase skill names
   - skill_name.lower() compared against normalized_query
   - Original skill name (with original casing) returned in MatchResult

3. Ensure matched item preserves original skill name casing
   - Input: "USE TERRAFORM-BASE"
   - Match against: "terraform-base" (lowercase)
   - Return: "terraform-base" (original from manifest)

Edge Cases to Handle:
- ALL CAPS query
- Mixed CamelCase and lowercase
- Skill names with hyphens in different cases
</requirements>

<context>
BDD Specification: specs/DRAFT-direct-skill-matcher.md
Source Feature: tests/bdd/direct-skill-matching.feature

Existing Code (from prompts 001-002):
- lib/skill_router/matching/normalizer.py: DefaultQueryNormalizer (verify lowercase)
- lib/skill_router/matching/direct_matcher.py: DirectSkillMatcher (verify case handling)
</context>

<implementation>
Follow TDD approach:
1. Write tests for case-insensitive matching scenarios
2. Verify normalizer converts to lowercase (may already work)
3. Verify matcher compares with lowercased skill names
4. Verify original skill name returned in result

Architecture Guidelines:
- Case normalization happens in normalizer only
- Matcher stores original skill names, compares lowercase versions
- No changes to existing interfaces needed
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Match skill name case-insensitively
- [ ] Scenario: Match mixed case skill request
</verification>

<success_criteria>
- Case-insensitive matching works for ALL CAPS queries
- Case-insensitive matching works for MixedCase queries
- Original skill name from manifest returned in MatchResult
- No new interfaces or classes needed (verify existing implementation)
</success_criteria>
Archived: 2026-01-05 00:06:35
