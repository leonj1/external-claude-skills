---
executor: bdd
source_feature: ./tests/bdd/manifest-loading.feature
---

<objective>
Implement the happy path scenarios for YAML manifest loading.
The implementation must successfully parse valid YAML manifests and populate all data models.
</objective>

<gherkin>
Feature: YAML Manifest Loading and Validation
  As a skill router user
  I want the system to load and validate YAML manifests
  So that I have reliable skill configuration

  Background:
    Given a skill router system

  # Happy Path Scenarios

  Scenario: Successfully load a valid manifest file
    Given a manifest file exists at the configured path
    And the manifest contains valid YAML syntax
    When the system loads the manifest
    Then the manifest is parsed successfully
    And the skills section is available
    And the tasks section is available
    And the categories section is available

  Scenario: Load manifest with all required skill fields
    Given a manifest file with a skill definition containing
      | field       | value                          |
      | name        | terraform-base                 |
      | description | Terraform state backend setup  |
      | path        | infrastructure/terraform-base  |
      | depends_on  | []                             |
    When the system loads the manifest
    Then the skill "terraform-base" is registered
    And the skill has the correct description
    And the skill has the correct path
    And the skill has an empty dependency list

  Scenario: Load manifest with skill dependencies
    Given a manifest file with skills
      | name           | depends_on       |
      | terraform-base | []               |
      | ecr-setup      | [terraform-base] |
    When the system loads the manifest
    Then skill "ecr-setup" depends on "terraform-base"

  Scenario: Load manifest with task definitions
    Given a manifest file with a task definition containing
      | field       | value                                    |
      | name        | static-website                           |
      | description | Static website or landing page           |
      | triggers    | [build a static website, create a landing page] |
      | skills      | [nextjs-standards, aws-static-hosting]   |
    When the system loads the manifest
    Then the task "static-website" is registered
    And the task has 2 triggers
    And the task requires 2 skills

  Scenario: Load manifest with category definitions
    Given a manifest file with a category definition containing
      | field       | value                              |
      | name        | web-development                    |
      | description | Websites and web applications      |
      | tasks       | [static-website, admin-panel]      |
      | skills      | []                                 |
    When the system loads the manifest
    Then the category "web-development" is registered
    And the category contains 2 tasks
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **ManifestLoader class** (lib/skill_router/manifest_loader.py):
   - Implements `IManifestLoader` interface
   - `load(path: str) -> Manifest`: Load from file path
   - `load_from_string(content: str) -> Manifest`: Load from YAML string
   - Uses PyYAML's `safe_load` for parsing

2. **YAML to Model Conversion**:
   - Parse skills section into `Dict[str, Skill]`
   - Parse tasks section into `Dict[str, Task]`
   - Parse categories section into `Dict[str, Category]`
   - Handle missing sections gracefully (empty dicts)

3. **Field Mapping**:
   - Skill: name (from key), description, path, depends_on (default: [])
   - Task: name (from key), description, triggers, skills
   - Category: name (from key), description, tasks (default: []), skills (default: [])

Edge Cases to Handle:
- Empty depends_on/triggers/skills lists
- Missing optional sections (categories)
- Sections with no entries
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-skill-router.md
DRAFT Specification: specs/DRAFT-manifest-loading.md
Gap Analysis: specs/GAP-ANALYSIS.md

Prerequisites (from prompt 001):
- Skill, Task, Category, Manifest models exist
- IManifestLoader interface exists
- Exception classes exist

Dependencies:
- pyyaml for YAML parsing
</context>

<implementation>
Follow TDD approach:
1. Write tests for each Gherkin scenario
2. Implement ManifestLoader to make tests pass
3. Verify all fields are correctly mapped

Test fixtures needed:
- Valid manifest YAML string
- Manifest with skills, tasks, categories
- Manifest with dependencies

Architecture Guidelines:
- ManifestLoader implements IManifestLoader
- Use yaml.safe_load for security
- Build Manifest object from parsed dict
- Keep under 500 lines
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Successfully load a valid manifest file
- [ ] Scenario: Load manifest with all required skill fields
- [ ] Scenario: Load manifest with skill dependencies
- [ ] Scenario: Load manifest with task definitions
- [ ] Scenario: Load manifest with category definitions
</verification>

<success_criteria>
- All 5 happy path Gherkin scenarios pass
- ManifestLoader correctly parses valid YAML
- All skill fields are captured (name, description, path, depends_on)
- All task fields are captured (name, description, triggers, skills)
- All category fields are captured (name, description, tasks, skills)
- Dependencies are correctly represented as lists
</success_criteria>
