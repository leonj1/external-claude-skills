"""Tests for skill router exceptions."""
import pytest
from lib.skill_router.exceptions import (
    ManifestError,
    ManifestNotFoundError,
    ManifestParseError,
    ManifestValidationError
)


class TestManifestNotFoundError:
    """Test ManifestNotFoundError exception."""

    def test_exception_includes_path_in_message(self):
        """ManifestNotFoundError includes path in message."""
        path = "/path/to/manifest.yaml"
        error = ManifestNotFoundError(path)

        assert path in str(error)
        assert hasattr(error, 'path')
        assert error.path == path

    def test_inherits_from_manifest_error(self):
        """ManifestNotFoundError inherits from ManifestError."""
        error = ManifestNotFoundError("/path/to/manifest.yaml")
        assert isinstance(error, ManifestError)


class TestManifestParseError:
    """Test ManifestParseError exception."""

    def test_exception_includes_line_number(self):
        """ManifestParseError includes line number when available."""
        error = ManifestParseError("Invalid YAML syntax", line=10)

        assert "10" in str(error) or error.line == 10
        assert hasattr(error, 'line')
        assert error.line == 10

    def test_exception_without_line_number(self):
        """ManifestParseError works without line number."""
        error = ManifestParseError("Invalid YAML syntax")

        assert "Invalid YAML syntax" in str(error)

    def test_inherits_from_manifest_error(self):
        """ManifestParseError inherits from ManifestError."""
        error = ManifestParseError("Invalid YAML syntax")
        assert isinstance(error, ManifestError)


class TestManifestValidationError:
    """Test ManifestValidationError exception."""

    def test_exception_includes_errors_list(self):
        """ManifestValidationError includes list of errors."""
        errors = [
            "Skill 'ecr-setup' depends on unknown skill 'missing-base'",
            "Task 'static-website' references unknown skill 'aws-hosting'"
        ]
        error = ManifestValidationError(errors)

        assert hasattr(error, 'errors')
        assert error.errors == errors
        assert len(error.errors) == 2

    def test_exception_message_format(self):
        """ManifestValidationError formats error message."""
        errors = [
            "Skill 'ecr-setup' depends on unknown skill 'missing-base'"
        ]
        error = ManifestValidationError(errors)

        error_str = str(error)
        assert "missing-base" in error_str or error.errors[0] in error_str

    def test_inherits_from_manifest_error(self):
        """ManifestValidationError inherits from ManifestError."""
        errors = ["Some error"]
        error = ManifestValidationError(errors)
        assert isinstance(error, ManifestError)
