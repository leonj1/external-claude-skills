---
executor: bdd
source_feature: ./tests/bdd/dependency-resolution.feature
scenario_filter: edge_cases
---

<objective>
Implement edge case handling for the dependency resolver. The resolver must
gracefully handle missing dependencies, empty skill lists, and deeply nested
dependency chains without crashing.
</objective>

<gherkin>
Feature: Dependency Resolution with Topological Sort
  As a skill router
  I want to resolve skill dependencies in correct order
  So that skills are loaded after their prerequisites

  # Edge Case Scenarios

  Scenario: Handle skill with missing dependency reference
    Given skill "broken-skill" depends on "non-existent-skill"
    And "non-existent-skill" is not in the manifest
    When the dependency resolver processes "broken-skill"
    Then the missing dependency is skipped
    And a warning is logged

  Scenario: Handle empty skills list
    Given a request for no skills
    When the dependency resolver processes the skills
    Then the execution order is empty

  Scenario: Handle deeply nested dependencies
    Given a chain of 5 dependent skills
      | skill    | depends_on |
      | level-1  | []         |
      | level-2  | [level-1]  |
      | level-3  | [level-2]  |
      | level-4  | [level-3]  |
      | level-5  | [level-4]  |
    When the dependency resolver processes skill "level-5"
    Then the execution order contains 5 skills
    And skills appear in level order from 1 to 5
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. MissingDependencyWarning class for logging missing deps
2. Skip missing dependencies with warning (don't crash)
3. Handle empty skill list input (return empty list)
4. Support arbitrary depth dependency chains

Missing Dependency Handling:
- When skill references non-existent dependency, skip it
- Log MissingDependencyWarning with skill name and missing dep
- Continue resolution with available dependencies
- Include warning in DependencyResult.warnings

Empty Input Handling:
- resolve([]) returns DependencyResult with empty execution_order
- No errors or warnings for empty input

Deep Chain Handling:
- No artificial depth limit
- Recursive collection handles arbitrary depth
- Order preserved: root deps first, then children, down to leaf

</requirements>

<context>
BDD Specification: specs/DRAFT-dependency-resolver.md
Feature File: tests/bdd/dependency-resolution.feature
Previous Prompts: 001, 002, 003

Existing Code to Extend:
- lib/skill_router/exceptions.py: Add MissingDependencyWarning
- lib/skill_router/dependency_resolver.py: Add edge case handling

New Warning Class:
```python
class MissingDependencyWarning:
    """Warning issued when a dependency reference is missing."""
    def __init__(self, skill: str, missing: str):
        self.skill = skill
        self.missing = missing
        self.message = f"Skill '{skill}' depends on '{missing}' which is not in manifest"
```
</context>

<implementation>
Follow TDD approach:
1. Write tests from Gherkin scenarios
2. Implement edge case handling
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max)
- Check for missing deps in collect_dependencies()
- Return empty result for empty input (no special case needed if loop handles it)
- No recursion depth limit (Python default is 1000, sufficient for skills)
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Handle skill with missing dependency reference
- [ ] Scenario: Handle empty skills list
- [ ] Scenario: Handle deeply nested dependencies
</verification>

<success_criteria>
- All 3 edge case Gherkin scenarios pass
- Missing dependencies skipped with warning
- Empty input returns empty result
- Deep chains (5+ levels) resolve correctly
- MissingDependencyWarning class implemented
- DependencyResult.warnings populated correctly
- Code follows project coding standards
</success_criteria>
