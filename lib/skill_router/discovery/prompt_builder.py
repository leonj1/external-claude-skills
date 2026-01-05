"""LLM prompt builder for skill discovery.

Formats user requests and skill summaries into structured prompts
for LLM-based skill matching (Tier 3 routing).
"""
from typing import List
from lib.skill_router.interfaces.discovery import IPromptBuilder
from lib.skill_router.discovery.models import SkillSummary


class DiscoveryPromptBuilder(IPromptBuilder):
    """Builds structured prompts for LLM skill discovery.

    Creates prompts that include:
    - User's original request
    - Available tasks (high-level, map to multiple skills)
    - Available skills (low-level, direct capabilities)
    - Clear instructions for task vs skill selection
    - JSON output format specification
    """

    PROMPT_TEMPLATE = """You are a skill router for a development automation system. Your job is to analyze the user's request and select the most appropriate task or skill.

## User Request
{user_request}

## Available Tasks (High-Level)
Tasks are high-level workflows that map to multiple skills:
{tasks_section}

## Available Skills (Low-Level)
Skills are direct, specific capabilities:
{skills_section}

## Instructions
- Choose a **TASK** if the request is high-level (e.g., "build a portal", "create an app")
- Choose a **SKILL** if the request is specific infrastructure (e.g., "set up PostgreSQL", "configure Cognito")
- Return up to {max_results} matches, ranked by confidence

## Output Format
Respond with JSON only:
{{"type": "task" or "skill", "name": "the-name", "confidence": 0.0-1.0, "reasoning": "why this matches"}}

Or for multiple matches (array sorted by confidence descending):
[
  {{"type": "task", "name": "...", "confidence": 0.9, "reasoning": "..."}},
  {{"type": "skill", "name": "...", "confidence": 0.7, "reasoning": "..."}}
]"""

    def build_prompt(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int
    ) -> str:
        """Build a prompt for LLM skill discovery.

        Args:
            user_request: The user's natural language request
            skill_summaries: List of available skills with descriptions
            max_results: Maximum number of skills to return

        Returns:
            Formatted prompt string ready for LLM invocation

        Raises:
            ValueError: If user_request is empty or skill_summaries is empty
        """
        if not user_request or not user_request.strip():
            raise ValueError("user_request cannot be empty")

        if not skill_summaries:
            raise ValueError("skill_summaries cannot be empty")

        # Separate tasks from skills
        # Tasks have names ending with common task patterns or descriptions indicating workflows
        tasks = []
        skills = []

        for summary in skill_summaries:
            # Heuristic: tasks typically have names like "customer-portal", "admin-panel", "rest-api"
            # or descriptions mentioning "application", "portal", "dashboard", "service"
            desc_lower = summary.description.lower()
            is_task = any(keyword in desc_lower for keyword in [
                'application', 'portal', 'dashboard', 'service', 'app',
                'web application', 'system', 'platform', 'panel'
            ])

            if is_task:
                tasks.append(summary)
            else:
                skills.append(summary)

        # Format tasks section
        if tasks:
            tasks_lines = []
            for task in tasks:
                tasks_lines.append(f"- **{task.name}**: {task.description}")
            tasks_section = "\n".join(tasks_lines)
        else:
            tasks_section = "(No tasks available)"

        # Format skills section
        if skills:
            skills_lines = []
            for skill in skills:
                skills_lines.append(f"- **{skill.name}**: {skill.description}")
            skills_section = "\n".join(skills_lines)
        else:
            skills_section = "(No skills available)"

        # Build final prompt
        return self.PROMPT_TEMPLATE.format(
            user_request=user_request,
            tasks_section=tasks_section,
            skills_section=skills_section,
            max_results=max_results
        )
