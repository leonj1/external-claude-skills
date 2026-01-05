# DRAFT: Hook Integration for Claude Code

## Overview

This specification defines the hook integration layer that connects the Skill Router system to Claude Code's hooks system. The integration enables automatic skill context injection into prompts based on user queries.

## Root Request Trace

**Root Request**: "Read specs.md and implement the Skill Router system with YAML manifest, 3-tier routing, dependency resolution, and hook integration"

**This spec traces to**: "hook integration" - Claude Code integration layer

## Interfaces Needed

### ISkillContextGenerator

```python
from abc import ABC, abstractmethod
from typing import Optional
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

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

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

### SkillContext

```python
from dataclasses import dataclass, field
from typing import List
from enum import Enum

class SkillRole(Enum):
    """Role of a skill in the context."""
    PRIMARY = "PRIMARY"      # Directly requested or matched
    DEPENDENCY = "DEPENDENCY"  # Required by a primary skill

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

## Implementation Classes

### SkillContentLoader

```python
class SkillContentLoader(ISkillContentLoader):
    """Loads SKILL.md files from the filesystem.

    Resolves skill paths relative to the skills root directory.
    """

    def __init__(self, skills_root: Optional[Path] = None):
        """Initialize with optional skills root.

        Args:
            skills_root: Root directory for skills (default ~/.claude/skills)
        """
        self._skills_root = skills_root or Path("~/.claude/skills").expanduser()

    def set_skills_root(self, path: Path) -> None:
        """Set the skills root directory."""
        self._skills_root = path

    def load(self, skill_name: str, skill_path: str) -> Tuple[str, Optional[str]]:
        """Load SKILL.md content for a skill."""
        # Implementation resolves path and reads file
        pass
```

### SkillContextGenerator

```python
class SkillContextGenerator(ISkillContextGenerator):
    """Generates XML skill context from route results.

    Transforms RouteResult into formatted <skill_context> XML block.
    """

    def __init__(
        self,
        content_loader: ISkillContentLoader,
        manifest_loader: IManifestLoader
    ):
        """Initialize with dependencies.

        Args:
            content_loader: For loading SKILL.md content
            manifest_loader: For loading manifest to get skill paths
        """
        self._content_loader = content_loader
        self._manifest_loader = manifest_loader
        self._manifest: Optional[Manifest] = None

    def generate(self, route_result: RouteResult) -> str:
        """Generate skill context XML from route result."""
        # Returns empty string for error results
        # Otherwise builds XML with sections for each skill
        pass
```

### QuerySource

```python
class EnvironmentQuerySource(IQuerySource):
    """Obtains query from PROMPT environment variable or stdin.

    Checks PROMPT env var first, falls back to stdin.
    """

    def __init__(self, env_var: str = "PROMPT"):
        """Initialize with environment variable name.

        Args:
            env_var: Name of environment variable to check
        """
        self._env_var = env_var

    def get_query(self) -> str:
        """Get query from environment or stdin."""
        pass
```

## Logic Flow

### route_and_inject.py Hook Script

```
1. Initialize components
   - Create ManifestLoader
   - Create SkillContentLoader (with ~/.claude/skills root)
   - Create SkillContextGenerator(content_loader, manifest_loader)
   - Create EnvironmentQuerySource
   - Create Router with all tier matchers

2. Get user query
   query = query_source.get_query()
   IF query is empty:
       EXIT (no output)

3. Route the query
   route_result = router.route(query)
   IF route_result.route_type == ERROR:
       EXIT (no output)

4. Generate skill context
   context = context_generator.generate(route_result)

5. Output to stdout
   PRINT context

6. Exit successfully
```

### SkillContextGenerator.generate() Logic

```
1. Check for error result
   IF route_result.route_type == ERROR:
       RETURN ""

2. Load manifest (cached)
   IF self._manifest is None:
       self._manifest = self._manifest_loader.load(manifest_path)

3. Determine primary skills
   primary_skills = set(route_result.skills)

4. Build sections in execution order
   sections = []
   FOR skill_name IN route_result.execution_order:
       skill = self._manifest.skills.get(skill_name)
       IF skill is None:
           CONTINUE

       role = PRIMARY if skill_name in primary_skills else DEPENDENCY
       content, warning = self._content_loader.load(skill_name, skill.path)

       sections.append(SkillSection(
           name=skill_name,
           role=role,
           content=content,
           warning=warning
       ))

5. Build SkillContext
   skill_context = SkillContext(
       route_type=route_result.route_type.value,
       matched=route_result.matched,
       execution_order=route_result.execution_order,
       sections=sections
   )

6. Format as XML
   RETURN format_xml(skill_context)
```

### XML Output Format

```xml
<skill_context>
Matched: {route_type} '{matched}'
Execution order: {skill1} -> {skill2} -> {skill3}

## {skill_name_1} [PRIMARY]
{skill_1_content}

---

## {skill_name_2} [DEPENDENCY]
{skill_2_content}

---

## {skill_name_3} [PRIMARY]
{skill_3_content}

---

</skill_context>
```

### SkillContentLoader.load() Logic

```
1. Resolve skill path
   full_path = self._skills_root / skill_path / "SKILL.md"

2. Check if file exists
   IF NOT full_path.exists():
       placeholder = f"(Skill file not found: {full_path})"
       warning = f"Missing SKILL.md for skill '{skill_name}'"
       RETURN (placeholder, warning)

3. Read content
   TRY:
       content = full_path.read_text()
       RETURN (content, None)
   EXCEPT IOError as e:
       placeholder = f"(Error reading skill file: {e})"
       warning = f"Could not read SKILL.md for skill '{skill_name}': {e}"
       RETURN (placeholder, warning)
```

### EnvironmentQuerySource.get_query() Logic

```
1. Check environment variable
   query = os.environ.get(self._env_var, "")
   IF query:
       RETURN query.strip()

2. Fall back to stdin
   TRY:
       query = sys.stdin.read().strip()
       RETURN query
   EXCEPT:
       RETURN ""
```

## File Structure

```
lib/skill_router/
  interfaces/
    __init__.py
    hook.py              # ISkillContextGenerator, ISkillContentLoader, IQuerySource
  hook_integration/
    __init__.py
    skill_content_loader.py
    skill_context_generator.py
    query_source.py
    models.py            # SkillRole, SkillSection, SkillContext

hooks/
  route_and_inject.py    # CLI hook script
```

## Context Budget

| Item | Estimate |
|------|----------|
| Files to read | 4 (~150 lines) - existing interfaces, models |
| New interface code | ~50 lines |
| New implementation code | ~120 lines |
| Hook script | ~40 lines |
| Test code | ~200 lines |
| **Total new code** | ~410 lines |
| **Estimated context usage** | ~25% |

## Acceptance Criteria

From `tests/bdd/hook-integration.feature`:

1. Single skill context injection with PRIMARY marking
2. Multiple skills in execution order
3. PRIMARY vs DEPENDENCY marking
4. Task skills all marked as PRIMARY
5. Output wrapped in `<skill_context>` tags
6. Execution order summary in output
7. Route type and matched name in output
8. SKILL.md content loading
9. Missing SKILL.md handling with placeholder
10. Query from PROMPT env var or stdin
11. No output for error route results
12. End-to-end flow from query to context

## Dependencies

- `lib/skill_router/interfaces/router.py` - RouteResult, RouteType
- `lib/skill_router/interfaces/manifest.py` - IManifestLoader
- `lib/skill_router/models.py` - Manifest, Skill
- `lib/skill_router/manifest_loader.py` - ManifestLoader
- Router orchestration (Task 1.6) - IRouter implementation
