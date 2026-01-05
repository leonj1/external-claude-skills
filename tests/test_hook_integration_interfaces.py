"""Tests for hook integration interfaces and models."""
import pytest
from pathlib import Path
from typing import Tuple, Optional

from lib.skill_router.interfaces.hook import (
    ISkillContextGenerator,
    ISkillContentLoader,
    IQuerySource,
)
from lib.skill_router.interfaces.router import RouteResult, RouteType
from lib.skill_router.hook_integration.models import (
    SkillRole,
    SkillSection,
    SkillContext,
)


# Test Implementations
class TestSkillContextGenerator(ISkillContextGenerator):
    """Test implementation of ISkillContextGenerator."""

    def generate(self, route_result: RouteResult) -> str:
        """Generate test skill context."""
        if not route_result.is_match():
            return ""
        return f"<skill-context type='{route_result.route_type.value}'>{route_result.matched}</skill-context>"


class TestSkillContentLoader(ISkillContentLoader):
    """Test implementation of ISkillContentLoader."""

    def __init__(self):
        self.skills_root: Optional[Path] = None
        self.load_calls = []

    def load(self, skill_name: str, skill_path: str) -> Tuple[str, Optional[str]]:
        """Load test skill content."""
        self.load_calls.append((skill_name, skill_path))
        if skill_name == "error-skill":
            return "Placeholder content", "Failed to load SKILL.md"
        return f"Content for {skill_name}", None

    def set_skills_root(self, path: Path) -> None:
        """Set test skills root."""
        self.skills_root = path


class TestQuerySource(IQuerySource):
    """Test implementation of IQuerySource."""

    def __init__(self, query: str = ""):
        self.query = query

    def get_query(self) -> str:
        """Get test query."""
        return self.query


# Tests for ISkillContextGenerator
class TestISkillContextGenerator:
    """Tests for ISkillContextGenerator interface."""

    def test_generate_with_skill_match(self):
        """Test generating context from skill match."""
        generator = TestSkillContextGenerator()
        route_result = RouteResult.skill_match("test-skill", ["test-skill"])

        context = generator.generate(route_result)

        assert context == "<skill-context type='skill'>test-skill</skill-context>"

    def test_generate_with_task_match(self):
        """Test generating context from task match."""
        generator = TestSkillContextGenerator()
        route_result = RouteResult.task_match("test-task", ["skill1", "skill2"], ["skill1", "skill2"])

        context = generator.generate(route_result)

        assert context == "<skill-context type='task'>test-task</skill-context>"

    def test_generate_with_discovery_match(self):
        """Test generating context from discovery match."""
        generator = TestSkillContextGenerator()
        route_result = RouteResult.discovery_match("discovered-skill", ["discovered-skill"], 0.85)

        context = generator.generate(route_result)

        assert context == "<skill-context type='discovery'>discovered-skill</skill-context>"

    def test_generate_with_error_result(self):
        """Test generating context from error result returns empty string."""
        generator = TestSkillContextGenerator()
        route_result = RouteResult.no_match()

        context = generator.generate(route_result)

        assert context == ""

    def test_cannot_instantiate_abstract_class(self):
        """Test that ISkillContextGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ISkillContextGenerator()


# Tests for ISkillContentLoader
class TestISkillContentLoader:
    """Tests for ISkillContentLoader interface."""

    def test_load_successful(self):
        """Test loading skill content successfully."""
        loader = TestSkillContentLoader()

        content, warning = loader.load("test-skill", "skills/test-skill")

        assert content == "Content for test-skill"
        assert warning is None
        assert ("test-skill", "skills/test-skill") in loader.load_calls

    def test_load_with_warning(self):
        """Test loading skill content with warning."""
        loader = TestSkillContentLoader()

        content, warning = loader.load("error-skill", "skills/error-skill")

        assert content == "Placeholder content"
        assert warning == "Failed to load SKILL.md"

    def test_set_skills_root(self):
        """Test setting skills root directory."""
        loader = TestSkillContentLoader()
        test_path = Path("/test/skills")

        loader.set_skills_root(test_path)

        assert loader.skills_root == test_path

    def test_cannot_instantiate_abstract_class(self):
        """Test that ISkillContentLoader cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ISkillContentLoader()


# Tests for IQuerySource
class TestIQuerySource:
    """Tests for IQuerySource interface."""

    def test_get_query(self):
        """Test getting query from source."""
        query_source = TestQuerySource("test query")

        query = query_source.get_query()

        assert query == "test query"

    def test_get_empty_query(self):
        """Test getting empty query."""
        query_source = TestQuerySource("")

        query = query_source.get_query()

        assert query == ""

    def test_cannot_instantiate_abstract_class(self):
        """Test that IQuerySource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IQuerySource()


# Tests for SkillRole Enum
class TestSkillRole:
    """Tests for SkillRole enum."""

    def test_primary_value(self):
        """Test PRIMARY role has correct value."""
        assert SkillRole.PRIMARY.value == "PRIMARY"

    def test_dependency_value(self):
        """Test DEPENDENCY role has correct value."""
        assert SkillRole.DEPENDENCY.value == "DEPENDENCY"

    def test_enum_members(self):
        """Test enum has exactly two members."""
        assert len(SkillRole) == 2
        assert set(SkillRole) == {SkillRole.PRIMARY, SkillRole.DEPENDENCY}


# Tests for SkillSection Dataclass
class TestSkillSection:
    """Tests for SkillSection dataclass."""

    def test_creation_with_all_fields(self):
        """Test creating SkillSection with all fields."""
        section = SkillSection(
            name="test-skill",
            role=SkillRole.PRIMARY,
            content="Test content",
            warning="Test warning"
        )

        assert section.name == "test-skill"
        assert section.role == SkillRole.PRIMARY
        assert section.content == "Test content"
        assert section.warning == "Test warning"

    def test_creation_without_warning(self):
        """Test creating SkillSection without warning (defaults to None)."""
        section = SkillSection(
            name="test-skill",
            role=SkillRole.DEPENDENCY,
            content="Test content"
        )

        assert section.name == "test-skill"
        assert section.role == SkillRole.DEPENDENCY
        assert section.content == "Test content"
        assert section.warning is None

    def test_primary_role_section(self):
        """Test creating section with PRIMARY role."""
        section = SkillSection(
            name="primary-skill",
            role=SkillRole.PRIMARY,
            content="Primary content"
        )

        assert section.role == SkillRole.PRIMARY

    def test_dependency_role_section(self):
        """Test creating section with DEPENDENCY role."""
        section = SkillSection(
            name="dep-skill",
            role=SkillRole.DEPENDENCY,
            content="Dependency content"
        )

        assert section.role == SkillRole.DEPENDENCY


# Tests for SkillContext Dataclass
class TestSkillContext:
    """Tests for SkillContext dataclass."""

    def test_creation_with_all_fields(self):
        """Test creating SkillContext with all fields."""
        sections = [
            SkillSection("skill1", SkillRole.PRIMARY, "Content 1"),
            SkillSection("skill2", SkillRole.DEPENDENCY, "Content 2")
        ]

        context = SkillContext(
            route_type="skill",
            matched="skill1",
            execution_order=["skill1", "skill2"],
            sections=sections
        )

        assert context.route_type == "skill"
        assert context.matched == "skill1"
        assert context.execution_order == ["skill1", "skill2"]
        assert len(context.sections) == 2
        assert context.sections[0].name == "skill1"
        assert context.sections[1].name == "skill2"

    def test_creation_with_empty_sections(self):
        """Test creating SkillContext with empty sections (defaults to empty list)."""
        context = SkillContext(
            route_type="task",
            matched="test-task",
            execution_order=["skill1"]
        )

        assert context.route_type == "task"
        assert context.matched == "test-task"
        assert context.execution_order == ["skill1"]
        assert context.sections == []

    def test_skill_route_type(self):
        """Test creating context with skill route type."""
        context = SkillContext(
            route_type="skill",
            matched="test-skill",
            execution_order=["test-skill"]
        )

        assert context.route_type == "skill"

    def test_task_route_type(self):
        """Test creating context with task route type."""
        context = SkillContext(
            route_type="task",
            matched="test-task",
            execution_order=["skill1", "skill2"]
        )

        assert context.route_type == "task"

    def test_discovery_route_type(self):
        """Test creating context with discovery route type."""
        context = SkillContext(
            route_type="discovery",
            matched="discovered-skill",
            execution_order=["discovered-skill"]
        )

        assert context.route_type == "discovery"

    def test_multiple_sections_with_mixed_roles(self):
        """Test context with multiple sections having different roles."""
        sections = [
            SkillSection("primary", SkillRole.PRIMARY, "Primary content"),
            SkillSection("dep1", SkillRole.DEPENDENCY, "Dep content 1"),
            SkillSection("dep2", SkillRole.DEPENDENCY, "Dep content 2", "Warning")
        ]

        context = SkillContext(
            route_type="task",
            matched="test-task",
            execution_order=["primary", "dep1", "dep2"],
            sections=sections
        )

        assert len(context.sections) == 3
        assert context.sections[0].role == SkillRole.PRIMARY
        assert context.sections[1].role == SkillRole.DEPENDENCY
        assert context.sections[2].role == SkillRole.DEPENDENCY
        assert context.sections[2].warning == "Warning"
