---
executor: bdd
source_feature: ./tests/bdd/llm-discovery.feature
---

<objective>
Implement the DiscoveryPromptBuilder component that formats user requests and skill summaries into LLM prompts for Tier 3 discovery.
</objective>

<gherkin>
Feature: LLM-Based Discovery - Prompt Building
  As a developer implementing Tier 3 routing
  I need to build properly formatted prompts for the LLM
  So that the LLM can make informed task/skill selection decisions

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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Create `DiscoveryPromptBuilder` class implementing `IPromptBuilder` interface
2. Define `PROMPT_TEMPLATE` class constant with structured prompt format
3. Implement `build_prompt()` method that:
   - Takes user_request, skill_summaries, and max_results
   - Formats all task names and descriptions into the prompt
   - Formats all skill names and descriptions into the prompt
   - Includes clear instructions for task vs skill selection
   - Returns properly interpolated prompt string

4. Prompt template must include:
   - Section for user request
   - Section for available tasks (high-level, maps to multiple skills)
   - Section for available skills (low-level, direct capabilities)
   - Instructions to choose TASK for high-level requests
   - Instructions to choose SKILL for specific infrastructure
   - JSON output format specification

Edge Cases to Handle:
- Empty user request (raise ValueError)
- Empty skill summaries list (raise ValueError)
- Skill summaries with missing fields
</requirements>

<context>
BDD Specification: specs/DRAFT-llm-discovery-implementation.md

Interfaces to implement:
- `lib/skill_router/interfaces/discovery.py` - IPromptBuilder interface

Data models to use:
- `lib/skill_router/discovery/models.py` - SkillSummary dataclass

File to create:
- `lib/skill_router/discovery/prompt_builder.py`

Expected JSON output format from prompt:
```json
{"type": "task" or "skill", "name": "the-name", "confidence": 0.0-1.0, "reasoning": "..."}
```
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Implement IPromptBuilder interface from interfaces/discovery.py
- Use SkillSummary model from discovery/models.py
- Keep prompt template as class constant for easy modification
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: LLM receives formatted task options
- [ ] Scenario: LLM receives clear instructions
</verification>

<success_criteria>
- DiscoveryPromptBuilder implements IPromptBuilder interface
- build_prompt() includes all task names and descriptions
- build_prompt() includes all skill names and descriptions
- Prompt instructs to choose task for high-level requests
- Prompt instructs to choose skill for specific infrastructure
- Code follows project coding standards
- Tests provide complete coverage of scenarios
</success_criteria>
