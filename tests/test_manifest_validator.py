"""Tests for manifest validation functionality."""
import pytest
from lib.skill_router.manifest_validator import ManifestValidator
from lib.skill_router.models import Manifest, Skill, Task, Category


class TestManifestValidatorSkillReferences:
    """Test validation of skill references in tasks."""

    def test_validate_missing_skill_in_task(self):
        """Scenario: Validate skill references in tasks exist."""
        # Create manifest with task referencing non-existent skill
        manifest = Manifest(
            skills={
                "nextjs-standards": Skill(
                    name="nextjs-standards",
                    description="NextJS standards",
                    path="skills/nextjs"
                )
            },
            tasks={
                "static-website": Task(
                    name="static-website",
                    description="Static website",
                    triggers=["build website"],
                    skills=["nextjs-standards", "aws-hosting"]  # aws-hosting doesn't exist
                )
            },
            categories={}
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Validation fails with missing skill error
        assert len(errors) > 0

        # Error identifies "aws-hosting" as missing
        assert any("aws-hosting" in error for error in errors)
        assert any("static-website" in error for error in errors)


class TestManifestValidatorTaskReferences:
    """Test validation of task references in categories."""

    def test_validate_missing_task_in_category(self):
        """Scenario: Validate task references in categories exist."""
        # Create manifest with category referencing non-existent task
        manifest = Manifest(
            skills={},
            tasks={
                "static-website": Task(
                    name="static-website",
                    description="Static website",
                    triggers=[],
                    skills=[]
                )
            },
            categories={
                "web-development": Category(
                    name="web-development",
                    description="Web development",
                    tasks=["static-website", "blog"],  # blog doesn't exist
                    skills=[]
                )
            }
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Validation fails with missing task error
        assert len(errors) > 0

        # Error identifies "blog" as missing
        assert any("blog" in error for error in errors)
        assert any("web-development" in error for error in errors)


class TestManifestValidatorDependencyReferences:
    """Test validation of dependency references."""

    def test_validate_missing_dependency(self):
        """Scenario: Validate dependency references exist."""
        # Create manifest with skill depending on non-existent skill
        manifest = Manifest(
            skills={
                "ecr-setup": Skill(
                    name="ecr-setup",
                    description="ECR setup",
                    path="skills/ecr",
                    depends_on=["missing-base"]  # missing-base doesn't exist
                )
            },
            tasks={},
            categories={}
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Validation fails with missing dependency error
        assert len(errors) > 0

        # Error identifies "missing-base" as missing
        assert any("missing-base" in error for error in errors)
        assert any("ecr-setup" in error for error in errors)


class TestManifestValidatorValidManifest:
    """Test validation of a complete, valid manifest."""

    def test_successfully_validate_complete_manifest(self):
        """Scenario: Successfully validate a complete manifest."""
        # Create manifest with consistent references
        manifest = Manifest(
            skills={
                "terraform-base": Skill(
                    name="terraform-base",
                    description="Terraform base",
                    path="skills/terraform",
                    depends_on=[]
                ),
                "ecr-setup": Skill(
                    name="ecr-setup",
                    description="ECR setup",
                    path="skills/ecr",
                    depends_on=["terraform-base"]  # Valid reference
                ),
                "nextjs-standards": Skill(
                    name="nextjs-standards",
                    description="NextJS standards",
                    path="skills/nextjs"
                )
            },
            tasks={
                "static-website": Task(
                    name="static-website",
                    description="Static website",
                    triggers=["build website"],
                    skills=["nextjs-standards"]  # Valid reference
                )
            },
            categories={
                "web-development": Category(
                    name="web-development",
                    description="Web development",
                    tasks=["static-website"],  # Valid reference
                    skills=["nextjs-standards"]  # Valid reference
                )
            }
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Validation passes (no errors)
        assert errors == []


class TestManifestValidatorCategorySkillReferences:
    """Test validation of skill references in categories."""

    def test_validate_missing_skill_in_category(self):
        """Validate skill references in categories exist."""
        manifest = Manifest(
            skills={
                "terraform-base": Skill(
                    name="terraform-base",
                    description="Terraform base",
                    path="skills/terraform"
                )
            },
            tasks={},
            categories={
                "infrastructure": Category(
                    name="infrastructure",
                    description="Infrastructure tasks",
                    tasks=[],
                    skills=["terraform-base", "missing-skill"]  # missing-skill doesn't exist
                )
            }
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Validation fails
        assert len(errors) > 0

        # Error identifies "missing-skill" as missing
        assert any("missing-skill" in error for error in errors)
        assert any("infrastructure" in error for error in errors)


class TestManifestValidatorMultipleErrors:
    """Test collecting multiple validation errors."""

    def test_collect_all_validation_errors(self):
        """Collect all errors, don't fail fast."""
        manifest = Manifest(
            skills={},
            tasks={
                "task1": Task(
                    name="task1",
                    description="Task 1",
                    triggers=[],
                    skills=["missing-skill-1", "missing-skill-2"]
                )
            },
            categories={
                "cat1": Category(
                    name="cat1",
                    description="Category 1",
                    tasks=["missing-task-1"],
                    skills=["missing-skill-3"]
                )
            }
        )

        validator = ManifestValidator()
        errors = validator.validate(manifest)

        # Should have multiple errors (at least 4: 2 skills in task, 1 task in category, 1 skill in category)
        assert len(errors) >= 4
