"""Data models for hook integration components."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SkillRole(Enum):
    """Role of a skill in the context."""
    PRIMARY = "PRIMARY"       # Directly requested or matched
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
