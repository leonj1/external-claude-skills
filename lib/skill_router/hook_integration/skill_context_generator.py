"""Skill context generator implementation."""
from typing import Dict, Any, List

from lib.skill_router.interfaces.hook import ISkillContentLoader, ISkillContextGenerator
from lib.skill_router.interfaces.router import RouteResult, RouteType
from lib.skill_router.hook_integration.models import SkillRole, SkillSection, SkillContext


class SkillContextGenerator(ISkillContextGenerator):
    """Generates formatted XML skill context from a RouteResult.

    Determines which skills are PRIMARY vs DEPENDENCY and assembles
    the final XML output with execution order and skill content.
    """

    def __init__(
        self,
        content_loader: ISkillContentLoader,
        manifest: Any
    ):
        """Initialize the context generator.

        Args:
            content_loader: Loader for reading SKILL.md files
            manifest: Manifest object containing skills dict
        """
        self._content_loader = content_loader
        self._manifest = manifest

    def generate(self, route_result: RouteResult) -> str:
        """Generate skill context XML from route result.

        Args:
            route_result: The routing result containing matched skills

        Returns:
            Formatted skill context XML string, empty string for error results
        """
        # Return empty string for error routes
        if route_result.route_type == RouteType.ERROR:
            return ""

        # Return minimal context if no skills in execution order
        if not route_result.execution_order:
            return self._format_minimal_context(route_result)

        # Determine which skills are primary (directly requested/matched)
        primary_skills = set(route_result.skills)

        # Build sections for each skill in execution order
        sections: List[SkillSection] = []
        for skill_name in route_result.execution_order:
            # Get skill data from manifest
            skill_data = self._manifest.skills.get(skill_name)
            if skill_data is None:
                # Skill not in manifest, create placeholder
                content = f"(Skill '{skill_name}' not found in manifest)"
                warning = f"Warning: Skill '{skill_name}' referenced in execution order but not found in manifest"
                skill_path = skill_name
            else:
                skill_path = skill_data.path

            # Load skill content
            if skill_data is not None:
                content, warning = self._content_loader.load(skill_name, skill_path)
            else:
                content = f"(Skill '{skill_name}' not found in manifest)"
                warning = f"Warning: Skill '{skill_name}' referenced in execution order but not found in manifest"

            # Determine role
            role = SkillRole.PRIMARY if skill_name in primary_skills else SkillRole.DEPENDENCY

            # Create section
            section = SkillSection(
                name=skill_name,
                role=role,
                content=content,
                warning=warning
            )
            sections.append(section)

        # Create context object
        context = SkillContext(
            route_type=route_result.route_type.value,
            matched=route_result.matched,
            execution_order=route_result.execution_order,
            sections=sections
        )

        # Format and return
        return self._format_context(context)

    def _format_minimal_context(self, route_result: RouteResult) -> str:
        """Format minimal context when execution order is empty.

        Args:
            route_result: Route result with empty execution order

        Returns:
            Minimal XML context with header only
        """
        lines = [
            "<skill_context>",
            f"Matched: {route_result.route_type.value} '{route_result.matched}'",
            "Execution order: (none)",
            "",
            "</skill_context>"
        ]
        return "\n".join(lines)

    def _format_context(self, context: SkillContext) -> str:
        """Format SkillContext into XML string.

        Args:
            context: The skill context to format

        Returns:
            Formatted XML string
        """
        lines = ["<skill_context>"]

        # Add header with route type and matched name
        lines.append(f"Matched: {context.route_type} '{context.matched}'")

        # Add execution order
        execution_str = " -> ".join(context.execution_order)
        lines.append(f"Execution order: {execution_str}")
        lines.append("")

        # Add each skill section
        for section in context.sections:
            marker = f"[{section.role.value}]"
            lines.append(f"## {section.name} {marker}")
            lines.append(section.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Close tag
        lines.append("</skill_context>")

        return "\n".join(lines)
