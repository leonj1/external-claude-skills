# DRAFT: Manifest Loading

> Status: DRAFT
> Task: 1.1 Manifest Loading - YAML parsing and validation
> Parent: Skill Router System
> Root Request: "Read specs.md and implement the Skill Router system with YAML manifest, 3-tier routing, dependency resolution, and hook integration"

---

## 1. Overview

The Manifest Loader is responsible for loading, parsing, and validating the YAML skill manifest file. It transforms raw YAML into strongly-typed Python data models and validates structural integrity.

**Scope**: YAML parsing and validation ONLY. No routing logic, no dependency resolution.

---

## 2. Interfaces Needed

### 2.1 IManifestLoader

```python
from abc import ABC, abstractmethod
from typing import Optional

class IManifestLoader(ABC):
    """Loads and parses the skill manifest file."""

    @abstractmethod
    def load(self, path: str) -> "Manifest":
        """
        Load manifest from YAML file path.

        Args:
            path: Absolute or relative path to manifest.yaml

        Returns:
            Manifest: Parsed and validated manifest object

        Raises:
            ManifestNotFoundError: File does not exist
            ManifestParseError: Invalid YAML syntax
            ManifestValidationError: Schema violations
        """
        pass

    @abstractmethod
    def load_from_string(self, content: str) -> "Manifest":
        """
        Load manifest from YAML string content.

        Args:
            content: Raw YAML string

        Returns:
            Manifest: Parsed and validated manifest object

        Raises:
            ManifestParseError: Invalid YAML syntax
            ManifestValidationError: Schema violations
        """
        pass
```

### 2.2 IManifestValidator

```python
from abc import ABC, abstractmethod
from typing import List

class IManifestValidator(ABC):
    """Validates manifest structure and references."""

    @abstractmethod
    def validate(self, manifest: "Manifest") -> List[str]:
        """
        Validate manifest integrity.

        Args:
            manifest: Parsed manifest object

        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        pass
```

---

## 3. Data Models

### 3.1 Skill

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Skill:
    """A single skill definition."""
    name: str
    description: str
    path: str
    depends_on: List[str] = field(default_factory=list)
```

### 3.2 Task

```python
@dataclass
class Task:
    """A task that composes multiple skills."""
    name: str
    description: str
    triggers: List[str]
    skills: List[str]
```

### 3.3 Category

```python
@dataclass
class Category:
    """A category grouping tasks and skills."""
    name: str
    description: str
    tasks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
```

### 3.4 Manifest

```python
from typing import Dict

@dataclass
class Manifest:
    """The complete skill manifest."""
    skills: Dict[str, Skill]
    tasks: Dict[str, Task]
    categories: Dict[str, Category]
```

### 3.5 Exceptions

```python
class ManifestError(Exception):
    """Base exception for manifest errors."""
    pass

class ManifestNotFoundError(ManifestError):
    """Manifest file not found."""
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Manifest not found: {path}")

class ManifestParseError(ManifestError):
    """YAML parsing failed."""
    def __init__(self, message: str, line: int = None):
        self.line = line
        super().__init__(f"Parse error{f' at line {line}' if line else ''}: {message}")

class ManifestValidationError(ManifestError):
    """Schema or reference validation failed."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation errors: {'; '.join(errors)}")
```

---

## 4. Logic Flow

### 4.1 ManifestLoader.load(path) Pseudocode

```
function load(path: string) -> Manifest:
    # Step 1: Check file exists
    if not file_exists(path):
        raise ManifestNotFoundError(path)

    # Step 2: Read file content
    content = read_file(path)

    # Step 3: Delegate to load_from_string
    return load_from_string(content)
```

### 4.2 ManifestLoader.load_from_string(content) Pseudocode

```
function load_from_string(content: string) -> Manifest:
    # Step 1: Parse YAML
    try:
        raw_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ManifestParseError(str(e), e.problem_mark.line if hasattr(e, 'problem_mark') else None)

    # Step 2: Handle empty/null manifest
    if raw_data is None:
        raw_data = {}

    # Step 3: Build Manifest object
    manifest = build_manifest(raw_data)

    # Step 4: Validate
    validator = ManifestValidator()
    errors = validator.validate(manifest)
    if errors:
        raise ManifestValidationError(errors)

    return manifest
```

### 4.3 build_manifest(raw_data) Pseudocode

```
function build_manifest(raw_data: dict) -> Manifest:
    skills = {}
    tasks = {}
    categories = {}

    # Parse skills section
    for name, data in raw_data.get("skills", {}).items():
        skills[name] = Skill(
            name=name,
            description=data.get("description", ""),
            path=data.get("path", ""),
            depends_on=data.get("depends_on", [])
        )

    # Parse tasks section
    for name, data in raw_data.get("tasks", {}).items():
        tasks[name] = Task(
            name=name,
            description=data.get("description", ""),
            triggers=data.get("triggers", []),
            skills=data.get("skills", [])
        )

    # Parse categories section
    for name, data in raw_data.get("categories", {}).items():
        categories[name] = Category(
            name=name,
            description=data.get("description", ""),
            tasks=data.get("tasks", []),
            skills=data.get("skills", [])
        )

    return Manifest(skills=skills, tasks=tasks, categories=categories)
```

### 4.4 ManifestValidator.validate(manifest) Pseudocode

```
function validate(manifest: Manifest) -> List[str]:
    errors = []

    # Rule 1: All skill dependencies must exist
    for skill in manifest.skills.values():
        for dep in skill.depends_on:
            if dep not in manifest.skills:
                errors.append(f"Skill '{skill.name}' depends on unknown skill '{dep}'")

    # Rule 2: All task skills must exist
    for task in manifest.tasks.values():
        for skill_name in task.skills:
            if skill_name not in manifest.skills:
                errors.append(f"Task '{task.name}' references unknown skill '{skill_name}'")

    # Rule 3: All category tasks must exist
    for category in manifest.categories.values():
        for task_name in category.tasks:
            if task_name not in manifest.tasks:
                errors.append(f"Category '{category.name}' references unknown task '{task_name}'")
        for skill_name in category.skills:
            if skill_name not in manifest.skills:
                errors.append(f"Category '{category.name}' references unknown skill '{skill_name}'")

    # Rule 4: Skills must have non-empty path
    for skill in manifest.skills.values():
        if not skill.path:
            errors.append(f"Skill '{skill.name}' has empty path")

    # Rule 5: Tasks must have at least one trigger
    for task in manifest.tasks.values():
        if not task.triggers:
            errors.append(f"Task '{task.name}' has no triggers")

    # Rule 6: Tasks must have at least one skill
    for task in manifest.tasks.values():
        if not task.skills:
            errors.append(f"Task '{task.name}' has no skills")

    return errors
```

---

## 5. Component Structure

```
lib/
  skill_router/
    __init__.py
    models.py           # Skill, Task, Category, Manifest dataclasses
    exceptions.py       # ManifestError hierarchy
    interfaces/
      __init__.py
      manifest.py       # IManifestLoader, IManifestValidator
    manifest_loader.py  # IManifestLoader implementation
    manifest_validator.py  # IManifestValidator implementation
```

---

## 6. Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 0 (greenfield design) |
| New code to write | ~120 lines |
| Test code to write | ~150 lines |
| Estimated context usage | ~12% |

**Verdict**: Well within 60% threshold. Proceed with implementation.

---

## 7. Test Scenarios

### 7.1 Happy Path

- Load valid manifest with skills, tasks, and categories
- Parse manifest with minimal data (only skills)
- Parse manifest from string content
- Empty manifest returns empty collections

### 7.2 Error Cases

- File not found raises ManifestNotFoundError
- Invalid YAML syntax raises ManifestParseError with line number
- Missing skill dependency raises ManifestValidationError
- Task referencing non-existent skill raises ManifestValidationError
- Category referencing non-existent task raises ManifestValidationError
- Skill with empty path raises ManifestValidationError
- Task with no triggers raises ManifestValidationError
- Task with no skills raises ManifestValidationError

---

## 8. Example Manifest

```yaml
skills:
  terraform-base:
    description: "Base Terraform infrastructure patterns"
    path: "infrastructure/terraform-base"
    depends_on: []

  ecr-setup:
    description: "ECR repository configuration"
    path: "infrastructure/ecr-setup"
    depends_on:
      - terraform-base

tasks:
  deploy-container:
    description: "Deploy containerized application"
    triggers:
      - "deploy container"
      - "deploy docker"
      - "containerize and deploy"
    skills:
      - ecr-setup
      - terraform-base

categories:
  infrastructure:
    description: "Infrastructure as code skills"
    tasks:
      - deploy-container
    skills:
      - terraform-base
```

---

## 9. Dependencies

- `pyyaml` (PyPI) - YAML parsing library
- Standard library only for remaining functionality

---

## 10. Notes

- Validation does NOT check for circular dependencies (that's task 1.2)
- This module is pure data loading - no routing logic
- The `path` field is relative to the skills root directory (resolution happens elsewhere)
