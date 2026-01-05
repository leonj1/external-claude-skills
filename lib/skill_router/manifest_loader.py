"""Manifest loader implementation for parsing YAML manifests."""
from pathlib import Path
from typing import Dict, Any
import yaml

from lib.skill_router.interfaces.manifest import IManifestLoader
from lib.skill_router.models import Manifest, Skill, Task, Category
from lib.skill_router.exceptions import (
    ManifestNotFoundError,
    ManifestParseError,
    ManifestValidationError
)
from lib.skill_router.manifest_validator import ManifestValidator


class ManifestLoader(IManifestLoader):
    """Loads and parses YAML manifests into Manifest objects."""

    def __init__(self):
        """Initialize the manifest loader with a validator."""
        self.validator = ManifestValidator()

    def load(self, path: str) -> Manifest:
        """Load a manifest from a file path.

        Args:
            path: File system path to the manifest file

        Returns:
            Parsed Manifest object

        Raises:
            ManifestNotFoundError: If the file does not exist
            ManifestParseError: If the YAML is invalid
        """
        file_path = Path(path)

        if not file_path.exists():
            raise ManifestNotFoundError(path)

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return self.load_from_string(content)
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            line_num = line.line + 1 if line else None
            raise ManifestParseError(f"Invalid YAML syntax: {str(e)}", line=line_num)

    def load_from_string(self, content: str) -> Manifest:
        """Load a manifest from a YAML string.

        Args:
            content: YAML content as a string

        Returns:
            Parsed Manifest object

        Raises:
            ManifestParseError: If the YAML is invalid
        """
        try:
            data = yaml.safe_load(content)

            if data is None:
                raise ManifestParseError("Empty manifest")

            # Parse skills section
            skills = self._parse_skills(data.get('skills', {}))

            # Parse tasks section
            tasks = self._parse_tasks(data.get('tasks', {}))

            # Parse categories section
            categories = self._parse_categories(data.get('categories', {}))

            # Create manifest
            manifest = Manifest(
                skills=skills,
                tasks=tasks,
                categories=categories
            )

            # Validate manifest
            validation_errors = self.validator.validate(manifest)
            if validation_errors:
                raise ManifestValidationError(validation_errors)

            return manifest
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            line_num = line.line + 1 if line else None
            raise ManifestParseError(f"Invalid YAML syntax: {str(e)}", line=line_num)

    def _parse_skills(self, skills_data: Dict[str, Any]) -> Dict[str, Skill]:
        """Parse skills section into Skill objects.

        Args:
            skills_data: Raw skills data from YAML

        Returns:
            Dictionary mapping skill names to Skill objects
        """
        skills = {}
        for name, data in skills_data.items():
            skill = Skill(
                name=name,
                description=data.get('description', ''),
                path=data.get('path', ''),
                depends_on=data.get('depends_on', [])
            )
            skills[name] = skill
        return skills

    def _parse_tasks(self, tasks_data: Dict[str, Any]) -> Dict[str, Task]:
        """Parse tasks section into Task objects.

        Args:
            tasks_data: Raw tasks data from YAML

        Returns:
            Dictionary mapping task names to Task objects
        """
        tasks = {}
        for name, data in tasks_data.items():
            task = Task(
                name=name,
                description=data.get('description', ''),
                triggers=data.get('triggers', []),
                skills=data.get('skills', [])
            )
            tasks[name] = task
        return tasks

    def _parse_categories(self, categories_data: Dict[str, Any]) -> Dict[str, Category]:
        """Parse categories section into Category objects.

        Args:
            categories_data: Raw categories data from YAML

        Returns:
            Dictionary mapping category names to Category objects
        """
        categories = {}
        for name, data in categories_data.items():
            category = Category(
                name=name,
                description=data.get('description', ''),
                tasks=data.get('tasks', []),
                skills=data.get('skills', [])
            )
            categories[name] = category
        return categories
