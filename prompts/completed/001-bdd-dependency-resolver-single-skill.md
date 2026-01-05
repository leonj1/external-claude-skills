---
executor: bdd
source_feature: ./tests/bdd/dependency-resolution.feature
scenario_filter: single_skill
---

<objective>
Implement single skill dependency resolution using topological sort (Kahn's algorithm).
The resolver must determine correct execution order for a single requested skill,
ensuring all dependencies are loaded before dependents.
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

  # Single Skill Resolution Scenarios

  Scenario: Resolve skill with no dependencies
    Given a request for skill "nextjs-standards"
    When the dependency resolver processes the skill
    Then the execution order contains only "nextjs-standards"

  Scenario: Resolve skill with single dependency
    Given a request for skill "ecr-setup"
    When the dependency resolver processes the skill
    Then the execution order is
      | order | skill           |
      | 1     | terraform-base  |
      | 2     | ecr-setup       |

  Scenario: Resolve skill with multiple dependencies
    Given a request for skill "aws-ecs-deployment"
    When the dependency resolver processes the skill
    Then "terraform-base" appears before "aws-ecs-deployment"
    And "ecr-setup" appears before "aws-ecs-deployment"
    And "terraform-base" appears before "ecr-setup"

  Scenario: Resolve skill with transitive dependencies
    Given a request for skill "k8s-deployment"
    When the dependency resolver processes the skill
    Then the execution order is
      | order | skill           |
      | 1     | terraform-base  |
      | 2     | eks-cluster     |
      | 3     | k8s-deployment  |
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. IDependencyResolver interface with `resolve(skill_name, skills)` method
2. ITopologicalSorter interface with `sort(nodes, edges)` method
3. KahnsDependencyResolver class implementing IDependencyResolver
4. collect_dependencies() to gather transitive dependencies recursively
5. Kahn's algorithm for topological sort:
   - Build in-degree map for all nodes
   - Initialize queue with nodes having in-degree 0
   - Process queue, decrementing in-degrees of dependents
   - Return ordered list

Execution Order Rules:
- Skill with no dependencies returns only itself
- Skill with dependencies returns dependencies first, then skill
- Transitive dependencies resolved recursively (A->B->C means order: C, B, A)
- Multiple dependencies at same level can appear in any order relative to each other

</requirements>

<context>
BDD Specification: specs/DRAFT-dependency-resolver.md
Feature File: tests/bdd/dependency-resolution.feature

Existing Code to Reuse:
- lib/skill_router/models.py: Skill dataclass with depends_on field
- lib/skill_router/exceptions.py: Base exception classes
- lib/skill_router/interfaces/: Interface directory structure

New Components Needed:
- lib/skill_router/interfaces/dependency.py: IDependencyResolver, ITopologicalSorter
- lib/skill_router/dependency_resolver.py: KahnsDependencyResolver implementation
- lib/skill_router/dependency_graph.py: DependencyGraph, DependencyResult dataclasses
</context>

<implementation>
Follow TDD approach:
1. Write tests from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Use existing Skill model from models.py
- Create new interfaces in interfaces/ directory
- Implementation in separate dependency_resolver.py file
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Resolve skill with no dependencies
- [ ] Scenario: Resolve skill with single dependency
- [ ] Scenario: Resolve skill with multiple dependencies
- [ ] Scenario: Resolve skill with transitive dependencies
</verification>

<success_criteria>
- All 4 single skill resolution Gherkin scenarios pass
- IDependencyResolver interface defined
- ITopologicalSorter interface defined
- KahnsDependencyResolver implements resolve() method
- Code follows project coding standards
</success_criteria>
