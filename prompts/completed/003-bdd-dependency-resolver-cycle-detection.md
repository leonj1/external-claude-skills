---
executor: bdd
source_feature: ./tests/bdd/dependency-resolution.feature
scenario_filter: cycle_detection
---

<objective>
Implement cycle detection for skill dependencies. The resolver must detect
circular dependencies (both simple and complex) and handle them gracefully
without crashing, while providing appropriate warnings.
</objective>

<gherkin>
Feature: Dependency Resolution with Topological Sort
  As a skill router
  I want to resolve skill dependencies in correct order
  So that skills are loaded after their prerequisites

  # Cycle Detection Scenarios

  Scenario: Detect simple circular dependency
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-a]  |
    When the dependency resolver checks for cycles
    Then a cycle is detected containing "skill-a" and "skill-b"

  Scenario: Detect complex circular dependency
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-c]  |
      | skill-c  | [skill-a]  |
    When the dependency resolver checks for cycles
    Then a cycle is detected

  Scenario: Handle circular dependency gracefully during resolution
    Given a manifest with circular dependencies
      | skill    | depends_on |
      | skill-a  | [skill-b]  |
      | skill-b  | [skill-a]  |
    When the dependency resolver processes skill "skill-a"
    Then resolution completes with a warning
    And all skills are included in the result
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. detect_cycles(skills) method on IDependencyResolver
2. find_cycles(edges) method on ITopologicalSorter
3. CyclicDependencyError exception class
4. Graceful cycle handling in resolve() and resolve_multi()
5. DependencyResult.warnings and has_cycle fields

Cycle Detection Algorithm (DFS-based):
- Track visited nodes and recursion stack
- When node in recursion stack is revisited, cycle found
- Extract cycle path from recursion stack
- Return list of all cycles found

Graceful Handling Rules:
- Cycle detection does not crash the resolver
- Resolution completes with warning when cycle exists
- All skills in the cycle are included in result
- DependencyResult.has_cycle = True when cycle detected
- DependencyResult.warnings contains cycle description

</requirements>

<context>
BDD Specification: specs/DRAFT-dependency-resolver.md
Feature File: tests/bdd/dependency-resolution.feature
Previous Prompts: 001, 002

Existing Code to Extend:
- lib/skill_router/exceptions.py: Add DependencyError, CyclicDependencyError
- lib/skill_router/dependency_resolver.py: Add cycle detection
- lib/skill_router/dependency_graph.py: DependencyResult with warnings

New Exception Classes:
```python
class DependencyError(Exception):
    """Base exception for dependency resolution errors."""
    pass

class CyclicDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""
    def __init__(self, cycle: Tuple[str, ...]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
        super().__init__(f"Circular dependency detected: {cycle_str}")
```
</context>

<implementation>
Follow TDD approach:
1. Write tests from Gherkin scenarios
2. Implement cycle detection
3. Implement graceful handling
4. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max)
- Use DFS algorithm for cycle detection
- Modify Kahn's algorithm to handle remaining nodes as cycle
- Return warnings rather than raising exceptions for graceful handling
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Detect simple circular dependency
- [ ] Scenario: Detect complex circular dependency
- [ ] Scenario: Handle circular dependency gracefully during resolution
</verification>

<success_criteria>
- All 3 cycle detection Gherkin scenarios pass
- detect_cycles() returns list of cycle tuples
- Simple cycles (A->B->A) detected correctly
- Complex cycles (A->B->C->A) detected correctly
- Resolution completes with warning, not exception
- DependencyResult includes has_cycle and warnings
- Code follows project coding standards
</success_criteria>
