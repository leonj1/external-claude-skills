"""Skill content loader implementation."""
import os
from pathlib import Path
from typing import Tuple, Optional

from lib.skill_router.interfaces.hook import ISkillContentLoader


class SkillContentLoader(ISkillContentLoader):
    """Loads SKILL.md file content from skill directories.

    Resolves paths relative to a configurable skills root directory.
    Returns placeholder text and warning for missing files.
    """

    def __init__(self, skills_root: Optional[Path] = None):
        """Initialize the content loader.

        Args:
            skills_root: Base path for skill directories.
                        Defaults to ~/.claude/skills if None.
        """
        if skills_root is None:
            skills_root = Path.home() / ".claude" / "skills"
        self._skills_root = skills_root

    def set_skills_root(self, path: Path) -> None:
        """Set the root directory for skill resolution.

        Args:
            path: Path to the skills root directory
        """
        self._skills_root = path

    def load(self, skill_name: str, skill_path: str) -> Tuple[str, Optional[str]]:
        """Load skill content from SKILL.md file.

        Path resolution:
            full_path = skills_root / skill_path / "SKILL.md"

        Args:
            skill_name: Name of the skill
            skill_path: Relative path to skill directory

        Returns:
            Tuple of (content, warning_message).
            - (content, None) if file exists and loaded
            - (placeholder, warning) if file or directory missing
        """
        # Construct full path
        full_path = self._skills_root / skill_path / "SKILL.md"

        # Check if file exists
        if full_path.exists():
            try:
                content = full_path.read_text(encoding='utf-8')
                return (content, None)
            except Exception as e:
                # File exists but couldn't read it
                placeholder = f"(Skill file not found: {full_path})"
                warning = f"Warning: Failed to read SKILL.md for '{skill_name}' at {full_path}: {e}"
                return (placeholder, warning)

        # File doesn't exist
        placeholder = f"(Skill file not found: {full_path})"
        warning = f"Warning: SKILL.md not found for '{skill_name}' at {full_path}"
        return (placeholder, warning)
