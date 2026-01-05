# DRAFT: LLM Discovery (Tier 3 Routing)

## Overview

LLM Discovery implements Tier 3 of the 3-tier routing system. When Tier 1 (direct skill match) and Tier 2 (task trigger match) fail to match, the system uses Claude Haiku to intelligently select the most appropriate task or skill based on semantic understanding.

## Traces to Root Request

- **Root**: "Read specs.md and implement the Skill Router system with YAML manifest, **3-tier routing**, dependency resolution, and hook integration"
- **This sub-task**: Implements Tier 3 (LLM fallback) of the "3-tier routing" requirement

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 4 (~200 lines) |
| New code to write | ~180 lines |
| Test code to write | ~300 lines |
| Estimated context usage | ~20% |

**Verdict**: APPROVED (under 60% threshold)

---

## Interfaces Needed

### ILLMDiscovery (New)

```python
from abc import ABC, abstractmethod
from lib.skill_router.models import Manifest


class ILLMDiscovery(ABC):
    """Interface for LLM-based skill/task discovery."""

    @abstractmethod
    def discover(self, query: str, manifest: Manifest) -> "DiscoveryResult":
        """Use LLM to match query to best task or skill.

        Args:
            query: User query string
            manifest: Loaded manifest with tasks and skills

        Returns:
            DiscoveryResult with matched type, name, and associated skills
        """
        pass
```

### IPromptBuilder (New)

```python
from abc import ABC, abstractmethod
from lib.skill_router.models import Manifest


class IPromptBuilder(ABC):
    """Interface for building LLM prompts."""

    @abstractmethod
    def build(self, query: str, manifest: Manifest) -> str:
        """Build prompt for LLM discovery.

        Args:
            query: User query string
            manifest: Loaded manifest with tasks and skills

        Returns:
            Formatted prompt string for LLM
        """
        pass
```

### ILLMClient (New)

```python
from abc import ABC, abstractmethod


class ILLMClient(ABC):
    """Interface for LLM API calls."""

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 150) -> str:
        """Send prompt to LLM and return response.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text
        """
        pass
```

### IResponseParser (New)

```python
from abc import ABC, abstractmethod
from lib.skill_router.models import Manifest


class IResponseParser(ABC):
    """Interface for parsing LLM responses."""

    @abstractmethod
    def parse(self, response: str, manifest: Manifest) -> "DiscoveryResult":
        """Parse LLM response into discovery result.

        Args:
            response: Raw LLM response text
            manifest: Manifest for validation

        Returns:
            DiscoveryResult with parsed type and name
        """
        pass
```

---

## Data Models

### DiscoveryResult (New)

```python
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DiscoveryResult:
    """Represents the result of LLM discovery.

    Attributes:
        match_type: "task", "skill", or "error"
        matched_name: Name of matched task or skill, or None
        skills: List of skill names (from task or single skill)
        is_valid: Whether the discovery found a valid match
    """
    match_type: str
    matched_name: Optional[str]
    skills: List[str]
    is_valid: bool

    @classmethod
    def error(cls) -> "DiscoveryResult":
        """Factory method for error result."""
        return cls(match_type="error", matched_name=None, skills=[], is_valid=False)

    @classmethod
    def from_task(cls, task_name: str, skills: List[str]) -> "DiscoveryResult":
        """Factory method for task match."""
        return cls(match_type="discovery", matched_name=task_name, skills=skills, is_valid=True)

    @classmethod
    def from_skill(cls, skill_name: str) -> "DiscoveryResult":
        """Factory method for skill match."""
        return cls(match_type="discovery", matched_name=skill_name, skills=[skill_name], is_valid=True)
```

### LLMResponse (Internal)

```python
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Parsed JSON structure from LLM.

    Attributes:
        type: "task" or "skill"
        name: Name of the matched item
    """
    type: str
    name: str
```

---

## Implementation Classes

### DiscoveryPromptBuilder

```python
class DiscoveryPromptBuilder(IPromptBuilder):
    """Builds prompts for LLM discovery."""

    def build(self, query: str, manifest: Manifest) -> str:
        """Build prompt with task and skill options.

        Format:
        - Lists all tasks with descriptions
        - Lists all skills with descriptions
        - Instructs LLM to return JSON with type and name
        """
        tasks_text = self._format_tasks(manifest)
        skills_text = self._format_skills(manifest)

        return f"""Match this request to the best task or skill.

## Request
{query}

## Available Tasks (high-level, maps to multiple skills)
{tasks_text}

## Available Skills (low-level, direct capabilities)
{skills_text}

## Instructions
- If the request is high-level (build something, create something), choose a TASK
- If the request is specific infrastructure/tooling, choose a SKILL
- Return JSON: {{"type": "task" or "skill", "name": "the-name"}}

## Response:"""

    def _format_tasks(self, manifest: Manifest) -> str:
        """Format tasks as bullet list."""
        return "\n".join([
            f"- {name}: {task.description}"
            for name, task in manifest.tasks.items()
        ])

    def _format_skills(self, manifest: Manifest) -> str:
        """Format skills as bullet list."""
        return "\n".join([
            f"- {name}: {skill.description}"
            for name, skill in manifest.skills.items()
        ])
```

### ClaudeHaikuClient

```python
import anthropic


class ClaudeHaikuClient(ILLMClient):
    """Claude Haiku API client."""

    MODEL = "claude-3-5-haiku-20241022"

    def __init__(self, client: anthropic.Anthropic = None):
        """Initialize with optional Anthropic client.

        Args:
            client: Anthropic client instance (creates new if None)
        """
        self.client = client or anthropic.Anthropic()

    def complete(self, prompt: str, max_tokens: int = 150) -> str:
        """Send prompt to Claude Haiku.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Response text from Haiku

        Raises:
            anthropic.APIError: On API failure
        """
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
```

### JSONResponseParser

```python
import json
from typing import Optional


class JSONResponseParser(IResponseParser):
    """Parses JSON responses from LLM."""

    def __init__(self, fallback_task: Optional[str] = None):
        """Initialize with optional fallback.

        Args:
            fallback_task: Task name to use when parsing fails
        """
        self.fallback_task = fallback_task

    def parse(self, response: str, manifest: Manifest) -> DiscoveryResult:
        """Parse LLM JSON response.

        Handles:
        - Valid JSON with task match
        - Valid JSON with skill match
        - Malformed JSON (falls back)
        - Non-existent task/skill names

        Args:
            response: Raw LLM response text
            manifest: Manifest for validation

        Returns:
            DiscoveryResult with parsed or fallback result
        """
        try:
            parsed = json.loads(response)
            match_type = parsed.get("type", "task")
            match_name = parsed.get("name", "")
        except (json.JSONDecodeError, TypeError):
            return self._create_fallback(manifest)

        return self._validate_and_create(match_type, match_name, manifest)

    def _validate_and_create(
        self, match_type: str, match_name: str, manifest: Manifest
    ) -> DiscoveryResult:
        """Validate match exists in manifest and create result."""
        if match_type == "skill" and match_name in manifest.skills:
            return DiscoveryResult.from_skill(match_name)

        if match_name in manifest.tasks:
            task = manifest.tasks[match_name]
            return DiscoveryResult.from_task(match_name, task.skills)

        # Name not found in manifest
        return DiscoveryResult.error()

    def _create_fallback(self, manifest: Manifest) -> DiscoveryResult:
        """Create fallback result for malformed responses."""
        if self.fallback_task and self.fallback_task in manifest.tasks:
            task = manifest.tasks[self.fallback_task]
            return DiscoveryResult.from_task(self.fallback_task, task.skills)

        # Use first task as fallback
        if manifest.tasks:
            first_task_name = next(iter(manifest.tasks))
            task = manifest.tasks[first_task_name]
            return DiscoveryResult.from_task(first_task_name, task.skills)

        return DiscoveryResult.error()
```

### LLMDiscovery

```python
class LLMDiscovery(ILLMDiscovery):
    """LLM-based skill/task discovery (Tier 3)."""

    def __init__(
        self,
        prompt_builder: IPromptBuilder,
        llm_client: ILLMClient,
        response_parser: IResponseParser
    ):
        """Initialize with dependencies.

        Args:
            prompt_builder: Builds LLM prompts
            llm_client: Sends prompts to LLM
            response_parser: Parses LLM responses
        """
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.response_parser = response_parser

    def discover(self, query: str, manifest: Manifest) -> DiscoveryResult:
        """Use LLM to discover best match.

        Flow:
        1. Build prompt with query and options
        2. Send to LLM
        3. Parse response
        4. Return result

        Args:
            query: User query string
            manifest: Loaded manifest

        Returns:
            DiscoveryResult with match or error
        """
        prompt = self.prompt_builder.build(query, manifest)
        response = self.llm_client.complete(prompt)
        return self.response_parser.parse(response, manifest)
```

---

## Logic Flow (Pseudocode)

```
FUNCTION llm_discover(query, manifest):
    # Step 1: Build prompt
    tasks_text = format_tasks(manifest.tasks)
    skills_text = format_skills(manifest.skills)
    prompt = build_prompt(query, tasks_text, skills_text)

    # Step 2: Call LLM
    response = llm_client.complete(prompt, max_tokens=150)

    # Step 3: Parse response
    TRY:
        parsed = json.parse(response)
        match_type = parsed.type  # "task" or "skill"
        match_name = parsed.name
    CATCH json_error:
        RETURN fallback_to_first_task(manifest)

    # Step 4: Validate and return
    IF match_type == "skill" AND match_name IN manifest.skills:
        RETURN DiscoveryResult.from_skill(match_name)
    ELSE IF match_name IN manifest.tasks:
        RETURN DiscoveryResult.from_task(match_name, manifest.tasks[match_name].skills)
    ELSE:
        RETURN DiscoveryResult.error()
```

---

## Integration Points

### With Router Orchestration (Task 1.6)

The router calls LLM discovery after Tier 1 and Tier 2 fail:

```python
# In SkillRouter.route():
tier1_result = self.direct_matcher.match(query, manifest.skills)
if tier1_result.is_match():
    return tier1_result.to_route_result()

tier2_result = self.task_matcher.match(query, manifest.tasks)
if tier2_result.is_match():
    execution_order = self.dependency_resolver.resolve(tier2_result.skills)
    return RouteResult(
        route_type="task",
        matched=tier2_result.task_name,
        skills=tier2_result.skills,
        execution_order=execution_order
    )

# Tier 3: LLM Discovery
discovery = self.llm_discovery.discover(query, manifest)
if discovery.is_valid:
    execution_order = self.dependency_resolver.resolve(discovery.skills)
    return RouteResult(
        route_type="discovery",
        matched=discovery.matched_name,
        skills=discovery.skills,
        execution_order=execution_order
    )

return RouteResult.error()
```

### With Dependency Resolver (Task 1.2)

Once a match is found, its skills are passed to the dependency resolver:

```python
if discovery.match_type == "skill":
    execution_order = dependency_resolver.resolve([discovery.matched_name])
else:  # task
    execution_order = dependency_resolver.resolve(discovery.skills)
```

---

## File Structure

```
lib/skill_router/
  interfaces/
    discovery.py        # ILLMDiscovery, IPromptBuilder, ILLMClient, IResponseParser
  discovery/
    __init__.py
    result.py           # DiscoveryResult
    prompt_builder.py   # DiscoveryPromptBuilder
    llm_client.py       # ClaudeHaikuClient
    response_parser.py  # JSONResponseParser
    llm_discovery.py    # LLMDiscovery implementation
```

---

## Test Scenarios (from BDD)

| Scenario | Query | Expected Type | Expected Match |
|----------|-------|---------------|----------------|
| High-level task | "I need a way for customers to log in" | discovery | customer-portal |
| Portal request | "set up a portal for our clients" | discovery | customer-portal |
| Auth request | "configure authentication for my app" | discovery | auth-cognito or customer-portal |
| Database request | "set up a PostgreSQL database" | discovery | rds-postgres |
| Malformed JSON | "do something" (LLM returns invalid JSON) | discovery | first task (fallback) |
| Non-existent task | "build something special" (LLM returns unknown name) | error | None |
| Non-existent skill | "configure something" (LLM returns unknown skill) | error | None |

---

## Error Handling

| Error Condition | Behavior |
|-----------------|----------|
| Malformed JSON from LLM | Fall back to first task in manifest |
| LLM returns non-existent task name | Return error result |
| LLM returns non-existent skill name | Return error result |
| Empty manifest (no tasks/skills) | Return error result |
| LLM API failure | Propagate exception (handled at router level) |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Haiku model | Cost-effective for simple classification task |
| 150 max tokens | Response is short JSON, no need for more |
| JSON response format | Easy to parse, explicit structure |
| Fallback to first task | Better UX than hard failure on malformed response |
| Error on unknown names | Don't guess; surface issue to caller |
| Dependency injection | Enables testing with mock LLM client |
| Separate prompt builder | Testable in isolation, swappable formats |
