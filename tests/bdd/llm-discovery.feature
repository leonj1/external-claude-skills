Feature: LLM-Based Discovery (Tier 3 Routing)
  As a user with an ambiguous request
  I want the system to intelligently match my intent
  So that I get appropriate skills even without exact phrases

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains tasks
      | name            | description                        |
      | customer-portal | Customer-facing web application    |
      | admin-panel     | Internal admin dashboard           |
      | rest-api        | RESTful API service                |
    And the manifest contains skills
      | name             | description                    |
      | auth-cognito     | AWS Cognito authentication     |
      | auth-auth0       | Auth0 authentication           |
      | rds-postgres     | PostgreSQL database setup      |
      | nextjs-standards | Next.js project conventions    |

  # LLM Task Selection Scenarios

  Scenario: LLM selects appropriate task for high-level request
    Given a user query "I need a way for customers to log into their accounts"
    And tier 1 and tier 2 matching returned no results
    When the router invokes LLM discovery
    Then the LLM returns a task match
    And the route type is "discovery"
    And the matched item is a valid task name

  Scenario: LLM selects task for building request
    Given a user query "set up a portal for our clients"
    And tier 1 and tier 2 matching returned no results
    When the router invokes LLM discovery
    Then the LLM returns a task match
    And the route type is "discovery"

  # LLM Skill Selection Scenarios

  Scenario: LLM selects skill for specific infrastructure request
    Given a user query "configure authentication for my app"
    And tier 1 and tier 2 matching returned no results
    When the router invokes LLM discovery
    Then the LLM may return a skill match
    And the route type is "discovery"

  Scenario: LLM selects skill for database request
    Given a user query "set up a PostgreSQL database"
    And tier 1 and tier 2 matching returned no results
    When the router invokes LLM discovery
    Then the LLM returns a match
    And the route type is "discovery"

  # LLM Input Format Scenarios

  Scenario: LLM receives formatted task options
    Given a user query "make something for users"
    And tier 1 and tier 2 matching returned no results
    When the router prepares the LLM prompt
    Then the prompt includes all task names and descriptions
    And the prompt includes all skill names and descriptions

  Scenario: LLM receives clear instructions
    Given a user query "build something"
    And tier 1 and tier 2 matching returned no results
    When the router prepares the LLM prompt
    Then the prompt instructs to choose task for high-level requests
    And the prompt instructs to choose skill for specific infrastructure

  # LLM Response Parsing Scenarios

  Scenario: Successfully parse valid LLM JSON response
    Given a user query "set up user login"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns a valid JSON response with type "task" and name "customer-portal"
    Then the router parses the response successfully
    And the route type is "discovery"
    And the matched item is "customer-portal"

  Scenario: Successfully parse LLM skill response
    Given a user query "configure Cognito"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns a valid JSON response with type "skill" and name "auth-cognito"
    Then the router parses the response successfully
    And the route type is "discovery"
    And the matched item is "auth-cognito"

  # LLM Error Handling Scenarios

  Scenario: Handle malformed LLM JSON response
    Given a user query "do something"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns an invalid JSON response
    Then the router falls back to the first task
    And the route type is "discovery"
    And a valid task is returned

  Scenario: Handle LLM returning non-existent task
    Given a user query "build something special"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns a task name that does not exist in the manifest
    Then the router returns an error result
    And the route type is "error"

  Scenario: Handle LLM returning non-existent skill
    Given a user query "configure something"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns a skill name that does not exist in the manifest
    Then the router returns an error result
    And the route type is "error"

  # Discovery Result Scenarios

  Scenario: Discovery result includes resolved skills
    Given a user query "create a user management system"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns task "customer-portal"
    And task "customer-portal" requires skills
      | skill           |
      | nextjs-standards |
      | auth-cognito    |
    Then the route result includes all task skills
    And the execution order is resolved

  Scenario: Discovery skill result includes dependencies
    Given a user query "set up AWS authentication"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns skill "auth-cognito"
    And skill "auth-cognito" depends on "terraform-base"
    Then the execution order includes "terraform-base"
    And the execution order includes "auth-cognito"
