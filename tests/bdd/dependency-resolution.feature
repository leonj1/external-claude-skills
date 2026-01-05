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

  # Cycle Detection Scenarios

  Scenario: Detect simple circular dependency
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-a]  |
    When the dependency resolver checks for cycles
    Then a cycle is detected containing "skill-a" and "skill-b"

  Scenario: Detect complex circular dependency
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-c]  |
      | skill-c  | [skill-a]  |
    When the dependency resolver checks for cycles
    Then a cycle is detected

  Scenario: Handle circular dependency gracefully during resolution
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-a]  |
    When the dependency resolver processes skill "skill-a"
    Then resolution completes with a warning
    And all skills are included in the result

  # Edge Case Scenarios

  Scenario: Handle skill with missing dependency reference
    Given skill "broken-skill" depends on "non-existent-skill"
    And "non-existent-skill" is not in the manifest
    When the dependency resolver processes "broken-skill"
    Then the missing dependency is skipped
    And a warning is logged

  Scenario: Handle empty skills list
    Given a request for no skills
    When the dependency resolver processes the skills
    Then the execution order is empty

  Scenario: Handle deeply nested dependencies
    Given a chain of 5 dependent skills
      | skill    | depends_on |
      | level-1  | []         |
      | level-2  | [level-1]  |
      | level-3  | [level-2]  |
      | level-4  | [level-3]  |
      | level-5  | [level-4]  |
    When the dependency resolver processes skill "level-5"
    Then the execution order contains 5 skills
    And skills appear in level order from 1 to 5
