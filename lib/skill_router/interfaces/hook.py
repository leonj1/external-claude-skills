"""Interfaces for hook integration components."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional

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
