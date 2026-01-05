---
executor: bdd
source_feature: ./tests/bdd/router-orchestration.feature
---

<objective>
Implement the DirectSkillMatcher for Tier 1 matching. This matcher identifies
queries that explicitly reference a skill by name using predefined patterns
like "use {skill}", "apply {skill}", etc.
</objective>

<gherkin>
Feature: Router Orchestration (3-Tier Flow)
  As a skill router system
  I want to orchestrate the 3-tier matching flow
  So that queries are routed efficiently and correctly

  Background:
    Given a skill router system with all components initialized
    And the manifest is loaded and validated

  # Tier 1 Direct Skill Matching

  Scenario: Tier 1 match short-circuits remaining tiers
    Given a user query "use terraform-base"
    When the router processes the query
    Then tier 1 direct skill matching executes
    And tier 1 finds a match
    And tier 2 does not execute
    And tier 3 does not execute

  Scenario: Skill match returns correct route result
    Given a user query "apply ecr-setup"
    When the router processes the query
    Then the route result has type "skill"
    And the route result has matched "ecr-setup"
    And the route result skills list contains "ecr-setup"
    And the execution order includes "ecr-setup" and its dependencies

  Scenario: Direct skill match responds quickly
    Given a user query "use terraform-base"
    When the router processes the query
    Then the response time is under latency threshold for tier 1
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. DirectSkillMatcher class implementing IDirectSkillMatcher
2. Default patterns list:
   - "use {skill}"
   - "apply {skill}"
   - "run {skill}"
   - "execute {skill}"
   - "{skill} skill"
   - "deploy with {skill}"
   - "set up {skill}"
   - "configure {skill}"
3. match(query: str, skills: Dict[str, Skill]) method:
   - Check if any skill name appears in query
   - Check if any pattern matches with skill name substituted
   - Return SkillMatchResult with matched skill or no_match
4. Constructor with optional custom patterns

Edge Cases to Handle:
- Skill name appearing as substring of another word
- Multiple potential matches (return first found)
- No skills in manifest
- Empty query after normalization
</requirements>

<context>
BDD Specification: specs/DRAFT-router-orchestration.md

Pattern Matching Logic:
1. For each skill name in manifest:
   - Check if skill name appears directly in query
   - Check each pattern with {skill} replaced by skill name
2. Return first match found

Example Patterns:
- Query: "use terraform-base" -> Pattern "use {skill}" -> Matches "terraform-base"
- Query: "apply ecr-setup" -> Pattern "apply {skill}" -> Matches "ecr-setup"
- Query: "terraform-base skill" -> Pattern "{skill} skill" -> Matches "terraform-base"

File Structure:
```
lib/skill_router/
  router/
    direct_matcher.py      # DirectSkillMatcher implementation
```
</context>

<implementation>
Follow TDD approach:
1. Write tests for exact skill name matching
2. Write tests for pattern-based matching
3. Write tests for no match scenarios
4. Write tests for custom patterns
5. Write tests for edge cases
6. Implement DirectSkillMatcher to make tests pass

Architecture Guidelines:
- Use simple string matching (no regex needed)
- Format patterns with skill name using str.format()
- Follow strict-architecture rules (500 lines max)
- Return early on first match
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Tier 1 match short-circuits remaining tiers
- [ ] Scenario: Skill match returns correct route result
- [ ] Scenario: Direct skill match responds quickly
</verification>

<success_criteria>
- DirectSkillMatcher implements IDirectSkillMatcher
- All default patterns work correctly
- Pattern matching returns correct SkillMatchResult
- No match returns SkillMatchResult.no_match()
- Custom patterns can be provided
- All tests pass
- Code follows project coding standards
</success_criteria>
