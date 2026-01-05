"""Tests for skill router interfaces."""
import pytest
from abc import ABC
from lib.skill_router.interfaces.manifest import IManifestLoader, IManifestValidator
from lib.skill_router.models import Manifest


class TestIManifestLoader:
    """Test IManifestLoader interface."""

    def test_interface_is_abstract(self):
        """IManifestLoader is an abstract base class."""
        assert issubclass(IManifestLoader, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IManifestLoader()

    def test_load_method_is_abstract(self):
        """IManifestLoader defines abstract load method."""
        # Create a concrete implementation without load method
        class IncompleteLoader(IManifestLoader):
            def load_from_string(self, content: str) -> Manifest:
                pass

        with pytest.raises(TypeError):
            IncompleteLoader()

    def test_load_from_string_method_is_abstract(self):
        """IManifestLoader defines abstract load_from_string method."""
        # Create a concrete implementation without load_from_string method
        class IncompleteLoader(IManifestLoader):
            def load(self, path: str) -> Manifest:
                pass

        with pytest.raises(TypeError):
            IncompleteLoader()

    def test_complete_implementation_works(self):
        """Complete implementation of IManifestLoader can be instantiated."""
        class CompleteLoader(IManifestLoader):
            def load(self, path: str) -> Manifest:
                return Manifest(skills={}, tasks={}, categories={})

            def load_from_string(self, content: str) -> Manifest:
                return Manifest(skills={}, tasks={}, categories={})

        loader = CompleteLoader()
        assert isinstance(loader, IManifestLoader)


class TestIManifestValidator:
    """Test IManifestValidator interface."""

    def test_interface_is_abstract(self):
        """IManifestValidator is an abstract base class."""
        assert issubclass(IManifestValidator, ABC)

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IManifestValidator()

    def test_validate_method_is_abstract(self):
        """IManifestValidator defines abstract validate method."""
        # Create a concrete implementation without validate method
        class IncompleteValidator(IManifestValidator):
            pass

        with pytest.raises(TypeError):
            IncompleteValidator()

    def test_complete_implementation_works(self):
        """Complete implementation of IManifestValidator can be instantiated."""
        class CompleteValidator(IManifestValidator):
            def validate(self, manifest: Manifest) -> list[str]:
                return []

        validator = CompleteValidator()
        assert isinstance(validator, IManifestValidator)
