# DRAFT: Skill Router System

> Status: DRAFT
> Task: Skill Router System with YAML manifest, 3-tier routing, dependency resolution, and hook integration

---

## 1. Overview

The Skill Router is a system that maps user queries to executable skills through intelligent routing. It uses a YAML manifest to define skills, tasks, and their relationships, then routes incoming requests through a 3-tier matching system.

---

## 2. Interfaces Needed

### 2.1 IManifestLoader

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class IManifestLoader(ABC):
    """Loads and parses the skill manifest file."""

    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """Load manifest from path, return parsed dict."""
        pass

    @abstractmethod
    def validate(self, manifest: Dict[str, Any]) -> bool:
        """Validate manifest structure and references."""
        pass
```

### 2.2 ISkillMatcher

```python
from abc import ABC, abstractmethod
from typing import Optional

class ISkillMatcher(ABC):
    """Matches user queries to skills or tasks."""

    @abstractmethod
    def match(self, query: str, manifest: Dict[str, Any]) -> Optional[str]:
        """Attempt to match query. Return skill/task name or None."""
        pass
```

### 2.3 IDependencyResolver

```python
from abc import ABC, abstractmethod
from typing import List

class IDependencyResolver(ABC):
    """Resolves skill dependencies into execution order."""

    @abstractmethod
    def resolve(self, skills: List[str], all_skills: Dict[str, Any]) -> List[str]:
        """Return topologically sorted execution order."""
        pass

    @abstractmethod
    def detect_cycles(self, skills: Dict[str, Any]) -> List[List[str]]:
        """Return list of cycles if any exist."""
        pass
```

### 2.4 IRouter

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class RouteResult:
    route_type: str      # "task", "skill", "discovery", or "error"
    matched: str         # matched task or skill name
    skills: List[str]    # primary skills to load
    execution_order: List[str]  # dependency-resolved order

class IRouter(ABC):
    """Routes user queries through the 3-tier system."""

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """Route query through tiers, return result."""
        pass
```

### 2.5 ILLMDiscovery

```python
from abc import ABC, abstractmethod

class ILLMDiscovery(ABC):
    """LLM-based fallback for ambiguous queries."""

    @abstractmethod
    def discover(self, query: str, options: Dict[str, Any]) -> Dict[str, str]:
        """Ask LLM to match query. Return {"type": "task"|"skill", "name": "..."}."""
        pass
```

### 2.6 IHookIntegration

```python
from abc import ABC, abstractmethod
from typing import List

class IHookIntegration(ABC):
    """Integrates routing results with Claude Code hooks."""

    @abstractmethod
    def inject_skills(self, result: RouteResult) -> str:
        """Generate skill context injection string."""
        pass

    @abstractmethod
    def load_skill_content(self, skill_name: str) -> str:
        """Load content from skill's SKILL.md file."""
        pass
```

---

## 3. Data Models

### 3.1 Manifest Schema

```yaml
# YAML Schema Definition

skills:
  <skill-name>:
    description: string      # Human-readable description
    path: string             # Relative path to skill directory
    depends_on: list[string] # List of skill names this depends on

tasks:
  <task-name>:
    description: string      # Human-readable description
    triggers: list[string]   # Phrases that activate this task
    skills: list[string]     # Skills this task requires

categories:
  <category-name>:
    description: string      # Human-readable description
    tasks: list[string]      # Tasks in this category
    skills: list[string]     # Optional: direct skill access
```

### 3.2 Python Data Classes

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Skill:
    name: str
    description: str
    path: str
    depends_on: List[str] = field(default_factory=list)

@dataclass
class Task:
    name: str
    description: str
    triggers: List[str]
    skills: List[str]

@dataclass
class Category:
    name: str
    description: str
    tasks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

@dataclass
class Manifest:
    skills: Dict[str, Skill]
    tasks: Dict[str, Task]
    categories: Dict[str, Category]
```

### 3.3 RouteResult

```python
@dataclass
class RouteResult:
    route_type: str      # "task" | "skill" | "discovery" | "error"
    matched: str         # Name of matched task or skill
    skills: List[str]    # Primary skills requested
    execution_order: List[str]  # Topologically sorted order
```

---

## 4. Logic Flow

### 4.1 Router.route(query) Pseudocode

```
function route(query: string) -> RouteResult:
    manifest = manifest_loader.load(MANIFEST_PATH)
    query_lower = normalize(query)

    # Tier 1: Direct Skill Match
    skill = direct_skill_matcher.match(query_lower, manifest.skills)
    if skill:
        execution_order = dependency_resolver.resolve([skill], manifest.skills)
        return RouteResult(
            route_type="skill",
            matched=skill,
            skills=[skill],
            execution_order=execution_order
        )

    # Tier 2: Task Trigger Match
    task = task_trigger_matcher.match(query_lower, manifest.tasks)
    if task:
        task_skills = manifest.tasks[task].skills
        execution_order = dependency_resolver.resolve(task_skills, manifest.skills)
        return RouteResult(
            route_type="task",
            matched=task,
            skills=task_skills,
            execution_order=execution_order
        )

    # Tier 3: LLM Discovery
    discovery_result = llm_discovery.discover(query, manifest)
    if discovery_result.type == "skill":
        execution_order = dependency_resolver.resolve([discovery_result.name], manifest.skills)
        return RouteResult(
            route_type="discovery",
            matched=discovery_result.name,
            skills=[discovery_result.name],
            execution_order=execution_order
        )
    elif discovery_result.type == "task":
        task_skills = manifest.tasks[discovery_result.name].skills
        execution_order = dependency_resolver.resolve(task_skills, manifest.skills)
        return RouteResult(
            route_type="discovery",
            matched=discovery_result.name,
            skills=task_skills,
            execution_order=execution_order
        )

    # No match found
    return RouteResult(route_type="error", matched="", skills=[], execution_order=[])
```

### 4.2 DirectSkillMatcher.match(query, skills) Pseudocode

```
function match(query: string, skills: dict) -> string | None:
    patterns = [
        "use {skill}",
        "apply {skill}",
        "run {skill}",
        "execute {skill}",
        "{skill} skill",
        "deploy with {skill}",
        "set up {skill}",
        "configure {skill}"
    ]

    for skill_name in skills.keys():
        # Exact substring match
        if skill_name in query:
            return skill_name

        # Pattern-based match
        for pattern in patterns:
            if pattern.format(skill=skill_name) in query:
                return skill_name

    return None
```

### 4.3 TaskTriggerMatcher.match(query, tasks) Pseudocode

```
function match(query: string, tasks: dict) -> string | None:
    best_match = None
    best_score = 0.0
    THRESHOLD = 0.6  # 60% word overlap required

    for task_name, task_data in tasks.items():
        for trigger in task_data.triggers:
            trigger_words = set(tokenize(trigger.lower()))
            query_words = set(tokenize(query))

            overlap = len(trigger_words & query_words)
            coverage = overlap / len(trigger_words) if trigger_words else 0

            if coverage > best_score and coverage >= THRESHOLD:
                best_score = coverage
                best_match = task_name

    return best_match
```

### 4.4 DependencyResolver.resolve(skills, all_skills) Pseudocode

```
function resolve(skill_names: list, all_skills: dict) -> list:
    # Step 1: Collect all dependencies recursively
    collected = set()

    function collect(name: string):
        if name in collected or name not in all_skills:
            return
        collected.add(name)
        for dep in all_skills[name].depends_on:
            collect(dep)

    for skill in skill_names:
        collect(skill)

    # Step 2: Topological sort (Kahn's algorithm)
    result = []
    remaining = collected.copy()

    while remaining:
        # Find skill with all dependencies satisfied
        for skill_name in remaining:
            deps = set(all_skills[skill_name].depends_on)
            if deps.issubset(set(result)):
                result.append(skill_name)
                remaining.remove(skill_name)
                break
        else:
            # Cycle detected - append remaining in arbitrary order
            result.extend(remaining)
            break

    return result
```

### 4.5 LLMDiscovery.discover(query, manifest) Pseudocode

```
function discover(query: string, manifest: Manifest) -> dict:
    # Build compact options text
    tasks_text = format_tasks_for_llm(manifest.tasks)
    skills_text = format_skills_for_llm(manifest.skills)

    prompt = f"""Match this request to the best task or skill.

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

    response = llm_client.complete(prompt, model="claude-3-5-haiku", max_tokens=150)

    try:
        return json.parse(response.text)
    except:
        # Fallback: return first task
        return {"type": "task", "name": first(manifest.tasks.keys())}
```

### 4.6 HookIntegration.inject_skills(result) Pseudocode

```
function inject_skills(result: RouteResult) -> string:
    output = []
    output.append("<skill_context>")
    output.append(f"Matched: {result.route_type} '{result.matched}'")
    output.append(f"Execution order: {' -> '.join(result.execution_order)}")
    output.append("")

    for skill_name in result.execution_order:
        is_primary = skill_name in result.skills
        marker = "[PRIMARY]" if is_primary else "[DEPENDENCY]"

        output.append(f"## {skill_name} {marker}")
        content = load_skill_content(skill_name)
        output.append(content)
        output.append("---")

    output.append("</skill_context>")
    return "\n".join(output)
```

---

## 5. Component Structure

```
~/.claude/
  skills/
    manifest.yaml           # Central manifest file
    infrastructure/
      terraform-base/
        SKILL.md
      ecr-setup/
        SKILL.md
      aws-static-hosting/
        SKILL.md
    frameworks/
      nextjs-standards/
        SKILL.md
    auth/
      auth-cognito/
        SKILL.md
  lib/
    skill_router/
      __init__.py
      interfaces.py         # All interface definitions
      models.py             # Data classes
      manifest_loader.py    # IManifestLoader impl
      matchers/
        __init__.py
        direct_skill.py     # DirectSkillMatcher
        task_trigger.py     # TaskTriggerMatcher
      dependency_resolver.py # IDependencyResolver impl
      llm_discovery.py      # ILLMDiscovery impl
      router.py             # IRouter impl
      hook_integration.py   # IHookIntegration impl
  hooks/
    route_and_inject.py     # Pre-tool hook script
```

---

## 6. Hook Configuration

```json
// ~/.claude/config.json
{
  "hooks": {
    "pre-tool": [
      {
        "script": "~/.claude/hooks/route_and_inject.py",
        "environment": ["PROMPT"],
        "inject": "prepend"
      }
    ]
  }
}
```

---

## 7. Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 0 (greenfield design) |
| New code to write | ~400 lines |
| Test code to write | ~300 lines |
| Estimated context usage | ~35% |

**Verdict**: Within 60% threshold. Proceed with implementation.

---

## 8. Implementation Order

1. `models.py` - Data classes for Skill, Task, Category, Manifest, RouteResult
2. `interfaces.py` - All abstract base classes
3. `manifest_loader.py` - YAML loading and validation
4. `dependency_resolver.py` - Topological sort algorithm
5. `matchers/direct_skill.py` - Tier 1 matching
6. `matchers/task_trigger.py` - Tier 2 matching
7. `llm_discovery.py` - Tier 3 LLM fallback
8. `router.py` - Orchestrates the 3-tier flow
9. `hook_integration.py` - Skill content injection
10. `route_and_inject.py` - Claude Code hook entry point

---

## 9. Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Tasks vs Skills | Separate concepts | Tasks are user-facing intents; Skills are implementation units |
| Triggers | Explicit phrase list | Faster than LLM, predictable matching |
| Direct skill access | Always available | Power users and automation can skip discovery |
| Categories | Optional | Only for browsing UI, not required for routing |
| Dependencies | On skills only | Tasks don't have dependencies - they compose skills |
| LLM fallback | Tier 3 only | Minimizes latency and cost for known patterns |
| Topological sort | Kahn's algorithm | Handles DAGs, detects cycles gracefully |

---

## 10. Error Handling

| Scenario | Handling |
|----------|----------|
| Manifest file missing | Raise ManifestNotFoundError with path |
| Invalid YAML syntax | Raise ManifestParseError with line number |
| Missing skill reference in task | Raise ManifestValidationError listing missing skills |
| Circular dependency | Log warning, append remaining skills in arbitrary order |
| LLM response parse failure | Fallback to first task in manifest |
| Skill directory missing | Log warning, continue with placeholder content |
