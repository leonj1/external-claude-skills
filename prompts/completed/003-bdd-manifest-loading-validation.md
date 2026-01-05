---
executor: bdd
source_feature: ./tests/bdd/manifest-loading.feature
---

<objective>
Implement the validation scenarios for manifest reference checking.
The implementation must detect missing skill, task, and dependency references.
</objective>

<gherkin>
Feature: YAML Manifest Loading and Validation
  As a skill router user
  I want the system to load and validate YAML manifests
  So that I have reliable skill configuration

  Background:
    Given a skill router system

  # Validation Scenarios

  Scenario: Validate skill references in tasks exist
    Given a manifest file with a task referencing skills
      | task_name      | skills                           |
      | static-website | [nextjs-standards, aws-hosting]  |
    And the manifest defines skill "nextjs-standards"
    And the manifest does not define skill "aws-hosting"
    When the system validates the manifest
    Then validation fails with a missing skill error
    And the error identifies "aws-hosting" as missing

  Scenario: Validate task references in categories exist
    Given a manifest file with a category referencing tasks
      | category_name   | tasks                    |
      | web-development | [static-website, blog]   |
    And the manifest defines task "static-website"
    And the manifest does not define task "blog"
    When the system validates the manifest
    Then validation fails with a missing task error
    And the error identifies "blog" as missing

  Scenario: Validate dependency references exist
    Given a manifest file with skills
      | name      | depends_on         |
      | ecr-setup | [missing-base]     |
    And the manifest does not define skill "missing-base"
    When the system validates the manifest
    Then validation fails with a missing dependency error
    And the error identifies "missing-base" as missing

  Scenario: Successfully validate a complete manifest
    Given a manifest file with consistent references
    When the system validates the manifest
    Then validation passes
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **ManifestValidator class** (lib/skill_router/manifest_validator.py):
   - Implements `IManifestValidator` interface
   - `validate(manifest: Manifest) -> List[str]`: Return list of error messages

2. **Validation Rules**:
   - Rule 1: All skill dependencies must exist in manifest.skills
   - Rule 2: All skills referenced by tasks must exist in manifest.skills
   - Rule 3: All tasks referenced by categories must exist in manifest.tasks
   - Rule 4: All skills referenced by categories must exist in manifest.skills

3. **Error Message Format**:
   - Dependency error: "Skill '{name}' depends on unknown skill '{dep}'"
   - Task skill error: "Task '{name}' references unknown skill '{skill}'"
   - Category task error: "Category '{name}' references unknown task '{task}'"
   - Category skill error: "Category '{name}' references unknown skill '{skill}'"

4. **Integration with Loader**:
   - ManifestLoader should use ManifestValidator after parsing
   - Raise ManifestValidationError if validation fails

Edge Cases to Handle:
- Multiple missing references (collect all errors)
- Empty reference lists (no validation needed)
- Self-consistent manifest (returns empty error list)
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-skill-router.md
DRAFT Specification: specs/DRAFT-manifest-loading.md
Gap Analysis: specs/GAP-ANALYSIS.md

Prerequisites (from prompts 001-002):
- All models exist (Skill, Task, Category, Manifest)
- IManifestValidator interface exists
- ManifestValidationError exception exists
- ManifestLoader exists (for integration)

Note: This does NOT include circular dependency detection (that's task 1.2)
</context>

<implementation>
Follow TDD approach:
1. Write tests for each validation rule
2. Implement ManifestValidator to make tests pass
3. Integrate validator into ManifestLoader

Test fixtures needed:
- Manifest with missing skill in task
- Manifest with missing task in category
- Manifest with missing dependency
- Manifest with all references valid

Architecture Guidelines:
- ManifestValidator implements IManifestValidator
- Collect all errors before returning (don't fail fast)
- Integration: Loader calls validator, raises on errors
- Keep under 500 lines
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Validate skill references in tasks exist
- [ ] Scenario: Validate task references in categories exist
- [ ] Scenario: Validate dependency references exist
- [ ] Scenario: Successfully validate a complete manifest
</verification>

<success_criteria>
- All 4 validation Gherkin scenarios pass
- ManifestValidator detects all missing references
- Error messages clearly identify the missing item
- Valid manifests pass validation with empty error list
- ManifestLoader raises ManifestValidationError for invalid manifests
</success_criteria>
