---
executor: bdd
source_feature: ./tests/bdd/llm-discovery.feature
task: "1.5a - LLM Discovery Interfaces"
---

<objective>
Define the interface contracts and data models for Tier 3 LLM-based skill discovery.
These are interfaces and models ONLY - no implementation code.
The design enables testable, swappable components for prompt building, LLM invocation, and response parsing.
</objective>

<gherkin>
Feature: LLM-Based Discovery (Tier 3 Routing)
  As a user with an ambiguous request
  I want the system to intelligently match my intent
  So that I get appropriate skills even without exact phrases

  # Relevant scenarios for interface design:

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

  Scenario: Successfully parse valid LLM JSON response
    Given a user query "set up user login"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns a valid JSON response with type "task" and name "customer-portal"
    Then the router parses the response successfully
    And the route type is "discovery"
    And the matched item is "customer-portal"

  Scenario: Handle malformed LLM JSON response
    Given a user query "do something"
    And tier 1 and tier 2 matching returned no results
    When the LLM returns an invalid JSON response
    Then the router falls back to the first task
    And the route type is "discovery"
    And a valid task is returned
</gherkin>

<requirements>
Based on the DRAFT specification and BDD scenarios, define:

## 1. Interfaces (in lib/skill_router/interfaces/discovery.py)

### ILLMDiscovery
- Top-level interface for LLM-based skill discovery
- Coordinates: prompt builder -> LLM client -> response parser
- Method: `discover(user_request: str, skill_summaries: List[SkillSummary], max_results: int = 3) -> DiscoveryResult`

### IPromptBuilder
- Builds prompts for LLM skill discovery
- Allows different prompting strategies (zero-shot, few-shot, chain-of-thought)
- Method: `build_prompt(user_request: str, skill_summaries: List[SkillSummary], max_results: int) -> str`

### ILLMClient
- Abstraction over the LLM API call
- Enables mocking, different providers, retry logic
- Method: `invoke(prompt: str) -> LLMResponse`
- Raises: `LLMClientError` on API failure, timeout, or rate limit

### IResponseParser
- Parses LLM output into structured DiscoveryResult
- Handles malformed responses gracefully
- Method: `parse(llm_response: LLMResponse) -> DiscoveryResult`
- Raises: `ParseError` if response cannot be parsed

## 2. Data Models (in lib/skill_router/discovery/models.py)

### SkillSummary (frozen dataclass)
- `name: str` - Unique skill identifier (e.g., "docker-backend")
- `description: str` - Brief description of what the skill does
- Validation: name and description cannot be empty

### SkillMatch (frozen dataclass)
- `skill_name: str` - Name of the matched skill
- `confidence: float` - 0.0 to 1.0 confidence score
- `reasoning: str` - LLM's explanation for the match
- Validation: confidence must be 0.0-1.0

### DiscoveryResult (frozen dataclass)
- `matches: List[SkillMatch]` - Skills ranked by confidence (descending)
- `raw_response: str` - Original LLM response for debugging
- `model_used: str` - e.g., "claude-3-haiku-20240307"
- `prompt_tokens: Optional[int]` - Token usage for cost tracking
- `completion_tokens: Optional[int]`
- Property: `top_match` returns highest confidence match or None
- Property: `has_matches` returns True if any skills matched

### LLMResponse (frozen dataclass)
- `text: str` - The response content
- `model: str` - Model that generated the response
- `prompt_tokens: Optional[int]`
- `completion_tokens: Optional[int]`
- `finish_reason: Optional[str]` - "stop", "length", etc.

## 3. Exceptions (add to lib/skill_router/exceptions.py)

### LLMDiscoveryError(Exception)
- Base exception for LLM discovery errors

### LLMClientError(LLMDiscoveryError)
- Error from LLM API (network, auth, rate limit)

### ParseError(LLMDiscoveryError)
- Error parsing LLM response into structured result

Edge Cases to Handle:
- Empty skill name or description in SkillSummary
- Confidence score outside 0.0-1.0 range
- Empty matches list in DiscoveryResult
- None/null values for optional fields
</requirements>

<context>
Draft Specification: specs/DRAFT-llm-discovery-interfaces.md
BDD Specification: specs/BDD-SPEC-skill-router.md
Gap Analysis: specs/GAP-ANALYSIS.md

Existing Patterns to Follow:
- Interface style: See lib/skill_router/interfaces/manifest.py (ABC, @abstractmethod)
- Interface style: See lib/skill_router/interfaces/matching.py (ISkillMatcher, ITaskMatcher)
- Exception style: See lib/skill_router/exceptions.py (ManifestError hierarchy)
- Model style: See lib/skill_router/models.py (dataclasses with validation)

File Structure:
```
lib/skill_router/
    discovery/
        __init__.py
        models.py          # SkillSummary, SkillMatch, DiscoveryResult, LLMResponse
    interfaces/
        discovery.py       # ILLMDiscovery, IPromptBuilder, ILLMClient, IResponseParser
    exceptions.py          # Add LLMDiscoveryError, LLMClientError, ParseError
```

Dependencies:
- Python 3.8+ (dataclasses, ABC)
- No external dependencies (interfaces only)
</context>

<implementation>
Follow TDD approach:
1. Write interface contract tests first
2. Define interfaces with proper ABC structure
3. Create frozen dataclass models with validation
4. Add exceptions following existing hierarchy

Architecture Guidelines:
- All interfaces use ABC and @abstractmethod
- All models use @dataclass(frozen=True) for immutability
- Confidence scores normalized 0.0-1.0
- DiscoveryResult preserves raw response for debugging
- Token counts optional (for cost tracking)
- No implementation details - just contracts
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
</implementation>

<verification>
Interface contracts validated:
- [ ] ILLMDiscovery.discover signature correct
- [ ] IPromptBuilder.build_prompt signature correct
- [ ] ILLMClient.invoke signature correct
- [ ] IResponseParser.parse signature correct

Data models validated:
- [ ] SkillSummary validates non-empty name/description
- [ ] SkillMatch validates confidence in 0.0-1.0 range
- [ ] DiscoveryResult.top_match property works
- [ ] DiscoveryResult.has_matches property works
- [ ] LLMResponse captures all fields

Exceptions validated:
- [ ] LLMDiscoveryError is base exception
- [ ] LLMClientError inherits from LLMDiscoveryError
- [ ] ParseError inherits from LLMDiscoveryError
</verification>

<success_criteria>
- All interfaces follow existing project patterns (ABC, @abstractmethod)
- All data models are frozen dataclasses with proper validation
- All exceptions follow existing hierarchy pattern
- Unit tests verify interface contracts and model validation
- Code follows project coding standards
- No implementation logic - interfaces and models only
</success_criteria>
