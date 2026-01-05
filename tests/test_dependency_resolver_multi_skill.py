"""Tests for multiple skills dependency resolution using topological sort.

Based on Gherkin scenarios from tests/bdd/dependency-resolution.feature
Scenario filter: multi_skill
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.dependency_resolver import KahnsDependencyResolver
from lib.skill_router.dependency_graph import DependencyResult


@pytest.fixture
def skills_manifest():
    """Background: skill router with loaded manifest containing skills with dependencies."""
    return {
        "terraform-base": Skill(
            name="terraform-base",
            description="Base Terraform setup",
            path="./skills/terraform-base",
            depends_on=[]
        ),
        "ecr-setup": Skill(
            name="ecr-setup",
            description="AWS ECR setup",
            path="./skills/ecr-setup",
            depends_on=["terraform-base"]
        ),
        "aws-static-hosting": Skill(
            name="aws-static-hosting",
            description="AWS static hosting",
            path="./skills/aws-static-hosting",
            depends_on=["terraform-base"]
        ),
        "aws-ecs-deployment": Skill(
            name="aws-ecs-deployment",
            description="AWS ECS deployment",
            path="./skills/aws-ecs-deployment",
            depends_on=["terraform-base", "ecr-setup"]
        ),
        "eks-cluster": Skill(
            name="eks-cluster",
            description="AWS EKS cluster",
            path="./skills/eks-cluster",
            depends_on=["terraform-base"]
        ),
        "k8s-deployment": Skill(
            name="k8s-deployment",
            description="Kubernetes deployment",
            path="./skills/k8s-deployment",
            depends_on=["eks-cluster"]
        ),
        "auth-cognito": Skill(
            name="auth-cognito",
            description="AWS Cognito authentication",
            path="./skills/auth-cognito",
            depends_on=["terraform-base"]
        ),
        "rds-postgres": Skill(
            name="rds-postgres",
            description="AWS RDS PostgreSQL",
            path="./skills/rds-postgres",
            depends_on=["terraform-base"]
        ),
        "nextjs-standards": Skill(
            name="nextjs-standards",
            description="Next.js coding standards",
            path="./skills/nextjs-standards",
            depends_on=[]
        ),
        "github-actions-cicd": Skill(
            name="github-actions-cicd",
            description="GitHub Actions CI/CD",
            path="./skills/github-actions-cicd",
            depends_on=[]
        ),
        "react-admin-standards": Skill(
            name="react-admin-standards",
            description="React Admin standards",
            path="./skills/react-admin-standards",
            depends_on=[]
        ),
        "fastapi-standards": Skill(
            name="fastapi-standards",
            description="FastAPI standards",
            path="./skills/fastapi-standards",
            depends_on=[]
        ),
    }


@pytest.fixture
def resolver():
    """Create dependency resolver instance."""
    return KahnsDependencyResolver()


class TestResolveMultipleSkillsWithSharedDependencies:
    """Scenario: Resolve multiple skills with shared dependencies."""

    def test_resolve_multiple_skills_with_shared_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skills:
          | skill              |
          | aws-static-hosting |
          | aws-ecs-deployment |
        When the dependency resolver processes the skills
        Then "terraform-base" appears exactly once
        And "terraform-base" appears first
        And both "aws-static-hosting" and "aws-ecs-deployment" appear after "terraform-base"
        """
        result = resolver.resolve_multi(
            ["aws-static-hosting", "aws-ecs-deployment"],
            skills_manifest
        )

        assert isinstance(result, DependencyResult)
        execution_order = result.execution_order

        # "terraform-base" appears exactly once
        terraform_count = execution_order.count("terraform-base")
        assert terraform_count == 1, "terraform-base must appear exactly once"

        # "terraform-base" appears first
        assert execution_order[0] == "terraform-base"

        # Both skills appear after terraform-base
        terraform_idx = execution_order.index("terraform-base")
        static_idx = execution_order.index("aws-static-hosting")
        ecs_idx = execution_order.index("aws-ecs-deployment")

        assert static_idx > terraform_idx
        assert ecs_idx > terraform_idx


class TestResolveMultipleIndependentSkills:
    """Scenario: Resolve multiple independent skills."""

    def test_resolve_multiple_independent_skills(self, resolver, skills_manifest):
        """
        Given a request for skills:
          | skill               |
          | nextjs-standards    |
          | github-actions-cicd |
        When the dependency resolver processes the skills
        Then the execution order contains both skills
        And the order between them is arbitrary
        """
        result = resolver.resolve_multi(
            ["nextjs-standards", "github-actions-cicd"],
            skills_manifest
        )

        assert isinstance(result, DependencyResult)
        execution_order = result.execution_order

        # Both skills are present
        assert "nextjs-standards" in execution_order
        assert "github-actions-cicd" in execution_order

        # Only these two skills (no dependencies)
        assert len(execution_order) == 2


class TestResolveTaskSkillsWithComplexDependencies:
    """Scenario: Resolve task skills with complex dependencies."""

    def test_resolve_task_skills_with_complex_dependencies(self, resolver, skills_manifest):
        """
        Given task "admin-panel" requires skills:
          | skill                |
          | react-admin-standards |
          | fastapi-standards    |
          | aws-ecs-deployment   |
          | rds-postgres         |
          | auth-cognito         |
        And skill "react-admin-standards" has no dependencies
        And skill "fastapi-standards" has no dependencies
        When the dependency resolver processes the task skills
        Then "terraform-base" appears before all dependent skills
        And "ecr-setup" appears before "aws-ecs-deployment"
        """
        task_skills = [
            "react-admin-standards",
            "fastapi-standards",
            "aws-ecs-deployment",
            "rds-postgres",
            "auth-cognito"
        ]

        result = resolver.resolve_multi(task_skills, skills_manifest)

        assert isinstance(result, DependencyResult)
        execution_order = result.execution_order

        # Get indices
        terraform_idx = execution_order.index("terraform-base")
        ecr_idx = execution_order.index("ecr-setup")
        ecs_idx = execution_order.index("aws-ecs-deployment")
        rds_idx = execution_order.index("rds-postgres")
        cognito_idx = execution_order.index("auth-cognito")

        # "terraform-base" appears before all dependent skills
        assert terraform_idx < ecs_idx
        assert terraform_idx < rds_idx
        assert terraform_idx < cognito_idx

        # "ecr-setup" appears before "aws-ecs-deployment"
        assert ecr_idx < ecs_idx


class TestValidateExecutionOrderRespectsAllDependencies:
    """Scenario: Validate execution order respects all dependencies."""

    def test_validate_execution_order_respects_all_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skill "aws-ecs-deployment"
        When the dependency resolver processes the skill
        Then for each skill in the execution order
        And all its dependencies appear earlier in the order
        """
        result = resolver.resolve("aws-ecs-deployment", skills_manifest)

        assert isinstance(result, DependencyResult)
        execution_order = result.execution_order

        # For each skill, verify all dependencies appear before it
        for i, skill_name in enumerate(execution_order):
            skill = skills_manifest[skill_name]
            for dep in skill.depends_on:
                dep_idx = execution_order.index(dep)
                assert dep_idx < i, f"Dependency '{dep}' must appear before '{skill_name}'"


class TestCollectAllTransitiveDependencies:
    """Scenario: Collect all transitive dependencies."""

    def test_collect_all_transitive_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skill "aws-ecs-deployment"
        When the dependency resolver collects dependencies
        Then the collected set contains "terraform-base"
        And the collected set contains "ecr-setup"
        And the collected set contains "aws-ecs-deployment"
        """
        collected = resolver.collect_dependencies("aws-ecs-deployment", skills_manifest)

        assert isinstance(collected, set)
        assert "terraform-base" in collected
        assert "ecr-setup" in collected
        assert "aws-ecs-deployment" in collected
