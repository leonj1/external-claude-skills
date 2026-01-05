---
executor: bdd
source_feature: ./tests/bdd/dependency-resolution.feature
scenario_filter: multi_skill
---

<objective>
Implement multiple skills dependency resolution. The resolver must handle requests
for multiple skills at once, deduplicating shared dependencies and returning a
single execution order that satisfies all requested skills.
</objective>

<gherkin>
Feature: Dependency Resolution with Topological Sort
  As a skill router
  I want to resolve skill dependencies in correct order
  So that skills are loaded after their prerequisites

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains skills with dependencies
      | name                 | depends_on                    |
      | terraform-base       | []                            |
      | ecr-setup            | [terraform-base]              |
      | aws-static-hosting   | [terraform-base]              |
      | aws-ecs-deployment   | [terraform-base, ecr-setup]   |
      | eks-cluster          | [terraform-base]              |
      | k8s-deployment       | [eks-cluster]                 |
      | auth-cognito         | [terraform-base]              |
      | rds-postgres         | [terraform-base]              |
      | nextjs-standards     | []                            |
      | github-actions-cicd  | []                            |

  # Multiple Skills Resolution Scenarios

  Scenario: Resolve multiple skills with shared dependencies
    Given a request for skills
      | skill              |
      | aws-static-hosting |
      | aws-ecs-deployment |
    When the dependency resolver processes the skills
    Then "terraform-base" appears exactly once
    And "terraform-base" appears first
    And both "aws-static-hosting" and "aws-ecs-deployment" appear after "terraform-base"

  Scenario: Resolve multiple independent skills
    Given a request for skills
      | skill               |
      | nextjs-standards    |
      | github-actions-cicd |
    When the dependency resolver processes the skills
    Then the execution order contains both skills
    And the order between them is arbitrary

  Scenario: Resolve task skills with complex dependencies
    Given task "admin-panel" requires skills
      | skill                |
      | react-admin-standards |
      | fastapi-standards    |
      | aws-ecs-deployment   |
      | rds-postgres         |
      | auth-cognito         |
    And skill "react-admin-standards" has no dependencies
    And skill "fastapi-standards" has no dependencies
    When the dependency resolver processes the task skills
    Then "terraform-base" appears before all dependent skills
    And "ecr-setup" appears before "aws-ecs-deployment"

  # Topological Sort Validation Scenarios

  Scenario: Validate execution order respects all dependencies
    Given a request for skill "aws-ecs-deployment"
    When the dependency resolver processes the skill
    Then for each skill in the execution order
    And all its dependencies appear earlier in the order

  Scenario: Collect all transitive dependencies
    Given a request for skill "aws-ecs-deployment"
    When the dependency resolver collects dependencies
    Then the collected set contains "terraform-base"
    And the collected set contains "ecr-setup"
    And the collected set contains "aws-ecs-deployment"
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. resolve_multi(skill_names, skills) method on IDependencyResolver
2. collect_dependencies(skill_name, skills) method for transitive collection
3. Deduplication of shared dependencies across multiple skills
4. Support for Task-based skill resolution

Multi-Skill Resolution Rules:
- Shared dependencies appear exactly once in output
- Dependencies always appear before any skill that depends on them
- Independent skills (no shared deps) can appear in any order relative to each other
- All requested skills appear in output

Dependency Collection Rules:
- Returns Set of all skill names needed (including target)
- Recursive traversal of depends_on chains
- Union of all dependencies when multiple skills requested

</requirements>

<context>
BDD Specification: specs/DRAFT-dependency-resolver.md
Feature File: tests/bdd/dependency-resolution.feature
Previous Prompt: 001-bdd-dependency-resolver-single-skill.md

Existing Code to Reuse:
- lib/skill_router/models.py: Skill, Task dataclasses
- lib/skill_router/dependency_resolver.py: KahnsDependencyResolver (from prompt 001)
- lib/skill_router/interfaces/dependency.py: IDependencyResolver (from prompt 001)

Components to Extend:
- Add resolve_multi() and collect_dependencies() to IDependencyResolver
- Implement methods in KahnsDependencyResolver
</context>

<implementation>
Follow TDD approach:
1. Write tests from Gherkin scenarios
2. Extend existing implementation to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max)
- Extend existing interfaces and implementations
- Reuse single-skill resolution logic where possible
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Resolve multiple skills with shared dependencies
- [ ] Scenario: Resolve multiple independent skills
- [ ] Scenario: Resolve task skills with complex dependencies
- [ ] Scenario: Validate execution order respects all dependencies
- [ ] Scenario: Collect all transitive dependencies
</verification>

<success_criteria>
- All 5 multi-skill resolution Gherkin scenarios pass
- resolve_multi() handles multiple skills correctly
- collect_dependencies() returns complete transitive set
- Shared dependencies appear exactly once
- Code follows project coding standards
</success_criteria>
