# DRAFT: Hook Integration Implementation

## Task Reference
- **Task ID**: 1.7b
- **Parent**: 1.7 Hook Integration
- **Root Request**: "Read specs.md and implement the Skill Router system with YAML manifest, 3-tier routing, dependency resolution, and hook integration"
- **Traces To**: "hook integration"

## Overview
Implementation of the hook integration layer that connects the Skill Router to Claude Code. This includes three classes implementing the interfaces from 1.7a and one CLI script that wires everything together.

## Interfaces Being Implemented
From `lib/skill_router/interfaces/hook.py`:
- `ISkillContentLoader` -> `SkillContentLoader`
- `ISkillContextGenerator` -> `SkillContextGenerator`
- `IQuerySource` -> `EnvironmentQuerySource`

From `lib/skill_router/hook_integration/models.py`:
- Uses: `SkillRole`, `SkillSection`, `SkillContext`

---

## Class 1: SkillContentLoader

### Purpose
Loads SKILL.md file content from skill directories. Resolves paths relative to a configurable skills root.

### Implements
`ISkillContentLoader`

### Constructor
```python
def __init__(self, skills_root: Optional[Path] = None):
    """
    Args:
        skills_root: Base path for skill directories.
                     Defaults to ~/.claude/skills if None.
    """
```

### Method: set_skills_root
```python
def set_skills_root(self, path: Path) -> None:
    """Set the root directory for skill resolution."""
```

### Method: load
```python
def load(self, skill_name: str, skill_path: str) -> Tuple[str, Optional[str]]:
    """
    Load skill content from SKILL.md file.

    Path resolution:
        full_path = skills_root / skill_path / "SKILL.md"

    Returns:
        - (content, None) if file exists and loaded
        - (placeholder, warning) if file or directory missing

    Placeholder format:
        "(Skill file not found: {expected_path})"

    Warning format:
        "Warning: SKILL.md not found for '{skill_name}' at {expected_path}"
    """
```

### Logic Flow
```
load(skill_name, skill_path):
    1. Construct full_path = skills_root / skill_path / "SKILL.md"
    2. IF full_path.exists():
           content = full_path.read_text()
           RETURN (content, None)
    3. ELSE:
           placeholder = f"(Skill file not found: {full_path})"
           warning = f"Warning: SKILL.md not found for '{skill_name}' at {full_path}"
           RETURN (placeholder, warning)
```

---

## Class 2: SkillContextGenerator

### Purpose
Generates formatted XML skill context from a RouteResult. Determines which skills are PRIMARY vs DEPENDENCY and assembles the final output.

### Implements
`ISkillContextGenerator`

### Dependencies (Constructor Injection)
```python
def __init__(
    self,
    content_loader: ISkillContentLoader,
    manifest_data: Dict[str, Any]
):
    """
    Args:
        content_loader: Loader for reading SKILL.md files
        manifest_data: Parsed manifest containing skills dict
    """
```

### Method: generate
```python
def generate(self, route_result: RouteResult) -> str:
    """
    Generate skill context XML from route result.

    Returns:
        Empty string if route_result.route_type == "error"
        Formatted XML otherwise
    """
```

### Logic Flow
```
generate(route_result):
    1. IF route_result.route_type == "error":
           RETURN ""

    2. IF execution_order is empty:
           RETURN minimal context with header only

    3. primary_skills = set(route_result.skills)

    4. sections = []
       FOR skill_name IN route_result.execution_order:
           skill_data = manifest_data["skills"].get(skill_name, {})
           skill_path = skill_data.get("path", skill_name)

           content, warning = content_loader.load(skill_name, skill_path)

           role = SkillRole.PRIMARY if skill_name in primary_skills else SkillRole.DEPENDENCY

           section = SkillSection(
               name=skill_name,
               role=role,
               content=content,
               warning=warning
           )
           sections.append(section)

    5. context = SkillContext(
           route_type=route_result.route_type,
           matched=route_result.matched,
           execution_order=route_result.execution_order,
           sections=sections
       )

    6. RETURN format_context(context)
```

### Helper Method: format_context
```python
def _format_context(self, context: SkillContext) -> str:
    """
    Format SkillContext into XML string.

    Output format:

    <skill_context>
    Matched: {route_type} '{matched}'
    Execution order: skill1 -> skill2 -> skill3

    ## skill1 [PRIMARY]
    {content}

    ---

    ## skill2 [DEPENDENCY]
    {content}

    ---

    </skill_context>
    """
```

### Format Logic
```
format_context(context):
    1. lines = ["<skill_context>"]

    2. lines.append(f"Matched: {context.route_type} '{context.matched}'")

    3. execution_str = " -> ".join(context.execution_order)
       lines.append(f"Execution order: {execution_str}")
       lines.append("")

    4. FOR section IN context.sections:
           marker = f"[{section.role.value}]"
           lines.append(f"## {section.name} {marker}")
           lines.append(section.content)
           lines.append("")
           lines.append("---")
           lines.append("")

    5. lines.append("</skill_context>")

    6. RETURN "\n".join(lines)
```

---

## Class 3: EnvironmentQuerySource

### Purpose
Obtains the user query from environment variable PROMPT or falls back to stdin.

### Implements
`IQuerySource`

### Constructor
```python
def __init__(
    self,
    env_var_name: str = "PROMPT",
    stdin_fallback: bool = True
):
    """
    Args:
        env_var_name: Environment variable to check first
        stdin_fallback: Whether to read stdin if env var not set
    """
```

### Method: get_query
```python
def get_query(self) -> str:
    """
    Get query from environment or stdin.

    Order:
        1. Check os.environ.get(env_var_name)
        2. If not set and stdin_fallback, read sys.stdin
        3. Return stripped string, or empty string if nothing
    """
```

### Logic Flow
```
get_query():
    1. query = os.environ.get(self.env_var_name)

    2. IF query is not None:
           RETURN query.strip()

    3. IF self.stdin_fallback:
           TRY:
               query = sys.stdin.read()
               RETURN query.strip()
           EXCEPT:
               RETURN ""

    4. RETURN ""
```

---

## CLI Script: route_and_inject.py

### Purpose
Entry point hook script that wires together all components and outputs skill context to stdout.

### Location
`lib/skill_router/hook_integration/route_and_inject.py`

### Dependencies
- `IQuerySource` (EnvironmentQuerySource)
- `ISkillRouter` (from router orchestration)
- `ISkillContextGenerator` (SkillContextGenerator)
- `ISkillContentLoader` (SkillContentLoader)
- Manifest loader

### Main Flow
```python
#!/usr/bin/env python3
"""Hook script for routing queries and injecting skill context."""

import sys
from pathlib import Path

# Imports from skill_router package
from lib.skill_router.hook_integration.skill_content_loader import SkillContentLoader
from lib.skill_router.hook_integration.skill_context_generator import SkillContextGenerator
from lib.skill_router.hook_integration.environment_query_source import EnvironmentQuerySource
from lib.skill_router.router import SkillRouter  # Orchestrated router from 1.6
from lib.skill_router.manifest_loader import ManifestLoader


def main() -> int:
    """Main entry point for hook integration."""

    # 1. Get manifest path (default ~/.claude/skills/manifest.yaml)
    manifest_path = Path("~/.claude/skills/manifest.yaml").expanduser()

    # 2. Load manifest
    loader = ManifestLoader()
    manifest_data = loader.load(manifest_path)

    # 3. Get query from environment/stdin
    query_source = EnvironmentQuerySource()
    query = query_source.get_query()

    if not query:
        return 0  # No query, exit silently

    # 4. Route the query
    router = SkillRouter(manifest_data)
    route_result = router.route(query)

    # 5. Generate skill context
    skills_root = manifest_path.parent
    content_loader = SkillContentLoader(skills_root)
    context_generator = SkillContextGenerator(content_loader, manifest_data)

    context_output = context_generator.generate(route_result)

    # 6. Output to stdout
    if context_output:
        print(context_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Logic Summary
```
main():
    1. Determine manifest_path (default ~/.claude/skills/manifest.yaml)
    2. Load manifest using ManifestLoader
    3. Get query via EnvironmentQuerySource
    4. IF no query: exit(0)
    5. Route query via SkillRouter
    6. Set up SkillContentLoader with skills_root = manifest_path.parent
    7. Create SkillContextGenerator with content_loader and manifest_data
    8. Generate context from route_result
    9. Print context to stdout
    10. RETURN 0
```

---

## File Structure

```
lib/skill_router/hook_integration/
    __init__.py
    models.py                      # (Already exists from 1.7a)
    skill_content_loader.py        # NEW: SkillContentLoader class
    skill_context_generator.py     # NEW: SkillContextGenerator class
    environment_query_source.py    # NEW: EnvironmentQuerySource class
    route_and_inject.py            # NEW: CLI hook script
```

---

## Data Models Used

From `models.py` (existing):

```python
class SkillRole(Enum):
    PRIMARY = "PRIMARY"
    DEPENDENCY = "DEPENDENCY"

@dataclass
class SkillSection:
    name: str
    role: SkillRole
    content: str
    warning: Optional[str] = None

@dataclass
class SkillContext:
    route_type: str
    matched: str
    execution_order: List[str]
    sections: List[SkillSection]
```

---

## BDD Scenario Coverage

| Scenario | Class/Method |
|----------|--------------|
| Inject single skill context | SkillContextGenerator.generate |
| Inject multiple skill contexts in execution order | SkillContextGenerator.generate |
| Mark primary and dependency skills distinctly | SkillContextGenerator + SkillRole |
| Inject task skills as primary | SkillContextGenerator.generate |
| Generate correct output structure | SkillContextGenerator._format_context |
| Include execution order summary | SkillContextGenerator._format_context |
| Include route type and matched name | SkillContextGenerator._format_context |
| Load skill content from SKILL.md | SkillContentLoader.load |
| Handle missing SKILL.md file | SkillContentLoader.load |
| Handle missing skill directory | SkillContentLoader.load |
| Hook receives query from env var | EnvironmentQuerySource.get_query |
| Hook receives query from stdin | EnvironmentQuerySource.get_query |
| Hook outputs to stdout | route_and_inject.main |
| Handle error route result | SkillContextGenerator.generate |
| Handle empty execution order | SkillContextGenerator.generate |
| Full flow from query to context | route_and_inject.main |

---

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 4 (~200 lines: interfaces/hook.py, models.py, router.py, manifest_loader.py) |
| New code to write | ~150 lines (4 files) |
| Test code to write | ~200 lines |
| Estimated context usage | ~25% |

---

## Exit Criteria

1. SkillContentLoader implements ISkillContentLoader
   - Loads SKILL.md files from skill directories
   - Returns placeholder and warning for missing files
   - Supports configurable skills_root

2. SkillContextGenerator implements ISkillContextGenerator
   - Generates formatted XML skill context
   - Correctly marks PRIMARY vs DEPENDENCY skills
   - Returns empty string for error route results
   - Includes execution order summary

3. EnvironmentQuerySource implements IQuerySource
   - Reads from PROMPT environment variable
   - Falls back to stdin when env var not set
   - Returns empty string when no input available

4. route_and_inject.py CLI script
   - Wires all components together
   - Outputs skill context to stdout
   - Exits gracefully with no query

5. All BDD scenarios from hook-integration.feature pass
