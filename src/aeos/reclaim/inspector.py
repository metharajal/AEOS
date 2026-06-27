"""
AEOS Reclaim Inspector — read-only, no network, no secret values.

Produces a control map and exit options for AI/no-code/low-code projects.
Evidence fields contain only file:line references — never variable values.
"""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FILE_SIZE = 100 * 1024  # 100 KB

_VAR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")

_GITIGNORE_ENV_TOKENS: frozenset[str] = frozenset({".env", ".env.*", "*.env", "/.env"})

_LOCAL_BACKEND_DIRS: frozenset[str] = frozenset({"server", "api", "backend"})
_LOCAL_SCHEMA_DIRS: frozenset[str] = frozenset({"prisma", "drizzle", "migrations"})

_SUPABASE_CLIENT_DEPS: frozenset[str] = frozenset(
    {
        "@supabase/supabase-js",
        "@supabase/ssr",
        "@supabase/auth-helpers-nextjs",
        "@supabase/auth-helpers-react",
    }
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReclaimGenerator:
    name: str  # "lovable" | "bolt" | "replit"
    detected: bool
    evidence: str  # file:line reference — never content


@dataclass
class ReclaimProvider:
    name: str  # "supabase" | "vercel" | "firebase" | "clerk"
    detected: bool
    roles: list[str]
    evidence: str  # file:line reference — never content


@dataclass
class ReclaimControlMap:
    frontend_code: str  # "controlled" | "partial" | "unknown"
    backend_runtime: str  # "controlled" | "likely_external" | "unknown"
    database_schema: str  # "controlled" | "partial" | "missing" | "unknown"
    auth: str  # "controlled" | "external" | "likely_external" | "unknown"
    storage: str  # "controlled" | "likely_external" | "unknown"
    secrets_control: str  # "local" | "external" | "unknown"
    secrets_exposure: str  # "none" | "risk" | "confirmed"
    deployment: str  # "controlled" | "external" | "likely_external" | "unknown"
    portability: str  # "strong" | "partial" | "weak"


@dataclass
class ReclaimMissingAsset:
    asset: str
    impact: str
    present: bool = False


@dataclass
class ReclaimExitOption:
    id: str
    label: str
    complexity: str  # "low"|"medium"|"high"|"very_high"|"extreme"
    sovereignty: str  # "partial"|"medium"|"high"|"very_high"|"maximum"
    advantages: list[str]
    risks: list[str]
    next_action: str


@dataclass
class ReclaimInspectResult:
    path: Path
    status: str  # "OK" | "WARNING" | "ERROR"
    generators: list[ReclaimGenerator] = field(default_factory=list)
    providers: list[ReclaimProvider] = field(default_factory=list)
    control_map: ReclaimControlMap = field(
        default_factory=lambda: ReclaimControlMap(
            frontend_code="unknown",
            backend_runtime="unknown",
            database_schema="unknown",
            auth="unknown",
            storage="unknown",
            secrets_control="unknown",
            secrets_exposure="none",
            deployment="unknown",
            portability="partial",
        )
    )
    missing_assets: list[ReclaimMissingAsset] = field(default_factory=list)
    exit_options: list[ReclaimExitOption] = field(default_factory=list)
    requires_manual_action: bool = False
    recommended_next_action: str = ""


# ---------------------------------------------------------------------------
# Helpers — read-only, never reads secret values
# ---------------------------------------------------------------------------


def _extract_env_var_names(env_file: Path) -> list[str]:
    """Extract variable names only — never values. Skips files > 100 KB."""
    if not env_file.is_file():
        return []
    if env_file.stat().st_size > _MAX_FILE_SIZE:
        return []
    names: list[str] = []
    with env_file.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _VAR_RE.match(line)
            if m:
                names.append(m.group(1))
    return names


def _get_package_deps(path: Path) -> set[str]:
    pkg = path / "package.json"
    if not pkg.is_file() or pkg.stat().st_size > _MAX_FILE_SIZE:
        return set()
    try:
        data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
        return set(
            {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }.keys()
        )
    except (json.JSONDecodeError, OSError):
        return set()


def _check_gitignore_protects(path: Path) -> bool:
    gitignore = path / ".gitignore"
    if not gitignore.is_file():
        return False
    try:
        lines = {
            line.strip()
            for line in gitignore.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        }
        return bool(lines & _GITIGNORE_ENV_TOKENS)
    except OSError:
        return False


def _check_env_git_history(path: Path) -> tuple[bool, bool]:
    """Return (env_in_history, env_currently_tracked). Read-only git calls."""
    git = shutil.which("git")
    if not git:
        return False, False
    try:
        probe = subprocess.run(  # noqa: S603
            [git, "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if probe.returncode != 0:
            return False, False
    except (OSError, subprocess.TimeoutExpired):
        return False, False
    try:
        log = subprocess.run(  # noqa: S603
            [git, "-C", str(path), "log", "--oneline", "--", ".env"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        in_history = bool(log.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        in_history = False
    try:
        ls = subprocess.run(  # noqa: S603
            [git, "-C", str(path), "ls-files", ".env"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        in_tracking = bool(ls.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        in_tracking = False
    return in_history, in_tracking


# ---------------------------------------------------------------------------
# Generator detection
# ---------------------------------------------------------------------------


def _detect_generators(path: Path) -> list[ReclaimGenerator]:
    env_names: list[str] = []
    for env_file in (path / ".env", path / ".env.example"):
        env_names.extend(_extract_env_var_names(env_file))

    # --- Lovable ---
    lovable_evidence = ""
    if (path / ".lovable").is_dir():
        lovable_evidence = ".lovable/:1"
    elif (path / "src" / "integrations" / "supabase").is_dir():
        lovable_evidence = "src/integrations/supabase/:1"
    else:
        for f in ("lovable.config.ts", "lovable.config.js", "lovable.config.json"):
            if (path / f).is_file():
                lovable_evidence = f"{f}:1"
                break
        if not lovable_evidence:
            for name in env_names:
                if name.startswith("LOVABLE_"):
                    lovable_evidence = f".env:{name}"
                    break

    # --- Bolt ---
    bolt_evidence = ""
    if (path / ".bolt").is_dir():
        bolt_evidence = ".bolt/:1"
    else:
        for name in env_names:
            if name.startswith("BOLT_"):
                bolt_evidence = f".env:{name}"
                break

    # --- Replit ---
    replit_evidence = ""
    for fname in (".replit", "replit.nix"):
        if (path / fname).is_file():
            replit_evidence = f"{fname}:1"
            break

    return [
        ReclaimGenerator(
            name="lovable",
            detected=bool(lovable_evidence),
            evidence=lovable_evidence,
        ),
        ReclaimGenerator(
            name="bolt",
            detected=bool(bolt_evidence),
            evidence=bolt_evidence,
        ),
        ReclaimGenerator(
            name="replit",
            detected=bool(replit_evidence),
            evidence=replit_evidence,
        ),
    ]


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------


def _detect_providers(path: Path) -> list[ReclaimProvider]:
    deps = _get_package_deps(path)
    env_names: set[str] = set()
    for env_file in (path / ".env", path / ".env.example"):
        env_names.update(_extract_env_var_names(env_file))

    # --- Supabase ---
    supabase_evidence = ""
    supabase_roles: list[str] = []

    if (path / "supabase" / "config.toml").is_file():
        supabase_evidence = "supabase/config.toml:1"
        if "database" not in supabase_roles:
            supabase_roles.append("database")
    elif (path / "supabase" / "migrations").is_dir():
        supabase_evidence = "supabase/migrations/:1"
        if "database" not in supabase_roles:
            supabase_roles.append("database")

    client_dep = next((d for d in _SUPABASE_CLIENT_DEPS if d in deps), None)
    if client_dep:
        if not supabase_evidence:
            supabase_evidence = f"package.json:{client_dep}"
        if "database" not in supabase_roles:
            supabase_roles.append("database")
        if "auth" not in supabase_roles:
            supabase_roles.append("auth")

    if (path / "src" / "integrations" / "supabase").is_dir():
        if not supabase_evidence:
            supabase_evidence = "src/integrations/supabase/:1"
        if "database" not in supabase_roles:
            supabase_roles.append("database")
        if "auth" not in supabase_roles:
            supabase_roles.append("auth")

    if not supabase_evidence:
        for name in env_names:
            if (
                name.startswith("SUPABASE_")
                or name.startswith("VITE_SUPABASE_")
                or name.startswith("NEXT_PUBLIC_SUPABASE_")
            ):
                supabase_evidence = f".env:{name}"
                if "database" not in supabase_roles:
                    supabase_roles.append("database")
                break

    # --- Vercel ---
    vercel_evidence = ""
    if (path / "vercel.json").is_file():
        vercel_evidence = "vercel.json:1"
    elif (path / ".vercel").is_dir():
        vercel_evidence = ".vercel/:1"
    else:
        for name in env_names:
            if name.startswith("VERCEL_"):
                vercel_evidence = f".env:{name}"
                break

    # --- Firebase ---
    firebase_evidence = ""
    if (path / "firebase.json").is_file():
        firebase_evidence = "firebase.json:1"
    elif (path / ".firebaserc").is_file():
        firebase_evidence = ".firebaserc:1"
    else:
        fb_dep = next((d for d in deps if d.startswith("firebase")), None)
        if fb_dep:
            firebase_evidence = f"package.json:{fb_dep}"
        else:
            for name in env_names:
                if (
                    name.startswith("FIREBASE_")
                    or name.startswith("NEXT_PUBLIC_FIREBASE_")
                    or name.startswith("VITE_FIREBASE_")
                ):
                    firebase_evidence = f".env:{name}"
                    break

    # --- Clerk ---
    clerk_evidence = ""
    clerk_dep = next((d for d in deps if d.startswith("@clerk/")), None)
    if clerk_dep:
        clerk_evidence = f"package.json:{clerk_dep}"
    else:
        for name in env_names:
            if name.startswith("CLERK_") or name.startswith("NEXT_PUBLIC_CLERK_"):
                clerk_evidence = f".env:{name}"
                break

    return [
        ReclaimProvider(
            name="supabase",
            detected=bool(supabase_evidence),
            roles=supabase_roles,
            evidence=supabase_evidence,
        ),
        ReclaimProvider(
            name="vercel",
            detected=bool(vercel_evidence),
            roles=["deployment"] if vercel_evidence else [],
            evidence=vercel_evidence,
        ),
        ReclaimProvider(
            name="firebase",
            detected=bool(firebase_evidence),
            roles=["auth", "database", "storage"] if firebase_evidence else [],
            evidence=firebase_evidence,
        ),
        ReclaimProvider(
            name="clerk",
            detected=bool(clerk_evidence),
            roles=["auth"] if clerk_evidence else [],
            evidence=clerk_evidence,
        ),
    ]


# ---------------------------------------------------------------------------
# Control map
# ---------------------------------------------------------------------------


def _build_control_map(
    path: Path,
    generators: list[ReclaimGenerator],
    providers: list[ReclaimProvider],
    in_env_history: bool,
    env_currently_tracked: bool,
    gitignore_protects: bool,
) -> ReclaimControlMap:
    has_lovable = any(g.name == "lovable" and g.detected for g in generators)
    has_bolt = any(g.name == "bolt" and g.detected for g in generators)
    has_generator = has_lovable or has_bolt

    def _provider(name: str) -> ReclaimProvider | None:
        return next((p for p in providers if p.name == name), None)

    sup = _provider("supabase")
    verc = _provider("vercel")
    fb = _provider("firebase")
    clerk = _provider("clerk")

    supabase_detected = sup is not None and sup.detected
    vercel_detected = verc is not None and verc.detected
    firebase_detected = fb is not None and fb.detected
    clerk_detected = clerk is not None and clerk.detected

    has_external_provider = supabase_detected or vercel_detected or firebase_detected

    # frontend_code
    has_src = (path / "src").is_dir()
    if has_generator and has_src:
        frontend_code = "partial"
    elif has_src:
        frontend_code = "controlled"
    else:
        frontend_code = "unknown"

    # backend_runtime
    has_local_backend = any((path / d).is_dir() for d in _LOCAL_BACKEND_DIRS)
    if has_local_backend:
        backend_runtime = "controlled"
    elif has_external_provider:
        backend_runtime = "likely_external"
    else:
        backend_runtime = "unknown"

    # database_schema
    has_supabase_migrations = (path / "supabase" / "migrations").is_dir()
    has_local_schema = any((path / d).is_dir() for d in _LOCAL_SCHEMA_DIRS)
    if has_local_schema:
        database_schema = "controlled"
    elif has_supabase_migrations:
        database_schema = "partial"
    elif supabase_detected or firebase_detected:
        database_schema = "unknown"
    else:
        database_schema = "missing"

    # auth — clerk = external (certain), firebase = external, supabase = likely_external
    supabase_has_auth = sup is not None and sup.detected and "auth" in sup.roles
    if clerk_detected or firebase_detected:
        auth = "external"
    elif supabase_has_auth:
        auth = "likely_external"
    else:
        auth = "unknown"

    # storage
    if firebase_detected or supabase_detected:
        storage = "likely_external"
    else:
        storage = "unknown"

    # secrets_control (independent of exposure history)
    if gitignore_protects and not env_currently_tracked:
        secrets_control = "local"
    elif env_currently_tracked:
        secrets_control = "external"
    else:
        secrets_control = "unknown"

    # secrets_exposure (about past/current exposure in git)
    if in_env_history:
        secrets_exposure = "confirmed"
    elif env_currently_tracked:
        secrets_exposure = "risk"
    else:
        secrets_exposure = "none"

    # deployment
    has_dockerfile = (path / "Dockerfile").is_file()
    has_compose = (path / "docker-compose.yml").is_file() or (
        path / "docker-compose.yaml"
    ).is_file()
    if has_dockerfile or has_compose:
        deployment = "controlled"
    elif vercel_detected or firebase_detected:
        deployment = "external"
    elif supabase_detected:
        deployment = "likely_external"
    else:
        deployment = "unknown"

    # portability
    is_portable = (
        (has_dockerfile or has_compose) and has_local_backend and has_local_schema
    )
    is_very_external = (
        not has_local_backend and not has_local_schema and has_external_provider
    )
    if is_portable:
        portability = "strong"
    elif is_very_external:
        portability = "weak"
    else:
        portability = "partial"

    return ReclaimControlMap(
        frontend_code=frontend_code,
        backend_runtime=backend_runtime,
        database_schema=database_schema,
        auth=auth,
        storage=storage,
        secrets_control=secrets_control,
        secrets_exposure=secrets_exposure,
        deployment=deployment,
        portability=portability,
    )


# ---------------------------------------------------------------------------
# Missing assets
# ---------------------------------------------------------------------------


def _detect_missing_assets(path: Path) -> list[ReclaimMissingAsset]:
    has_compose = (path / "docker-compose.yml").is_file() or (
        path / "docker-compose.yaml"
    ).is_file()
    has_local_backend = any((path / d).is_dir() for d in _LOCAL_BACKEND_DIRS)
    has_local_schema = any((path / d).is_dir() for d in _LOCAL_SCHEMA_DIRS)
    return [
        ReclaimMissingAsset(
            asset="Dockerfile",
            impact="no portable containerized deployment",
            present=(path / "Dockerfile").is_file(),
        ),
        ReclaimMissingAsset(
            asset="docker-compose.yml",
            impact="no local reproducible stack",
            present=has_compose,
        ),
        ReclaimMissingAsset(
            asset="server/ or api/",
            impact="no local backend runtime",
            present=has_local_backend,
        ),
        ReclaimMissingAsset(
            asset="local DB migrations",
            impact="no portable database schema",
            present=has_local_schema,
        ),
        ReclaimMissingAsset(
            asset="supabase/functions/",
            impact="no local edge functions",
            present=(path / "supabase" / "functions").is_dir(),
        ),
        ReclaimMissingAsset(
            asset=".env.example",
            impact="environment variables not documented",
            present=(path / ".env.example").is_file(),
        ),
    ]


# ---------------------------------------------------------------------------
# Exit options (always 5, in fixed order)
# ---------------------------------------------------------------------------


def _build_exit_options(
    control_map: ReclaimControlMap,
    providers: list[ReclaimProvider],
) -> list[ReclaimExitOption]:
    supabase_detected = any(p.name == "supabase" and p.detected for p in providers)

    if control_map.secrets_exposure == "confirmed":
        next_1 = "Rotate exposed keys · run `aeos supabase check --path .`"
    elif control_map.secrets_exposure == "risk":
        next_1 = "Remove .env from tracking · rotate keys · run `aeos supabase check`"
    elif supabase_detected:
        next_1 = "Run `aeos supabase check --path <project>` · verify RLS"
    else:
        next_1 = "Review provider config · ensure secrets are gitignored"

    return [
        ReclaimExitOption(
            id="secure_in_place",
            label="Stay on current provider but secure",
            complexity="low",
            sovereignty="partial",
            advantages=[
                "no migration required",
                "immediate improvement",
                "zero infrastructure cost",
            ],
            risks=[
                "continued vendor lock-in",
                "keys must be rotated manually",
            ],
            next_action=next_1,
        ),
        ReclaimExitOption(
            id="own_supabase_cloud",
            label="Migrate to own Supabase Cloud project",
            complexity="medium",
            sovereignty="medium",
            advantages=[
                "you own the project",
                "full Dashboard access",
                "minimal migration effort",
            ],
            risks=[
                "still cloud-dependent",
                "direct billing",
                "data export required",
            ],
            next_action=("Export schema · create new Supabase project · update .env"),
        ),
        ReclaimExitOption(
            id="self_hosted_supabase",
            label="Migrate to self-hosted Supabase",
            complexity="high",
            sovereignty="high",
            advantages=[
                "full infrastructure control",
                "same Supabase API surface",
                "data on-premises",
            ],
            risks=[
                "operational burden",
                "no managed Dashboard",
                "updates and backups required",
            ],
            next_action=("Add docker-compose.yml with Supabase stack · migrate data"),
        ),
        ReclaimExitOption(
            id="postgres_open_backend",
            label="Migrate to PostgreSQL + open backend",
            complexity="very_high",
            sovereignty="very_high",
            advantages=[
                "zero Supabase dependency",
                "standard open-source stack",
                "maximum portability",
            ],
            risks=[
                "API layer rewrite required",
                "auth migration required",
                "significant engineering effort",
            ],
            next_action=(
                "Extract SQL schema · write API layer · replace Supabase client"
            ),
        ),
        ReclaimExitOption(
            id="full_sovereign_rebuild",
            label="Full sovereign rebuild",
            complexity="extreme",
            sovereignty="maximum",
            advantages=[
                "total control",
                "local-first from day zero",
                "zero legacy debt",
            ],
            risks=[
                "maximum cost and delay",
                "UX gap during rebuild",
            ],
            next_action=(
                "Define target architecture · `aeos init` · progressive migration"
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Status and recommended action
# ---------------------------------------------------------------------------


def _compute_status(
    control_map: ReclaimControlMap,
    generators: list[ReclaimGenerator],
) -> str:
    if control_map.secrets_exposure in ("confirmed", "risk"):
        return "ERROR"
    any_generator = any(g.detected for g in generators)
    if any_generator or control_map.portability in ("weak", "partial"):
        return "WARNING"
    return "OK"


def _recommended_next_action(
    control_map: ReclaimControlMap,
    providers: list[ReclaimProvider],
) -> str:
    if control_map.secrets_exposure == "confirmed":
        return "Rotate exposed keys immediately · run `aeos supabase check --path .`"
    if control_map.secrets_exposure == "risk":
        return "Remove .env from Git tracking · rotate keys"
    if control_map.portability == "weak":
        return "Start with Option 1: secure in place · then plan migration"
    if any(p.name == "supabase" and p.detected for p in providers):
        return "Run `aeos supabase check --path <project>` for detailed analysis"
    return "Review provider configuration · ensure all secrets are gitignored"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_reclaim_inspect(path: Path) -> ReclaimInspectResult:
    """Inspect a project for reclaim opportunities. Read-only, no network."""
    resolved = path.resolve()
    generators = _detect_generators(resolved)
    providers = _detect_providers(resolved)
    in_env_history, env_currently_tracked = _check_env_git_history(resolved)
    gitignore_protects = _check_gitignore_protects(resolved)
    control_map = _build_control_map(
        resolved,
        generators,
        providers,
        in_env_history,
        env_currently_tracked,
        gitignore_protects,
    )
    missing_assets = _detect_missing_assets(resolved)
    exit_options = _build_exit_options(control_map, providers)
    status = _compute_status(control_map, generators)
    recommended = _recommended_next_action(control_map, providers)
    requires_manual = (
        control_map.secrets_exposure != "none"
        or control_map.portability == "weak"
        or any(g.detected for g in generators)
    )
    return ReclaimInspectResult(
        path=resolved,
        status=status,
        generators=generators,
        providers=providers,
        control_map=control_map,
        missing_assets=missing_assets,
        exit_options=exit_options,
        requires_manual_action=requires_manual,
        recommended_next_action=recommended,
    )
