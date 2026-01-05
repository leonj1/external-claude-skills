# DRAFT: Dependency Resolver

> Sub-task 1.2 of Skill Router System
> Traces to Root Request term: "dependency resolution"

## Overview

The Dependency Resolver is a standalone module that resolves skill dependencies using topological sort (Kahn's algorithm). It determines the correct execution order for skills, ensuring dependencies are loaded before dependents.

## Interfaces Needed

### IDependencyResolver

Primary interface for dependency resolution operations.

```python
from abc import ABC, abstractmethod
from typing import List, Set, Tuple
from lib.skill_router.models import Skill

class IDependencyResolver(ABC):
    """Interface for resolving skill dependencies into execution order."""

    @abstractmethod
    def resolve(self, skill_name: str, skills: dict[str, Skill]) -> List[str]:
        """Resolve dependencies for a single skill.

        Args:
            skill_name: The target skill to resolve
            skills: Dictionary of all available skills

        Returns:
            List of skill names in execution order (dependencies first)
        """
        pass

    @abstractmethod
    def resolve_multi(self, skill_names: List[str], skills: dict[str, Skill]) -> List[str]:
        """Resolve dependencies for multiple skills.

        Args:
            skill_names: List of target skills to resolve
            skills: Dictionary of all available skills

        Returns:
            List of skill names in execution order (dependencies first)
        """
        pass

    @abstractmethod
    def detect_cycles(self, skills: dict[str, Skill]) -> List[Tuple[str, ...]]:
        """Detect circular dependencies in the skill graph.

        Args:
            skills: Dictionary of all available skills

        Returns:
            List of tuples, each representing a cycle (empty if no cycles)
        """
        pass

    @abstractmethod
    def collect_dependencies(self, skill_name: str, skills: dict[str, Skill]) -> Set[str]:
        """Collect all transitive dependencies for a skill.

        Args:
            skill_name: The target skill
            skills: Dictionary of all available skills

        Returns:
            Set of all skill names (including the target) that need to be loaded
        """
        pass
```

### ITopologicalSorter

Lower-level interface for the sorting algorithm itself.

```python
from abc import ABC, abstractmethod
from typing import List, Set, Tuple

class ITopologicalSorter(ABC):
    """Interface for topological sort operations on a dependency graph."""

    @abstractmethod
    def sort(self, nodes: Set[str], edges: dict[str, List[str]]) -> List[str]:
        """Sort nodes respecting dependency edges.

        Args:
            nodes: Set of node names to include in sort
            edges: Dictionary mapping node -> list of dependencies

        Returns:
            List of nodes in topological order

        Raises:
            CyclicDependencyError: If a cycle is detected
        """
        pass

    @abstractmethod
    def find_cycles(self, edges: dict[str, List[str]]) -> List[Tuple[str, ...]]:
        """Find all cycles in the dependency graph.

        Args:
            edges: Dictionary mapping node -> list of dependencies

        Returns:
            List of tuples representing cycles
        """
        pass
```

## Data Models

### DependencyResult

Result object returned by resolve operations.

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DependencyResult:
    """Result of dependency resolution.

    Attributes:
        execution_order: Skills in correct execution order
        warnings: Any warnings encountered (missing deps, cycles handled)
        has_cycle: True if a cycle was detected and handled
    """
    execution_order: List[str]
    warnings: List[str] = field(default_factory=list)
    has_cycle: bool = False
```

### DependencyGraph

Internal representation of the skill dependency graph.

```python
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class DependencyGraph:
    """Internal representation of skill dependencies.

    Attributes:
        nodes: Set of all skill names in the graph
        edges: Map of skill -> list of skills it depends on
        reverse_edges: Map of skill -> list of skills that depend on it
    """
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    reverse_edges: Dict[str, List[str]] = field(default_factory=dict)

    def add_node(self, name: str) -> None:
        """Add a node to the graph."""
        self.nodes.add(name)
        if name not in self.edges:
            self.edges[name] = []
        if name not in self.reverse_edges:
            self.reverse_edges[name] = []

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add dependency edge: from_node depends on to_node."""
        self.edges[from_node].append(to_node)
        self.reverse_edges[to_node].append(from_node)

    def in_degree(self, node: str) -> int:
        """Count of dependencies for a node."""
        return len(self.edges.get(node, []))
```

## Exception Classes

Add to `lib/skill_router/exceptions.py`:

```python
class DependencyError(Exception):
    """Base exception for dependency resolution errors."""
    pass


class CyclicDependencyError(DependencyError):
    """Raised when a circular dependency is detected.

    Attributes:
        cycle: Tuple of skill names forming the cycle
    """
    def __init__(self, cycle: Tuple[str, ...]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
        super().__init__(f"Circular dependency detected: {cycle_str}")


class MissingDependencyWarning:
    """Warning issued when a dependency reference is missing.

    Not an exception - resolution continues with warning.

    Attributes:
        skill: The skill with the missing dependency
        missing: The dependency that was not found
    """
    def __init__(self, skill: str, missing: str):
        self.skill = skill
        self.missing = missing
        self.message = f"Skill '{skill}' depends on '{missing}' which is not in manifest"
```

## Logic Flow

### resolve_multi (Primary Entry Point)

```
FUNCTION resolve_multi(skill_names, skills):
    # Step 1: Collect all required skills
    collected = empty set
    FOR each skill_name in skill_names:
        collected = collected UNION collect_dependencies(skill_name, skills)

    # Step 2: Build dependency graph for collected skills only
    graph = build_graph(collected, skills)

    # Step 3: Run Kahn's algorithm
    result = kahns_algorithm(graph)

    RETURN result
```

### collect_dependencies (Recursive Collection)

```
FUNCTION collect_dependencies(skill_name, skills):
    IF skill_name NOT IN skills:
        log_warning(MissingDependencyWarning)
        RETURN empty set

    collected = {skill_name}
    FOR each dep in skills[skill_name].depends_on:
        collected = collected UNION collect_dependencies(dep, skills)

    RETURN collected
```

### kahns_algorithm (Topological Sort)

```
FUNCTION kahns_algorithm(graph):
    # Initialize
    in_degree = map of node -> count of incoming edges
    queue = all nodes with in_degree == 0
    result = empty list

    WHILE queue not empty:
        node = dequeue from queue
        append node to result

        FOR each dependent in graph.reverse_edges[node]:
            in_degree[dependent] -= 1
            IF in_degree[dependent] == 0:
                enqueue dependent to queue

    # Check for cycle
    IF len(result) < len(graph.nodes):
        # Cycle detected - handle gracefully
        remaining = graph.nodes - set(result)
        log_warning("Cycle detected, adding remaining: " + remaining)
        result.extend(remaining)
        RETURN DependencyResult(result, warnings, has_cycle=True)

    RETURN DependencyResult(result, warnings, has_cycle=False)
```

### detect_cycles (Cycle Detection)

```
FUNCTION detect_cycles(skills):
    cycles = empty list
    visited = empty set
    rec_stack = empty set

    FUNCTION dfs(node, path):
        IF node in rec_stack:
            # Found cycle - extract it from path
            cycle_start = path.index(node)
            cycle = tuple(path[cycle_start:])
            cycles.append(cycle)
            RETURN

        IF node in visited:
            RETURN

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        FOR each dep in skills[node].depends_on:
            dfs(dep, path)

        path.pop()
        rec_stack.remove(node)

    FOR each skill in skills:
        dfs(skill, empty list)

    RETURN cycles
```

## Integration Points

### Input: Skill Model

Uses existing `Skill` dataclass from `lib/skill_router/models.py`:

```python
@dataclass
class Skill:
    name: str
    description: str
    path: str
    depends_on: List[str] = field(default_factory=list)
```

### Output: Execution Order

Returns `List[str]` of skill names in dependency-resolved order, ready for the Router Orchestration module (Sub-task 1.6) to load skill contents.

### Consumers

- **Router Orchestration (1.6)**: Calls `resolve_multi()` after routing to determine load order
- **Manifest Validator (1.1)**: May call `detect_cycles()` during manifest validation

## File Structure

```
lib/skill_router/
    __init__.py
    models.py              # Existing - Skill, Task, Manifest
    exceptions.py          # Existing + new DependencyError, CyclicDependencyError
    interfaces.py          # New - IDependencyResolver, ITopologicalSorter
    dependency_resolver.py # New - Implementation
    dependency_graph.py    # New - DependencyGraph, DependencyResult
```

## Context Budget

| Category | Count | Lines |
|----------|-------|-------|
| Files to read | 3 | ~120 lines |
| New code to write | ~150 lines | |
| Test code to write | ~200 lines | |
| **Estimated context usage** | **~25%** | |

Files to read:
- `lib/skill_router/models.py` (~66 lines) - Skill model
- `lib/skill_router/exceptions.py` (~47 lines) - Base exceptions
- `tests/bdd/dependency-resolution.feature` (~155 lines) - BDD scenarios

New code breakdown:
- `interfaces.py`: ~50 lines (IDependencyResolver, ITopologicalSorter)
- `dependency_resolver.py`: ~80 lines (KahnsDependencyResolver)
- `dependency_graph.py`: ~40 lines (DependencyGraph, DependencyResult)
- Exception additions: ~20 lines

Test code breakdown:
- Unit tests for KahnsDependencyResolver: ~120 lines
- Unit tests for cycle detection: ~50 lines
- Edge case tests: ~30 lines

**Status: APPROVED** - Context usage well under 60% threshold.
