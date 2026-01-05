"""Interfaces for dependency resolution components."""
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple
from lib.skill_router.models import Skill
from lib.skill_router.dependency_graph import DependencyResult


class IDependencyResolver(ABC):
    """Interface for dependency resolution."""

    @abstractmethod
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
        pass

    @abstractmethod
    def resolve_multi(self, skill_names: List[str], skills: Dict[str, Skill]) -> DependencyResult:
        """Resolve dependencies for multiple skills.

        Args:
            skill_names: List of skill names to resolve
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            DependencyResult containing execution order and metadata
        """
        pass

    @abstractmethod
    def collect_dependencies(self, skill_name: str, skills: Dict[str, Skill]) -> Set[str]:
        """Collect all transitive dependencies for a skill.

        Args:
            skill_name: Name of the skill
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            Set of all skill names needed (including the target skill)
        """
        pass

    @abstractmethod
    def detect_cycles(self, skills: Dict[str, Skill]) -> List[Tuple[str, ...]]:
        """Detect circular dependencies in the skill graph.

        Args:
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            List of detected cycles, each represented as a tuple of skill names
        """
        pass


class ITopologicalSorter(ABC):
    """Interface for topological sorting algorithms."""

    @abstractmethod
    def sort(self, nodes: List[str], edges: Dict[str, List[str]]) -> List[str]:
        """Sort nodes in topological order using Kahn's algorithm.

        Args:
            nodes: List of all node names
            edges: Dictionary mapping node names to their dependencies

        Returns:
            List of nodes in topological order (dependencies first)
        """
        pass

    @abstractmethod
    def find_cycles(self, edges: Dict[str, List[str]]) -> List[Tuple[str, ...]]:
        """Find cycles in the dependency graph.

        Args:
            edges: Dictionary mapping node names to their dependencies

        Returns:
            List of detected cycles, each as tuple of node names
        """
        pass
