---
executor: bdd
source_feature: ./tests/bdd/manifest-loading.feature
---

<objective>
Create the foundational data models, exceptions, and interfaces for the Manifest Loading feature.
This is the foundation layer required before implementing loading and validation logic.
</objective>

<gherkin>
Feature: YAML Manifest Loading and Validation
  As a skill router user
  I want the system to load and validate YAML manifests
  So that I have reliable skill configuration

  Background:
    Given a skill router system

  # This prompt establishes the data structures referenced by all scenarios
</gherkin>

<requirements>
Based on the BDD spec and DRAFT-manifest-loading.md, implement:

1. **Data Models** (lib/skill_router/models.py):
   - `Skill` dataclass: name, description, path, depends_on (list)
   - `Task` dataclass: name, description, triggers (list), skills (list)
   - `Category` dataclass: name, description, tasks (list), skills (list)
   - `Manifest` dataclass: skills (dict), tasks (dict), categories (dict)

2. **Exceptions** (lib/skill_router/exceptions.py):
   - `ManifestError`: Base exception class
   - `ManifestNotFoundError`: File not found, includes path attribute
   - `ManifestParseError`: YAML syntax error, includes line number
   - `ManifestValidationError`: Reference errors, includes errors list

3. **Interfaces** (lib/skill_router/interfaces/manifest.py):
   - `IManifestLoader`: Abstract base class with `load(path)` and `load_from_string(content)` methods
   - `IManifestValidator`: Abstract base class with `validate(manifest)` method

4. **Package structure**:
   - `lib/skill_router/__init__.py`
   - `lib/skill_router/interfaces/__init__.py`
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-skill-router.md
DRAFT Specification: specs/DRAFT-manifest-loading.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- None (greenfield project)
- Use standard library: dataclasses, abc, typing
- External dependency: pyyaml

New Components Needed:
- All models are new
- All exceptions are new
- All interfaces are new
</context>

<implementation>
Follow TDD approach:
1. Write tests for model instantiation and field access
2. Write tests for exception creation and messages
3. Write tests for interface contracts
4. Implement models, exceptions, and interfaces

Architecture Guidelines:
- Use @dataclass for models with default_factory for lists
- Inherit exceptions from base ManifestError
- Use ABC and @abstractmethod for interfaces
- Include type hints on all methods
- Keep files under 500 lines
</implementation>

<verification>
Foundation components must be testable:
- [ ] Skill model can be instantiated with all fields
- [ ] Task model can be instantiated with all fields
- [ ] Category model can be instantiated with all fields
- [ ] Manifest model holds dictionaries of skills, tasks, categories
- [ ] ManifestNotFoundError includes path in message
- [ ] ManifestParseError includes line number when available
- [ ] ManifestValidationError includes list of errors
- [ ] IManifestLoader defines abstract load methods
- [ ] IManifestValidator defines abstract validate method
</verification>

<success_criteria>
- All data models are implemented with correct fields
- All exceptions are implemented with proper inheritance
- All interfaces define required abstract methods
- Tests verify model instantiation and exception formatting
- Package structure is correct with __init__.py files
</success_criteria>
