"""
Supabase RLS Inspector — local-first, read-only static analysis of Row Level
Security policies parsed from supabase/migrations/*.sql files.

No network access. No secret reads. No file modification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FILE_SIZE = 500 * 1024  # 500 KB

# Tables whose SELECT being open to all auth users is suspicious
_SENSITIVE_TABLE_TOKENS: frozenset[str] = frozenset(
    {
        "personnel",
        "users",
        "profiles",
        "notifications",
        "budget",
        "payments",
        "paiements",
        "documents",
        "user_roles",
        "salaires",
        "contracts",
        "contrats",
    }
)

# Columns that indicate multi-tenant scoping is expected
_TENANT_COLUMN_TOKENS: frozenset[str] = frozenset(
    {
        "commune_id",
        "tenant_id",
        "org_id",
        "organization_id",
        "municipality_id",
        "profile_id",
    }
)

# Columns that, when present, confirm multi-tenant scoping IS applied
_TENANT_SCOPE_RE = re.compile(
    r"\b(commune_id|tenant_id|org_id|organization_id|municipality_id|profile_id)\b",
    re.IGNORECASE,
)

# Tables with user-generated content that need moderation DELETE
_MODERATABLE_TABLE_TOKENS: frozenset[str] = frozenset(
    {
        "posts",
        "forum_posts",
        "comments",
        "commentaires",
        "messages",
        "reviews",
        "signalements",
        "plaintes",
    }
)

# ---------------------------------------------------------------------------
# SQL parsing regexes
# ---------------------------------------------------------------------------

# ALTER TABLE <schema.>table ENABLE ROW LEVEL SECURITY
_RLS_ENABLE_RE = re.compile(
    r"""ALTER\s+TABLE\s+
        (?:(?P<schema>\w+)\s*\.\s*)?
        (?P<table>\w+)\s+
        ENABLE\s+ROW\s+LEVEL\s+SECURITY""",
    re.IGNORECASE | re.VERBOSE,
)

# ALTER TABLE <schema.>table FORCE ROW LEVEL SECURITY
_RLS_FORCE_RE = re.compile(
    r"""ALTER\s+TABLE\s+
        (?:(?P<schema>\w+)\s*\.\s*)?
        (?P<table>\w+)\s+
        FORCE\s+ROW\s+LEVEL\s+SECURITY""",
    re.IGNORECASE | re.VERBOSE,
)

# CREATE TABLE <schema.>table
_CREATE_TABLE_RE = re.compile(
    r"""CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+
        (?:(?P<schema>\w+)\s*\.\s*)?
        (?P<table>\w+)\s*\(""",
    re.IGNORECASE | re.VERBOSE,
)

# DROP POLICY name ON <schema.>table
_DROP_POLICY_RE = re.compile(
    r"""DROP\s+POLICY(?:\s+IF\s+EXISTS)?\s+
        (?P<name>"[^"]+"|'[^']+'|\w+)\s+
        ON\s+(?:(?:\w+)\s*\.\s*)?(?P<table>\w+)""",
    re.IGNORECASE | re.VERBOSE,
)

# CREATE POLICY "name" ON <schema.>table FOR command [AS {PERMISSIVE|RESTRICTIVE}]
# [TO role] [USING (...)] [WITH CHECK (...)]
_CREATE_POLICY_RE = re.compile(
    r"""CREATE\s+POLICY\s+
        (?P<name>"[^"]+"|'[^']+'|\w+)\s+
        ON\s+
        (?:(?:\w+)\s*\.\s*)?
        (?P<table>\w+)
        (?P<rest>[^;]*);""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

_FOR_RE = re.compile(
    r"\bFOR\s+(?P<cmd>SELECT|INSERT|UPDATE|DELETE|ALL)\b", re.IGNORECASE
)
# These regexes only locate the keyword; content is extracted by _extract_balanced.
_USING_KW_RE = re.compile(r"\bUSING\s*\(", re.IGNORECASE)
_WITH_CHECK_KW_RE = re.compile(r"\bWITH\s+CHECK\s*\(", re.IGNORECASE)

# Overly permissive expression detection
_TRUE_ONLY_RE = re.compile(r"^\s*true\s*$", re.IGNORECASE)
_AUTH_ROLE_AUTHENTICATED_RE = re.compile(
    r"auth\s*\.\s*role\s*\(\s*\)\s*=\s*['\"]authenticated['\"]",
    re.IGNORECASE,
)
_AUTH_UID_NOT_NULL_RE = re.compile(
    r"auth\s*\.\s*uid\s*\(\s*\)\s+IS\s+NOT\s+NULL",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RLSPolicy:
    name: str
    table: str
    command: str  # SELECT | INSERT | UPDATE | DELETE | ALL
    using_expr: str
    with_check_expr: str
    source_file: str  # relative path, never content
    source_line: int


@dataclass
class RLSTableInfo:
    name: str
    rls_enabled: bool = False
    rls_forced: bool = False
    policies: list[RLSPolicy] = field(default_factory=list)


@dataclass
class RLSFinding:
    severity: str  # OK | WARNING | ERROR
    table: str
    rule: str
    message: str
    recommendation: str
    source_file: str = ""


@dataclass
class RLSInspectResult:
    path: Path
    status: str  # OK | WARNING | ERROR
    migrations_scanned: int
    tables: list[RLSTableInfo] = field(default_factory=list)
    policies: list[RLSPolicy] = field(default_factory=list)
    findings: list[RLSFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SQL parsing helpers
# ---------------------------------------------------------------------------


def _strip_comments(sql: str) -> str:
    """Remove -- line comments and /* block comments */ from SQL."""
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _extract_balanced(text: str, kw_re: re.Pattern[str]) -> str:
    """
    Find kw_re (which must end with a literal `(`), then extract the
    balanced parenthesised expression that follows.  Handles arbitrary
    nesting such as `auth.uid()` or `has_role(auth.uid(), 'agent')`.
    Returns the content between the outermost parens (stripped), or "".
    """
    m = kw_re.search(text)
    if not m:
        return ""
    # The keyword pattern ends with `(`, so we start counting from here.
    depth = 1
    start = m.end()
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i].strip()
    return ""


def _normalize_name(raw: str) -> str:
    """Strip surrounding quotes from a SQL identifier."""
    raw = raw.strip()
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    return raw


def _parse_policy_rest(rest: str) -> tuple[str, str, str]:
    """
    Parse the tail of a CREATE POLICY ... ON table <rest>.
    Returns (command, using_expr, with_check_expr).
    Uses balanced-paren extraction so auth.uid() is handled correctly.
    """
    command = "ALL"
    m = _FOR_RE.search(rest)
    if m:
        command = m.group("cmd").upper()

    using_expr = _extract_balanced(rest, _USING_KW_RE)
    with_check_expr = _extract_balanced(rest, _WITH_CHECK_KW_RE)

    return command, using_expr, with_check_expr


def _scan_migrations(
    migrations_dir: Path, project_root: Path
) -> tuple[
    dict[str, RLSTableInfo],
    list[RLSPolicy],
    int,
]:
    """
    Parse all *.sql migration files in chronological order.
    Returns (tables_by_name, all_policies, files_scanned).
    Read-only — never modifies any file.
    """
    tables: dict[str, RLSTableInfo] = {}
    all_policies: list[RLSPolicy] = []
    files_scanned = 0

    sql_files = sorted(migrations_dir.rglob("*.sql"))
    for sql_file in sql_files:
        if sql_file.stat().st_size > _MAX_FILE_SIZE:
            continue
        try:
            raw = sql_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        files_scanned += 1
        sql = _strip_comments(raw)
        rel = str(sql_file.relative_to(project_root))

        # Detect CREATE TABLE
        for m in _CREATE_TABLE_RE.finditer(sql):
            tname = m.group("table").lower()
            if tname not in tables:
                tables[tname] = RLSTableInfo(name=tname)

        # Detect ENABLE ROW LEVEL SECURITY
        for m in _RLS_ENABLE_RE.finditer(sql):
            tname = m.group("table").lower()
            if tname not in tables:
                tables[tname] = RLSTableInfo(name=tname)
            tables[tname].rls_enabled = True

        # Detect FORCE ROW LEVEL SECURITY
        for m in _RLS_FORCE_RE.finditer(sql):
            tname = m.group("table").lower()
            if tname not in tables:
                tables[tname] = RLSTableInfo(name=tname)
            tables[tname].rls_forced = True

        # Detect DROP POLICY — remove matching policy from table
        for m in _DROP_POLICY_RE.finditer(sql):
            tname = m.group("table").lower()
            pname = _normalize_name(m.group("name"))
            if tname in tables:
                tables[tname].policies = [
                    p for p in tables[tname].policies if p.name != pname
                ]
            all_policies[:] = [
                p for p in all_policies if not (p.table == tname and p.name == pname)
            ]

        # Detect CREATE POLICY
        for m in _CREATE_POLICY_RE.finditer(sql):
            pname = _normalize_name(m.group("name"))
            tname = m.group("table").lower()
            rest = m.group("rest")
            command, using_expr, with_check_expr = _parse_policy_rest(rest)

            # Approximate source line
            start = m.start()
            line_no = raw[:start].count("\n") + 1

            policy = RLSPolicy(
                name=pname,
                table=tname,
                command=command,
                using_expr=using_expr,
                with_check_expr=with_check_expr,
                source_file=rel,
                source_line=line_no,
            )

            if tname not in tables:
                tables[tname] = RLSTableInfo(name=tname)

            # Remove any existing policy with same name before adding
            tables[tname].policies = [
                p for p in tables[tname].policies if p.name != pname
            ]
            tables[tname].policies.append(policy)
            all_policies[:] = [
                p for p in all_policies if not (p.table == tname and p.name == pname)
            ]
            all_policies.append(policy)

    return tables, all_policies, files_scanned


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------


def _is_sensitive_table(name: str) -> bool:
    n = name.lower()
    return any(token in n for token in _SENSITIVE_TABLE_TOKENS)


def _is_moderatable_table(name: str) -> bool:
    n = name.lower()
    return any(token in n for token in _MODERATABLE_TABLE_TOKENS)


def _expr_is_too_permissive(expr: str) -> bool:
    """True if the expression is `true` or a bare `auth.uid() IS NOT NULL`."""
    return bool(_TRUE_ONLY_RE.match(expr)) or bool(_AUTH_UID_NOT_NULL_RE.match(expr))


def _expr_uses_auth_role_authenticated(expr: str) -> bool:
    return bool(_AUTH_ROLE_AUTHENTICATED_RE.search(expr))


def _expr_lacks_tenant_scope(expr: str) -> bool:
    """True when expression contains no multi-tenant column reference."""
    return not bool(_TENANT_SCOPE_RE.search(expr))


def _schema_has_tenant_columns(all_policies: list[RLSPolicy]) -> bool:
    """Return True if ANY policy in the project references a tenant column."""
    return any(
        _TENANT_SCOPE_RE.search(p.using_expr + p.with_check_expr) for p in all_policies
    )


def _analyze_table(
    info: RLSTableInfo,
    project_has_tenant_columns: bool,
) -> list[RLSFinding]:
    findings: list[RLSFinding] = []

    # RLS not enabled
    if not info.rls_enabled:
        findings.append(
            RLSFinding(
                severity="ERROR",
                table=info.name,
                rule="NO_RLS",
                message=f"Table '{info.name}' has no RLS enabled.",
                recommendation=(
                    f"Add: ALTER TABLE {info.name} ENABLE ROW LEVEL SECURITY;"
                ),
            )
        )
        return findings  # further policy checks are moot without RLS

    # RLS enabled but no policies
    if not info.policies:
        findings.append(
            RLSFinding(
                severity="ERROR",
                table=info.name,
                rule="NO_POLICIES",
                message=(
                    f"Table '{info.name}' has RLS enabled but no policies"
                    " — all access denied."
                ),
                recommendation=(
                    f"Add at least one policy on '{info.name}'"
                    " or verify this is intentional."
                ),
            )
        )
        return findings

    # Gather commands covered by policies
    commands_covered: set[str] = set()
    for p in info.policies:
        if p.command == "ALL":
            commands_covered.update({"SELECT", "INSERT", "UPDATE", "DELETE"})
        else:
            commands_covered.add(p.command)

    for policy in info.policies:
        source_ref = f"{policy.source_file}:{policy.source_line}"

        # INSERT without WITH CHECK
        if policy.command in ("INSERT", "ALL") and not policy.with_check_expr:
            findings.append(
                RLSFinding(
                    severity="WARNING",
                    table=info.name,
                    rule="INSERT_NO_WITH_CHECK",
                    message=(
                        f"Policy '{policy.name}' on '{info.name}' covers INSERT"
                        " but has no WITH CHECK clause."
                    ),
                    recommendation=(
                        "Add WITH CHECK to validate the inserted row's ownership."
                    ),
                    source_file=source_ref,
                )
            )

        # UPDATE without WITH CHECK
        if policy.command in ("UPDATE", "ALL") and not policy.with_check_expr:
            findings.append(
                RLSFinding(
                    severity="WARNING",
                    table=info.name,
                    rule="UPDATE_NO_WITH_CHECK",
                    message=(
                        f"Policy '{policy.name}' on '{info.name}' covers UPDATE"
                        " but has no WITH CHECK clause."
                    ),
                    recommendation=(
                        "Add WITH CHECK to prevent privilege escalation on update."
                    ),
                    source_file=source_ref,
                )
            )

        # auth.role() = 'authenticated' — overly broad
        for expr in (policy.using_expr, policy.with_check_expr):
            if expr and _expr_uses_auth_role_authenticated(expr):
                findings.append(
                    RLSFinding(
                        severity="WARNING",
                        table=info.name,
                        rule="AUTH_ROLE_AUTHENTICATED",
                        message=(
                            f"Policy '{policy.name}' on '{info.name}' uses"
                            " auth.role() = 'authenticated'"
                            " — any logged-in user passes."
                        ),
                        recommendation=(
                            "Replace with a specific condition: auth.uid() = user_id"
                            " or a role check function."
                        ),
                        source_file=source_ref,
                    )
                )
                break

        # SELECT too permissive
        if policy.command in ("SELECT", "ALL") and policy.using_expr:
            if _expr_is_too_permissive(policy.using_expr):
                sev = "ERROR" if _is_sensitive_table(info.name) else "WARNING"
                findings.append(
                    RLSFinding(
                        severity=sev,
                        table=info.name,
                        rule="SELECT_TOO_PERMISSIVE",
                        message=(
                            f"Policy '{policy.name}' on '{info.name}'"
                            " has a SELECT USING clause that allows all rows."
                        ),
                        recommendation=(
                            "Scope SELECT to auth.uid() = user_id"
                            " or restrict to authorized roles."
                        ),
                        source_file=source_ref,
                    )
                )

        # INSERT/UPDATE scope without tenant filter when project uses tenants
        if project_has_tenant_columns and policy.command in ("INSERT", "UPDATE", "ALL"):
            check_expr = policy.with_check_expr or policy.using_expr
            if check_expr and _expr_lacks_tenant_scope(check_expr):
                findings.append(
                    RLSFinding(
                        severity="WARNING",
                        table=info.name,
                        rule="MISSING_TENANT_SCOPE",
                        message=(
                            f"Policy '{policy.name}' on '{info.name}' writes data"
                            " without a tenant/commune scope filter."
                        ),
                        recommendation=(
                            "Add a commune_id / tenant_id / org_id filter"
                            " to prevent cross-tenant writes."
                        ),
                        source_file=source_ref,
                    )
                )

    # No DELETE policy on moderatable tables
    if _is_moderatable_table(info.name) and "DELETE" not in commands_covered:
        findings.append(
            RLSFinding(
                severity="WARNING",
                table=info.name,
                rule="NO_DELETE_POLICY",
                message=(
                    f"Table '{info.name}' contains user content"
                    " but has no DELETE policy — users cannot delete"
                    " their own entries and admins cannot moderate."
                ),
                recommendation=(
                    "Add a self-delete policy (auth.uid() = user_id) and a moderation"
                    " delete policy for agents/admins."
                ),
            )
        )

    # Sensitive table SELECT open to any authenticated user
    if _is_sensitive_table(info.name):
        for policy in info.policies:
            if policy.command in ("SELECT", "ALL") and policy.using_expr:
                if _expr_is_too_permissive(
                    policy.using_expr
                ) or _expr_uses_auth_role_authenticated(policy.using_expr):
                    # Already captured above; skip duplicate
                    pass
                elif _AUTH_UID_NOT_NULL_RE.search(policy.using_expr):
                    findings.append(
                        RLSFinding(
                            severity="ERROR",
                            table=info.name,
                            rule="SENSITIVE_TABLE_OPEN_SELECT",
                            message=(
                                f"Sensitive table '{info.name}' has SELECT open to all"
                                " authenticated users — may expose private fields."
                            ),
                            recommendation=(
                                "Restrict SELECT to the row owner"
                                " (auth.uid() = user_id) or to specific roles."
                            ),
                            source_file=f"{policy.source_file}:{policy.source_line}",
                        )
                    )

    return findings


def _build_recommendations(
    tables: dict[str, RLSTableInfo],
    findings: list[RLSFinding],
) -> list[str]:
    recs: list[str] = []
    rules_seen: set[str] = {f.rule for f in findings}

    if "NO_RLS" in rules_seen:
        affected = [f.table for f in findings if f.rule == "NO_RLS"]
        recs.append(
            f"Enable RLS on {len(affected)} table(s) without protection: "
            + ", ".join(affected[:5])
            + ("..." if len(affected) > 5 else "")
        )

    if "NO_POLICIES" in rules_seen:
        affected = [f.table for f in findings if f.rule == "NO_POLICIES"]
        recs.append(
            f"Add policies to {len(affected)} table(s) with RLS but no policies: "
            + ", ".join(affected[:5])
        )

    if "INSERT_NO_WITH_CHECK" in rules_seen:
        recs.append(
            "Add WITH CHECK to INSERT policies to validate row ownership at write time."
        )

    if "UPDATE_NO_WITH_CHECK" in rules_seen:
        recs.append(
            "Add WITH CHECK to UPDATE policies to prevent privilege escalation."
        )

    if "AUTH_ROLE_AUTHENTICATED" in rules_seen:
        recs.append(
            "Replace auth.role() = 'authenticated'"
            " with specific user or role conditions."
        )

    if "SELECT_TOO_PERMISSIVE" in rules_seen:
        recs.append(
            "Scope SELECT policies: use auth.uid() = user_id"
            " or restrict to authorized roles."
        )

    if "MISSING_TENANT_SCOPE" in rules_seen:
        recs.append(
            "Add commune_id / tenant_id / org_id filters to INSERT/UPDATE policies"
            " to enforce multi-tenant isolation."
        )

    if "NO_DELETE_POLICY" in rules_seen:
        affected = [f.table for f in findings if f.rule == "NO_DELETE_POLICY"]
        recs.append(
            f"Add DELETE policies to moderatable table(s): {', '.join(affected)}."
            " Include self-delete and agent/admin moderation rules."
        )

    if "SENSITIVE_TABLE_OPEN_SELECT" in rules_seen:
        affected = [
            f.table for f in findings if f.rule == "SENSITIVE_TABLE_OPEN_SELECT"
        ]
        recs.append(
            f"Restrict SELECT on sensitive table(s): {', '.join(affected)}."
            " Limit exposure of phone, email, or financial data."
        )

    if not findings:
        recs.append(
            "No RLS issues detected — keep policies under review as schema evolves."
        )

    return recs


def _compute_status(findings: list[RLSFinding]) -> str:
    if any(f.severity == "ERROR" for f in findings):
        return "ERROR"
    if any(f.severity == "WARNING" for f in findings):
        return "WARNING"
    return "OK"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_rls_inspect(path: Path) -> RLSInspectResult:
    """
    Inspect Supabase RLS policies from local migration files.
    Read-only — does not connect to any database, does not read .env,
    does not modify any file.
    """
    resolved = path.resolve()
    migrations_dir = resolved / "supabase" / "migrations"

    if not migrations_dir.is_dir():
        return RLSInspectResult(
            path=resolved,
            status="OK",
            migrations_scanned=0,
            recommendations=[
                "No supabase/migrations/ directory found — nothing to inspect."
            ],
        )

    tables, all_policies, files_scanned = _scan_migrations(migrations_dir, resolved)

    project_has_tenant_columns = _schema_has_tenant_columns(all_policies)

    findings: list[RLSFinding] = []
    for info in tables.values():
        findings.extend(_analyze_table(info, project_has_tenant_columns))

    # Sort: ERROR first, then WARNING, then OK; stable within each group
    _sev_order = {"ERROR": 0, "WARNING": 1, "OK": 2}
    findings.sort(key=lambda f: (_sev_order.get(f.severity, 9), f.table))

    recommendations = _build_recommendations(tables, findings)
    status = _compute_status(findings)

    return RLSInspectResult(
        path=resolved,
        status=status,
        migrations_scanned=files_scanned,
        tables=list(tables.values()),
        policies=all_policies,
        findings=findings,
        recommendations=recommendations,
    )
