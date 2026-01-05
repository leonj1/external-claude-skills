"""Data models for the Skill Router system."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Skill:
    """Represents a skill in the manifest.

    Attributes:
        name: Unique identifier for the skill
        description: Human-readable description
        path: File system path to skill implementation
        depends_on: List of skill names this skill depends on
    """
    name: str
    description: str
    path: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class Task:
    """Represents a task in the manifest.

    Attributes:
        name: Unique identifier for the task
        description: Human-readable description
        triggers: List of phrases that trigger this task
        skills: List of skill names required for this task
    """
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


@dataclass
class Category:
    """Represents a category in the manifest.

    Attributes:
        name: Unique identifier for the category
        description: Human-readable description
        tasks: List of task names in this category
        skills: List of skill names in this category
    """
    name: str
    description: str
    tasks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


@dataclass
class Manifest:
    """Represents the complete manifest structure.

    Attributes:
        skills: Dictionary mapping skill names to Skill objects
        tasks: Dictionary mapping task names to Task objects
        categories: Dictionary mapping category names to Category objects
    """
    skills: Dict[str, Skill] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    categories: Dict[str, Category] = field(default_factory=dict)
