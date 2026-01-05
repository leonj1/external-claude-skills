"""Integration tests for SkillRoutingService.

These tests use real manifest data and real components - no mocks.
"""
import os
import tempfile
import pytest

from lib.skill_router.service import SkillRoutingService, RouteResponse


SAMPLE_MANIFEST = """
skills:
  terraform-base:
    description: "Terraform state backend, providers, and module conventions"
    path: infrastructure/terraform-base
    depends_on: []

  ecr-setup:
    description: "AWS ECR container registry setup"
    path: infrastructure/ecr-setup
    depends_on: [terraform-base]

  aws-ecs-deployment:
    description: "ECS Fargate container deployment with load balancing"
    path: infrastructure/aws-ecs-deployment
    depends_on: [terraform-base, ecr-setup]

  nextjs-standards:
    description: "Next.js project structure and conventions"
    path: frameworks/nextjs-standards
    depends_on: []

  fastapi-standards:
    description: "FastAPI project structure and conventions"
    path: frameworks/fastapi-standards
    depends_on: []

tasks:
  container-service:
    description: "Containerized service deployment to AWS ECS"
    triggers:
      - "deploy my app to AWS ECS"
      - "deploy to ECS"
      - "containerized service"
    skills: [aws-ecs-deployment]

  static-website:
    description: "Static website or landing page"
    triggers:
      - "build a static website"
      - "create a landing page"
    skills: [nextjs-standards]

  api-backend:
    description: "REST API backend service"
    triggers:
      - "create a REST API"
      - "build an API backend"
      - "fastapi backend"
    skills: [fastapi-standards]
"""


@pytest.fixture
def manifest_file():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(SAMPLE_MANIFEST)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def service(manifest_file):
    """Create a SkillRoutingService instance."""
    return SkillRoutingService(manifest_file)


class TestServiceRouting:
    """Test service routing functionality."""

    def test_direct_skill_match(self, service):
        """Direct skill name in query should match that skill."""
        response = service.route("I want to use terraform-base")

        assert response.matched_task == "terraform-base"
        assert response.skills == ["terraform-base"]
        assert response.execution_order == ["terraform-base"]
        assert response.route_type == "skill"
        assert response.tier == 1
        assert response.confidence == 1.0

    def test_task_trigger_match_ecs(self, service):
        """Query matching task trigger should return task and resolved skills."""
        response = service.route("deploy my app to AWS ECS")

        assert response.matched_task == "container-service"
        assert response.skills == ["aws-ecs-deployment"]
        assert response.route_type == "task"
        assert response.tier == 2
        # Execution order should include dependencies
        assert "terraform-base" in response.execution_order
        assert "ecr-setup" in response.execution_order
        assert "aws-ecs-deployment" in response.execution_order

    def test_task_trigger_match_static_website(self, service):
        """Static website query should match static-website task."""
        response = service.route("build a static website")

        assert response.matched_task == "static-website"
        assert response.skills == ["nextjs-standards"]
        assert response.execution_order == ["nextjs-standards"]
        assert response.route_type == "task"
        assert response.tier == 2

    def test_task_trigger_match_api(self, service):
        """API query should match api-backend task."""
        response = service.route("create a REST API")

        assert response.matched_task == "api-backend"
        assert response.skills == ["fastapi-standards"]
        assert response.route_type == "task"
        assert response.tier == 2

    def test_no_match_returns_error(self, service):
        """Unrecognized query should return error response."""
        response = service.route("do something completely unrelated xyz123")

        assert response.matched_task is None
        assert response.skills == []
        assert response.execution_order == []
        assert response.route_type == "error"
        assert response.tier == 0
        assert response.confidence == 0.0

    def test_dependency_resolution_order(self, service):
        """Verify dependencies are resolved in correct order."""
        response = service.route("deploy to ECS")

        # aws-ecs-deployment depends on terraform-base and ecr-setup
        # ecr-setup depends on terraform-base
        # So order should be: terraform-base -> ecr-setup -> aws-ecs-deployment
        assert response.execution_order.index("terraform-base") < response.execution_order.index("ecr-setup")
        assert response.execution_order.index("ecr-setup") < response.execution_order.index("aws-ecs-deployment")

    def test_case_insensitive_matching(self, service):
        """Matching should be case-insensitive."""
        response = service.route("DEPLOY MY APP TO AWS ECS")

        assert response.matched_task == "container-service"
        assert response.route_type == "task"

    def test_partial_trigger_match(self, service):
        """Partial trigger matches should still work with word overlap."""
        response = service.route("I want to deploy to ECS please")

        assert response.matched_task == "container-service"
        assert response.route_type == "task"


class TestRouteResponseDataclass:
    """Test RouteResponse dataclass behavior."""

    def test_no_match_factory(self):
        """RouteResponse.no_match() should return error response."""
        response = RouteResponse.no_match()

        assert response.matched_task is None
        assert response.skills == []
        assert response.execution_order == []
        assert response.route_type == "error"
        assert response.tier == 0
        assert response.confidence == 0.0


class TestSkillPathValidation:
    """Test that skill paths exist and have contents using real manifest.yaml."""

    @pytest.fixture
    def real_manifest_service(self):
        """Load the real manifest.yaml from the repo root."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manifest_path = os.path.join(repo_root, "manifest.yaml")
        return SkillRoutingService(manifest_path), repo_root

    def test_all_skill_paths_exist(self, real_manifest_service):
        """All skill paths in manifest should exist as directories."""
        service, repo_root = real_manifest_service
        skills = service.list_skills()

        for skill in skills:
            path = os.path.join(repo_root, skill["path"])
            assert os.path.exists(path), f"Skill path does not exist: {path}"
            assert os.path.isdir(path), f"Skill path is not a directory: {path}"

    def test_all_skill_paths_have_contents(self, real_manifest_service):
        """All skill directories should contain at least one file."""
        service, repo_root = real_manifest_service
        skills = service.list_skills()

        for skill in skills:
            path = os.path.join(repo_root, skill["path"])
            contents = os.listdir(path)
            assert len(contents) > 0, f"Skill path is empty: {path}"
