Feature: Direct Skill Matching (Tier 1 Routing)
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

  # Exact Name Match Scenarios

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

  # Pattern-Based Match Scenarios

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

  # Case Sensitivity Scenarios

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

  # Priority and Ambiguity Scenarios

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

  # Edge Case Scenarios

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
