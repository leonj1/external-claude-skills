"""Exception classes for the Skill Router system."""
from typing import List, Optional


class ManifestError(Exception):
    """Base exception for all manifest-related errors."""
    pass


class ManifestNotFoundError(ManifestError):
    """Raised when a manifest file cannot be found.

    Attributes:
        path: The file path that was not found
    """
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Manifest file not found: {path}")


class ManifestParseError(ManifestError):
    """Raised when a manifest file contains invalid YAML syntax.

    Attributes:
        message: Description of the parse error
        line: Optional line number where the error occurred
    """
    def __init__(self, message: str, line: Optional[int] = None):
        self.line = line
        if line is not None:
            super().__init__(f"{message} (line {line})")
        else:
            super().__init__(message)


class ManifestValidationError(ManifestError):
    """Raised when a manifest fails validation checks.

    Attributes:
        errors: List of validation error messages
    """
    def __init__(self, errors: List[str]):
        self.errors = errors
        error_summary = f"Manifest validation failed with {len(errors)} error(s):\n"
        error_summary += "\n".join(f"  - {error}" for error in errors)
        super().__init__(error_summary)


class DependencyError(Exception):
    """Base exception for dependency resolution errors."""
    pass


class CyclicDependencyError(DependencyError):
    """Raised when a circular dependency is detected.

    Attributes:
        cycle: Tuple of skill names forming the cycle
    """
    def __init__(self, cycle: tuple):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
        super().__init__(f"Circular dependency detected: {cycle_str}")


class LLMDiscoveryError(Exception):
    """Base exception for all LLM discovery-related errors."""
    pass


class LLMClientError(LLMDiscoveryError):
    """Raised when LLM API call fails.

    This includes network errors, authentication failures,
    rate limiting, timeouts, and other API-related issues.
    """
    pass


class RateLimitError(LLMClientError):
    """Raised when API rate limit is exceeded (HTTP 429)."""
    pass


class AuthenticationError(LLMClientError):
    """Raised when API authentication fails (HTTP 401)."""
    pass


class TimeoutError(LLMClientError):
    """Raised when API request times out or connection fails."""
    pass


class ParseError(LLMDiscoveryError):
    """Raised when LLM response cannot be parsed.

    This occurs when the LLM returns malformed JSON or
    a response that doesn't match the expected structure.
    """
    pass
