"""Tests for skill router data models."""
import pytest
from dataclasses import FrozenInstanceError
from lib.skill_router.models import Skill, Task, Category, Manifest


class TestSkillModel:
    """Test the Skill dataclass."""

    def test_skill_instantiation_all_fields(self):
        """Skill model can be instantiated with all fields."""
        skill = Skill(
            name="terraform-base",
            description="Terraform state backend setup",
            path="infrastructure/terraform-base",
            depends_on=["aws-base"]
        )

        assert skill.name == "terraform-base"
        assert skill.description == "Terraform state backend setup"
        assert skill.path == "infrastructure/terraform-base"
        assert skill.depends_on == ["aws-base"]

    def test_skill_empty_dependencies(self):
        """Skill with empty depends_on list."""
        skill = Skill(
            name="terraform-base",
            description="Terraform state backend setup",
            path="infrastructure/terraform-base",
            depends_on=[]
        )

        assert skill.depends_on == []

    def test_skill_default_dependencies(self):
        """Skill with default depends_on (should be empty list)."""
        skill = Skill(
            name="terraform-base",
            description="Terraform state backend setup",
            path="infrastructure/terraform-base"
        )

        assert skill.depends_on == []
        assert isinstance(skill.depends_on, list)


class TestTaskModel:
    """Test the Task dataclass."""

    def test_task_instantiation_all_fields(self):
        """Task model can be instantiated with all fields."""
        task = Task(
            name="static-website",
            description="Static website or landing page",
            triggers=["build a static website", "create a landing page"],
            skills=["nextjs-standards", "aws-static-hosting"]
        )

        assert task.name == "static-website"
        assert task.description == "Static website or landing page"
        assert len(task.triggers) == 2
        assert len(task.skills) == 2

    def test_task_empty_lists(self):
        """Task with empty triggers and skills."""
        task = Task(
            name="static-website",
            description="Static website or landing page",
            triggers=[],
            skills=[]
        )

        assert task.triggers == []
        assert task.skills == []


class TestCategoryModel:
    """Test the Category dataclass."""

    def test_category_instantiation_all_fields(self):
        """Category model can be instantiated with all fields."""
        category = Category(
            name="web-development",
            description="Websites and web applications",
            tasks=["static-website", "admin-panel"],
            skills=["nextjs-standards"]
        )

        assert category.name == "web-development"
        assert category.description == "Websites and web applications"
        assert len(category.tasks) == 2
        assert len(category.skills) == 1

    def test_category_default_lists(self):
        """Category with default tasks and skills (should be empty lists)."""
        category = Category(
            name="web-development",
            description="Websites and web applications"
        )

        assert category.tasks == []
        assert category.skills == []
        assert isinstance(category.tasks, list)
        assert isinstance(category.skills, list)


class TestManifestModel:
    """Test the Manifest dataclass."""

    def test_manifest_holds_dictionaries(self):
        """Manifest model holds dictionaries of skills, tasks, categories."""
        skill = Skill(
            name="terraform-base",
            description="Terraform state backend setup",
            path="infrastructure/terraform-base"
        )

        task = Task(
            name="static-website",
            description="Static website or landing page",
            triggers=["build a static website"],
            skills=["nextjs-standards"]
        )

        category = Category(
            name="web-development",
            description="Websites and web applications",
            tasks=["static-website"]
        )

        manifest = Manifest(
            skills={"terraform-base": skill},
            tasks={"static-website": task},
            categories={"web-development": category}
        )

        assert "terraform-base" in manifest.skills
        assert "static-website" in manifest.tasks
        assert "web-development" in manifest.categories
        assert isinstance(manifest.skills, dict)
        assert isinstance(manifest.tasks, dict)
        assert isinstance(manifest.categories, dict)

    def test_manifest_empty_dictionaries(self):
        """Manifest with empty dictionaries."""
        manifest = Manifest(
            skills={},
            tasks={},
            categories={}
        )

        assert manifest.skills == {}
        assert manifest.tasks == {}
        assert manifest.categories == {}
