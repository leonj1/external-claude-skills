Feature: Task Trigger Matching (Tier 2 Routing)
  As a user
  I want my high-level requests to match predefined tasks
  So that I get the right combination of skills for my goal

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains tasks
      | name             | description                  | triggers                                                              |
      | static-website   | Static website hosting       | build a static website, create a landing page, make a marketing site  |
      | admin-panel      | Internal admin dashboard     | build an admin panel, create a dashboard, create an internal tool     |
      | rest-api         | RESTful API service          | build an API, create a REST API, build a backend service              |
      | serverless-api   | Serverless Lambda API        | build a serverless API, create a Lambda function                      |

  # Exact Trigger Match Scenarios

  Scenario: Match task with exact trigger phrase
    Given a user query "build a static website"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match different task with exact trigger
    Given a user query "create a dashboard"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "admin-panel"

  # Word Overlap Matching Scenarios

  Scenario: Match task when query contains trigger words
    Given a user query "I want to build a static website for my business"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match task with 60 percent word overlap
    Given a user query "build static website"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: No match when word overlap below threshold
    Given a user query "website"
    When the router processes the query at tier 2
    Then no task trigger match is found
    And the router proceeds to tier 3

  # Best Match Selection Scenarios

  Scenario: Select task with highest word overlap score
    Given a user query "build a REST API backend service"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "rest-api"

  Scenario: Distinguish between similar tasks
    Given a user query "build a serverless API"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "serverless-api"

  Scenario: Match admin panel over generic dashboard
    Given a user query "create an internal tool for admin"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "admin-panel"

  # Case and Formatting Scenarios

  Scenario: Match triggers case-insensitively
    Given a user query "BUILD A STATIC WEBSITE"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  Scenario: Match with extra whitespace in query
    Given a user query "  build   a   static   website  "
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"

  # Skills Resolution Scenarios

  Scenario: Return all skills required by matched task
    Given task "static-website" requires skills
      | skill               |
      | nextjs-standards    |
      | aws-static-hosting  |
      | github-actions-cicd |
    And a user query "create a landing page"
    When the router processes the query
    Then the route type is "task"
    And the matched item is "static-website"
    And the primary skills list contains "nextjs-standards"
    And the primary skills list contains "aws-static-hosting"
    And the primary skills list contains "github-actions-cicd"

  # Tier Priority Scenarios

  Scenario: Tier 1 takes priority over Tier 2
    Given a user query "use terraform-base to build a static website"
    And the manifest contains skill "terraform-base"
    When the router processes the query
    Then the route type is "skill"
    And the matched item is "terraform-base"

  # No Match Scenarios

  Scenario: No match for ambiguous request
    Given a user query "help me with authentication"
    When the router processes the query at tier 2
    Then no task trigger match is found
    And the router proceeds to tier 3

  Scenario: No match for unrelated query
    Given a user query "what is the weather today"
    When the router processes the query at tier 2
    Then no task trigger match is found
