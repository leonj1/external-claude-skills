"""Interfaces for router orchestration components."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from enum import Enum


class RouteType(Enum):
    """Type of route match."""
    SKILL = "skill"           # Tier 1: Direct skill match
    TASK = "task"             # Tier 2: Task trigger match
    DISCOVERY = "discovery"   # Tier 3: LLM discovery
    ERROR = "error"           # No match found


@dataclass(frozen=True)
class RouteResult:
    """Represents the result of routing a user query.

    Attributes:
        route_type: How the match was found (skill, task, discovery, error)
        matched: Name of matched skill or task
        skills: List of skill names to load
        execution_order: Dependency-resolved order for skill loading
        tier: Which tier produced the match (1, 2, or 3)
        confidence: Match confidence (1.0 for tier 1/2, LLM confidence for tier 3)
    """
    route_type: RouteType
    matched: str
    skills: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    tier: int = 0
    confidence: float = 1.0

    @classmethod
    def skill_match(cls, skill_name: str, execution_order: List[str]) -> "RouteResult":
        """Factory for Tier 1 skill match.

        Args:
            skill_name: Name of the matched skill
            execution_order: Dependency-resolved execution order

        Returns:
            RouteResult with skill match type and tier 1
        """
        return cls(
            route_type=RouteType.SKILL,
            matched=skill_name,
            skills=[skill_name],
            execution_order=execution_order,
            tier=1,
            confidence=1.0
        )

    @classmethod
    def task_match(cls, task_name: str, skills: List[str], execution_order: List[str]) -> "RouteResult":
        """Factory for Tier 2 task match.

        Args:
            task_name: Name of the matched task
            skills: List of skill names required by the task
            execution_order: Dependency-resolved execution order

        Returns:
            RouteResult with task match type and tier 2
        """
        return cls(
            route_type=RouteType.TASK,
            matched=task_name,
            skills=skills,
            execution_order=execution_order,
            tier=2,
            confidence=1.0
        )

    @classmethod
    def discovery_match(cls, skill_name: str, execution_order: List[str], confidence: float) -> "RouteResult":
        """Factory for Tier 3 LLM discovery match.

        Args:
            skill_name: Name of the matched skill
            execution_order: Dependency-resolved execution order
            confidence: LLM confidence score (0.0-1.0)

        Returns:
            RouteResult with discovery match type and tier 3
        """
        return cls(
            route_type=RouteType.DISCOVERY,
            matched=skill_name,
            skills=[skill_name],
            execution_order=execution_order,
            tier=3,
            confidence=confidence
        )

    @classmethod
    def no_match(cls) -> "RouteResult":
        """Factory for no match (error) result.

        Returns:
            RouteResult with error type and empty data
        """
        return cls(
            route_type=RouteType.ERROR,
            matched="",
            skills=[],
            execution_order=[],
            tier=0,
            confidence=0.0
        )

    def is_match(self) -> bool:
        """Check if this result represents a valid match.

        Returns:
            True if route type is not ERROR, False otherwise
        """
        return self.route_type != RouteType.ERROR


class IRouter(ABC):
    """Interface for the top-level skill routing orchestrator.

    Coordinates the 3-tier matching flow and constructs unified RouteResult.
    """

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """Route a user query through the 3-tier matching pipeline.

        Args:
            query: User's natural language request

        Returns:
            RouteResult containing match type, matched entity, skills, and execution order

        Raises:
            ManifestError: If manifest loading or validation fails
        """
        pass
