---
executor: bdd
source_feature: ./tests/bdd/router-orchestration.feature
---

<objective>
Implement the Router Orchestration interfaces and data models for the 3-tier routing pipeline.
This includes IRouter, IQueryNormalizer, RouteResult, RouteType, and SkillMatchResult.
</objective>

<gherkin>
Feature: Router Orchestration (3-Tier Flow)
  As a skill router system
  I want to orchestrate the 3-tier matching flow
  So that queries are routed efficiently and correctly

  Background:
    Given a skill router system with all components initialized
    And the manifest is loaded and validated

  # Route Result Construction Scenarios (models)

  Scenario: Skill match returns correct route result
    Given a user query "apply ecr-setup"
    When the router processes the query
    Then the route result has type "skill"
    And the route result has matched "ecr-setup"
    And the route result skills list contains "ecr-setup"
    And the execution order includes "ecr-setup" and its dependencies

  Scenario: Task match returns correct route result
    Given a user query "create a REST API"
    And task "rest-api" exists with skills
      | skill             |
      | fastapi-standards |
      | aws-ecs-deployment |
      | rds-postgres      |
    When the router processes the query
    Then the route result has type "task"
    And the route result has matched "rest-api"
    And the route result skills list contains all task skills

  Scenario: Discovery match returns correct route result
    Given a user query "help with database setup"
    And tier 1 and tier 2 find no match
    And the LLM selects skill "rds-postgres"
    When the router processes the query
    Then the route result has type "discovery"
    And the route result has matched "rds-postgres"

  Scenario: Return error when no match found at any tier
    Given a user query "random nonsense query"
    And tier 1 finds no match
    And tier 2 finds no match
    And tier 3 returns no valid match
    When the router processes the query
    Then the route result has type "error"
    And the route result has empty matched
    And the route result has empty skills list
    And the route result has empty execution order
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. RouteType enum with values: SKILL, TASK, DISCOVERY, ERROR
2. RouteResult dataclass with:
   - route_type: RouteType
   - matched: str (skill or task name)
   - skills: List[str] (skill names to load)
   - execution_order: List[str] (dependency-resolved order)
   - tier: int (1, 2, or 3)
   - confidence: float (1.0 for tier 1/2, LLM confidence for tier 3)
3. Factory methods on RouteResult:
   - skill_match(skill_name, execution_order)
   - task_match(task_name, skills, execution_order)
   - discovery_match(skill_name, execution_order, confidence)
   - no_match()
4. is_match() method to check if result is valid
5. SkillMatchResult dataclass for Tier 1 results
6. IRouter interface with route(query: str) -> RouteResult
7. IQueryNormalizer interface with normalize(query: str) -> str

Edge Cases to Handle:
- Empty matched string for error results
- Empty skills list for error results
- Empty execution_order for error results
- tier=0 and confidence=0.0 for error results
</requirements>

<context>
BDD Specification: specs/DRAFT-router-orchestration.md

Existing Components to Wire:
- IDirectSkillMatcher from lib/skill_router/interfaces/ (Tier 1)
- ITaskMatcher from lib/skill_router/interfaces/ (Tier 2)
- ILLMDiscovery from lib/skill_router/interfaces/discovery.py (Tier 3)
- IDependencyResolver from lib/skill_router/interfaces/dependency.py

File Structure:
```
lib/skill_router/
  router/
    __init__.py
    interfaces.py          # IRouter, IQueryNormalizer
    models.py              # RouteResult, RouteType, SkillMatchResult
```
</context>

<implementation>
Follow TDD approach:
1. Write tests for RouteType enum values
2. Write tests for RouteResult dataclass and factory methods
3. Write tests for SkillMatchResult dataclass
4. Write tests for interface contracts
5. Implement to make tests pass

Architecture Guidelines:
- Use frozen dataclasses for immutability
- Use Enum for RouteType
- Use ABC for interfaces
- Follow strict-architecture rules (500 lines max)
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Skill match returns correct route result
- [ ] Scenario: Task match returns correct route result
- [ ] Scenario: Discovery match returns correct route result
- [ ] Scenario: Return error when no match found at any tier
</verification>

<success_criteria>
- RouteType enum has all 4 values
- RouteResult has all required fields and factory methods
- SkillMatchResult has skill_name, pattern_matched, and factory methods
- IRouter and IQueryNormalizer interfaces defined
- All tests pass
- Code follows project coding standards
</success_criteria>
