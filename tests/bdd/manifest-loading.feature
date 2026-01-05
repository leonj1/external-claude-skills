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
    Then an EmptyManifestError is raised
    And the error message contains "manifest file is empty"
