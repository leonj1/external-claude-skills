# DRAFT Specification: LLM Discovery Implementation

## Overview
Task 1.5b implementation of Tier 3 LLM-based discovery components using Claude Haiku.

**Traces To Root**: "3-tier routing" - Implements Tier 3 LLM fallback with concrete classes.

## Interfaces Implemented

From `lib/skill_router/interfaces/discovery.py`:
- `IPromptBuilder` -> `DiscoveryPromptBuilder`
- `ILLMClient` -> `ClaudeHaikuClient`
- `IResponseParser` -> `JSONResponseParser`
- `ILLMDiscovery` -> `LLMDiscovery`

## Data Models Used

From `lib/skill_router/discovery/models.py`:
- `SkillSummary` - Input skill information
- `SkillMatch` - Output match with confidence
- `LLMResponse` - Raw API response wrapper
- `DiscoveryResult` - Final structured result

---

## Component 1: DiscoveryPromptBuilder

**File**: `lib/skill_router/discovery/prompt_builder.py`

### Responsibilities
- Format user request with skill summaries into LLM prompt
- Use zero-shot prompting with JSON output format
- Include clear instructions for task vs skill selection

### Class Design

```python
class DiscoveryPromptBuilder(IPromptBuilder):
    """Builds zero-shot prompts for skill discovery."""

    PROMPT_TEMPLATE: str  # Class constant with prompt structure

    def build_prompt(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int
    ) -> str
```

### Prompt Template Structure
```
Match this request to the best task or skill.

## Request
{user_request}

## Available Tasks (high-level, maps to multiple skills)
{formatted_tasks}

## Available Skills (low-level, direct capabilities)
{formatted_skills}

## Instructions
- If request is high-level (build something, create something), choose a TASK
- If request is specific infrastructure/tooling, choose a SKILL
- Return JSON: {"type": "task" or "skill", "name": "the-name", "confidence": 0.0-1.0, "reasoning": "..."}
- You may return up to {max_results} matches as JSON array

## Response:
```

### Logic Flow
1. Validate inputs (non-empty request, non-empty summaries)
2. Format skill summaries into compact list
3. Interpolate into template
4. Return formatted prompt

---

## Component 2: ClaudeHaikuClient

**File**: `lib/skill_router/discovery/llm_client.py`

### Responsibilities
- Invoke Claude Haiku API with prompt
- Handle API errors with typed exceptions
- Track token usage for cost monitoring

### Class Design

```python
class LLMClientError(Exception):
    """Base exception for LLM client failures."""
    pass

class RateLimitError(LLMClientError):
    """API rate limit exceeded."""
    pass

class AuthenticationError(LLMClientError):
    """API authentication failed."""
    pass

class TimeoutError(LLMClientError):
    """API request timed out."""
    pass

class ClaudeHaikuClient(ILLMClient):
    """Client for Claude Haiku API invocation."""

    MODEL_ID: str = "claude-3-5-haiku-20241022"
    MAX_TOKENS: int = 300

    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with optional API key.

        If api_key is None, reads from ANTHROPIC_API_KEY env var.
        """
        pass

    def invoke(self, prompt: str) -> LLMResponse:
        """Invoke Haiku with prompt, return structured response."""
        pass
```

### Logic Flow
1. Construct API client (anthropic.Anthropic)
2. Build messages array with user prompt
3. Call `client.messages.create()`
4. Map response to LLMResponse dataclass
5. Handle exceptions -> typed LLMClientError subclasses

### Error Mapping
| API Exception | Typed Exception |
|---------------|-----------------|
| 401 Unauthorized | AuthenticationError |
| 429 Too Many Requests | RateLimitError |
| Timeout/Connection | TimeoutError |
| Other | LLMClientError |

---

## Component 3: JSONResponseParser

**File**: `lib/skill_router/discovery/response_parser.py`

### Responsibilities
- Parse JSON from LLM response text
- Handle malformed JSON gracefully
- Validate parsed structure matches expected schema
- Convert to DiscoveryResult with SkillMatch items

### Class Design

```python
class ParseError(Exception):
    """Exception for response parsing failures."""
    pass

class JSONResponseParser(IResponseParser):
    """Parses JSON responses from LLM into DiscoveryResult."""

    def parse(self, llm_response: LLMResponse) -> DiscoveryResult:
        """Parse LLM response text into structured result."""
        pass

    def _extract_json(self, text: str) -> dict | list:
        """Extract JSON from response text, handling markdown code blocks."""
        pass

    def _validate_match(self, match_data: dict) -> SkillMatch:
        """Validate and convert dict to SkillMatch."""
        pass
```

### Expected JSON Formats

**Single Match**:
```json
{"type": "task", "name": "customer-portal", "confidence": 0.9, "reasoning": "..."}
```

**Multiple Matches**:
```json
[
  {"type": "task", "name": "customer-portal", "confidence": 0.9, "reasoning": "..."},
  {"type": "skill", "name": "auth-cognito", "confidence": 0.7, "reasoning": "..."}
]
```

### Logic Flow
1. Extract raw text from LLMResponse
2. Strip markdown code blocks if present
3. Parse JSON (handle both single object and array)
4. Validate each match has required fields
5. Create SkillMatch objects with validation
6. Sort by confidence descending
7. Build DiscoveryResult with metadata

### Error Handling
- Invalid JSON -> ParseError
- Missing required fields -> ParseError
- Invalid confidence range -> ParseError (unless clampable)
- Empty response -> DiscoveryResult with empty matches

---

## Component 4: LLMDiscovery

**File**: `lib/skill_router/discovery/llm_discovery.py`

### Responsibilities
- Orchestrate the complete discovery flow
- Compose prompt builder, client, and parser
- Handle errors gracefully with fallback behavior

### Class Design

```python
class LLMDiscovery(ILLMDiscovery):
    """Orchestrates LLM-based skill discovery."""

    def __init__(
        self,
        prompt_builder: IPromptBuilder,
        llm_client: ILLMClient,
        response_parser: IResponseParser
    ):
        """Initialize with injected dependencies."""
        pass

    def discover(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int = 3
    ) -> DiscoveryResult:
        """Execute discovery pipeline."""
        pass
```

### Logic Flow
1. Call `prompt_builder.build_prompt()`
2. Call `llm_client.invoke()` with prompt
3. Call `response_parser.parse()` with response
4. Return DiscoveryResult

### Error Handling Strategy
| Error Type | Behavior |
|------------|----------|
| LLMClientError | Re-raise (caller decides fallback) |
| ParseError | Return empty DiscoveryResult with error in metadata |

---

## Factory Functions

**File**: `lib/skill_router/discovery/factory.py`

```python
def create_llm_discovery(api_key: Optional[str] = None) -> ILLMDiscovery:
    """Create default LLMDiscovery instance with Claude Haiku.

    Args:
        api_key: Optional Anthropic API key (defaults to env var)

    Returns:
        Configured LLMDiscovery instance
    """
    prompt_builder = DiscoveryPromptBuilder()
    llm_client = ClaudeHaikuClient(api_key)
    response_parser = JSONResponseParser()
    return LLMDiscovery(prompt_builder, llm_client, response_parser)
```

---

## BDD Scenario Mapping

| Gherkin Scenario | Implementation Component |
|------------------|-------------------------|
| LLM receives formatted task options | DiscoveryPromptBuilder.build_prompt() |
| LLM receives clear instructions | DiscoveryPromptBuilder.PROMPT_TEMPLATE |
| Successfully parse valid LLM JSON response | JSONResponseParser.parse() |
| Handle malformed LLM JSON response | JSONResponseParser._extract_json() |
| Handle LLM returning non-existent task | Router layer (not this module) |
| Discovery result includes resolved skills | Router layer (not this module) |

---

## File Structure

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

---

## Context Budget

| Category | Count | Lines |
|----------|-------|-------|
| Files to read | 2 | ~220 lines |
| - interfaces/discovery.py | | ~123 lines |
| - discovery/models.py | | ~117 lines |
| New code to write | | ~250 lines |
| - prompt_builder.py | | ~50 lines |
| - llm_client.py | | ~80 lines |
| - response_parser.py | | ~70 lines |
| - llm_discovery.py | | ~40 lines |
| - factory.py | | ~10 lines |
| Test code to write | | ~300 lines |
| **Estimated context usage** | | **~25%** |

---

## Dependencies

**External**:
- `anthropic` - Claude API client

**Internal**:
- `lib.skill_router.interfaces.discovery` - Interface definitions
- `lib.skill_router.discovery.models` - Data models

---

## Testing Strategy

**Unit Tests** (mockable interfaces):
- `test_prompt_builder.py` - Template formatting
- `test_llm_client.py` - API calls with mocked anthropic
- `test_response_parser.py` - JSON parsing edge cases
- `test_llm_discovery.py` - Orchestration with mocked components

**Integration Tests** (optional, uses real API):
- `test_llm_discovery_integration.py` - End-to-end with Haiku

---

## Acceptance Criteria

1. DiscoveryPromptBuilder formats prompts matching BDD scenarios
2. ClaudeHaikuClient invokes API and returns LLMResponse
3. JSONResponseParser handles valid JSON, arrays, and malformed input
4. LLMDiscovery composes all components correctly
5. Factory creates properly wired instance
6. All BDD scenarios from `llm-discovery.feature` pass
