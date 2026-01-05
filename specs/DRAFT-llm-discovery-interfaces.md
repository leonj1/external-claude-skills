# DRAFT: LLM Discovery Interfaces (Task 1.5a)

## Overview
Defines the interface contracts and data models for Tier 3 LLM-based skill discovery. These interfaces enable testable, swappable components for prompt building, LLM invocation, and response parsing.

## Interfaces Needed

### ILLMDiscovery
The top-level interface for Tier 3 discovery. Orchestrates the prompt-LLM-parse pipeline.

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class ILLMDiscovery(ABC):
    """
    Top-level interface for LLM-based skill discovery.
    Coordinates: prompt builder -> LLM client -> response parser
    """

    @abstractmethod
    def discover(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int = 3
    ) -> DiscoveryResult:
        """
        Given user request + available skills, ask LLM which skills apply.

        Args:
            user_request: The natural language task description
            skill_summaries: List of skill name/description pairs for LLM context
            max_results: Maximum skills to return (default 3)

        Returns:
            DiscoveryResult with ranked skills and confidence scores
        """
        pass
```

### IPromptBuilder
Constructs the prompt sent to the LLM. Separation allows different prompt strategies.

```python
class IPromptBuilder(ABC):
    """
    Builds prompts for LLM skill discovery.
    Allows different prompting strategies (zero-shot, few-shot, chain-of-thought).
    """

    @abstractmethod
    def build_prompt(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int
    ) -> str:
        """
        Construct the LLM prompt.

        Args:
            user_request: What the user wants to accomplish
            skill_summaries: Available skills with names and descriptions
            max_results: How many skills the LLM should recommend

        Returns:
            Complete prompt string ready for LLM
        """
        pass
```

### ILLMClient
Abstraction over the LLM API call. Enables mocking, different providers, retry logic.

```python
class ILLMClient(ABC):
    """
    Interface for LLM API invocation.
    Abstracts provider details (Claude, GPT, etc).
    """

    @abstractmethod
    def invoke(self, prompt: str) -> LLMResponse:
        """
        Send prompt to LLM and get response.

        Args:
            prompt: The complete prompt string

        Returns:
            LLMResponse with raw text and metadata

        Raises:
            LLMClientError: On API failure, timeout, or rate limit
        """
        pass
```

### IResponseParser
Parses LLM output into structured DiscoveryResult. Handles malformed responses gracefully.

```python
class IResponseParser(ABC):
    """
    Parses LLM text response into structured DiscoveryResult.
    Handles JSON extraction and validation.
    """

    @abstractmethod
    def parse(self, llm_response: LLMResponse) -> DiscoveryResult:
        """
        Extract structured skill recommendations from LLM response.

        Args:
            llm_response: Raw LLM response object

        Returns:
            DiscoveryResult with skill matches and confidence

        Raises:
            ParseError: If response cannot be parsed into valid structure
        """
        pass
```

## Data Models

### SkillSummary
Input model representing a skill available for discovery.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SkillSummary:
    """
    Lightweight skill representation for LLM context.
    Contains only what the LLM needs to make a decision.
    """
    name: str           # Unique skill identifier (e.g., "docker-backend")
    description: str    # Brief description of what the skill does

    def __post_init__(self):
        if not self.name:
            raise ValueError("Skill name cannot be empty")
        if not self.description:
            raise ValueError("Skill description cannot be empty")
```

### SkillMatch
A single skill recommendation from the LLM with confidence score.

```python
@dataclass(frozen=True)
class SkillMatch:
    """
    A skill matched by the LLM with confidence score.
    """
    skill_name: str     # Name of the matched skill
    confidence: float   # 0.0 to 1.0 confidence score
    reasoning: str      # LLM's explanation for the match

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
```

### DiscoveryResult
Output model containing all matched skills from an LLM discovery call.

```python
from typing import List, Optional

@dataclass(frozen=True)
class DiscoveryResult:
    """
    Result of LLM skill discovery.
    Contains ranked list of skill matches.
    """
    matches: List[SkillMatch]           # Skills ranked by confidence (descending)
    raw_response: str                   # Original LLM response for debugging
    model_used: str                     # e.g., "claude-3-haiku-20240307"
    prompt_tokens: Optional[int] = None # Token usage for cost tracking
    completion_tokens: Optional[int] = None

    @property
    def top_match(self) -> Optional[SkillMatch]:
        """Returns highest confidence match or None if empty."""
        return self.matches[0] if self.matches else None

    @property
    def has_matches(self) -> bool:
        """True if any skills were matched."""
        return len(self.matches) > 0
```

### LLMResponse
Intermediate model for raw LLM API response.

```python
@dataclass(frozen=True)
class LLMResponse:
    """
    Raw response from LLM API before parsing.
    """
    text: str                           # The response content
    model: str                          # Model that generated the response
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None # "stop", "length", etc.
```

### Error Types

```python
class LLMDiscoveryError(Exception):
    """Base exception for LLM discovery errors."""
    pass

class LLMClientError(LLMDiscoveryError):
    """Error from LLM API (network, auth, rate limit)."""
    pass

class ParseError(LLMDiscoveryError):
    """Error parsing LLM response into structured result."""
    pass
```

## Logic Flow (Pseudocode)

```
LLMDiscovery.discover(user_request, skill_summaries, max_results):
    1. prompt = prompt_builder.build_prompt(user_request, skill_summaries, max_results)
    2. llm_response = llm_client.invoke(prompt)
    3. result = response_parser.parse(llm_response)
    4. return result
```

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 0 (greenfield interfaces) |
| New code to write | ~120 lines (interfaces + models) |
| Test code to write | ~80 lines (interface contract tests) |
| Estimated context usage | ~15% |

## Dependencies

- Python 3.8+ (dataclasses, ABC)
- No external dependencies (interfaces only)

## File Structure

```
src/skill_router/
    discovery/
        __init__.py
        interfaces.py      # ILLMDiscovery, IPromptBuilder, ILLMClient, IResponseParser
        models.py          # SkillSummary, SkillMatch, DiscoveryResult, LLMResponse
        errors.py          # LLMDiscoveryError, LLMClientError, ParseError
```

## Notes

- All models use `frozen=True` for immutability
- Confidence scores normalized 0.0-1.0
- DiscoveryResult preserves raw response for debugging
- Token counts optional (for cost tracking)
- No implementation details - just contracts
