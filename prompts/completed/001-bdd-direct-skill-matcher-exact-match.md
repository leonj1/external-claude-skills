---
executor: bdd
source_feature: ./tests/bdd/direct-skill-matching.feature
scenario_filter: exact name match
---

<objective>
Implement exact name matching for Tier 1 Direct Skill Matcher.
Match user queries containing skill names directly embedded in the text.
</objective>

<gherkin>
Feature: Direct Skill Matching (Tier 1 Routing) - Exact Name Match
  As a power user
  I want to directly request skills by name
  So that I can bypass discovery and use specific capabilities

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains skills
      | name                  | description                     |
      | terraform-base        | Terraform state backend setup   |
      | aws-ecs-deployment    | ECS Fargate deployment          |
      | auth-cognito          | AWS Cognito authentication      |
      | nextjs-standards      | Next.js project conventions     |

  Scenario: Match skill by exact name in query
    Given a user query "use terraform-base for this project"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "terraform-base"
    And the primary skills list contains "terraform-base"

  Scenario: Match skill name embedded in query
    Given a user query "I want to deploy with aws-ecs-deployment"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "aws-ecs-deployment"

  Scenario: Match skill with hyphenated name
    Given a user query "configure auth-cognito for login"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "auth-cognito"
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. IQueryNormalizer interface and DefaultQueryNormalizer implementation
   - Convert query to lowercase
   - Strip whitespace
   - Handle punctuation around skill names

2. MatchResult dataclass with factory methods
   - skill_name: Optional[str]
   - match_type: Optional[str] ("exact", "pattern", None)
   - confidence: float (1.0 for exact match)
   - Factory methods: no_match(), exact_match(skill_name), pattern_match(skill_name)

3. ISkillMatcher interface with match(query, skills) method

4. DirectSkillMatcher implementation (exact match portion)
   - Normalize query before matching
   - Sort skill names by length descending (longer names first)
   - Check if normalized skill name appears in normalized query
   - Return MatchResult.exact_match() on match

Edge Cases to Handle:
- Hyphenated skill names (terraform-base, auth-cognito)
- Skill name embedded anywhere in query
- Multiple words in query around skill name
</requirements>

<context>
BDD Specification: specs/DRAFT-direct-skill-matcher.md
Source Feature: tests/bdd/direct-skill-matching.feature

Existing Code to Reuse:
- lib/skill_router/models.py: Skill dataclass
- lib/skill_router/interfaces/dependency.py: Interface pattern to follow

New Files to Create:
- lib/skill_router/interfaces/matching.py: ISkillMatcher, IPatternRegistry, IQueryNormalizer
- lib/skill_router/matching/result.py: MatchResult dataclass
- lib/skill_router/matching/normalizer.py: DefaultQueryNormalizer
- lib/skill_router/matching/direct_matcher.py: DirectSkillMatcher
</context>

<implementation>
Follow TDD approach:
1. Write tests from Gherkin scenarios first
2. Implement interfaces (ISkillMatcher, IQueryNormalizer)
3. Implement MatchResult dataclass
4. Implement DefaultQueryNormalizer
5. Implement DirectSkillMatcher (exact match logic only)

Architecture Guidelines:
- Follow interface-first design (see interfaces/dependency.py pattern)
- Use dataclasses for data models
- Max 500 lines per file
- No env vars in function signatures
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Match skill by exact name in query
- [ ] Scenario: Match skill name embedded in query
- [ ] Scenario: Match skill with hyphenated name
</verification>

<success_criteria>
- All exact match Gherkin scenarios pass
- Interfaces defined for ISkillMatcher, IQueryNormalizer
- MatchResult dataclass with factory methods
- Query normalization handles lowercase conversion
- Hyphenated skill names matched correctly
</success_criteria>
Archived: 2026-01-05 00:05:07
