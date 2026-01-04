Feature: Hook Integration for Claude Code
  As a Claude Code user
  I want skill routing to integrate with the hooks system
  So that relevant skills are automatically loaded into context

  Background:
    Given a skill router system
    And the Claude Code hooks system is configured
    And the manifest contains skills with content files
      | skill              | path                            |
      | terraform-base     | infrastructure/terraform-base   |
      | ecr-setup          | infrastructure/ecr-setup        |
      | aws-ecs-deployment | infrastructure/aws-ecs-deployment |
      | nextjs-standards   | frameworks/nextjs-standards     |

  # Skill Context Injection Scenarios

  Scenario: Inject single skill context
    Given a route result for skill "terraform-base"
    When the hook integration generates skill context
    Then the output contains skill context tags
    And the output includes skill "terraform-base" content
    And "terraform-base" is marked as primary

  Scenario: Inject multiple skill contexts in execution order
    Given a route result for skill "aws-ecs-deployment"
    And the execution order is
      | skill              |
      | terraform-base     |
      | ecr-setup          |
      | aws-ecs-deployment |
    When the hook integration generates skill context
    Then skills appear in the output in execution order
    And "terraform-base" content appears first
    And "ecr-setup" content appears second
    And "aws-ecs-deployment" content appears third

  Scenario: Mark primary and dependency skills distinctly
    Given a route result for skill "aws-ecs-deployment"
    And "aws-ecs-deployment" is the primary skill
    And "terraform-base" is a dependency
    When the hook integration generates skill context
    Then "aws-ecs-deployment" is marked as "[PRIMARY]"
    And "terraform-base" is marked as "[DEPENDENCY]"

  Scenario: Inject task skills as primary
    Given a route result for task "static-website"
    And the task requires skills
      | skill               |
      | nextjs-standards    |
      | aws-static-hosting  |
      | github-actions-cicd |
    When the hook integration generates skill context
    Then "nextjs-standards" is marked as "[PRIMARY]"
    And "aws-static-hosting" is marked as "[PRIMARY]"
    And "github-actions-cicd" is marked as "[PRIMARY]"

  # Output Format Scenarios

  Scenario: Generate correct output structure
    Given a route result for skill "terraform-base"
    When the hook integration generates skill context
    Then the output starts with "<skill_context>"
    And the output ends with "</skill_context>"
    And the output includes matched route information

  Scenario: Include execution order summary in output
    Given a route result for skill "aws-ecs-deployment"
    And the execution order is
      | skill              |
      | terraform-base     |
      | ecr-setup          |
      | aws-ecs-deployment |
    When the hook integration generates skill context
    Then the output includes "Execution order: terraform-base -> ecr-setup -> aws-ecs-deployment"

  Scenario: Include route type and matched name
    Given a route result with type "task" and matched "static-website"
    When the hook integration generates skill context
    Then the output includes "Matched: task 'static-website'"

  # Skill Content Loading Scenarios

  Scenario: Load skill content from SKILL.md file
    Given skill "terraform-base" has a SKILL.md file
    And the SKILL.md contains documentation content
    When the hook integration loads skill content
    Then the full SKILL.md content is returned

  Scenario: Handle missing SKILL.md file
    Given skill "new-skill" does not have a SKILL.md file
    When the hook integration loads skill content for "new-skill"
    Then a placeholder message is returned
    And a warning is logged

  Scenario: Handle missing skill directory
    Given skill "broken-skill" has path "non-existent/path"
    When the hook integration loads skill content for "broken-skill"
    Then a placeholder message is returned
    And the placeholder includes the expected path

  # Hook Script Integration Scenarios

  Scenario: Hook receives query from environment variable
    Given the environment variable PROMPT contains "build a static website"
    When the route_and_inject hook executes
    Then the router processes "build a static website"

  Scenario: Hook receives query from stdin
    Given stdin contains "build a static website"
    And PROMPT environment variable is not set
    When the route_and_inject hook executes
    Then the router processes "build a static website"

  Scenario: Hook outputs to stdout for injection
    Given a user query "use terraform-base"
    When the route_and_inject hook executes
    Then skill context is written to stdout
    And the output can be prepended to the prompt

  # Error Result Handling Scenarios

  Scenario: Handle error route result
    Given a route result with type "error"
    When the hook integration generates skill context
    Then no skill context is output
    And the process exits gracefully

  Scenario: Handle empty execution order
    Given a route result with empty execution order
    When the hook integration generates skill context
    Then minimal context output is generated
    And no skill sections are included

  # End-to-End Integration Scenarios

  Scenario: Full flow from query to context injection
    Given a user query "deploy my app with aws-ecs-deployment"
    When the complete routing and injection flow executes
    Then direct skill match finds "aws-ecs-deployment"
    And dependencies are resolved
    And skill context is generated
    And output includes terraform-base, ecr-setup, and aws-ecs-deployment

  Scenario: Full flow for task-based query
    Given a user query "build a landing page for our product"
    When the complete routing and injection flow executes
    Then task trigger match finds "static-website"
    And task skills are collected
    And dependencies are resolved
    And skill context is generated with all required skills
