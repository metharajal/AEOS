import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DANGEROUS_ENV_FILES: tuple[str, ...] = (
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.staging",
    ".env.test",
)

_GITIGNORE_ENV_PATTERNS: frozenset[str] = frozenset(
    {".env", ".env.*", "*.env", "/.env"}
)
_GITIGNORE_KEY_PATTERNS: frozenset[str] = frozenset({"*.pem", "*.key"})
_GITIGNORE_NODE_PATTERNS: frozenset[str] = frozenset(
    {"node_modules", "node_modules/", "/node_modules"}
)
_GITIGNORE_VENV_PATTERNS: frozenset[str] = frozenset(
    {".venv", ".venv/", "venv", "venv/", "env/", ".env/"}
)

_CREDENTIAL_FILENAMES: frozenset[str] = frozenset(
    {
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "service-account.json",
        "credentials.json",
        "gcloud-key.json",
    }
)
_CREDENTIAL_EXTENSIONS: frozenset[str] = frozenset({".pem", ".key", ".p12", ".pfx"})

_SENSITIVE_DB_PORTS: frozenset[str] = frozenset(
    {"5432", "3306", "6379", "27017", "9200", "5433"}
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
    ".github",
)

_SCAN_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".env",
        ".example",
        ".sample",
        ".template",
    }
)

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
        "coverage",
    }
)

_SCAN_MAX_BYTES: int = 500 * 1024

# Secret patterns: (label, regex, severity)
# IMPORTANT: regex captures pattern presence, matched value is NEVER stored
_SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("AWS_ACCESS_KEY_ID", r"AKIA[0-9A-Z]{16}", "ERROR"),
    ("AWS_SECRET_ACCESS_KEY", r"AWS_SECRET_ACCESS_KEY\s*=\s*\S{8,}", "ERROR"),
    ("OpenAI API key", r"sk-[A-Za-z0-9]{20,}", "ERROR"),
    ("Anthropic API key", r"sk-ant-[A-Za-z0-9_-]{20,}", "ERROR"),
    ("GitHub PAT", r"ghp_[A-Za-z0-9]{36}", "ERROR"),
    ("GitHub OAuth token", r"gho_[A-Za-z0-9]{36}", "ERROR"),
    ("Slack Bot token", r"xoxb-[0-9]+-[A-Za-z0-9-]+", "ERROR"),
    ("Slack User token", r"xoxp-[0-9]+-[A-Za-z0-9-]+", "ERROR"),
    ("Bearer token", r"Bearer\s+[A-Za-z0-9._\-]{20,}", "ERROR"),
    ("GOOGLE_APPLICATION_CREDENTIALS", r"GOOGLE_APPLICATION_CREDENTIALS", "WARNING"),
    ("SUPABASE_SERVICE_ROLE_KEY", r"SUPABASE_SERVICE_ROLE_KEY", "WARNING"),
    ("STRIPE_SECRET_KEY", r"STRIPE_SECRET_KEY", "WARNING"),
    ("OPENAI_API_KEY", r"OPENAI_API_KEY", "WARNING"),
    ("ANTHROPIC_API_KEY", r"ANTHROPIC_API_KEY", "WARNING"),
    ("AWS_ACCESS_KEY_ID var", r"AWS_ACCESS_KEY_ID", "WARNING"),
    ("DATABASE_URL", r"DATABASE_URL", "WARNING"),
    ("PRIVATE_KEY", r"PRIVATE_KEY", "WARNING"),
    ("SERVICE_ROLE_KEY", r"SERVICE_ROLE_KEY", "WARNING"),
]

# Placeholder detector: if matched value looks like a placeholder, skip
_PLACEHOLDER_RE: re.Pattern[str] = re.compile(
    r"^(your[-_]|YOUR[-_]|<|{\s*\{|\$\{|\[|xxx|changeme|placeholder"
    r"|example|test|dummy|fake|none|null|undefined|replace|insert)",
    re.IGNORECASE,
)

_PASSWORD_RE: re.Pattern[str] = re.compile(
    r"[Pp]assword\s*[=:]\s*([^\s\"'#]{6,})", re.IGNORECASE
)
_SECRET_ASSIGN_RE: re.Pattern[str] = re.compile(
    r"[Ss]ecret\s*[=:]\s*([^\s\"'#]{8,})", re.IGNORECASE
)
_TOKEN_ASSIGN_RE: re.Pattern[str] = re.compile(
    r"\btoken\s*[=:]\s*([^\s\"'#]{8,})", re.IGNORECASE
)

_CORS_RE: re.Pattern[str] = re.compile(
    r"""(cors|origin|Access-Control-Allow-Origin).*["']\*["']""",
    re.IGNORECASE,
)

_EVAL_RE: re.Pattern[str] = re.compile(r"\beval\s*\(", re.IGNORECASE)
_OS_SYSTEM_RE: re.Pattern[str] = re.compile(r"\bos\.system\s*\(")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SecurityFinding:
    category: str
    severity: str
    message: str
    location: str
    recommendation: str
    evidence: str = ""


@dataclass
class SecurityCheckResult:
    path: Path
    status: str
    findings: list[SecurityFinding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gitignore_lines(path: Path) -> list[str]:
    gi = path / ".gitignore"
    if not gi.is_file():
        return []
    try:
        return [ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()]
    except OSError:
        return []


def _gitignore_covers(lines: list[str], patterns: frozenset[str]) -> bool:
    return any(ln in patterns for ln in lines)


def _path_is_excluded(rel: Path) -> bool:
    return any(part in _SCAN_EXCLUDES for part in rel.parts)


def _is_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER_RE.match(value.strip("\"' \t")))


# ---------------------------------------------------------------------------
# Check: env_files
# ---------------------------------------------------------------------------


def _check_env_files(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    gi_lines = _gitignore_lines(path)
    has_gitignore = (path / ".gitignore").is_file()

    for env_name in _DANGEROUS_ENV_FILES:
        if not (path / env_name).is_file():
            continue
        protected = has_gitignore and (
            _gitignore_covers(gi_lines, _GITIGNORE_ENV_PATTERNS) or env_name in gi_lines
        )
        if not protected:
            findings.append(
                SecurityFinding(
                    category="env_files",
                    severity="ERROR",
                    message=f"'{env_name}' detected without .gitignore protection",
                    location=env_name,
                    recommendation=(
                        f"Add '{env_name}' or '.env.*' to .gitignore immediately"
                        " — this file likely contains real secrets"
                    ),
                )
            )

    # Credential files at root
    for fname in _CREDENTIAL_FILENAMES:
        if (path / fname).is_file():
            findings.append(
                SecurityFinding(
                    category="env_files",
                    severity="ERROR",
                    message=f"Credential file '{fname}' detected at project root",
                    location=fname,
                    recommendation=(
                        "Remove this file from the repository and add it to"
                        " .gitignore — never commit credential files"
                    ),
                )
            )

    # Files with credential extensions at root
    for f in path.iterdir():
        if f.is_file() and f.suffix in _CREDENTIAL_EXTENSIONS:
            findings.append(
                SecurityFinding(
                    category="env_files",
                    severity="ERROR",
                    message=(
                        f"Key or certificate file '{f.name}' detected at project root"
                    ),
                    location=f.name,
                    recommendation=(
                        f"Add '*{f.suffix}' to .gitignore"
                        " and remove this file from the repository"
                    ),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Check: gitignore
# ---------------------------------------------------------------------------


def _check_gitignore(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    gi_path = path / ".gitignore"

    if not gi_path.is_file():
        findings.append(
            SecurityFinding(
                category="gitignore",
                severity="WARNING",
                message=(
                    ".gitignore not found"
                    " — sensitive files may be committed accidentally"
                ),
                location=".gitignore",
                recommendation=(
                    "Create a .gitignore file with at minimum: .env, .env.*,"
                    " *.pem, *.key, node_modules/, .venv/"
                ),
            )
        )
        return findings

    lines = _gitignore_lines(path)

    if not _gitignore_covers(lines, _GITIGNORE_ENV_PATTERNS):
        findings.append(
            SecurityFinding(
                category="gitignore",
                severity="WARNING",
                message=".gitignore does not protect .env files",
                location=".gitignore",
                recommendation="Add '.env' and '.env.*' to .gitignore",
            )
        )

    if not _gitignore_covers(lines, _GITIGNORE_KEY_PATTERNS):
        findings.append(
            SecurityFinding(
                category="gitignore",
                severity="WARNING",
                message=".gitignore does not protect private key files (*.pem, *.key)",
                location=".gitignore",
                recommendation="Add '*.pem' and '*.key' to .gitignore",
            )
        )

    has_pkg_json = (path / "package.json").is_file()
    if has_pkg_json and not _gitignore_covers(lines, _GITIGNORE_NODE_PATTERNS):
        findings.append(
            SecurityFinding(
                category="gitignore",
                severity="WARNING",
                message=".gitignore does not exclude node_modules/",
                location=".gitignore",
                recommendation="Add 'node_modules/' to .gitignore",
            )
        )

    has_python = (path / "pyproject.toml").is_file() or (
        path / "requirements.txt"
    ).is_file()
    if has_python and not _gitignore_covers(lines, _GITIGNORE_VENV_PATTERNS):
        findings.append(
            SecurityFinding(
                category="gitignore",
                severity="WARNING",
                message=(
                    ".gitignore does not exclude Python virtual environment (.venv/)"
                ),
                location=".gitignore",
                recommendation="Add '.venv/' and '__pycache__/' to .gitignore",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Check: secrets (source scan)
# ---------------------------------------------------------------------------


def _compile_secret_patterns() -> list[tuple[str, re.Pattern[str], str]]:
    return [
        (label, re.compile(pattern), severity)
        for label, pattern, severity in _SECRET_PATTERNS
    ]


def _scan_files_for_secrets(
    path: Path,
    compiled: list[tuple[str, re.Pattern[str], str]],
) -> list[SecurityFinding]:
    # matches[label] = list of (rel_path, line_number)
    matches: dict[str, list[tuple[str, int]]] = {label: [] for label, _, _ in compiled}
    severities: dict[str, str] = {label: sev for label, _, sev in compiled}

    _scan_directory_tree(path, compiled, matches)
    _scan_root_config_files(path, compiled, matches)

    findings: list[SecurityFinding] = []
    for label, _pattern, _sev in compiled:
        hits = matches[label]
        if not hits:
            continue
        first_file, first_line = hits[0]
        file_count = len({f for f, _ in hits})
        evidence = (
            f"pattern={label}, {file_count} file(s),"
            f" first match: {first_file}:{first_line}"
        )
        findings.append(
            SecurityFinding(
                category="secrets",
                severity=severities[label],
                message=f"Potential secret detected: {label}",
                location=first_file,
                recommendation=(
                    "Remove this secret from the codebase — use environment"
                    " variables instead and ensure the file is gitignored"
                ),
                evidence=evidence,
            )
        )

    # soft patterns: password=, secret=, token= with non-placeholder value
    findings.extend(_scan_soft_patterns(path))

    return findings


def _scan_directory_tree(
    path: Path,
    compiled: list[tuple[str, re.Pattern[str], str]],
    matches: dict[str, list[tuple[str, int]]],
) -> None:
    for dir_name in _SCAN_DIRS:
        scan_dir = path / dir_name
        if not scan_dir.is_dir():
            continue
        for file_path in scan_dir.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(path)
            if _path_is_excluded(rel):
                continue
            if file_path.suffix not in _SCAN_EXTENSIONS:
                continue
            if file_path.stat().st_size > _SCAN_MAX_BYTES:
                continue
            _scan_file(file_path, rel, compiled, matches)


def _scan_root_config_files(
    path: Path,
    compiled: list[tuple[str, re.Pattern[str], str]],
    matches: dict[str, list[tuple[str, int]]],
) -> None:
    root_extensions = frozenset(
        {".env", ".example", ".sample", ".template", ".toml", ".yaml", ".yml"}
    )
    for f in path.iterdir():
        if not f.is_file():
            continue
        if f.suffix not in root_extensions and not f.name.startswith(".env"):
            continue
        if f.stat().st_size > _SCAN_MAX_BYTES:
            continue
        rel = f.relative_to(path)
        _scan_file(f, rel, compiled, matches)


def _scan_file(
    file_path: Path,
    rel: Path,
    compiled: list[tuple[str, re.Pattern[str], str]],
    matches: dict[str, list[tuple[str, int]]],
) -> None:
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return
    rel_str = str(rel)
    for lineno, line in enumerate(lines, start=1):
        for label, pattern, _ in compiled:
            if pattern.search(line):
                matches[label].append((rel_str, lineno))


def _scan_soft_patterns(path: Path) -> list[SecurityFinding]:
    soft: list[tuple[str, re.Pattern[str]]] = [
        ("Hardcoded password", _PASSWORD_RE),
        ("Hardcoded secret assignment", _SECRET_ASSIGN_RE),
        ("Hardcoded token assignment", _TOKEN_ASSIGN_RE),
    ]
    matches: dict[str, list[tuple[str, int]]] = {label: [] for label, _ in soft}
    compiled_soft = [(label, pattern) for label, pattern in soft]

    def _check_line(line: str, rel_str: str, lineno: int) -> None:
        for label, pattern in compiled_soft:
            m = pattern.search(line)
            if m:
                value = m.group(1) if m.lastindex else ""
                if not _is_placeholder(value):
                    matches[label].append((rel_str, lineno))

    def _walk(scan_path: Path) -> None:
        for file_path in scan_path.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(path)
            if _path_is_excluded(rel):
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
            rel_str = str(rel)
            for lineno, line in enumerate(lines, start=1):
                _check_line(line, rel_str, lineno)

    for dir_name in _SCAN_DIRS:
        scan_dir = path / dir_name
        if scan_dir.is_dir():
            _walk(scan_dir)

    findings: list[SecurityFinding] = []
    for label, _ in soft:
        hits = matches[label]
        if not hits:
            continue
        first_file, first_line = hits[0]
        file_count = len({f for f, _ in hits})
        evidence = (
            f"pattern={label}, {file_count} file(s),"
            f" first match: {first_file}:{first_line}"
        )
        findings.append(
            SecurityFinding(
                category="secrets",
                severity="WARNING",
                message=f"Potential secret detected: {label}",
                location=first_file,
                recommendation=(
                    "Move this value to an environment variable"
                    " and remove it from the codebase"
                ),
                evidence=evidence,
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Check: config
# ---------------------------------------------------------------------------


def _check_config(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    findings.extend(_check_dockerfile(path))
    findings.extend(_check_docker_compose(path))
    findings.extend(_check_github_actions(path))
    findings.extend(_check_npm_scripts(path))
    findings.extend(_check_cors(path))
    return findings


def _check_dockerfile(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    df = path / "Dockerfile"
    if not df.is_file():
        return findings
    try:
        lines = df.read_text(encoding="utf-8").splitlines()
    except OSError:
        return findings

    has_user = False
    user_root = False
    has_nonpinned_from = False

    _nonpinned_re = re.compile(
        r"^FROM\s+(node|python|ubuntu|debian|alpine|ruby|golang)(:latest)?\s*$",
        re.IGNORECASE,
    )

    for line in lines:
        stripped = line.strip()
        if _nonpinned_re.match(stripped):
            has_nonpinned_from = True
        if re.match(r"^USER\s+", stripped, re.IGNORECASE):
            has_user = True
            if re.match(r"^USER\s+root\s*$", stripped, re.IGNORECASE):
                user_root = True

    if has_nonpinned_from:
        findings.append(
            SecurityFinding(
                category="config",
                severity="WARNING",
                message="Dockerfile uses non-pinned base image (e.g. node:latest)",
                location="Dockerfile",
                recommendation=(
                    "Pin the base image to a specific version"
                    " (e.g. node:20-alpine) for reproducible builds"
                ),
            )
        )
    if not has_user:
        findings.append(
            SecurityFinding(
                category="config",
                severity="WARNING",
                message="Dockerfile has no USER instruction — container runs as root",
                location="Dockerfile",
                recommendation=(
                    "Add a non-root USER instruction to the Dockerfile"
                    " (e.g. RUN adduser --disabled-password app && USER app)"
                ),
            )
        )
    if user_root:
        findings.append(
            SecurityFinding(
                category="config",
                severity="WARNING",
                message="Dockerfile explicitly sets USER root",
                location="Dockerfile",
                recommendation=(
                    "Replace 'USER root' with a non-root user"
                    " to follow least-privilege principle"
                ),
            )
        )
    return findings


def _check_docker_compose(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for fname in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        dc = path / fname
        if not dc.is_file():
            continue
        try:
            lines = dc.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        port_re = re.compile(r'["\']?(?:0\.0\.0\.0:)?(\d+):\d+["\']?')
        for lineno, line in enumerate(lines, start=1):
            m = port_re.search(line)
            if m:
                port = m.group(1)
                if port in _SENSITIVE_DB_PORTS:
                    findings.append(
                        SecurityFinding(
                            category="config",
                            severity="WARNING",
                            message=(
                                f"Sensitive port {port} exposed publicly in {fname}"
                            ),
                            location=f"{fname}:{lineno}",
                            recommendation=(
                                f"Bind port {port} to 127.0.0.1 instead of"
                                " all interfaces to avoid unintended exposure"
                            ),
                        )
                    )
        break
    return findings


def _check_github_actions(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    workflows_dir = path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return findings

    prt_re = re.compile(r"pull_request_target")
    echo_secret_re = re.compile(r"echo\s+.*\$\{\{.*secrets\.")
    curl_pipe_re = re.compile(r"curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh")

    for wf in workflows_dir.iterdir():
        if not wf.is_file() or wf.suffix not in {".yml", ".yaml"}:
            continue
        try:
            lines = wf.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        rel = str(wf.relative_to(path))
        for lineno, line in enumerate(lines, start=1):
            if prt_re.search(line):
                findings.append(
                    SecurityFinding(
                        category="config",
                        severity="ERROR",
                        message=(
                            "Dangerous trigger 'pull_request_target' detected"
                            f" in {wf.name}"
                        ),
                        location=f"{rel}:{lineno}",
                        recommendation=(
                            "'pull_request_target' can expose repository secrets"
                            " to untrusted PRs — restrict permissions explicitly"
                            " or use 'pull_request' instead"
                        ),
                    )
                )
            if echo_secret_re.search(line):
                findings.append(
                    SecurityFinding(
                        category="config",
                        severity="ERROR",
                        message=(
                            f"GitHub Actions secret exposed via echo in {wf.name}"
                        ),
                        location=f"{rel}:{lineno}",
                        recommendation=(
                            "Never echo secrets in CI — use masked outputs"
                            " or omit the log statement entirely"
                        ),
                    )
                )
            if curl_pipe_re.search(line):
                findings.append(
                    SecurityFinding(
                        category="config",
                        severity="WARNING",
                        message=(f"Pipe-to-shell pattern detected in {wf.name}"),
                        location=f"{rel}:{lineno}",
                        recommendation=(
                            "Avoid curl|bash patterns — download, verify checksum,"
                            " then execute"
                        ),
                    )
                )
    return findings


def _check_npm_scripts(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    pkg = path / "package.json"
    if not pkg.is_file():
        return findings
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return findings
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return findings
    pipe_re = re.compile(r"curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh")
    for script_name, script_value in scripts.items():
        if isinstance(script_value, str) and pipe_re.search(script_value):
            findings.append(
                SecurityFinding(
                    category="config",
                    severity="WARNING",
                    message=(f"Pipe-to-shell pattern in npm script '{script_name}'"),
                    location="package.json",
                    recommendation=(
                        "Avoid pipe-to-shell install patterns in npm scripts"
                        " — use pinned package versions instead"
                    ),
                )
            )
    return findings


def _check_cors(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    matches: list[tuple[str, int]] = []

    def _walk(scan_path: Path) -> None:
        for file_path in scan_path.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(path)
            if _path_is_excluded(rel):
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
            rel_str = str(rel)
            for lineno, line in enumerate(lines, start=1):
                if _CORS_RE.search(line):
                    matches.append((rel_str, lineno))

    for dir_name in _SCAN_DIRS:
        scan_dir = path / dir_name
        if scan_dir.is_dir():
            _walk(scan_dir)

    if matches:
        first_file, first_line = matches[0]
        file_count = len({f for f, _ in matches})
        findings.append(
            SecurityFinding(
                category="config",
                severity="WARNING",
                message="Permissive CORS wildcard '*' detected",
                location=first_file,
                recommendation=(
                    "Replace wildcard CORS with an explicit allowlist of"
                    " trusted origins"
                ),
                evidence=(
                    f"pattern=CORS wildcard, {file_count} file(s),"
                    f" first match: {first_file}:{first_line}"
                ),
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Check: dependencies
# ---------------------------------------------------------------------------


def _check_dependencies(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []

    pkg = path / "package.json"
    if pkg.is_file():
        lock_files = (
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "bun.lockb",
        )
        has_lock = any((path / lf).is_file() for lf in lock_files)
        if not has_lock:
            findings.append(
                SecurityFinding(
                    category="dependencies",
                    severity="WARNING",
                    message=(
                        "No npm lock file found — dependency versions are not pinned"
                    ),
                    location="package.json",
                    recommendation=(
                        "Run 'npm install' or 'pnpm install' to generate a lock file"
                        " and commit it to the repository"
                    ),
                )
            )

    req = path / "requirements.txt"
    if req.is_file():
        try:
            content = req.read_text(encoding="utf-8")
            if "--hash=" not in content:
                findings.append(
                    SecurityFinding(
                        category="dependencies",
                        severity="WARNING",
                        message="requirements.txt has no dependency hashes",
                        location="requirements.txt",
                        recommendation=(
                            "Use 'pip-compile --generate-hashes' to pin"
                            " dependencies with hashes for reproducible installs"
                        ),
                    )
                )
        except OSError:
            pass

    return findings


# ---------------------------------------------------------------------------
# Check: source_code
# ---------------------------------------------------------------------------


def _check_source_code(path: Path) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    eval_matches: list[tuple[str, int]] = []
    system_matches: list[tuple[str, int]] = []

    for dir_name in _SCAN_DIRS:
        scan_dir = path / dir_name
        if not scan_dir.is_dir():
            continue
        for file_path in scan_dir.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(path)
            if _path_is_excluded(rel):
                continue
            if file_path.suffix not in {".py", ".js", ".ts"}:
                continue
            if file_path.stat().st_size > _SCAN_MAX_BYTES:
                continue
            try:
                lines = file_path.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except OSError:
                continue
            rel_str = str(rel)
            for lineno, line in enumerate(lines, start=1):
                if _EVAL_RE.search(line):
                    eval_matches.append((rel_str, lineno))
                if _OS_SYSTEM_RE.search(line):
                    system_matches.append((rel_str, lineno))

    if eval_matches:
        first_file, first_line = eval_matches[0]
        file_count = len({f for f, _ in eval_matches})
        findings.append(
            SecurityFinding(
                category="source_code",
                severity="WARNING",
                message="Use of eval() detected in source code",
                location=first_file,
                recommendation=(
                    "Avoid eval() with dynamic input — it can execute arbitrary code"
                ),
                evidence=(
                    f"pattern=eval(), {file_count} file(s),"
                    f" first match: {first_file}:{first_line}"
                ),
            )
        )

    if system_matches:
        first_file, first_line = system_matches[0]
        file_count = len({f for f, _ in system_matches})
        findings.append(
            SecurityFinding(
                category="source_code",
                severity="WARNING",
                message=(
                    "Use of os.system() detected — prefer subprocess with argument list"
                ),
                location=first_file,
                recommendation=(
                    "Replace os.system() with subprocess.run(["
                    "...], check=True) to avoid shell injection"
                ),
                evidence=(
                    f"pattern=os.system(), {file_count} file(s),"
                    f" first match: {first_file}:{first_line}"
                ),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------


def _compute_status(findings: list[SecurityFinding]) -> str:
    if any(f.severity == "ERROR" for f in findings):
        return "ERROR"
    if any(f.severity == "WARNING" for f in findings):
        return "WARNING"
    return "OK"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_security_check(path: Path) -> SecurityCheckResult:
    compiled = _compile_secret_patterns()

    findings: list[SecurityFinding] = []
    findings.extend(_check_env_files(path))
    findings.extend(_check_gitignore(path))
    findings.extend(_scan_files_for_secrets(path, compiled))
    findings.extend(_check_config(path))
    findings.extend(_check_dependencies(path))
    findings.extend(_check_source_code(path))

    return SecurityCheckResult(
        path=path.resolve(),
        status=_compute_status(findings),
        findings=findings,
    )
