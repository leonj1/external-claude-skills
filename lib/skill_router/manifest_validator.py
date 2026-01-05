"""Manifest validator implementation for checking reference consistency."""
from typing import List

from lib.skill_router.interfaces.manifest import IManifestValidator
from lib.skill_router.models import Manifest


class ManifestValidator(IManifestValidator):
    """Validates manifest consistency by checking all references."""

    def validate(self, manifest: Manifest) -> List[str]:
        """Validate a manifest for consistency.

        Checks that:
        - All skill dependencies exist in manifest.skills
        - All skills referenced by tasks exist in manifest.skills
        - All tasks referenced by categories exist in manifest.tasks
        - All skills referenced by categories exist in manifest.skills

        Args:
            manifest: The manifest to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate skill dependencies
        errors.extend(self._validate_skill_dependencies(manifest))

        # Validate task skill references
        errors.extend(self._validate_task_skills(manifest))

        # Validate category task references
        errors.extend(self._validate_category_tasks(manifest))

        # Validate category skill references
        errors.extend(self._validate_category_skills(manifest))

        return errors

    def _validate_skill_dependencies(self, manifest: Manifest) -> List[str]:
        """Validate that all skill dependencies exist.

        Args:
            manifest: The manifest to validate

        Returns:
            List of error messages for missing dependencies
        """
        errors = []
        for skill_name, skill in manifest.skills.items():
            for dependency in skill.depends_on:
                if dependency not in manifest.skills:
                    errors.append(
                        f"Skill '{skill_name}' depends on unknown skill '{dependency}'"
                    )
        return errors

    def _validate_task_skills(self, manifest: Manifest) -> List[str]:
        """Validate that all skills referenced by tasks exist.

        Args:
            manifest: The manifest to validate

        Returns:
            List of error messages for missing skill references
        """
        errors = []
        for task_name, task in manifest.tasks.items():
            for skill_ref in task.skills:
                if skill_ref not in manifest.skills:
                    errors.append(
                        f"Task '{task_name}' references unknown skill '{skill_ref}'"
                    )
        return errors

    def _validate_category_tasks(self, manifest: Manifest) -> List[str]:
        """Validate that all tasks referenced by categories exist.

        Args:
            manifest: The manifest to validate

        Returns:
            List of error messages for missing task references
        """
        errors = []
        for category_name, category in manifest.categories.items():
            for task_ref in category.tasks:
                if task_ref not in manifest.tasks:
                    errors.append(
                        f"Category '{category_name}' references unknown task '{task_ref}'"
                    )
        return errors

    def _validate_category_skills(self, manifest: Manifest) -> List[str]:
        """Validate that all skills referenced by categories exist.

        Args:
            manifest: The manifest to validate

        Returns:
            List of error messages for missing skill references
        """
        errors = []
        for category_name, category in manifest.categories.items():
            for skill_ref in category.skills:
                if skill_ref not in manifest.skills:
                    errors.append(
                        f"Category '{category_name}' references unknown skill '{skill_ref}'"
                    )
        return errors
