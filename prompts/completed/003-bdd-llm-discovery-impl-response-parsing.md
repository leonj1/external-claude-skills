---
executor: bdd
source_feature: ./tests/bdd/llm-discovery.feature
---

<objective>
Implement the JSONResponseParser component that parses LLM responses into structured DiscoveryResult objects.
</objective>

<gherkin>
Feature: LLM-Based Discovery - Response Parsing
  As a developer implementing Tier 3 routing
  I need to parse LLM JSON responses reliably
  So that I can extract task/skill matches with confidence scores

  Background:
    Given a skill router with a loaded manifest
    And the manifest contains tasks
      | name            | description                        |
      | customer-portal | Customer-facing web application    |
      | admin-panel     | Internal admin dashboard           |
      | rest-api        | RESTful API service                |
    And the manifest contains skills
      | name           | description                    |
      | auth-cognito   | AWS Cognito authentication     |
      | auth-auth0     | Auth0 authentication           |
      | rds-postgres   | PostgreSQL database setup      |

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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Create `ParseError` exception for response parsing failures

2. Create `JSONResponseParser` class implementing `IResponseParser` interface:
   - `parse(llm_response: LLMResponse) -> DiscoveryResult` - Main parse method
   - `_extract_json(text: str) -> dict | list` - Extract JSON from response
   - `_validate_match(match_data: dict) -> SkillMatch` - Validate and convert

3. Parser behavior:
   - Extract raw text from LLMResponse
   - Strip markdown code blocks if present (```json ... ```)
   - Parse JSON (handle both single object and array)
   - Validate each match has required fields (type, name, confidence, reasoning)
   - Create SkillMatch objects with validation
   - Sort matches by confidence descending
   - Build DiscoveryResult with metadata

Expected JSON Formats:
Single Match:
```json
{"type": "task", "name": "customer-portal", "confidence": 0.9, "reasoning": "..."}
```

Multiple Matches:
```json
[
  {"type": "task", "name": "customer-portal", "confidence": 0.9, "reasoning": "..."},
  {"type": "skill", "name": "auth-cognito", "confidence": 0.7, "reasoning": "..."}
]
```

Error Handling:
- Invalid JSON -> ParseError
- Missing required fields -> ParseError
- Invalid confidence range -> ParseError (unless clampable 0.0-1.0)
- Empty response -> DiscoveryResult with empty matches
</requirements>

<context>
BDD Specification: specs/DRAFT-llm-discovery-implementation.md

Interfaces to implement:
- `lib/skill_router/interfaces/discovery.py` - IResponseParser interface

Data models to use:
- `lib/skill_router/discovery/models.py` - LLMResponse, SkillMatch, DiscoveryResult

File to create:
- `lib/skill_router/discovery/response_parser.py`

Note: Validation of task/skill existence in manifest is handled at the router layer, not in the parser. Parser only validates JSON structure.
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Implement IResponseParser interface from interfaces/discovery.py
- Use SkillMatch and DiscoveryResult models from discovery/models.py
- Handle markdown code block extraction gracefully
- Sort matches by confidence descending
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Successfully parse valid LLM JSON response
- [ ] Scenario: Successfully parse LLM skill response
- [ ] Scenario: Handle malformed LLM JSON response
- [ ] Scenario: Handle LLM returning non-existent task
- [ ] Scenario: Handle LLM returning non-existent skill
</verification>

<success_criteria>
- JSONResponseParser implements IResponseParser interface
- parse() extracts JSON from response text
- parse() handles markdown code blocks
- parse() creates SkillMatch objects with validated fields
- parse() returns DiscoveryResult sorted by confidence
- ParseError raised for invalid JSON or missing fields
- Code follows project coding standards
</success_criteria>
