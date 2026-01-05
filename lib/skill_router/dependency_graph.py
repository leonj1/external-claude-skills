"""Data structures for dependency graph and resolution results."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class DependencyResult:
    """Result of dependency resolution.

    Attributes:
        execution_order: List of skill names in execution order (dependencies first)
        has_cycle: Whether a circular dependency was detected
        warnings: List of warning messages generated during resolution
    """
    execution_order: List[str] = field(default_factory=list)
    has_cycle: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class MissingDependencyWarning:
    """Warning issued when a dependency reference is missing.

    Attributes:
        skill: Name of the skill with missing dependency
        missing: Name of the missing dependency
        message: Human-readable warning message
    """
    skill: str
    missing: str
    message: str = field(init=False)

    def __post_init__(self):
        """Initialize message based on skill and missing dependency."""
        self.message = f"Skill '{self.skill}' depends on '{self.missing}' which is not in manifest"
