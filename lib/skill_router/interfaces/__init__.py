"""Interfaces for the Skill Router system."""

from lib.skill_router.interfaces.manifest import IManifestLoader, IManifestValidator
from lib.skill_router.interfaces.router import IRouter, RouteType, RouteResult
from lib.skill_router.interfaces.hook import (
    ISkillContextGenerator,
    ISkillContentLoader,
    IQuerySource,
)

__all__ = [
    "IManifestLoader",
    "IManifestValidator",
    "IRouter",
    "RouteType",
    "RouteResult",
    "ISkillContextGenerator",
    "ISkillContentLoader",
    "IQuerySource",
]
