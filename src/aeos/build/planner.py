"""
AEOS Build Rail — Build Plan generator.

Produces a structured architecture plan for a new AEOS-native project.
Read-only. No files created. No AI inference. No network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_TYPES: frozenset[str] = frozenset({"web-app", "api", "internal-tool"})
VALID_STACKS: frozenset[str] = frozenset(
    {"nextjs-supabase", "nextjs-postgres", "fastapi-postgres", "generic"}
)

_GOVERNANCE_FILES: list[str] = [
    "README.md",
    "ARCHITECTURE.md",
    ".env.example",
    ".gitignore",
    "docs/DECISIONS.md",
]

_ARCH_SUMMARY: dict[tuple[str, str], str] = {
    ("web-app", "nextjs-supabase"): (
        "Next.js frontend with Supabase BaaS (auth, database, storage). "
        "API routes in Next.js App Router. RLS required on all Supabase tables."
    ),
    ("web-app", "nextjs-postgres"): (
        "Next.js frontend with self-hosted PostgreSQL. "
        "Full database sovereignty from day one. "
        "API routes or separate backend layer."
    ),
    ("web-app", "fastapi-postgres"): (
        "Next.js frontend with FastAPI backend and PostgreSQL. "
        "Separate frontend/backend services. JWT auth. Full database ownership."
    ),
    ("web-app", "generic"): (
        "Web application with undecided stack. "
        "Frontend and backend separation recommended. "
        "Architecture to be decided before scaffolding."
    ),
    ("api", "fastapi-postgres"): (
        "FastAPI backend with PostgreSQL. "
        "JWT auth, Alembic migrations, OpenAPI spec auto-generated. "
        "Full database ownership."
    ),
    ("api", "nextjs-supabase"): (
        "API-first Next.js application backed by Supabase. "
        "RLS required for all data access. Auth via Supabase Auth."
    ),
    ("api", "nextjs-postgres"): (
        "API-first Next.js application with self-hosted PostgreSQL. "
        "Full database sovereignty. Prisma or raw SQL migrations."
    ),
    ("api", "generic"): (
        "API service with undecided stack. "
        "Auth layer and database to be selected before scaffolding."
    ),
    ("internal-tool", "nextjs-supabase"): (
        "Internal Next.js tool with Supabase backend. "
        "Minimal public surface, restricted auth, audit trail recommended."
    ),
    ("internal-tool", "nextjs-postgres"): (
        "Internal Next.js tool with self-hosted PostgreSQL. "
        "Full sovereignty, restricted access, audit trail recommended."
    ),
    ("internal-tool", "fastapi-postgres"): (
        "Internal FastAPI tool with PostgreSQL. "
        "Strong auth boundaries, audit logging, minimal external dependencies."
    ),
    ("internal-tool", "generic"): (
        "Internal tool with undecided stack. "
        "Prioritize minimal external dependencies and strong auth boundaries."
    ),
}

_FOLDER_STRUCTURE: dict[str, list[str]] = {
    "nextjs-supabase": [
        "src/app/",
        "src/components/",
        "src/lib/",
        "supabase/migrations/",
        "public/",
        "docs/",
        "tests/",
        ".env.example",
        ".gitignore",
        "README.md",
        "ARCHITECTURE.md",
        "docs/DECISIONS.md",
    ],
    "nextjs-postgres": [
        "src/app/",
        "src/components/",
        "src/lib/",
        "src/db/",
        "migrations/",
        "public/",
        "docs/",
        "tests/",
        ".env.example",
        ".gitignore",
        "README.md",
        "ARCHITECTURE.md",
        "docs/DECISIONS.md",
    ],
    "fastapi-postgres": [
        "src/api/",
        "src/models/",
        "src/db/",
        "src/auth/",
        "migrations/",
        "docs/",
        "tests/unit/",
        "tests/integration/",
        ".env.example",
        ".gitignore",
        "README.md",
        "ARCHITECTURE.md",
        "docs/DECISIONS.md",
        "Dockerfile",
    ],
    "generic": [
        "src/",
        "docs/",
        "tests/",
        "scripts/",
        ".env.example",
        ".gitignore",
        "README.md",
        "ARCHITECTURE.md",
        "docs/DECISIONS.md",
    ],
}

_SECURITY_BASE: list[str] = [
    "No .env committed — .gitignore must include .env from day one",
    "Secrets only through environment variables — never hardcoded",
    "Auth boundaries documented in ARCHITECTURE.md before any code",
    "Least privilege by default — minimum permissions for every service account",
]

_SECURITY_EXTRA: dict[str, list[str]] = {
    "nextjs-supabase": [
        "RLS required on all Supabase tables — no table without a policy",
        "Supabase anon key must never grant write access without RLS",
    ],
    "nextjs-postgres": [
        "Database user must have minimal privileges — no superuser",
        "Connection string must be server-side only — never exposed to client",
    ],
    "fastapi-postgres": [
        "JWT signature verified on every protected route",
        "Database user must have minimal privileges — no superuser",
        "SQL queries must use parameterized statements — no string interpolation",
    ],
    "generic": [],
}

_SOVEREIGNTY_BASE: list[str] = [
    "Local development must work without cloud dependencies",
    "Database portability documented — schema must be exportable",
    "External providers identified and documented in ARCHITECTURE.md",
    "Exit strategy required before first production deploy",
]

_SOVEREIGNTY_EXTRA: dict[str, list[str]] = {
    "nextjs-supabase": [
        "Supabase is an external provider — document migration path"
        " to self-hosted Postgres",
        "Supabase Auth is an external dependency — document auth portability",
    ],
    "nextjs-postgres": [
        "PostgreSQL runs locally — maintain full database sovereignty",
        "Deployment must not be hardcoded to a single cloud provider",
    ],
    "fastapi-postgres": [
        "PostgreSQL runs locally — full database sovereignty maintained",
        "Alembic migrations are portable — document rollback procedures",
    ],
    "generic": [
        "Evaluate all external services before integrating",
        "Document portability assumptions for each dependency",
    ],
}

_TESTING_BASELINE: dict[str, list[str]] = {
    "web-app": [
        "Unit tests for all business logic",
        "Integration tests for API routes and data layer",
        "CI quality gate — tests must pass before merge",
        "End-to-end tests recommended before production deploy",
    ],
    "api": [
        "Unit tests for all business logic",
        "Integration tests for all endpoints",
        "Database integration tests with isolated test schema",
        "CI quality gate — tests must pass before merge",
    ],
    "internal-tool": [
        "Unit tests for all business logic",
        "Integration tests if applicable",
        "CI quality gate — tests must pass before merge",
    ],
}

_DEPLOYMENT_BASE: list[str] = [
    "Local run command required — project must run locally before cloud deploy",
    "Dockerfile recommended for reproducible deployments",
    "Cloud provider not hardcoded — all endpoints via environment variables",
    "CI/CD pipeline must not contain cloud credentials in code",
]

_DEPLOYMENT_EXTRA: dict[str, list[str]] = {
    "nextjs-supabase": [
        "Local run: npm run dev + Supabase local emulator (supabase start)",
        "Supabase project URL must be in .env — not hardcoded",
    ],
    "nextjs-postgres": [
        "Local run: npm run dev + local PostgreSQL (docker-compose recommended)",
        "Database connection string must be in .env — not hardcoded",
    ],
    "fastapi-postgres": [
        "Local run: uvicorn src.main:app --reload + local PostgreSQL",
        "docker-compose.yml recommended for local dev environment",
    ],
    "generic": [
        "Document local run command in README.md",
    ],
}

_NEXT_STEPS_BASE: dict[str, list[str]] = {
    "web-app": [
        "Run aeos build scaffold to generate the folder structure (coming soon)",
        "Create ARCHITECTURE.md with component diagram",
        "Fill .env.example with all required variables",
        "Set up CI pipeline with quality gate",
        "Document auth boundaries before writing any code",
    ],
    "api": [
        "Run aeos build scaffold to generate the folder structure (coming soon)",
        "Define OpenAPI spec before implementing endpoints",
        "Create ARCHITECTURE.md with API surface and data model",
        "Fill .env.example with all required variables",
        "Set up CI pipeline with quality gate",
    ],
    "internal-tool": [
        "Run aeos build scaffold to generate the folder structure (coming soon)",
        "Document users, roles, and access levels in ARCHITECTURE.md",
        "Fill .env.example with all required variables",
        "Set up CI pipeline with quality gate",
        "Define audit trail requirements before writing any code",
    ],
}

_NEXT_STEPS_EXTRA: dict[str, list[str]] = {
    "nextjs-supabase": [
        "Run aeos reclaim harden after first commit to audit sovereignty",
        "Set up Supabase local dev environment before adding RLS",
    ],
    "nextjs-postgres": [
        "Run aeos reclaim harden after first commit to audit sovereignty",
        "Initialize database migrations before writing any schema code",
    ],
    "fastapi-postgres": [
        "Run aeos reclaim harden after first commit to audit sovereignty",
        "Initialize Alembic before writing any models",
    ],
    "generic": [
        "Run aeos reclaim harden after first commit to audit sovereignty",
    ],
}


@dataclass
class BuildPlan:
    project_name: str
    project_type: str
    stack: str
    architecture_summary: str
    folder_structure: list[str]
    governance_files: list[str]
    security_baseline: list[str]
    sovereignty_baseline: list[str]
    testing_baseline: list[str]
    deployment_baseline: list[str]
    recommended_next_steps: list[str]
    command: str = field(default="build plan")
    read_only: bool = field(default=True)
    applied: bool = field(default=False)


def validate_project_type(project_type: str) -> None:
    if project_type not in VALID_TYPES:
        valid = ", ".join(sorted(VALID_TYPES))
        raise ValueError(f"Unknown project type '{project_type}'. Valid: {valid}.")


def validate_stack(stack: str) -> None:
    if stack not in VALID_STACKS:
        valid = ", ".join(sorted(VALID_STACKS))
        raise ValueError(f"Unknown stack '{stack}'. Valid: {valid}.")


def create_build_plan(name: str, project_type: str, stack: str) -> BuildPlan:
    validate_project_type(project_type)
    validate_stack(stack)

    arch = _ARCH_SUMMARY.get(
        (project_type, stack),
        f"{project_type} project with {stack} stack.",
    )
    folder = list(_FOLDER_STRUCTURE.get(stack, _FOLDER_STRUCTURE["generic"]))
    security = _SECURITY_BASE + _SECURITY_EXTRA.get(stack, [])
    sovereignty = _SOVEREIGNTY_BASE + _SOVEREIGNTY_EXTRA.get(stack, [])
    _fallback_test = _TESTING_BASELINE["internal-tool"]
    testing = list(_TESTING_BASELINE.get(project_type, _fallback_test))
    deployment = _DEPLOYMENT_BASE + _DEPLOYMENT_EXTRA.get(stack, [])
    _fallback_steps = _NEXT_STEPS_BASE["internal-tool"]
    _base_steps = _NEXT_STEPS_BASE.get(project_type, _fallback_steps)
    next_steps = _base_steps + _NEXT_STEPS_EXTRA.get(stack, [])

    return BuildPlan(
        project_name=name,
        project_type=project_type,
        stack=stack,
        architecture_summary=arch,
        folder_structure=folder,
        governance_files=list(_GOVERNANCE_FILES),
        security_baseline=security,
        sovereignty_baseline=sovereignty,
        testing_baseline=testing,
        deployment_baseline=deployment,
        recommended_next_steps=next_steps,
    )


def build_plan_to_dict(plan: BuildPlan) -> dict[str, object]:
    return {
        "command": plan.command,
        "read_only": plan.read_only,
        "applied": plan.applied,
        "project_name": plan.project_name,
        "project_type": plan.project_type,
        "stack": plan.stack,
        "architecture_summary": plan.architecture_summary,
        "folder_structure": plan.folder_structure,
        "governance_files": plan.governance_files,
        "security_baseline": plan.security_baseline,
        "sovereignty_baseline": plan.sovereignty_baseline,
        "testing_baseline": plan.testing_baseline,
        "deployment_baseline": plan.deployment_baseline,
        "recommended_next_steps": plan.recommended_next_steps,
    }
