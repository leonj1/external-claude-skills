# BDD Specification: Skill Router System

## Overview

The Skill Router is a system that maps user queries to executable skills through intelligent routing. It uses a YAML manifest to define skills, tasks, and their relationships, then routes incoming requests through a 3-tier matching system (direct skill match, task trigger match, LLM discovery).

## User Stories

- As a skill router user, I want the system to load and validate YAML manifests so that I have reliable skill configuration
- As a power user, I want to directly request skills by name so that I can bypass discovery and use specific capabilities
- As a user, I want my high-level requests to match predefined tasks so that I get the right combination of skills for my goal
- As a user with an ambiguous request, I want the system to intelligently match my intent so that I get appropriate skills even without exact phrases
- As a skill router, I want to resolve skill dependencies in correct order so that skills are loaded after their prerequisites
- As a Claude Code user, I want skill routing to integrate with the hooks system so that relevant skills are automatically loaded into context
- As a skill router system, I want to orchestrate the 3-tier matching flow so that queries are routed efficiently and correctly

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| manifest-loading.feature | 14 | Loading, validation, error handling |
| direct-skill-matching.feature | 14 | Tier 1 routing, patterns, edge cases |
| task-trigger-matching.feature | 14 | Tier 2 routing, word overlap, priority |
| llm-discovery.feature | 14 | Tier 3 routing, LLM integration, errors |
| dependency-resolution.feature | 15 | Topological sort, cycles, edge cases |
| hook-integration.feature | 16 | Context injection, content loading, E2E |
| router-orchestration.feature | 14 | 3-tier flow, normalization, errors |

**Total Scenarios: 101**

## Scenarios Summary

### manifest-loading.feature (14 scenarios)

**Happy Paths:**
1. Successfully load a valid manifest file
2. Load manifest with all required skill fields
3. Load manifest with skill dependencies
4. Load manifest with task definitions
5. Load manifest with category definitions

**Validation:**
6. Validate skill references in tasks exist
7. Validate task references in categories exist
8. Validate dependency references exist
9. Successfully validate a complete manifest

**Error Handling:**
10. Handle missing manifest file
11. Handle invalid YAML syntax
12. Handle manifest with missing required sections
13. Handle empty manifest file

### direct-skill-matching.feature (14 scenarios)

**Exact Name Match:**
1. Match skill by exact name in query
2. Match skill name embedded in query
3. Match skill with hyphenated name

**Pattern-Based Match:**
4. Match skill using common request patterns (8 examples)

**Case Sensitivity:**
5. Match skill name case-insensitively
6. Match mixed case skill request

**Priority and Ambiguity:**
7. Prioritize longer skill name when multiple match
8. No match when skill name not in query

**Edge Cases:**
9. Handle query with only skill name
10. Handle skill name with surrounding punctuation

### task-trigger-matching.feature (14 scenarios)

**Exact Trigger Match:**
1. Match task with exact trigger phrase
2. Match different task with exact trigger

**Word Overlap Matching:**
3. Match task when query contains trigger words
4. Match task with 60 percent word overlap
5. No match when word overlap below threshold

**Best Match Selection:**
6. Select task with highest word overlap score
7. Distinguish between similar tasks
8. Match admin panel over generic dashboard

**Case and Formatting:**
9. Match triggers case-insensitively
10. Match with extra whitespace in query

**Skills Resolution:**
11. Return all skills required by matched task

**Tier Priority:**
12. Tier 1 takes priority over Tier 2

**No Match:**
13. No match for ambiguous request
14. No match for unrelated query

### llm-discovery.feature (14 scenarios)

**LLM Task Selection:**
1. LLM selects appropriate task for high-level request
2. LLM selects task for building request

**LLM Skill Selection:**
3. LLM selects skill for specific infrastructure request
4. LLM selects skill for database request

**LLM Input Format:**
5. LLM receives formatted task options
6. LLM receives clear instructions

**LLM Response Parsing:**
7. Successfully parse valid LLM JSON response
8. Successfully parse LLM skill response

**LLM Error Handling:**
9. Handle malformed LLM JSON response
10. Handle LLM returning non-existent task
11. Handle LLM returning non-existent skill

**Discovery Results:**
12. Discovery result includes resolved skills
13. Discovery skill result includes dependencies

### dependency-resolution.feature (15 scenarios)

**Single Skill Resolution:**
1. Resolve skill with no dependencies
2. Resolve skill with single dependency
3. Resolve skill with multiple dependencies
4. Resolve skill with transitive dependencies

**Multiple Skills Resolution:**
5. Resolve multiple skills with shared dependencies
6. Resolve multiple independent skills
7. Resolve task skills with complex dependencies

**Topological Sort Validation:**
8. Validate execution order respects all dependencies
9. Collect all transitive dependencies

**Cycle Detection:**
10. Detect simple circular dependency
11. Detect complex circular dependency
12. Handle circular dependency gracefully during resolution

**Edge Cases:**
13. Handle skill with missing dependency reference
14. Handle empty skills list
15. Handle deeply nested dependencies

### hook-integration.feature (16 scenarios)

**Skill Context Injection:**
1. Inject single skill context
2. Inject multiple skill contexts in execution order
3. Mark primary and dependency skills distinctly
4. Inject task skills as primary

**Output Format:**
5. Generate correct output structure
6. Include execution order summary in output
7. Include route type and matched name

**Skill Content Loading:**
8. Load skill content from SKILL.md file
9. Handle missing SKILL.md file
10. Handle missing skill directory

**Hook Script Integration:**
11. Hook receives query from environment variable
12. Hook receives query from stdin
13. Hook outputs to stdout for injection

**Error Result Handling:**
14. Handle error route result
15. Handle empty execution order

**End-to-End Integration:**
16. Full flow from query to context injection
17. Full flow for task-based query

### router-orchestration.feature (14 scenarios)

**Tier Flow:**
1. Tier 1 match short-circuits remaining tiers
2. Tier 2 executes only when tier 1 fails
3. Tier 3 executes only when tier 1 and 2 fail

**Route Result Construction:**
4. Skill match returns correct route result
5. Task match returns correct route result
6. Discovery match returns correct route result

**Query Normalization:**
7. Normalize query to lowercase
8. Normalize query whitespace

**Error Handling:**
9. Return error when no match found at any tier
10. Handle manifest loading failure

**Performance:**
11. Direct skill match responds quickly
12. Task trigger match responds without LLM call

**Edge Cases:**
13. Handle empty query
14. Handle very long query
15. Handle special characters in query

## Acceptance Criteria

### Manifest Loading
- System loads and parses valid YAML manifest files
- All skill fields (name, description, path, depends_on) are captured
- Task definitions with triggers and skill lists are supported
- Category groupings are optional but supported
- Missing references (skills, tasks, dependencies) are detected
- Invalid YAML syntax reports line numbers
- Missing files report expected paths

### 3-Tier Routing
- **Tier 1 (Direct Skill Match)**: Skill names in query are detected immediately
- **Tier 2 (Task Trigger Match)**: 60% word overlap threshold for trigger matching
- **Tier 3 (LLM Discovery)**: Falls back to LLM for ambiguous queries
- Tiers short-circuit (Tier 1 match skips Tier 2 and 3)
- Query normalization (lowercase, whitespace) before matching

### Dependency Resolution
- Topological sort ensures dependencies load before dependents
- Transitive dependencies are collected recursively
- Circular dependencies are detected and handled gracefully
- Missing dependency references are skipped with warnings
- Shared dependencies appear only once in execution order

### Hook Integration
- Skill context wrapped in `<skill_context>` tags
- Skills appear in dependency-resolved execution order
- Primary skills marked `[PRIMARY]`, dependencies marked `[DEPENDENCY]`
- SKILL.md content loaded from skill directories
- Missing content returns placeholder with path
- Hook reads query from PROMPT env var or stdin
- Output suitable for prepending to prompts

## Key Interfaces

| Interface | Purpose |
|-----------|---------|
| IManifestLoader | Load and validate YAML manifest |
| ISkillMatcher | Match queries to skills (Tier 1) |
| ITaskMatcher | Match queries to tasks (Tier 2) |
| ILLMDiscovery | LLM-based discovery (Tier 3) |
| IDependencyResolver | Topological sort of dependencies |
| IHookIntegration | Generate skill context for injection |
| IRouter | Orchestrate 3-tier routing flow |

## Data Models

```
RouteResult:
  - route_type: "task" | "skill" | "discovery" | "error"
  - matched: string (task or skill name)
  - skills: list[string] (primary skills)
  - execution_order: list[string] (dependency-resolved order)
```

## Ready For

- `gherkin-to-test` agent for converting scenarios to TDD prompts
- `test-creator` agent for writing unit tests
- `coder` agent for implementation
