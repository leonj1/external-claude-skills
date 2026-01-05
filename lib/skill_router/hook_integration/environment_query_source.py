"""Environment query source implementation."""
import os
import sys
from lib.skill_router.interfaces.hook import IQuerySource


class EnvironmentQuerySource(IQuerySource):
    """Obtains user query from environment variable PROMPT or stdin.

    Tries environment variable first, then falls back to stdin if configured.
    """

    def __init__(
        self,
        env_var_name: str = "PROMPT",
        stdin_fallback: bool = True
    ):
        """Initialize the query source.

        Args:
            env_var_name: Environment variable to check first (default: PROMPT)
            stdin_fallback: Whether to read stdin if env var not set (default: True)
        """
        self._env_var_name = env_var_name
        self._stdin_fallback = stdin_fallback

    def get_query(self) -> str:
        """Get query from environment or stdin.

        Order:
            1. Check os.environ.get(env_var_name)
            2. If not set and stdin_fallback, read sys.stdin
            3. Return stripped string, or empty string if nothing

        Returns:
            The user query string, empty string if not available
        """
        # Try environment variable first
        query = os.environ.get(self._env_var_name)

        if query is not None:
            return query.strip()

        # Fall back to stdin if configured
        if self._stdin_fallback:
            try:
                query = sys.stdin.read()
                return query.strip()
            except Exception:
                # If reading stdin fails, return empty string
                return ""

        # No query available
        return ""
