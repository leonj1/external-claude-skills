"""Dependency resolver implementation using Kahn's topological sort algorithm."""
from collections import deque
from typing import Dict, List, Set, Tuple
from lib.skill_router.models import Skill
from lib.skill_router.interfaces.dependency import IDependencyResolver, ITopologicalSorter
from lib.skill_router.dependency_graph import DependencyResult, MissingDependencyWarning
from lib.skill_router.exceptions import CyclicDependencyError


class KahnsTopologicalSorter(ITopologicalSorter):
    """Topological sorter using Kahn's algorithm."""

    def sort(self, nodes: List[str], edges: Dict[str, List[str]]) -> List[str]:
        """Sort nodes in topological order using Kahn's algorithm.

        Args:
            nodes: List of all node names
            edges: Dictionary mapping node names to their dependencies

        Returns:
            List of nodes in topological order (dependencies first)
        """
        # Build in-degree map
        in_degree = {node: 0 for node in nodes}
        adjacency = {node: [] for node in nodes}

        # Build adjacency list (reverse of dependencies)
        for node, deps in edges.items():
            for dep in deps:
                if dep in adjacency:
                    adjacency[dep].append(node)
                    in_degree[node] += 1

        # Initialize queue with nodes having in-degree 0
        queue = deque([node for node in nodes if in_degree[node] == 0])
        result = []

        # Process queue
        while queue:
            node = queue.popleft()
            result.append(node)

            # Decrease in-degree for dependents
            for dependent in adjacency[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all nodes processed, there's a cycle
        if len(result) != len(nodes):
            # Include remaining nodes (cycle members)
            remaining = [n for n in nodes if n not in result]
            result.extend(remaining)

        return result

    def find_cycles(self, edges: Dict[str, List[str]]) -> List[Tuple[str, ...]]:
        """Find cycles in the dependency graph using DFS.

        Args:
            edges: Dictionary mapping node names to their dependencies

        Returns:
            List of detected cycles, each as tuple of node names
        """
        cycles = []
        visited = set()
        recursion_stack = []
        recursion_set = set()

        def dfs(node: str):
            """Depth-first search to detect cycles."""
            if node in recursion_set:
                # Cycle detected - extract it from recursion stack
                cycle_start = recursion_stack.index(node)
                cycle = tuple(recursion_stack[cycle_start:])
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.append(node)
            recursion_set.add(node)

            # Visit dependencies
            for dep in edges.get(node, []):
                if dep in edges:  # Only if dep is a known node
                    dfs(dep)

            recursion_stack.pop()
            recursion_set.remove(node)

        # Run DFS from each node
        for node in edges:
            if node not in visited:
                dfs(node)

        return cycles


class KahnsDependencyResolver(IDependencyResolver):
    """Dependency resolver using Kahn's topological sort."""

    def __init__(self):
        """Initialize the dependency resolver."""
        self.sorter = KahnsTopologicalSorter()

    def collect_dependencies(self, skill_name: str, skills: Dict[str, Skill]) -> Set[str]:
        """Collect all transitive dependencies for a skill.

        Args:
            skill_name: Name of the skill
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            Set of all skill names needed (including the target skill)
        """
        collected = set()
        to_process = [skill_name]

        while to_process:
            current = to_process.pop()
            if current in collected:
                continue

            collected.add(current)

            # Add dependencies to process
            if current in skills:
                skill = skills[current]
                for dep in skill.depends_on:
                    if dep not in collected and dep in skills:
                        to_process.append(dep)

        return collected

    def resolve(self, skill_name: str, skills: Dict[str, Skill]) -> DependencyResult:
        """Resolve dependencies for a single skill.

        Args:
            skill_name: Name of the skill to resolve
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            DependencyResult containing execution order and metadata

        Raises:
            KeyError: If skill_name not found in skills dictionary
        """
        if skill_name not in skills:
            raise KeyError(f"Skill '{skill_name}' not found in manifest")

        # Collect all dependencies
        all_skills = self.collect_dependencies(skill_name, skills)

        # Build edges for topological sort
        edges = {}
        warnings = []

        for skill in all_skills:
            skill_obj = skills[skill]
            edges[skill] = []

            for dep in skill_obj.depends_on:
                if dep in skills:
                    edges[skill].append(dep)
                else:
                    # Missing dependency - add warning
                    warning = MissingDependencyWarning(skill, dep)
                    warnings.append(warning.message)

        # Perform topological sort
        nodes = list(all_skills)
        execution_order = self.sorter.sort(nodes, edges)

        # Check for cycles
        cycles = self.sorter.find_cycles(edges)
        has_cycle = len(cycles) > 0

        if has_cycle:
            cycle = cycles[0]
            cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
            warnings.append(f"Circular dependency detected: {cycle_str}")

        return DependencyResult(
            execution_order=execution_order,
            has_cycle=has_cycle,
            warnings=warnings
        )

    def resolve_multi(self, skill_names: List[str], skills: Dict[str, Skill]) -> DependencyResult:
        """Resolve dependencies for multiple skills.

        Args:
            skill_names: List of skill names to resolve
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            DependencyResult containing execution order and metadata
        """
        # Collect dependencies for all requested skills
        all_skills = set()
        for skill_name in skill_names:
            all_skills.update(self.collect_dependencies(skill_name, skills))

        # Build edges for topological sort
        edges = {}
        warnings = []

        for skill in all_skills:
            skill_obj = skills[skill]
            edges[skill] = []

            for dep in skill_obj.depends_on:
                if dep in skills:
                    edges[skill].append(dep)
                else:
                    # Missing dependency - add warning
                    warning = MissingDependencyWarning(skill, dep)
                    warnings.append(warning.message)

        # Perform topological sort
        nodes = list(all_skills)
        execution_order = self.sorter.sort(nodes, edges)

        # Check for cycles
        cycles = self.sorter.find_cycles(edges)
        has_cycle = len(cycles) > 0

        if has_cycle:
            cycle = cycles[0]
            cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
            warnings.append(f"Circular dependency detected: {cycle_str}")

        return DependencyResult(
            execution_order=execution_order,
            has_cycle=has_cycle,
            warnings=warnings
        )

    def detect_cycles(self, skills: Dict[str, Skill]) -> List[Tuple[str, ...]]:
        """Detect circular dependencies in the skill graph.

        Args:
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            List of detected cycles, each represented as a tuple of skill names
        """
        # Build edges
        edges = {}
        for name, skill in skills.items():
            edges[name] = [dep for dep in skill.depends_on if dep in skills]

        return self.sorter.find_cycles(edges)
