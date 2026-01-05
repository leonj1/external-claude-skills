---
executor: bdd
source_feature: ./tests/bdd/manifest-loading.feature
---

<objective>
Implement the error handling scenarios for manifest loading.
The implementation must handle file not found, invalid YAML, missing sections, and empty files.
</objective>

<gherkin>
Feature: YAML Manifest Loading and Validation
  As a skill router user
  I want the system to load and validate YAML manifests
  So that I have reliable skill configuration

  Background:
    Given a skill router system

  # Error Handling Scenarios

  Scenario: Handle missing manifest file
    Given no manifest file exists at the configured path
    When the system attempts to load the manifest
    Then a manifest not found error is raised
    And the error includes the expected file path

  Scenario: Handle invalid YAML syntax
    Given a manifest file with invalid YAML syntax
    When the system attempts to load the manifest
    Then a manifest parse error is raised
    And the error includes the line number of the syntax error

  Scenario: Handle manifest with missing required sections
    Given a manifest file missing the skills section
    When the system validates the manifest
    Then validation fails with a missing section error
    And the error identifies "skills" as the missing section

  Scenario: Handle empty manifest file
    Given an empty manifest file
    When the system attempts to load the manifest
    Then a manifest parse error is raised
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **File Not Found Handling** (ManifestLoader.load):
   - Check if file exists before reading
   - Raise `ManifestNotFoundError(path)` if missing
   - Error message includes the attempted path

2. **Invalid YAML Handling** (ManifestLoader.load_from_string):
   - Catch `yaml.YAMLError` exceptions
   - Extract line number from `problem_mark` if available
   - Raise `ManifestParseError(message, line=N)`

3. **Missing Required Section Handling** (ManifestValidator.validate):
   - Check that `skills` section exists in manifest
   - Add validation rule: "Missing required section: skills"
   - Note: tasks and categories are optional

4. **Empty File Handling** (ManifestLoader.load_from_string):
   - Detect when yaml.safe_load returns None
   - Raise `ManifestParseError("Empty manifest")`

Edge Cases to Handle:
- File exists but is not readable (permission error)
- YAML is valid but empty object `{}`
- YAML has only whitespace or comments
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-skill-router.md
DRAFT Specification: specs/DRAFT-manifest-loading.md
Gap Analysis: specs/GAP-ANALYSIS.md

Prerequisites (from prompts 001-003):
- ManifestNotFoundError, ManifestParseError, ManifestValidationError exist
- ManifestLoader exists
- ManifestValidator exists

Note: The "missing required sections" scenario requires adding a new validation rule
</context>

<implementation>
Follow TDD approach:
1. Write tests for each error scenario
2. Implement error handling in ManifestLoader
3. Add missing section validation to ManifestValidator

Test fixtures needed:
- Non-existent file path
- File with invalid YAML (e.g., "key: [unclosed")
- File without skills section
- Empty file (0 bytes or only whitespace)

Architecture Guidelines:
- Use pathlib.Path.exists() for file checking
- Catch yaml.YAMLError and extract details
- Distinguish between empty file and empty sections
- Keep under 500 lines
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Handle missing manifest file
- [ ] Scenario: Handle invalid YAML syntax
- [ ] Scenario: Handle manifest with missing required sections
- [ ] Scenario: Handle empty manifest file
</verification>

<success_criteria>
- All 4 error handling Gherkin scenarios pass
- ManifestNotFoundError includes the file path
- ManifestParseError includes line number when available
- ManifestValidationError identifies "skills" as required
- Empty files are handled gracefully with clear error
</success_criteria>
