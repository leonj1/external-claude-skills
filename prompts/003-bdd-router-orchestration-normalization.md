---
executor: bdd
source_feature: ./tests/bdd/router-orchestration.feature
---

<objective>
Implement query normalization (QueryNormalizer) and error handling for the router.
Normalization ensures consistent matching regardless of case, whitespace, or formatting.
</objective>

<gherkin>
Feature: Router Orchestration (3-Tier Flow)
  As a skill router system
  I want to orchestrate the 3-tier matching flow
  So that queries are routed efficiently and correctly

  Background:
    Given a skill router system with all components initialized
    And the manifest is loaded and validated

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

  Scenario: Handle manifest loading failure
    Given the manifest file is corrupted
    When the router attempts to process a query
    Then an appropriate error is raised
    And the error message indicates manifest loading failed

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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. QueryNormalizer class implementing IQueryNormalizer
2. normalize(query: str) method that:
   - Converts to lowercase
   - Strips leading/trailing whitespace
   - Collapses multiple spaces to single space
   - Returns empty string for empty/whitespace-only input
3. Router integration:
   - Normalize query before Tier 1 matching
   - Return no_match immediately for empty normalized query
4. Error handling:
   - ManifestError for manifest loading failures
   - Safe handling of special characters (preserve for matching)
   - Graceful handling of very long queries

Edge Cases to Handle:
- Empty string input
- Whitespace-only input
- Very long queries (1000+ characters)
- Special characters including HTML/XSS attempts
- Unicode characters
</requirements>

<context>
BDD Specification: specs/DRAFT-router-orchestration.md

Query Normalization Rules:
| Transformation | Example |
|----------------|---------|
| Lowercase | "USE TERRAFORM-BASE" -> "use terraform-base" |
| Trim whitespace | "  query  " -> "query" |
| Collapse spaces | "build   a   website" -> "build a website" |
| Empty handling | "" or "   " -> "" (triggers no_match) |

Note: Special characters are preserved to allow matching skill names like "aws-ecs-deployment".

File Structure:
```
lib/skill_router/
  router/
    normalizer.py          # QueryNormalizer implementation
```
</context>

<implementation>
Follow TDD approach:
1. Write tests for lowercase conversion
2. Write tests for whitespace trimming
3. Write tests for whitespace collapsing
4. Write tests for empty/whitespace input
5. Write tests for special character handling
6. Write tests for long query handling
7. Implement QueryNormalizer to make tests pass

Architecture Guidelines:
- Use regex for whitespace collapsing
- Handle edge cases gracefully
- Follow strict-architecture rules (500 lines max)
- No external dependencies needed
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Normalize query to lowercase
- [ ] Scenario: Normalize query whitespace
- [ ] Scenario: Handle manifest loading failure
- [ ] Scenario: Handle empty query
- [ ] Scenario: Handle very long query
- [ ] Scenario: Handle special characters in query
</verification>

<success_criteria>
- QueryNormalizer implements IQueryNormalizer
- Lowercase conversion works correctly
- Whitespace handling works correctly
- Empty queries return no_match
- Long queries handled without error
- Special characters preserved safely
- All tests pass
- Code follows project coding standards
</success_criteria>
