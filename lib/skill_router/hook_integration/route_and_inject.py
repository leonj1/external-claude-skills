#!/usr/bin/env python3
"""Hook script for routing queries and injecting skill context.

This script is the entry point for Claude Code hook integration.
It reads a user query, routes it through the Skill Router, and
outputs formatted skill context to stdout for injection into prompts.

Usage:
    # With environment variable
    export PROMPT="use terraform-base"
    python route_and_inject.py

    # With stdin
    echo "use terraform-base" | python route_and_inject.py

Exit codes:
    0 - Success (query routed and context output, or no query)
    1 - Error (manifest loading failed, routing error, etc.)
"""
import sys
from pathlib import Path

from lib.skill_router.manifest_loader import ManifestLoader
from lib.skill_router.hook_integration.router_factory import create_router
from lib.skill_router.hook_integration.skill_content_loader import SkillContentLoader
from lib.skill_router.hook_integration.skill_context_generator import SkillContextGenerator
from lib.skill_router.hook_integration.environment_query_source import EnvironmentQuerySource


def main() -> int:
    """Main entry point for hook integration.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # 1. Get manifest path (default ~/.claude/skills/manifest.yaml)
        manifest_path = Path.home() / ".claude" / "skills" / "manifest.yaml"

        # 2. Load manifest
        loader = ManifestLoader()
        manifest = loader.load(str(manifest_path))

        # 3. Get query from environment/stdin
        query_source = EnvironmentQuerySource()
        query = query_source.get_query()

        if not query:
            # No query provided, exit silently
            return 0

        # 4. Route the query
        router = create_router(manifest)
        route_result = router.route(query)

        # 5. Generate skill context
        skills_root = manifest_path.parent
        content_loader = SkillContentLoader(skills_root)
        context_generator = SkillContextGenerator(content_loader, manifest)

        context_output = context_generator.generate(route_result)

        # 6. Output to stdout
        if context_output:
            print(context_output)

        return 0

    except Exception as e:
        # Log error to stderr
        print(f"Error in route_and_inject: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
