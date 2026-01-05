# DRAFT: Hook Integration Interfaces (Task 1.7a)

## Overview

This specification defines the interfaces and data models for the Hook Integration layer. These contracts enable the Skill Router to generate context for injection into Claude Code prompts.

## Root Request Trace

**Root Request**: "Read specs.md and implement the Skill Router system with YAML manifest, 3-tier routing, dependency resolution, and hook integration"

**This spec traces to**: "hook integration" - Defines the contracts for context generation, content loading, and query sourcing.

## Interfaces Needed

### ISkillContextGenerator

Transforms routing results into formatted XML skill context.

```python
from abc import ABC, abstractmethod
from lib.skill_router.interfaces.router import RouteResult

class ISkillContextGenerator(ABC):
    """Interface for generating skill context XML from route results.

    Transforms a RouteResult into formatted XML skill context that can
    be injected into Claude Code prompts.
    """

    @abstractmethod
    def generate(self, route_result: RouteResult) -> str:
        """Generate skill context XML from a route result.

        Args:
            route_result: The routing result containing matched skills

        Returns:
            Formatted skill context XML string, empty string for error results
        """
        pass
```

### ISkillContentLoader

Resolves skill paths and reads SKILL.md documentation content.

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional

class ISkillContentLoader(ABC):
    """Interface for loading skill content from SKILL.md files.

    Resolves skill paths and reads documentation content.
    """

    @abstractmethod
    def load(self, skill_name: str, skill_path: str) -> Tuple[str, Optional[str]]:
        """Load skill content from SKILL.md file.

        Args:
            skill_name: Name of the skill
            skill_path: Relative path to skill directory

        Returns:
            Tuple of (content, warning_message).
            Content is the SKILL.md text or placeholder.
            Warning is None if loaded successfully, else warning message.
        """
        pass

    @abstractmethod
    def set_skills_root(self, path: Path) -> None:
        """Set the root directory for skill resolution.

        Args:
            path: Path to the skills root directory
        """
        pass
```

### IQuerySource

Abstracts the source of the user query for routing.

```python
from abc import ABC, abstractmethod

class IQuerySource(ABC):
    """Interface for obtaining the user query for routing.

    Abstracts the source of the query (environment variable, stdin, etc).
    """

    @abstractmethod
    def get_query(self) -> str:
        """Get the user query from the configured source.

        Returns:
            The user query string, empty string if not available
        """
        pass
```

## Data Models

### SkillRole Enum

Indicates whether a skill is directly matched or a dependency.

```python
from enum import Enum

class SkillRole(Enum):
    """Role of a skill in the context."""
    PRIMARY = "PRIMARY"       # Directly requested or matched
    DEPENDENCY = "DEPENDENCY" # Required by a primary skill
```

### SkillSection

A single skill's content section in the context.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SkillSection:
    """A single skill's content section in the context.

    Attributes:
        name: Skill identifier
        role: Whether skill is PRIMARY or DEPENDENCY
        content: The SKILL.md content or placeholder
        warning: Optional warning if content couldn't be loaded
    """
    name: str
    role: SkillRole
    content: str
    warning: Optional[str] = None
```

### SkillContext

Complete skill context for injection into prompts.

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class SkillContext:
    """Complete skill context for injection.

    Attributes:
        route_type: How the match was found (skill, task, discovery)
        matched: Name of matched entity
        execution_order: Skills in dependency-resolved order
        sections: List of skill content sections
    """
    route_type: str
    matched: str
    execution_order: List[str]
    sections: List[SkillSection] = field(default_factory=list)
```

## File Structure

```
lib/skill_router/
  interfaces/
    __init__.py           # Export all interfaces
    hook.py               # ISkillContextGenerator, ISkillContentLoader, IQuerySource
  hook_integration/
    __init__.py           # Export all models
    models.py             # SkillRole, SkillSection, SkillContext
```

## Context Budget

| Item | Estimate |
|------|----------|
| Files to read | 2 (~50 lines) - existing interfaces for reference |
| New interface code (hook.py) | ~45 lines |
| New model code (models.py) | ~35 lines |
| Test code | ~80 lines |
| **Total new code** | ~160 lines |
| **Estimated context usage** | ~10% |

## Acceptance Criteria

1. `ISkillContextGenerator` interface defined with `generate(route_result) -> str`
2. `ISkillContentLoader` interface defined with `load()` and `set_skills_root()`
3. `IQuerySource` interface defined with `get_query() -> str`
4. `SkillRole` enum with PRIMARY and DEPENDENCY values
5. `SkillSection` dataclass with name, role, content, warning fields
6. `SkillContext` dataclass with route_type, matched, execution_order, sections
7. All interfaces use ABC pattern with `@abstractmethod`
8. All models use `@dataclass` decorator
9. Type hints on all methods and attributes

## Dependencies

- `lib/skill_router/interfaces/router.py` - RouteResult (for type hint in ISkillContextGenerator)

## Out of Scope (Task 1.7b)

The following are explicitly NOT part of this task:
- SkillContentLoader implementation
- SkillContextGenerator implementation
- EnvironmentQuerySource implementation
- route_and_inject.py hook script
- XML formatting logic
- File I/O operations
