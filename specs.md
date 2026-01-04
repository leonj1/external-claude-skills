Manifest Structure
yaml# ~/.claude/skills/manifest.yaml

# =============================================================================
# SKILLS: The actual capabilities (flat list, with dependencies)
# =============================================================================
skills:
  # Infrastructure - Base Layer
  terraform-base:
    description: "Terraform state backend, providers, and module conventions"
    path: infrastructure/terraform-base
    depends_on: []
    
  ecr-setup:
    description: "AWS ECR container registry setup"
    path: infrastructure/ecr-setup
    depends_on: [terraform-base]

  # Infrastructure - AWS
  aws-static-hosting:
    description: "S3 + CloudFront for static asset hosting"
    path: infrastructure/aws-static-hosting
    depends_on: [terraform-base]
    
  aws-ecs-deployment:
    description: "ECS Fargate container deployment with load balancing"
    path: infrastructure/aws-ecs-deployment
    depends_on: [terraform-base, ecr-setup]
    
  aws-lambda-deployment:
    description: "Lambda function deployment with API Gateway"
    path: infrastructure/aws-lambda-deployment
    depends_on: [terraform-base]

  # Infrastructure - Kubernetes
  eks-cluster:
    description: "AWS EKS Kubernetes cluster setup"
    path: infrastructure/eks-cluster
    depends_on: [terraform-base]
    
  k8s-deployment:
    description: "Kubernetes deployment manifests and Helm charts"
    path: infrastructure/k8s-deployment
    depends_on: [eks-cluster]

  # Application Frameworks
  nextjs-standards:
    description: "Next.js project structure and conventions"
    path: frameworks/nextjs-standards
    depends_on: []
    
  react-admin-standards:
    description: "React admin dashboard patterns and components"
    path: frameworks/react-admin-standards
    depends_on: []
    
  fastapi-standards:
    description: "FastAPI project structure and conventions"
    path: frameworks/fastapi-standards
    depends_on: []

  # Auth & Security
  auth-cognito:
    description: "AWS Cognito authentication setup"
    path: auth/auth-cognito
    depends_on: [terraform-base]
    
  auth-auth0:
    description: "Auth0 authentication integration"
    path: auth/auth-auth0
    depends_on: []

  # Data
  rds-postgres:
    description: "AWS RDS PostgreSQL database setup"
    path: data/rds-postgres
    depends_on: [terraform-base]
    
  dynamodb-setup:
    description: "DynamoDB table setup with access patterns"
    path: data/dynamodb-setup
    depends_on: [terraform-base]

  # CI/CD
  github-actions-cicd:
    description: "GitHub Actions CI/CD pipelines"
    path: cicd/github-actions
    depends_on: []


# =============================================================================
# TASKS: What users ask for (maps to one or more skills)
# =============================================================================
tasks:
  # Web Development - Static
  static-website:
    description: "Static website, landing page, marketing site, or documentation site"
    triggers:
      - "build a static website"
      - "create a landing page"
      - "make a marketing site"
      - "create a documentation site"
      - "build a homepage"
      - "create a product page"
      - "build a blog"
    skills: [nextjs-standards, aws-static-hosting, github-actions-cicd]
    
  documentation-site:
    description: "Technical documentation site"
    triggers:
      - "create documentation"
      - "build a docs site"
      - "create API documentation"
    skills: [nextjs-standards, aws-static-hosting]

  # Web Development - Dynamic
  admin-panel:
    description: "Internal admin dashboard or back-office tool"
    triggers:
      - "build an admin panel"
      - "create a dashboard"
      - "create an internal tool"
      - "build a back-office"
      - "create a management interface"
    skills: [react-admin-standards, fastapi-standards, aws-ecs-deployment, rds-postgres, auth-cognito]
    
  customer-portal:
    description: "Customer-facing web application with authentication"
    triggers:
      - "build a customer portal"
      - "create a user dashboard"
      - "build a client application"
      - "create a self-service portal"
    skills: [nextjs-standards, aws-ecs-deployment, auth-cognito, rds-postgres]

  # APIs
  rest-api:
    description: "RESTful API service"
    triggers:
      - "build an API"
      - "create a REST API"
      - "build a backend service"
      - "create microservices"
    skills: [fastapi-standards, aws-ecs-deployment, rds-postgres]
    
  serverless-api:
    description: "Serverless API with Lambda"
    triggers:
      - "build a serverless API"
      - "create a Lambda function"
      - "build a serverless backend"
    skills: [fastapi-standards, aws-lambda-deployment, dynamodb-setup]

  # Infrastructure Only
  kubernetes-setup:
    description: "Kubernetes cluster and deployment setup"
    triggers:
      - "set up Kubernetes"
      - "create a K8s cluster"
      - "deploy to Kubernetes"
    skills: [eks-cluster, k8s-deployment]


# =============================================================================
# CATEGORIES: Optional grouping for browsing/discovery (not required for routing)
# =============================================================================
categories:
  web-development:
    description: "Websites and web applications"
    tasks: [static-website, documentation-site, admin-panel, customer-portal]
    
  backend:
    description: "APIs and backend services"
    tasks: [rest-api, serverless-api]
    
  infrastructure:
    description: "Cloud infrastructure and DevOps"
    tasks: [kubernetes-setup]
    # Also exposes raw skills for direct access
    skills: [terraform-base, aws-static-hosting, aws-ecs-deployment, aws-lambda-deployment, eks-cluster]

Updated Router
python# skill_router.py
import yaml
import anthropic
from pathlib import Path
from dataclasses import dataclass

@dataclass
class RouteResult:
    route_type: str  # "task", "skill", or "discovery"
    matched: str     # task name or skill name
    skills: list[str]  # skills to load
    execution_order: list[str]  # dependency-resolved order


class SkillRouter:
    def __init__(self, manifest_path: str = "~/.claude/skills/manifest.yaml"):
        self.manifest_path = Path(manifest_path).expanduser()
        self.client = anthropic.Anthropic()
    
    def _load_manifest(self) -> dict:
        with open(self.manifest_path) as f:
            return yaml.safe_load(f)
    
    def route(self, user_query: str) -> RouteResult:
        """
        Route user query to skills via three-tier matching:
        1. Direct skill name match
        2. Task trigger match
        3. LLM-based discovery
        """
        manifest = self._load_manifest()
        query_lower = user_query.lower().strip()
        
        # Tier 1: Direct skill name match
        # User said something like "use aws-ecs-deployment" or "apply terraform-base"
        direct_skill = self._match_direct_skill(query_lower, manifest["skills"])
        if direct_skill:
            execution_order = self._resolve_dependencies(direct_skill, manifest["skills"])
            return RouteResult(
                route_type="skill",
                matched=direct_skill,
                skills=[direct_skill],
                execution_order=execution_order,
            )
        
        # Tier 2: Task trigger match
        # User said something that matches a known task trigger
        matched_task = self._match_task_triggers(query_lower, manifest["tasks"])
        if matched_task:
            task_skills = manifest["tasks"][matched_task]["skills"]
            execution_order = self._resolve_dependencies_multi(task_skills, manifest["skills"])
            return RouteResult(
                route_type="task",
                matched=matched_task,
                skills=task_skills,
                execution_order=execution_order,
            )
        
        # Tier 3: LLM-based discovery
        # Query doesn't match known patterns, ask LLM
        return self._llm_discovery(user_query, manifest)
    
    def _match_direct_skill(self, query: str, skills: dict) -> str | None:
        """Check if user is directly requesting a skill by name."""
        # Common patterns for direct skill requests
        patterns = [
            "use {skill}",
            "apply {skill}",
            "run {skill}",
            "execute {skill}",
            "{skill} skill",
            "deploy with {skill}",
            "set up {skill}",
            "configure {skill}",
        ]
        
        for skill_name in skills.keys():
            # Exact match
            if skill_name in query:
                return skill_name
            
            # Pattern match
            for pattern in patterns:
                if pattern.format(skill=skill_name) in query:
                    return skill_name
        
        return None
    
    def _match_task_triggers(self, query: str, tasks: dict) -> str | None:
        """Check if query matches any task triggers."""
        best_match = None
        best_score = 0
        
        for task_name, task_data in tasks.items():
            for trigger in task_data.get("triggers", []):
                # Simple word overlap scoring
                trigger_words = set(trigger.lower().split())
                query_words = set(query.split())
                overlap = len(trigger_words & query_words)
                coverage = overlap / len(trigger_words) if trigger_words else 0
                
                if coverage > best_score and coverage >= 0.6:  # 60% word overlap threshold
                    best_score = coverage
                    best_match = task_name
        
        return best_match
    
    def _llm_discovery(self, query: str, manifest: dict) -> RouteResult:
        """Use LLM to find the best task or skill."""
        
        # Build compact representation
        options = self._build_options_text(manifest)
        
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": f"""Match this request to the best task or skill.

## Request
{query}

## Available Tasks (high-level, maps to multiple skills)
{options['tasks']}

## Available Skills (low-level, direct capabilities)
{options['skills']}

## Instructions
- If the request is high-level (build something, create something), choose a TASK
- If the request is specific infrastructure/tooling, choose a SKILL
- Return JSON: {{"type": "task" or "skill", "name": "the-name"}}

## Response:"""
            }]
        )
        
        # Parse response
        import json
        try:
            result = json.loads(response.content[0].text.strip())
            match_type = result.get("type", "task")
            match_name = result.get("name", "")
        except:
            # Fallback to first task
            match_type = "task"
            match_name = list(manifest["tasks"].keys())[0]
        
        # Resolve based on type
        if match_type == "skill" and match_name in manifest["skills"]:
            execution_order = self._resolve_dependencies(match_name, manifest["skills"])
            return RouteResult(
                route_type="skill",
                matched=match_name,
                skills=[match_name],
                execution_order=execution_order,
            )
        elif match_name in manifest["tasks"]:
            task_skills = manifest["tasks"][match_name]["skills"]
            execution_order = self._resolve_dependencies_multi(task_skills, manifest["skills"])
            return RouteResult(
                route_type="task",
                matched=match_name,
                skills=task_skills,
                execution_order=execution_order,
            )
        else:
            return RouteResult(
                route_type="error",
                matched="",
                skills=[],
                execution_order=[],
            )
    
    def _build_options_text(self, manifest: dict) -> dict:
        """Build compact text representation for LLM."""
        tasks_text = "\n".join([
            f"- {name}: {data['description']}"
            for name, data in manifest["tasks"].items()
        ])
        
        skills_text = "\n".join([
            f"- {name}: {data['description']}"
            for name, data in manifest["skills"].items()
        ])
        
        return {"tasks": tasks_text, "skills": skills_text}
    
    def _resolve_dependencies(self, skill_name: str, skills: dict) -> list[str]:
        """Resolve dependencies for a single skill."""
        return self._resolve_dependencies_multi([skill_name], skills)
    
    def _resolve_dependencies_multi(self, skill_names: list[str], skills: dict) -> list[str]:
        """Resolve dependencies for multiple skills, return in execution order."""
        collected = set()
        
        def collect(name: str):
            if name in collected or name not in skills:
                return
            collected.add(name)
            for dep in skills[name].get("depends_on", []):
                collect(dep)
        
        for skill in skill_names:
            collect(skill)
        
        # Topological sort
        result = []
        remaining = collected.copy()
        
        while remaining:
            for skill_name in list(remaining):
                deps = set(skills.get(skill_name, {}).get("depends_on", []))
                if deps.issubset(set(result)):
                    result.append(skill_name)
                    remaining.remove(skill_name)
                    break
            else:
                # Cycle or missing dependency - add remaining in any order
                result.extend(remaining)
                break
        
        return result

Usage Examples
pythonrouter = SkillRouter()

# Example 1: High-level task
result = router.route("build a static website")
# RouteResult(
#     route_type="task",
#     matched="static-website", 
#     skills=["nextjs-standards", "aws-static-hosting", "github-actions-cicd"],
#     execution_order=["terraform-base", "aws-static-hosting", "nextjs-standards", "github-actions-cicd"]
# )

# Example 2: Direct skill request
result = router.route("use aws-ecs-deployment for this service")
# RouteResult(
#     route_type="skill",
#     matched="aws-ecs-deployment",
#     skills=["aws-ecs-deployment"],
#     execution_order=["terraform-base", "ecr-setup", "aws-ecs-deployment"]
# )

# Example 3: Ambiguous request (goes to LLM)
result = router.route("I need a way for users to log in")
# RouteResult(
#     route_type="task",
#     matched="customer-portal",  # LLM decided
#     skills=["nextjs-standards", "aws-ecs-deployment", "auth-cognito", "rds-postgres"],
#     execution_order=["terraform-base", "ecr-setup", "aws-ecs-deployment", "auth-cognito", "rds-postgres", "nextjs-standards"]
# )
```

---

## Routing Flow
```
User Query: "deploy my app with aws-ecs-deployment"
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 1: Direct Skill Match                     │
│  Check if query contains skill name             │
│  ✓ Found: "aws-ecs-deployment"                  │
│  → Skip to dependency resolution                │
└─────────────────────────────────────────────────┘
                │
                ▼
        Resolve: terraform-base → ecr-setup → aws-ecs-deployment


User Query: "build a landing page for our product"
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 1: Direct Skill Match                     │
│  ✗ No skill name found                          │
└─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 2: Task Trigger Match                     │
│  Check triggers for all tasks                   │
│  "create a landing page" matches 80%            │
│  ✓ Found: task "static-website"                 │
└─────────────────────────────────────────────────┘
                │
                ▼
        Resolve: terraform-base → aws-static-hosting → nextjs-standards → github-actions-cicd


User Query: "set up authentication for my app"
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 1: Direct Skill Match                     │
│  ✗ No skill name found                          │
└─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 2: Task Trigger Match                     │
│  ✗ No trigger matches well                      │
└─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  Tier 3: LLM Discovery                          │
│  Present all tasks + skills to Haiku            │
│  → LLM selects: skill "auth-cognito"            │
└─────────────────────────────────────────────────┘
                │
                ▼
        Resolve: terraform-base → auth-cognito

Key Design Decisions
AspectDecisionRationaleTasks vs SkillsSeparate conceptsTasks are user-facing intents; Skills are implementation unitsTriggersExplicit phrase listFaster than LLM, predictable matchingDirect skill accessAlways availablePower users and automation can skip discoveryCategoriesOptionalOnly for browsing UI, not required for routingDependenciesOn skills onlyTasks don't have dependencies—they compose skillsLLM fallbackTier 3 onlyMinimizes latency and cost for known patterns

Full Hook Integration
python#!/usr/bin/env python3
# ~/.claude/hooks/route_and_inject.py

import sys
import os
import yaml
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.claude/lib"))
from skill_router import SkillRouter

def main():
    query = os.environ.get("PROMPT", sys.stdin.read().strip())
    
    router = SkillRouter()
    result = router.route(query)
    
    if result.route_type == "error":
        return  # No skills to inject
    
    # Load skill contents
    manifest_path = Path("~/.claude/skills/manifest.yaml").expanduser()
    manifest = yaml.safe_load(open(manifest_path))
    skills_root = manifest_path.parent
    
    print("\n<skill_context>")
    print(f"Matched: {result.route_type} '{result.matched}'")
    print(f"Execution order: {' → '.join(result.execution_order)}\n")
    
    for skill_name in result.execution_order:
        skill_data = manifest["skills"].get(skill_name, {})
        skill_path = skills_root / skill_data.get("path", skill_name) / "SKILL.md"
        
        is_primary = skill_name in result.skills
        marker = "[PRIMARY]" if is_primary else "[DEPENDENCY]"
        
        print(f"## {skill_name} {marker}")
        if skill_path.exists():
            print(skill_path.read_text())
        else:
            print(f"(Skill file not found: {skill_path})")
        print("\n---\n")
    
    print("</skill_context>")

if __name__ == "__main__":
    main()
This structure cleanly separates what users ask for (tasks) from how it's implemented (skills), while still allowing direct skill access when needed.
