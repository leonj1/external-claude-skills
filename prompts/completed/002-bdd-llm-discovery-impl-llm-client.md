---
executor: bdd
source_feature: ./tests/bdd/llm-discovery.feature
---

<objective>
Implement the ClaudeHaikuClient component that invokes the Claude Haiku API for Tier 3 LLM-based discovery.
</objective>

<gherkin>
Feature: LLM-Based Discovery - LLM Client
  As a developer implementing Tier 3 routing
  I need a client to invoke Claude Haiku API
  So that I can get intelligent task/skill selection responses

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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Create exception hierarchy for LLM client errors:
   - `LLMClientError` - Base exception for LLM client failures
   - `RateLimitError` - API rate limit exceeded (429)
   - `AuthenticationError` - API authentication failed (401)
   - `TimeoutError` - API request timed out

2. Create `ClaudeHaikuClient` class implementing `ILLMClient` interface:
   - `MODEL_ID` class constant: "claude-3-5-haiku-20241022"
   - `MAX_TOKENS` class constant: 300
   - `__init__(api_key: Optional[str] = None)` - Initialize with optional API key
   - `invoke(prompt: str) -> LLMResponse` - Invoke Haiku with prompt

3. Client behavior:
   - If api_key is None, reads from ANTHROPIC_API_KEY env var
   - Constructs anthropic.Anthropic client
   - Builds messages array with user prompt
   - Calls client.messages.create()
   - Maps response to LLMResponse dataclass
   - Handles exceptions -> typed LLMClientError subclasses

Error Mapping:
| API Exception | Typed Exception |
|---------------|-----------------|
| 401 Unauthorized | AuthenticationError |
| 429 Too Many Requests | RateLimitError |
| Timeout/Connection | TimeoutError |
| Other | LLMClientError |
</requirements>

<context>
BDD Specification: specs/DRAFT-llm-discovery-implementation.md

Interfaces to implement:
- `lib/skill_router/interfaces/discovery.py` - ILLMClient interface

Data models to use:
- `lib/skill_router/discovery/models.py` - LLMResponse dataclass

File to create:
- `lib/skill_router/discovery/llm_client.py`

External dependency:
- `anthropic` - Claude API client
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass (mock API calls in tests)
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Implement ILLMClient interface from interfaces/discovery.py
- Use LLMResponse model from discovery/models.py
- API key handling in __init__ only (not in invoke method)
- Use anthropic Python SDK for API calls
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: LLM selects appropriate task for high-level request
- [ ] Scenario: LLM selects task for building request
- [ ] Scenario: LLM selects skill for specific infrastructure request
- [ ] Scenario: LLM selects skill for database request
</verification>

<success_criteria>
- ClaudeHaikuClient implements ILLMClient interface
- invoke() returns LLMResponse with text, model, token counts
- API errors are mapped to typed exceptions
- Client uses claude-3-5-haiku-20241022 model
- Tests mock API calls (no real API calls in unit tests)
- Code follows project coding standards
</success_criteria>
