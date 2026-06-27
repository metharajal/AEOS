import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KEY_TYPE_MAP: dict[str, str] = {
    "VITE_SUPABASE_PUBLISHABLE_KEY": "publishable",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "publishable",
    "SUPABASE_ANON_KEY": "publishable",
    "SUPABASE_SERVICE_ROLE_KEY": "secret",
    "SUPABASE_SECRET_KEY": "secret",
    "VITE_SUPABASE_URL": "url",
    "NEXT_PUBLIC_SUPABASE_URL": "url",
    "SUPABASE_URL": "url",
    "VITE_SUPABASE_PROJECT_ID": "project_id",
    "SUPABASE_PROJECT_ID": "project_id",
}

_PUBLISHABLE_RE = re.compile(r"^sb_publishable_", re.IGNORECASE)
_SECRET_RE = re.compile(r"^sb_secret_", re.IGNORECASE)
_VAR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
_SUPABASE_VAR_RE = re.compile(r"supabase", re.IGNORECASE)
_RLS_RE = re.compile(r"\bENABLE\s+ROW\s+LEVEL\s+SECURITY\b", re.IGNORECASE)
_POLICY_RE = re.compile(r"\bCREATE\s+POLICY\b", re.IGNORECASE)

_SDK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"""from\s+['"]@supabase/supabase-js['"]"""),
    re.compile(r"""require\s*\(\s*['"]@supabase/supabase-js['"]"""),
    re.compile(r"""from\s+['"]@supabase/ssr['"]"""),
    re.compile(r"""from\s+['"]@supabase/auth-helpers"""),
]

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
_SCAN_EXTENSIONS: frozenset[str] = frozenset(
    {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}
)
_SKIP_DIRS: frozenset[str] = frozenset(
    {"node_modules", ".git", "dist", "build", ".next", "__pycache__", ".venv"}
)
_GITIGNORE_ENV_TOKENS: frozenset[str] = frozenset({".env", ".env.*", "*.env", "/.env"})
_MAX_FILE_SIZE = 100 * 1024  # 100 KB

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SupabaseKeyRisk:
    variable_name: str
    key_type: str  # "publishable" | "secret" | "url" | "project_id" | "unknown"
    severity: str  # "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    in_git_history: bool
    in_current_tracking: bool


@dataclass
class SupabaseRLSEvidence:
    migrations_present: bool
    rls_enable_found: bool
    policies_found: bool
    evidence: str  # file:line references only — never SQL content


@dataclass
class SupabaseLocalFixes:
    gitignore_protects_env: bool
    env_not_tracked: bool
    env_example_exists: bool


@dataclass
class SupabaseRemediationStep:
    priority: int
    action: str
    status: str  # "done" | "required" | "manual"
    location: str


@dataclass
class SupabaseCheckResult:
    path: Path
    status: str  # "OK" | "WARNING" | "ERROR" | "CRITICAL"
    supabase_detected: bool
    key_risks: list[SupabaseKeyRisk] = field(default_factory=list)
    rls_evidence: SupabaseRLSEvidence = field(
        default_factory=lambda: SupabaseRLSEvidence(
            migrations_present=False,
            rls_enable_found=False,
            policies_found=False,
            evidence="",
        )
    )
    local_fixes: SupabaseLocalFixes = field(
        default_factory=lambda: SupabaseLocalFixes(
            gitignore_protects_env=False,
            env_not_tracked=False,
            env_example_exists=False,
        )
    )
    remediation_steps: list[SupabaseRemediationStep] = field(default_factory=list)
    requires_manual_action: bool = False


# ---------------------------------------------------------------------------
# Key classification
# ---------------------------------------------------------------------------


def _classify_key(name: str) -> str:
    if name in _KEY_TYPE_MAP:
        return _KEY_TYPE_MAP[name]
    if _SECRET_RE.match(name):
        return "secret"
    if _PUBLISHABLE_RE.match(name):
        return "publishable"
    return "unknown"


def _compute_key_severity(
    key_type: str, in_git_history: bool, in_current_tracking: bool
) -> str:
    if key_type == "secret":
        return "CRITICAL" if (in_git_history or in_current_tracking) else "ERROR"
    if key_type == "publishable":
        return "ERROR" if (in_git_history or in_current_tracking) else "WARNING"
    if key_type in ("url", "project_id"):
        return "WARNING" if (in_git_history or in_current_tracking) else "INFO"
    return "WARNING" if (in_git_history or in_current_tracking) else "INFO"


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _extract_var_names(env_file: Path) -> list[str]:
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


def _check_git_history(path: Path) -> tuple[bool, bool]:
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


def _detect_supabase(path: Path) -> bool:
    """Return True if Supabase is detected anywhere in the project."""
    # package.json dependencies
    pkg = path / "package.json"
    if pkg.is_file() and pkg.stat().st_size <= _MAX_FILE_SIZE:
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
            all_deps: dict[str, str] = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }
            if any(k.startswith("@supabase/") for k in all_deps):
                return True
        except (json.JSONDecodeError, OSError):
            pass

    # supabase/config.toml or supabase/migrations/
    if (path / "supabase" / "config.toml").is_file():
        return True
    if (path / "supabase" / "migrations").is_dir():
        return True

    # Source file imports
    for scan_dir in _SCAN_DIRS:
        base = path / scan_dir
        if not base.is_dir():
            continue
        for src_file in base.rglob("*"):
            if not src_file.is_file():
                continue
            if src_file.suffix not in _SCAN_EXTENSIONS:
                continue
            if any(part in _SKIP_DIRS for part in src_file.parts):
                continue
            if src_file.stat().st_size > _MAX_FILE_SIZE:
                continue
            try:
                content = src_file.read_text(encoding="utf-8", errors="replace")
                if any(p.search(content) for p in _SDK_PATTERNS):
                    return True
            except OSError:
                continue

    return False


def _scan_rls_evidence(path: Path) -> SupabaseRLSEvidence:
    """Scan migration SQL files for RLS statements. Reports file:line, never content."""
    migrations_dir = path / "supabase" / "migrations"
    if not migrations_dir.is_dir():
        return SupabaseRLSEvidence(
            migrations_present=False,
            rls_enable_found=False,
            policies_found=False,
            evidence="",
        )

    first_rls = ""
    first_policy = ""

    for sql_file in sorted(migrations_dir.rglob("*.sql")):
        if sql_file.stat().st_size > _MAX_FILE_SIZE:
            continue
        try:
            content = sql_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(sql_file.relative_to(path))
        for i, line in enumerate(content.splitlines(), start=1):
            if not first_rls and _RLS_RE.search(line):
                first_rls = f"{rel}:{i}"
            if not first_policy and _POLICY_RE.search(line):
                first_policy = f"{rel}:{i}"
        if first_rls and first_policy:
            break

    evidence_parts: list[str] = []
    if first_rls:
        evidence_parts.append(f"RLS: first match {first_rls}")
    if first_policy:
        evidence_parts.append(f"policies: first match {first_policy}")

    return SupabaseRLSEvidence(
        migrations_present=True,
        rls_enable_found=bool(first_rls),
        policies_found=bool(first_policy),
        evidence="; ".join(evidence_parts),
    )


def _check_local_fixes(path: Path, env_not_tracked: bool) -> SupabaseLocalFixes:
    """Check whether local protective measures are in place."""
    gitignore = path / ".gitignore"
    protects_env = False
    if gitignore.is_file():
        try:
            lines = {
                line.strip()
                for line in gitignore.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            }
            protects_env = bool(lines & _GITIGNORE_ENV_TOKENS)
        except OSError:
            pass

    return SupabaseLocalFixes(
        gitignore_protects_env=protects_env,
        env_not_tracked=env_not_tracked,
        env_example_exists=(path / ".env.example").is_file(),
    )


def _compute_key_risks(
    path: Path, in_history: bool, in_tracking: bool
) -> list[SupabaseKeyRisk]:
    """Build key risk list from variable names only — never reads values."""
    all_names: set[str] = set()

    for env_file in (path / ".env", path / ".env.example"):
        for name in _extract_var_names(env_file):
            if _SUPABASE_VAR_RE.search(name):
                all_names.add(name)

    risks: list[SupabaseKeyRisk] = []
    for name in sorted(all_names):
        key_type = _classify_key(name)
        severity = _compute_key_severity(key_type, in_history, in_tracking)
        risks.append(
            SupabaseKeyRisk(
                variable_name=name,
                key_type=key_type,
                severity=severity,
                in_git_history=in_history,
                in_current_tracking=in_tracking,
            )
        )
    return risks


def _build_remediation_steps(
    local_fixes: SupabaseLocalFixes,
    key_risks: list[SupabaseKeyRisk],
) -> list[SupabaseRemediationStep]:
    steps: list[SupabaseRemediationStep] = []
    priority = 1

    steps.append(
        SupabaseRemediationStep(
            priority=priority,
            action="Add .env and .env.* to .gitignore",
            status="done" if local_fixes.gitignore_protects_env else "required",
            location=".gitignore",
        )
    )
    priority += 1

    steps.append(
        SupabaseRemediationStep(
            priority=priority,
            action="Remove .env from Git tracking (git rm --cached .env)",
            status="done" if local_fixes.env_not_tracked else "required",
            location=".env",
        )
    )
    priority += 1

    steps.append(
        SupabaseRemediationStep(
            priority=priority,
            action="Create .env.example with placeholder values only",
            status="done" if local_fixes.env_example_exists else "required",
            location=".env.example",
        )
    )
    priority += 1

    has_secret_exposed = any(
        r.key_type == "secret" and (r.in_git_history or r.in_current_tracking)
        for r in key_risks
    )
    has_publishable_in_history = any(
        r.key_type == "publishable" and r.in_git_history for r in key_risks
    )

    if has_secret_exposed:
        steps.append(
            SupabaseRemediationStep(
                priority=priority,
                action="URGENT: Rotate Supabase service/secret key immediately",
                status="manual",
                location="Supabase Dashboard → Project Settings → API Keys",
            )
        )
        priority += 1

    if has_publishable_in_history:
        steps.append(
            SupabaseRemediationStep(
                priority=priority,
                action="Rotate Supabase anon/publishable key",
                status="manual",
                location="Supabase Dashboard → Project Settings → API → Regenerate",
            )
        )
        priority += 1

    steps.append(
        SupabaseRemediationStep(
            priority=priority,
            action="Verify Row Level Security (RLS) is enabled on all tables",
            status="manual",
            location="Supabase Dashboard → Table Editor → RLS",
        )
    )
    priority += 1

    steps.append(
        SupabaseRemediationStep(
            priority=priority,
            action="Re-run AEOS audit after fixes",
            status="required",
            location="uv run aeos supabase check --path <project>",
        )
    )

    return steps


def _compute_status(supabase_detected: bool, key_risks: list[SupabaseKeyRisk]) -> str:
    if not supabase_detected:
        return "OK"
    if any(r.severity == "CRITICAL" for r in key_risks):
        return "CRITICAL"
    if any(r.severity == "ERROR" for r in key_risks):
        return "ERROR"
    return "WARNING"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_supabase_check(path: Path) -> SupabaseCheckResult:
    """Check Supabase integration and produce a remediation plan. Read-only."""
    resolved = path.resolve()

    if not _detect_supabase(resolved):
        return SupabaseCheckResult(
            path=resolved,
            status="OK",
            supabase_detected=False,
        )

    in_history, in_tracking = _check_git_history(resolved)
    key_risks = _compute_key_risks(resolved, in_history, in_tracking)
    rls_evidence = _scan_rls_evidence(resolved)
    local_fixes = _check_local_fixes(resolved, not in_tracking)
    status = _compute_status(True, key_risks)
    remediation_steps = _build_remediation_steps(local_fixes, key_risks)
    requires_manual = any(s.status == "manual" for s in remediation_steps)

    return SupabaseCheckResult(
        path=resolved,
        status=status,
        supabase_detected=True,
        key_risks=key_risks,
        rls_evidence=rls_evidence,
        local_fixes=local_fixes,
        remediation_steps=remediation_steps,
        requires_manual_action=requires_manual,
    )
