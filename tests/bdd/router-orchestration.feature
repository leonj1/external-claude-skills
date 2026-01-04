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

  # Route Result Construction Scenarios

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

  # Query Normalization Scenarios

  Scenario: Normalize query to lowercase
    Given a user query "USE TERRAFORM-BASE"
    When the router normalizes the query
    Then the normalized query is "use terraform-base"

  Scenario: Normalize query whitespace
    Given a user query "  build   a   website  "
    When the router normalizes the query
    Then the normalized query has single spaces
    And the normalized query has no leading or trailing whitespace

  # Error Handling Scenarios

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

  Scenario: Handle manifest loading failure
    Given the manifest file is corrupted
    When the router attempts to process a query
    Then an appropriate error is raised
    And the error message indicates manifest loading failed

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

  # Edge Cases

  Scenario: Handle empty query
    Given an empty user query
    When the router processes the query
    Then the route result has type "error"

  Scenario: Handle very long query
    Given a user query with 1000 characters
    When the router processes the query
    Then the router completes without error
    And a route result is returned

  Scenario: Handle special characters in query
    Given a user query "build website <script>alert('xss')</script>"
    When the router processes the query
    Then special characters are handled safely
    And the router completes without error
