---
executor: bdd
source_feature: ./tests/bdd/llm-discovery.feature
---

<objective>
Implement the LLMDiscovery orchestrator and factory that composes all discovery components for Tier 3 routing.
</objective>

<gherkin>
Feature: LLM-Based Discovery - Orchestration
  As a developer implementing Tier 3 routing
  I need an orchestrator that composes prompt building, LLM invocation, and response parsing
  So that I have a single entry point for LLM-based discovery

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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Create `LLMDiscovery` class implementing `ILLMDiscovery` interface:
   - `__init__(prompt_builder, llm_client, response_parser)` - Inject dependencies
   - `discover(user_request, skill_summaries, max_results=3) -> DiscoveryResult`

2. Orchestration flow:
   - Call `prompt_builder.build_prompt()` with inputs
   - Call `llm_client.invoke()` with built prompt
   - Call `response_parser.parse()` with LLM response
   - Return DiscoveryResult

3. Error handling strategy:
   - LLMClientError -> Re-raise (caller decides fallback)
   - ParseError -> Return empty DiscoveryResult with error in metadata

4. Create factory function in `factory.py`:
   ```python
   def create_llm_discovery(api_key: Optional[str] = None) -> ILLMDiscovery:
       """Create default LLMDiscovery instance with Claude Haiku."""
       prompt_builder = DiscoveryPromptBuilder()
       llm_client = ClaudeHaikuClient(api_key)
       response_parser = JSONResponseParser()
       return LLMDiscovery(prompt_builder, llm_client, response_parser)
   ```

5. Update `__init__.py` to export public symbols:
   - LLMDiscovery
   - create_llm_discovery
   - DiscoveryPromptBuilder
   - ClaudeHaikuClient
   - JSONResponseParser
   - Exception classes (LLMClientError, ParseError, etc.)

Note: Skill dependency resolution and execution order are handled at the router layer, not in the LLMDiscovery component. These scenarios test the integration with the router.
</requirements>

<context>
BDD Specification: specs/DRAFT-llm-discovery-implementation.md

Interfaces to implement:
- `lib/skill_router/interfaces/discovery.py` - ILLMDiscovery interface

Components to compose:
- `lib/skill_router/discovery/prompt_builder.py` - DiscoveryPromptBuilder
- `lib/skill_router/discovery/llm_client.py` - ClaudeHaikuClient
- `lib/skill_router/discovery/response_parser.py` - JSONResponseParser

Files to create:
- `lib/skill_router/discovery/llm_discovery.py`
- `lib/skill_router/discovery/factory.py`
- Update `lib/skill_router/discovery/__init__.py`

File Structure:
```
lib/skill_router/discovery/
    __init__.py           # Exports public symbols
    models.py             # (exists) Data models
    prompt_builder.py     # DiscoveryPromptBuilder
    llm_client.py         # ClaudeHaikuClient + exceptions
    response_parser.py    # JSONResponseParser + ParseError
    llm_discovery.py      # LLMDiscovery orchestrator
    factory.py            # create_llm_discovery()
```
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Implement ILLMDiscovery interface from interfaces/discovery.py
- Use dependency injection for testability
- Factory function creates fully wired instance
- Export all public symbols from __init__.py
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Discovery result includes resolved skills
- [ ] Scenario: Discovery skill result includes dependencies
</verification>

<success_criteria>
- LLMDiscovery implements ILLMDiscovery interface
- discover() orchestrates prompt building, LLM invocation, and parsing
- Factory creates properly wired LLMDiscovery instance
- __init__.py exports all public symbols
- Error handling follows specified strategy
- Code follows project coding standards
- All BDD scenarios from llm-discovery.feature pass
</success_criteria>
