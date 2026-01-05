"""Interfaces for manifest loading and validation."""
from abc import ABC, abstractmethod
from typing import List
from lib.skill_router.models import Manifest


class IManifestLoader(ABC):
    """Interface for loading manifests from various sources.

    Implementations must provide methods to load manifests from
    file paths and string content.
    """

    @abstractmethod
    def load(self, path: str) -> Manifest:
        """Load a manifest from a file path.

        Args:
            path: File system path to the manifest file

        Returns:
            Parsed Manifest object

        Raises:
            ManifestNotFoundError: If the file does not exist
            ManifestParseError: If the YAML is invalid
            ManifestValidationError: If validation fails
        """
        pass

    @abstractmethod
    def load_from_string(self, content: str) -> Manifest:
        """Load a manifest from a YAML string.

        Args:
            content: YAML content as a string

        Returns:
            Parsed Manifest object

        Raises:
            ManifestParseError: If the YAML is invalid
            ManifestValidationError: If validation fails
        """
        pass


class IManifestValidator(ABC):
    """Interface for validating manifest consistency.

    Implementations must check that all references (dependencies,
    skill references, task references) point to existing entities.
    """

    @abstractmethod
    def validate(self, manifest: Manifest) -> List[str]:
        """Validate a manifest for consistency.

        Args:
            manifest: The manifest to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        pass
