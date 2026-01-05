"""Tests for manifest loading functionality."""
import pytest
import tempfile
import os
from pathlib import Path
from lib.skill_router.manifest_loader import ManifestLoader
from lib.skill_router.models import Manifest
from lib.skill_router.exceptions import ManifestNotFoundError, ManifestParseError


# Test fixtures with valid YAML
MINIMAL_MANIFEST = """
skills: {}
tasks: {}
categories: {}
"""

MANIFEST_WITH_SKILL = """
skills:
  terraform-base:
    description: Terraform state backend setup
    path: infrastructure/terraform-base
    depends_on: []
tasks: {}
categories: {}
"""

MANIFEST_WITH_DEPENDENCIES = """
skills:
  terraform-base:
    description: Terraform state backend setup
    path: infrastructure/terraform-base
    depends_on: []
  ecr-setup:
    description: ECR repository setup
    path: infrastructure/ecr-setup
    depends_on:
      - terraform-base
tasks: {}
categories: {}
"""

MANIFEST_WITH_TASK = """
skills:
  nextjs-standards:
    description: NextJS coding standards
    path: skills/nextjs-standards
  aws-static-hosting:
    description: AWS static hosting setup
    path: skills/aws-static-hosting
tasks:
  static-website:
    description: Static website or landing page
    triggers:
      - build a static website
      - create a landing page
    skills:
      - nextjs-standards
      - aws-static-hosting
categories: {}
"""

MANIFEST_WITH_CATEGORY = """
skills: {}
tasks:
  static-website:
    description: Static website
    triggers: []
    skills: []
  admin-panel:
    description: Admin panel
    triggers: []
    skills: []
categories:
  web-development:
    description: Websites and web applications
    tasks:
      - static-website
      - admin-panel
    skills: []
"""


class TestManifestLoaderLoadFromString:
    """Test loading manifests from YAML strings."""

    def test_successfully_load_valid_manifest(self):
        """Scenario: Successfully load a valid manifest file."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MINIMAL_MANIFEST)

        assert manifest is not None
        assert isinstance(manifest, Manifest)
        assert isinstance(manifest.skills, dict)
        assert isinstance(manifest.tasks, dict)
        assert isinstance(manifest.categories, dict)

    def test_load_manifest_with_all_skill_fields(self):
        """Scenario: Load manifest with all required skill fields."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MANIFEST_WITH_SKILL)

        # Skill "terraform-base" is registered
        assert "terraform-base" in manifest.skills
        skill = manifest.skills["terraform-base"]

        # Skill has correct description
        assert skill.description == "Terraform state backend setup"

        # Skill has correct path
        assert skill.path == "infrastructure/terraform-base"

        # Skill has empty dependency list
        assert skill.depends_on == []
        assert skill.name == "terraform-base"

    def test_load_manifest_with_dependencies(self):
        """Scenario: Load manifest with skill dependencies."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MANIFEST_WITH_DEPENDENCIES)

        # Skill "ecr-setup" depends on "terraform-base"
        assert "ecr-setup" in manifest.skills
        ecr_skill = manifest.skills["ecr-setup"]
        assert "terraform-base" in ecr_skill.depends_on

    def test_load_manifest_with_task_definitions(self):
        """Scenario: Load manifest with task definitions."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MANIFEST_WITH_TASK)

        # Task "static-website" is registered
        assert "static-website" in manifest.tasks
        task = manifest.tasks["static-website"]

        # Task has 2 triggers
        assert len(task.triggers) == 2
        assert "build a static website" in task.triggers
        assert "create a landing page" in task.triggers

        # Task requires 2 skills
        assert len(task.skills) == 2
        assert "nextjs-standards" in task.skills
        assert "aws-static-hosting" in task.skills

    def test_load_manifest_with_category_definitions(self):
        """Scenario: Load manifest with category definitions."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MANIFEST_WITH_CATEGORY)

        # Category "web-development" is registered
        assert "web-development" in manifest.categories
        category = manifest.categories["web-development"]

        # Category contains 2 tasks
        assert len(category.tasks) == 2
        assert "static-website" in category.tasks
        assert "admin-panel" in category.tasks


class TestManifestLoaderLoadFromFile:
    """Test loading manifests from file paths."""

    def test_load_from_file_path(self):
        """Load manifest from a file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(MINIMAL_MANIFEST)
            temp_path = f.name

        try:
            loader = ManifestLoader()
            manifest = loader.load(temp_path)

            assert manifest is not None
            assert isinstance(manifest, Manifest)
        finally:
            os.unlink(temp_path)

    def test_load_from_file_with_skills(self):
        """Load manifest file with skill definitions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(MANIFEST_WITH_SKILL)
            temp_path = f.name

        try:
            loader = ManifestLoader()
            manifest = loader.load(temp_path)

            assert "terraform-base" in manifest.skills
            assert manifest.skills["terraform-base"].path == "infrastructure/terraform-base"
        finally:
            os.unlink(temp_path)


class TestManifestLoaderEdgeCases:
    """Test edge cases in manifest loading."""

    def test_manifest_with_empty_sections(self):
        """Handle manifest with no entries in sections."""
        loader = ManifestLoader()
        manifest = loader.load_from_string(MINIMAL_MANIFEST)

        assert manifest.skills == {}
        assert manifest.tasks == {}
        assert manifest.categories == {}

    def test_skill_with_missing_optional_depends_on(self):
        """Handle skill without depends_on field (should default to empty list)."""
        yaml_content = """
skills:
  simple-skill:
    description: A simple skill
    path: skills/simple
tasks: {}
categories: {}
"""
        loader = ManifestLoader()
        manifest = loader.load_from_string(yaml_content)

        assert "simple-skill" in manifest.skills
        assert manifest.skills["simple-skill"].depends_on == []

    def test_task_with_empty_triggers_and_skills(self):
        """Handle task with empty triggers and skills lists."""
        yaml_content = """
skills: {}
tasks:
  empty-task:
    description: Task with no triggers or skills
    triggers: []
    skills: []
categories: {}
"""
        loader = ManifestLoader()
        manifest = loader.load_from_string(yaml_content)

        assert "empty-task" in manifest.tasks
        assert manifest.tasks["empty-task"].triggers == []
        assert manifest.tasks["empty-task"].skills == []
