---
executor: bdd
source_feature: ./tests/bdd/direct-skill-matching.feature
scenario_filter: pattern-based match
---

<objective>
Implement pattern-based matching for Tier 1 Direct Skill Matcher.
Match user queries using common request patterns like "use {skill}", "apply {skill}", etc.
</objective>

<gherkin>
Feature: Direct Skill Matching (Tier 1 Routing) - Pattern-Based Match
  As a power user
  I want to request skills using common phrases
  So that I can invoke skills naturally

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains skills
      | name                  | description                     |
      | terraform-base        | Terraform state backend setup   |
      | aws-ecs-deployment    | ECS Fargate deployment          |
      | auth-cognito          | AWS Cognito authentication      |
      | nextjs-standards      | Next.js project conventions     |

  Scenario Outline: Match skill using common request patterns
    Given a user query "<query>"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "<expected_skill>"

    Examples:
      | query                                | expected_skill     |
      | use terraform-base                   | terraform-base     |
      | apply aws-ecs-deployment             | aws-ecs-deployment |
      | run terraform-base setup             | terraform-base     |
      | execute auth-cognito configuration   | auth-cognito       |
      | terraform-base skill                 | terraform-base     |
      | deploy with aws-ecs-deployment       | aws-ecs-deployment |
      | set up auth-cognito                  | auth-cognito       |
      | configure nextjs-standards           | nextjs-standards   |
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. IPatternRegistry interface
   - get_patterns() -> List[str]: Return pattern templates
   - expand_pattern(pattern, skill_name) -> str: Substitute {skill} placeholder

2. DefaultPatternRegistry implementation with patterns:
   - "use {skill}"
   - "apply {skill}"
   - "run {skill}"
   - "execute {skill}"
   - "{skill} skill"
   - "deploy with {skill}"
   - "set up {skill}"
   - "configure {skill}"

3. Extend DirectSkillMatcher to support pattern matching
   - After exact match fails, try pattern-based matching
   - Expand each pattern with each skill name
   - Check if expanded pattern appears in normalized query
   - Return MatchResult.pattern_match() with confidence 0.9

Edge Cases to Handle:
- Pattern with skill at start ("{skill} skill")
- Pattern with skill at end ("use {skill}")
- Pattern with skill in middle ("deploy with {skill}")
- Patterns with multiple words ("set up {skill}")
</requirements>

<context>
BDD Specification: specs/DRAFT-direct-skill-matcher.md
Source Feature: tests/bdd/direct-skill-matching.feature

Existing Code (from prompt 001):
- lib/skill_router/interfaces/matching.py: ISkillMatcher, IQueryNormalizer
- lib/skill_router/matching/result.py: MatchResult
- lib/skill_router/matching/normalizer.py: DefaultQueryNormalizer
- lib/skill_router/matching/direct_matcher.py: DirectSkillMatcher (exact match)

New Files to Create:
- lib/skill_router/matching/patterns.py: DefaultPatternRegistry
</context>

<implementation>
Follow TDD approach:
1. Write tests for pattern matching scenarios
2. Implement IPatternRegistry interface
3. Implement DefaultPatternRegistry with DEFAULT_PATTERNS
4. Extend DirectSkillMatcher to inject IPatternRegistry
5. Add pattern matching logic after exact match

Architecture Guidelines:
- Pattern registry injectable for testability
- Patterns stored as constants in DEFAULT_PATTERNS
- Match confidence 0.9 for pattern matches (vs 1.0 for exact)
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: use terraform-base
- [ ] Scenario: apply aws-ecs-deployment
- [ ] Scenario: run terraform-base setup
- [ ] Scenario: execute auth-cognito configuration
- [ ] Scenario: terraform-base skill
- [ ] Scenario: deploy with aws-ecs-deployment
- [ ] Scenario: set up auth-cognito
- [ ] Scenario: configure nextjs-standards
</verification>

<success_criteria>
- All pattern match Gherkin scenarios pass
- IPatternRegistry interface defined
- DefaultPatternRegistry with 8 default patterns
- DirectSkillMatcher uses pattern registry
- Pattern matches return confidence 0.9
</success_criteria>
Archived: 2026-01-05 00:06:06
