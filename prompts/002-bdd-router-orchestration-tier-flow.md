---
executor: bdd
source_feature: ./tests/bdd/router-orchestration.feature
---

<objective>
Implement the 3-tier short-circuit routing logic that processes queries through
Tier 1 (Direct Skill), Tier 2 (Task Trigger), and Tier 3 (LLM Discovery) in sequence,
short-circuiting when a match is found.
</objective>

<gherkin>
Feature: Router Orchestration (3-Tier Flow)
  As a skill router system
  I want to orchestrate the 3-tier matching flow
  So that queries are routed efficiently and correctly

  Background:
    Given a skill router system with all components initialized
    And the manifest is loaded and validated

  # Tier Flow Scenarios

  Scenario: Tier 1 match short-circuits remaining tiers
    Given a user query "use terraform-base"
    When the router processes the query
    Then tier 1 direct skill matching executes
    And tier 1 finds a match
    And tier 2 does not execute
    And tier 3 does not execute

  Scenario: Tier 2 executes only when tier 1 fails
    Given a user query "build a static website"
    When the router processes the query
    Then tier 1 direct skill matching executes
    And tier 1 finds no match
    And tier 2 task trigger matching executes
    And tier 2 finds a match
    And tier 3 does not execute

  Scenario: Tier 3 executes only when tier 1 and 2 fail
    Given a user query "set up user authentication"
    And no direct skill match exists
    And no task trigger match exists
    When the router processes the query
    Then tier 1 finds no match
    And tier 2 finds no match
    And tier 3 LLM discovery executes

  # Performance Scenarios

  Scenario: Direct skill match responds quickly
    Given a user query "use terraform-base"
    When the router processes the query
    Then the response time is under latency threshold for tier 1

  Scenario: Task trigger match responds without LLM call
    Given a user query "build a static website"
    When the router processes the query
    Then no LLM API call is made
    And the response time is under latency threshold for tier 2
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. SkillRouter class implementing IRouter
2. Constructor accepting:
   - manifest: Manifest
   - normalizer: IQueryNormalizer
   - direct_matcher: IDirectSkillMatcher
   - task_matcher: ITaskMatcher
   - llm_discovery: ILLMDiscovery
   - dependency_resolver: IDependencyResolver
3. route(query: str) method with 3-tier flow:
   - Step 1: Normalize query
   - Step 2: Tier 1 - direct_matcher.match() - short-circuit if match
   - Step 3: Tier 2 - task_matcher.match() - short-circuit if match
   - Step 4: Tier 3 - llm_discovery.discover() - fallback
4. Short-circuit logic: return immediately when match found
5. Dependency resolution for each tier's matched skill(s)

Edge Cases to Handle:
- Empty normalized query returns no_match immediately
- LLM discovery failure returns no_match (graceful degradation)
- Tier 3 may match a task name instead of skill name
</requirements>

<context>
BDD Specification: specs/DRAFT-router-orchestration.md

Existing Components to Wire:
- IDirectSkillMatcher: Tier 1 matcher (already implemented)
- ITaskMatcher: Tier 2 matcher (already implemented)
- ILLMDiscovery: Tier 3 discovery (already implemented)
- IDependencyResolver: resolve() and resolve_multi() (already implemented)
- Manifest: skills and tasks dictionaries (already implemented)

Short-Circuit Logic Table:
| Tier | Match Found | Next Action |
|------|-------------|-------------|
| 1 | Yes | Return immediately, skip Tier 2 and 3 |
| 1 | No | Continue to Tier 2 |
| 2 | Yes | Return immediately, skip Tier 3 |
| 2 | No | Continue to Tier 3 |
| 3 | Yes | Return with discovery match |
| 3 | No | Return error (no match) |

File Structure:
```
lib/skill_router/
  router/
    skill_router.py        # SkillRouter orchestrator
```
</context>

<implementation>
Follow TDD approach:
1. Write tests for short-circuit behavior (mock all tier matchers)
2. Write tests verifying tier execution order
3. Write tests for dependency resolution integration
4. Write tests for performance (no LLM call when tier 1/2 match)
5. Implement SkillRouter to make tests pass

Architecture Guidelines:
- Use dependency injection for all matchers
- Short-circuit using early returns
- Follow strict-architecture rules (500 lines max)
- Use mocks for tier matchers in tests
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Tier 1 match short-circuits remaining tiers
- [ ] Scenario: Tier 2 executes only when tier 1 fails
- [ ] Scenario: Tier 3 executes only when tier 1 and 2 fail
- [ ] Scenario: Direct skill match responds quickly
- [ ] Scenario: Task trigger match responds without LLM call
</verification>

<success_criteria>
- SkillRouter implements IRouter interface
- Tier 1 match short-circuits Tier 2 and 3
- Tier 2 match short-circuits Tier 3
- Tier 3 executes only when Tier 1 and 2 fail
- No LLM API call when Tier 1 or 2 matches
- All tests pass
- Code follows project coding standards
</success_criteria>
