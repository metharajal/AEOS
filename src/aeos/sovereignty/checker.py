import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from aeos.ai.config import read_ai_config

_SENSITIVE_VAR_PATTERNS: tuple[str, ...] = (
    "API_KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "SUPABASE_ANON_KEY",
    "SERVICE_ROLE_KEY",
    "DATABASE_URL",
    "POSTGRES_URL",
    "MONGO_URL",
    "STRIPE_SECRET",
    "NEXTAUTH_SECRET",
    "RESEND_API_KEY",
)

_DATABASE_ENV_VARS: tuple[str, ...] = (
    "SUPABASE_URL",
    "VITE_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "DATABASE_URL",
    "DIRECT_URL",
    "POSTGRES_URL",
    "MONGO_URL",
    "PLANETSCALE_URL",
    "NEON_DATABASE_URL",
)

_AUTH_ENV_VARS: tuple[str, ...] = (
    "NEXTAUTH_SECRET",
    "NEXTAUTH_URL",
    "AUTH0_SECRET",
    "AUTH0_BASE_URL",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "CLERK_SECRET_KEY",
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
)

_DATABASE_PACKAGES: dict[str, str] = {
    "@supabase/supabase-js": "Supabase (hosted database)",
    "firebase": "Firebase (hosted database/auth/storage)",
    "@neondatabase/serverless": "Neon (hosted PostgreSQL)",
    "planetscale": "PlanetScale (hosted MySQL)",
    "mongoose": "Mongoose — possible MongoDB Atlas (hosted)",
    "@prisma/client": "Prisma ORM (requires external DATABASE_URL)",
    "prisma": "Prisma CLI (requires external DATABASE_URL)",
    "drizzle-orm": "Drizzle ORM (requires external DATABASE_URL)",
    "mongodb": "MongoDB driver — possible MongoDB Atlas (hosted)",
}

_AUTH_WARNINGS: dict[str, str] = {
    "@clerk/nextjs": "Clerk (hosted auth)",
    "@clerk/clerk-react": "Clerk (hosted auth)",
    "@auth0/auth0-react": "Auth0 (hosted auth)",
    "@auth0/nextjs-auth0": "Auth0 (hosted auth)",
    "next-auth": "NextAuth.js (may depend on hosted OAuth providers)",
}

_STORAGE_PACKAGES: dict[str, str] = {
    "cloudinary": "Cloudinary (hosted storage)",
    "@aws-sdk/client-s3": "AWS S3 SDK (external storage)",
    "@cloudinary/react": "Cloudinary React SDK (hosted storage)",
}

_PAYMENT_PACKAGES: dict[str, str] = {
    "stripe": "Stripe (hosted payment processor)",
}

_SERVICES_PACKAGES: dict[str, str] = {
    "resend": "Resend (hosted email service)",
    "inngest": "Inngest (hosted event/queue service)",
    "convex": "Convex (hosted backend-as-a-service)",
}

_AI_SDK_PACKAGES: dict[str, str] = {
    "openai": "OpenAI SDK (frontier AI provider)",
    "@anthropic-ai/sdk": "Anthropic SDK (frontier AI provider)",
    "ai": "Vercel AI SDK (may call frontier providers)",
}

_HOSTING_FILES: dict[str, str] = {
    "vercel.json": "Vercel",
    "netlify.toml": "Netlify",
    ".railway.json": "Railway",
    "fly.toml": "Fly.io",
    "render.yaml": "Render",
    "firebase.json": "Firebase",
    "supabase/config.toml": "Supabase CLI",
}

_PORTABILITY_CHECKS: list[tuple[str, str, str]] = [
    (
        "Dockerfile",
        "Dockerfile",
        "Add a Dockerfile for portable containerized deployment",
    ),
    (
        "docker-compose.yml",
        "docker-compose.yml",
        "Add docker-compose.yml for a local reproducible environment",
    ),
    (
        "README.md",
        "README.md",
        "Add README.md documenting how to run the project locally",
    ),
    (
        "migrations",
        "migrations/",
        "Add database migrations to enable local database setup",
    ),
    (
        ".env.example",
        ".env.example",
        "Add .env.example documenting required environment variables",
    ),
]

_ENV_EXAMPLE_FILES: tuple[str, ...] = (
    ".env.example",
    ".env.template",
    ".env.sample",
)

_SCAN_DIRS: tuple[str, ...] = (
    "src",
    "app",
    "pages",
    "components",
    "lib",
    "server",
    "api",
    "utils",
)

_SCAN_EXTENSIONS: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx", ".py"})

_SCAN_EXCLUDES: frozenset[str] = frozenset(
    {
        "node_modules",
        ".git",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        ".next",
        "out",
        ".turbo",
    }
)

_SCAN_MAX_BYTES: int = 500 * 1024

_SOURCE_PATTERNS: list[tuple[str, str, str, str]] = [
    # (label, category, regex, recommendation)
    (
        "Supabase SDK usage",
        "source_scan",
        r"@supabase/supabase-js|createClient|\.supabase\.co",
        "Remove direct Supabase SDK usage — use a local PostgreSQL adapter",
    ),
    (
        "Firebase usage",
        "source_scan",
        r"firebase/app|initializeApp|firebaseio\.com|firebaseapp\.com",
        "Replace Firebase with a self-hosted alternative"
        " (e.g. Pocketbase, Supabase local)",
    ),
    (
        "Clerk auth usage",
        "source_scan",
        r"ClerkProvider|@clerk/",
        "Replace Clerk with a self-hosted auth solution (e.g. Keycloak, Lucia)",
    ),
    (
        "Auth0 usage",
        "source_scan",
        r"Auth0Provider|@auth0/",
        "Replace Auth0 with a self-hosted auth solution (e.g. Keycloak, Ory)",
    ),
    (
        "NextAuth usage",
        "source_scan",
        r"next-auth|useSession",
        "Ensure NextAuth is configured with self-hosted providers only",
    ),
    (
        "OpenAI SDK usage",
        "source_scan",
        r"""from openai import|from ['"]openai['"]|new OpenAI\(""",
        "Ensure OpenAI calls are governed by aeos.toml (require_human_approval = true)",
    ),
    (
        "Anthropic SDK usage",
        "source_scan",
        r"""@anthropic-ai/sdk|new Anthropic\(""",
        "Ensure Anthropic calls are governed by aeos.toml"
        " (require_human_approval = true)",
    ),
    (
        "Hosted deployment URL",
        "source_scan",
        r"\.vercel\.app|\.netlify\.app|\.railway\.app|\.render\.com",
        "Replace hardcoded hosted URLs with environment variables"
        " pointing to self-hosted services",
    ),
    (
        "MCP server reference",
        "source_scan",
        r"mcpServers",
        "Review MCP server references — prefer local or self-hosted MCP servers",
    ),
]


@dataclass
class SovereigntyFinding:
    category: str
    severity: str
    message: str
    location: str
    recommendation: str
    evidence: str = ""


@dataclass
class SovereigntyCheckResult:
    path: Path
    status: str
    findings: list[SovereigntyFinding] = field(default_factory=list)


def _read_npm_deps(path: Path) -> set[str]:
    pkg_path = path / "package.json"
    if not pkg_path.is_file():
        return set()
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    deps: set[str] = set()
    for section in ("dependencies", "devDependencies"):
        section_data = data.get(section, {})
        if isinstance(section_data, dict):
            deps.update(section_data.keys())
    return deps


def _read_npm_scripts(path: Path) -> set[str]:
    pkg_path = path / "package.json"
    if not pkg_path.is_file():
        return set()
    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        return set(scripts.keys())
    return set()


def _read_env_var_names(path: Path) -> set[str]:
    names: set[str] = set()
    for filename in _ENV_EXAMPLE_FILES:
        env_path = path / filename
        if not env_path.is_file():
            continue
        try:
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                name = stripped.split("=")[0].strip()
                if name:
                    names.add(name)
        except OSError:
            continue
    return names


def _env_file_for_var(path: Path, var: str) -> str:
    for filename in _ENV_EXAMPLE_FILES:
        env_path = path / filename
        if not env_path.is_file():
            continue
        try:
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                name = raw.strip().split("=")[0].strip()
                if name == var:
                    return filename
        except OSError:
            continue
    return ".env.example"


def _dot_env_unprotected(path: Path) -> bool:
    if not (path / ".env").is_file():
        return False
    gitignore = path / ".gitignore"
    if not gitignore.is_file():
        return True
    try:
        for raw in gitignore.read_text(encoding="utf-8").splitlines():
            if raw.strip() in (".env", "/.env", ".env.*", "*.env"):
                return False
        return True
    except OSError:
        return False


def _path_is_excluded(p: Path) -> bool:
    return any(part in _SCAN_EXCLUDES for part in p.parts)


def _scan_source_code(path: Path) -> list[SovereigntyFinding]:
    compiled = [
        (label, category, re.compile(pattern), recommendation)
        for label, category, pattern, recommendation in _SOURCE_PATTERNS
    ]

    # matches[label] = list of (relative_path_str, line_number)
    matches: dict[str, list[tuple[str, int]]] = {
        label: [] for label, _, _, _ in _SOURCE_PATTERNS
    }

    for dir_name in _SCAN_DIRS:
        scan_dir = path / dir_name
        if not scan_dir.is_dir():
            continue
        for file_path in scan_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if _path_is_excluded(file_path.relative_to(path)):
                continue
            if file_path.suffix not in _SCAN_EXTENSIONS:
                continue
            if file_path.stat().st_size > _SCAN_MAX_BYTES:
                continue
            try:
                lines = file_path.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except OSError:
                continue
            rel = str(file_path.relative_to(path))
            for lineno, line in enumerate(lines, start=1):
                for label, _cat, pattern, _rec in compiled:
                    if pattern.search(line):
                        matches[label].append((rel, lineno))

    findings: list[SovereigntyFinding] = []
    for label, category, _pattern, recommendation in compiled:
        hits = matches[label]
        if not hits:
            continue
        first_file, first_line = hits[0]
        file_count = len({f for f, _ in hits})
        evidence = f"{file_count} file(s), first match: {first_file}:{first_line}"
        findings.append(
            SovereigntyFinding(
                category=category,
                severity="WARNING",
                message=f"{label} detected in source code",
                location=first_file,
                recommendation=recommendation,
                evidence=evidence,
            )
        )
    return findings


def _check_ai(path: Path) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    config = read_ai_config(path)
    if config is None:
        findings.append(
            SovereigntyFinding(
                category="ai",
                severity="WARNING",
                message="aeos.toml not found — AI sovereignty cannot be verified",
                location="aeos.toml",
                recommendation=(
                    "Run 'aeos init' to create a sovereign AI configuration"
                ),
            )
        )
        return findings
    if config.mode != "local-first":
        findings.append(
            SovereigntyFinding(
                category="ai",
                severity="WARNING",
                message=f"AI mode is '{config.mode}', not local-first",
                location="aeos.toml",
                recommendation="Set ai.mode = local-first in aeos.toml",
            )
        )
    if not config.require_human_approval:
        findings.append(
            SovereigntyFinding(
                category="ai",
                severity="WARNING",
                message="Frontier AI can be called without human approval",
                location="aeos.toml",
                recommendation=("Set ai.require_human_approval = true in aeos.toml"),
            )
        )
    return findings


def _check_database(
    path: Path, npm_deps: set[str], env_vars: set[str]
) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for pkg, label in _DATABASE_PACKAGES.items():
        if pkg in npm_deps:
            findings.append(
                SovereigntyFinding(
                    category="database",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Consider a local PostgreSQL or SQLite alternative"
                        " with a migration strategy"
                    ),
                )
            )
    for var in _DATABASE_ENV_VARS:
        if var in env_vars:
            loc = _env_file_for_var(path, var)
            findings.append(
                SovereigntyFinding(
                    category="database",
                    severity="WARNING",
                    message=f"Database variable '{var}' detected",
                    location=loc,
                    recommendation=(
                        "Verify this points to a local or self-hosted database,"
                        " not a hosted cloud service"
                    ),
                )
            )
    return findings


def _check_auth(
    path: Path, npm_deps: set[str], env_vars: set[str]
) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    seen: set[str] = set()
    for pkg, label in _AUTH_WARNINGS.items():
        if pkg in npm_deps and label not in seen:
            seen.add(label)
            findings.append(
                SovereigntyFinding(
                    category="auth",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Consider a self-hosted auth solution"
                        " (e.g. Keycloak, Ory, Lucia)"
                    ),
                )
            )
    for var in _AUTH_ENV_VARS:
        if var in env_vars:
            loc = _env_file_for_var(path, var)
            findings.append(
                SovereigntyFinding(
                    category="auth",
                    severity="WARNING",
                    message=f"Auth variable '{var}' detected",
                    location=loc,
                    recommendation=(
                        "Verify this is configured for a self-hosted auth provider"
                    ),
                )
            )
    return findings


def _check_storage(npm_deps: set[str]) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for pkg, label in _STORAGE_PACKAGES.items():
        if pkg in npm_deps:
            findings.append(
                SovereigntyFinding(
                    category="storage",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Consider a self-hosted storage solution"
                        " (e.g. MinIO, local filesystem)"
                    ),
                )
            )
    return findings


def _check_payment(npm_deps: set[str]) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for pkg, label in _PAYMENT_PACKAGES.items():
        if pkg in npm_deps:
            findings.append(
                SovereigntyFinding(
                    category="payment",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Ensure Stripe keys are managed via environment variables"
                        " and never committed"
                    ),
                )
            )
    return findings


def _check_services(npm_deps: set[str]) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for pkg, label in _SERVICES_PACKAGES.items():
        if pkg in npm_deps:
            findings.append(
                SovereigntyFinding(
                    category="services",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Consider a self-hosted or local alternative"
                        " for this external service"
                    ),
                )
            )
    return findings


def _check_ai_sdk(npm_deps: set[str]) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for pkg, label in _AI_SDK_PACKAGES.items():
        if pkg in npm_deps:
            findings.append(
                SovereigntyFinding(
                    category="ai_sdk",
                    severity="WARNING",
                    message=f"{label} detected",
                    location="package.json",
                    recommendation=(
                        "Ensure frontier AI calls are governed by aeos.toml"
                        " (require_human_approval = true)"
                    ),
                )
            )
    return findings


def _check_hosting(path: Path) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for filename, platform in _HOSTING_FILES.items():
        if (path / filename).is_file():
            findings.append(
                SovereigntyFinding(
                    category="hosting",
                    severity="WARNING",
                    message=f"{platform} configuration detected",
                    location=filename,
                    recommendation=(
                        f"Ensure the project can be deployed without {platform}"
                        " — add Dockerfile or docker-compose.yml"
                    ),
                )
            )
    return findings


def _check_mcp(path: Path) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    cursor_mcp = path / ".cursor" / "mcp.json"
    if cursor_mcp.is_file():
        try:
            data = json.loads(cursor_mcp.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "mcpServers" in data:
                findings.append(
                    SovereigntyFinding(
                        category="mcp",
                        severity="WARNING",
                        message="MCP server configuration detected",
                        location=".cursor/mcp.json",
                        recommendation=(
                            "Review external MCP connectors"
                            " — prefer local or self-hosted MCP servers"
                        ),
                    )
                )
        except (json.JSONDecodeError, OSError):
            pass
    for json_file in path.glob("*.json"):
        if json_file.name == "package.json":
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "mcpServers" in data:
                findings.append(
                    SovereigntyFinding(
                        category="mcp",
                        severity="WARNING",
                        message=(
                            f"MCP server configuration detected in '{json_file.name}'"
                        ),
                        location=json_file.name,
                        recommendation=(
                            "Review external MCP connectors"
                            " — prefer local or self-hosted MCP servers"
                        ),
                    )
                )
        except (json.JSONDecodeError, OSError):
            continue
    return findings


def _check_secrets(path: Path, env_vars: set[str]) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    if _dot_env_unprotected(path):
        findings.append(
            SovereigntyFinding(
                category="secrets",
                severity="ERROR",
                message=".env file detected without .gitignore protection",
                location=".env",
                recommendation=(
                    "Add '.env' to .gitignore immediately to prevent secret exposure"
                ),
            )
        )
    for var in env_vars:
        for pattern in _SENSITIVE_VAR_PATTERNS:
            if pattern in var:
                loc = _env_file_for_var(path, var)
                findings.append(
                    SovereigntyFinding(
                        category="secrets",
                        severity="WARNING",
                        message=f"Sensitive variable '{var}' found in env file",
                        location=loc,
                        recommendation=(
                            "Ensure this variable is never committed"
                            " with a real value — keep it in .gitignore"
                        ),
                    )
                )
                break
    return findings


def _check_portability(path: Path) -> list[SovereigntyFinding]:
    findings: list[SovereigntyFinding] = []
    for item, label, recommendation in _PORTABILITY_CHECKS:
        target = path / item
        exists = target.is_file() or target.is_dir()
        if item == "docker-compose.yml" and not exists:
            exists = (path / "docker-compose.yaml").is_file() or (
                path / "compose.yml"
            ).is_file()
        if item == "migrations" and not exists:
            exists = (path / "prisma" / "migrations").is_dir() or (
                path / "drizzle"
            ).is_dir()
        if not exists:
            findings.append(
                SovereigntyFinding(
                    category="portability",
                    severity="WARNING",
                    message=f"{label} not found",
                    location=label,
                    recommendation=recommendation,
                )
            )
    pkg_path = path / "package.json"
    if pkg_path.is_file():
        scripts = _read_npm_scripts(path)
        if "dev" not in scripts:
            findings.append(
                SovereigntyFinding(
                    category="portability",
                    severity="WARNING",
                    message="No local dev script found in package.json",
                    location="package.json",
                    recommendation=(
                        "Add a 'dev' script to package.json to enable local development"
                    ),
                )
            )
    return findings


def _compute_status(findings: list[SovereigntyFinding]) -> str:
    if any(f.severity == "ERROR" for f in findings):
        return "ERROR"
    if any(f.severity == "WARNING" for f in findings):
        return "WARNING"
    return "OK"


def run_sovereignty_check(path: Path) -> SovereigntyCheckResult:
    npm_deps = _read_npm_deps(path)
    env_vars = _read_env_var_names(path)

    findings: list[SovereigntyFinding] = []
    findings.extend(_check_ai(path))
    findings.extend(_check_database(path, npm_deps, env_vars))
    findings.extend(_check_auth(path, npm_deps, env_vars))
    findings.extend(_check_storage(npm_deps))
    findings.extend(_check_payment(npm_deps))
    findings.extend(_check_services(npm_deps))
    findings.extend(_check_ai_sdk(npm_deps))
    findings.extend(_check_hosting(path))
    findings.extend(_check_mcp(path))
    findings.extend(_check_secrets(path, env_vars))
    findings.extend(_check_portability(path))
    findings.extend(_scan_source_code(path))

    return SovereigntyCheckResult(
        path=path.resolve(),
        status=_compute_status(findings),
        findings=findings,
    )
