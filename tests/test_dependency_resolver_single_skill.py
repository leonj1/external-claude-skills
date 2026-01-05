"""Tests for single skill dependency resolution using topological sort.

Based on Gherkin scenarios from tests/bdd/dependency-resolution.feature
Scenario filter: single_skill
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
    }


@pytest.fixture
def resolver():
    """Create dependency resolver instance."""
    return KahnsDependencyResolver()


class TestResolveSkillWithNoDependencies:
    """Scenario: Resolve skill with no dependencies."""

    def test_resolve_skill_with_no_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skill "nextjs-standards"
        When the dependency resolver processes the skill
        Then the execution order contains only "nextjs-standards"
        """
        result = resolver.resolve("nextjs-standards", skills_manifest)

        assert isinstance(result, DependencyResult)
        assert result.execution_order == ["nextjs-standards"]
        assert len(result.execution_order) == 1


class TestResolveSkillWithSingleDependency:
    """Scenario: Resolve skill with single dependency."""

    def test_resolve_skill_with_single_dependency(self, resolver, skills_manifest):
        """
        Given a request for skill "ecr-setup"
        When the dependency resolver processes the skill
        Then the execution order is:
          | order | skill          |
          | 1     | terraform-base |
          | 2     | ecr-setup      |
        """
        result = resolver.resolve("ecr-setup", skills_manifest)

        assert isinstance(result, DependencyResult)
        assert len(result.execution_order) == 2
        assert result.execution_order[0] == "terraform-base"
        assert result.execution_order[1] == "ecr-setup"


class TestResolveSkillWithMultipleDependencies:
    """Scenario: Resolve skill with multiple dependencies."""

    def test_resolve_skill_with_multiple_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skill "aws-ecs-deployment"
        When the dependency resolver processes the skill
        Then "terraform-base" appears before "aws-ecs-deployment"
        And "ecr-setup" appears before "aws-ecs-deployment"
        And "terraform-base" appears before "ecr-setup"
        """
        result = resolver.resolve("aws-ecs-deployment", skills_manifest)

        assert isinstance(result, DependencyResult)
        execution_order = result.execution_order

        # Assert all three skills are present
        assert "terraform-base" in execution_order
        assert "ecr-setup" in execution_order
        assert "aws-ecs-deployment" in execution_order

        # Assert ordering constraints
        terraform_idx = execution_order.index("terraform-base")
        ecr_idx = execution_order.index("ecr-setup")
        ecs_idx = execution_order.index("aws-ecs-deployment")

        assert terraform_idx < ecs_idx, "terraform-base must appear before aws-ecs-deployment"
        assert ecr_idx < ecs_idx, "ecr-setup must appear before aws-ecs-deployment"
        assert terraform_idx < ecr_idx, "terraform-base must appear before ecr-setup"


class TestResolveSkillWithTransitiveDependencies:
    """Scenario: Resolve skill with transitive dependencies."""

    def test_resolve_skill_with_transitive_dependencies(self, resolver, skills_manifest):
        """
        Given a request for skill "k8s-deployment"
        When the dependency resolver processes the skill
        Then the execution order is:
          | order | skill          |
          | 1     | terraform-base |
          | 2     | eks-cluster    |
          | 3     | k8s-deployment |
        """
        result = resolver.resolve("k8s-deployment", skills_manifest)

        assert isinstance(result, DependencyResult)
        assert len(result.execution_order) == 3
        assert result.execution_order[0] == "terraform-base"
        assert result.execution_order[1] == "eks-cluster"
        assert result.execution_order[2] == "k8s-deployment"
