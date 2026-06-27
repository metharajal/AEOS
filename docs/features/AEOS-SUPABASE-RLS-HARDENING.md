# AEOS Supabase RLS Hardening Chain

**Date:** 2026-06-28
**Status:** Feature — Stable MVP
**Sprints:** 2T · 2U · 2V · 2W
**Commands:** `aeos supabase rls inspect | plan | generate | review`

---

## Summary

AEOS provides a local-first, read-only RLS hardening chain for Supabase projects.

It analyzes existing SQL migration files, identifies Row Level Security weaknesses,
produces a prioritized remediation plan, proposes an executable SQL migration, and
evaluates that migration for safety — all without connecting to any database, reading
any `.env` file, or modifying any file in the client project.

The chain is designed to assist a human engineer, not to replace their judgment.
No SQL is applied automatically. No migration is created in the client project.

---

## Doctrine

### Local-first

AEOS reads SQL migration files from the local filesystem.
No Supabase connection is required.
No API key, no project URL, no service role key is ever read or needed.
The entire analysis runs offline.

### Read-only by default

Every command in the chain carries two invariants that are enforced in code and
verified in tests:

- `read_only: true` — the command never modifies any file.
- `applied: false` — the command never applies any migration to any database.

These invariants cannot be disabled by a flag or option.

### No secret access

AEOS does not read `.env` files.
AEOS does not display secrets.
The review gate actively scans generated SQL for known secret patterns
(`anon_key`, `service_role_key`, `SUPABASE_URL`, `jwt_secret`, etc.) and
blocks the migration if any are found.

### No automatic apply

The chain ends at `review`.
There is no `aeos supabase rls apply` command in the current release.
Applying a migration to a real database is a deliberate human action, performed
outside AEOS, after reviewing and testing the proposed SQL.

### Human review required

The `generate` command produces a SQL proposal.
The `review` command evaluates that proposal and emits a verdict.
Neither command applies anything.
The engineer reads the verdict, inspects the SQL, runs their own tests, and decides
whether and how to apply the migration.

AEOS is a preparation tool, not an execution tool.

---

## The Chain

```
inspect → plan → generate → review
```

### 1. `aeos supabase rls inspect`

**What it does:**
Parses all SQL migration files in `supabase/migrations/`.
Detects tables, policies, and RLS status without connecting to the database.
Identifies security weaknesses in policy definitions.

**Findings produced:**

| Finding | Meaning |
|---|---|
| `NO_RLS` | Table exists but RLS is not enabled |
| `NO_POLICIES` | RLS is enabled but no policy is defined |
| `SELECT_TOO_PERMISSIVE` | SELECT policy allows all rows (`USING (true)` or `auth.uid() IS NOT NULL`) |
| `MISSING_TENANT_SCOPE` | INSERT/UPDATE policy has no `commune_id` / `tenant_id` filter |
| `UPDATE_NO_WITH_CHECK` | UPDATE policy has no `WITH CHECK` clause |
| `INSERT_NO_WITH_CHECK` | INSERT policy has no `WITH CHECK` clause |
| `NO_DELETE_POLICY` | Table with user content has no DELETE policy |

**Severity levels:** `ERROR` (CRITICAL) · `WARNING` (HIGH/MEDIUM) · `INFO` (LOW)

**Output:** tables, policies, findings, recommendations.

---

### 2. `aeos supabase rls plan`

**What it does:**
Converts inspector findings into a prioritized remediation plan.
Groups actions by priority and identifies the riskiest tables.

**Priority tiers:**

| Priority | Condition |
|---|---|
| `CRITICAL` | `SELECT_TOO_PERMISSIVE` — data leakage risk across tenants or users |
| `HIGH` | `MISSING_TENANT_SCOPE`, `UPDATE_NO_WITH_CHECK`, `INSERT_NO_WITH_CHECK`, `NO_RLS`, `NO_POLICIES` |
| `MEDIUM` | `NO_DELETE_POLICY`, `SELECT_TOO_PERMISSIVE` on public reference data |
| `LOW` | Informational |

**Fix order:** `CRITICAL → HIGH → MEDIUM → LOW`

**Output:** ordered action list with problem, fix, impact, test hint, and source file/line.

---

### 3. `aeos supabase rls generate`

**What it does:**
Converts the plan into a proposed SQL migration.
Groups related rules on the same `(table, policy)` pair into a single coherent block.
Produces a `BEGIN / COMMIT`-wrapped SQL file with two block types:

**Auto-generated blocks** (`is_todo: false`):
Executable `DROP POLICY IF EXISTS` + `CREATE POLICY` pairs.
Produced when AEOS has enough context to write a correct fix automatically.
Safe to review and apply after human validation.

**TODO blocks** (`is_todo: true`):
Commented-out SQL proposals marked with `-- TODO`.
Produced when the fix requires human judgment (e.g., `SELECT_TOO_PERMISSIVE`,
`INSERT_NO_WITH_CHECK` without a detectable policy pattern).
Must be edited by a human before any application.

**Key generation behaviors:**
- Detects tenant column (`commune_id`, `tenant_id`, `org_id`) by scanning existing policies.
- Detects `public.has_role(...)` calls for role-based checks.
- Uses `(SELECT tenant_col FROM public.profiles WHERE id = auth.uid())` as the
  correlated subquery for tenant isolation.
- All UPDATE blocks add both `USING` and `WITH CHECK` with identical expressions.
- All INSERT blocks add `WITH CHECK` matching the tenant constraint.

**Invariants enforced:**
- `read_only: true`
- `applied: false`
- No file is written to the client project.
- No database connection is opened.

**Output:** `generated_sql` string (proposed migration), block list, warning list, test plan.

---

### 4. `aeos supabase rls review`

**What it does:**
Evaluates the proposed SQL migration for safety before any human applies it.
Classifies each block and emits a verdict.

**Block classification:**

| Class | Condition |
|---|---|
| `safe` | Non-TODO block with no dangerous patterns detected |
| `todo` | Block marked `is_todo: true` — commented-out, needs human edit |
| `blocked` | Non-TODO block with at least one dangerous pattern detected |

**Dangerous patterns detected (on non-comment SQL lines only):**

| Pattern | Risk |
|---|---|
| `DROP TABLE` | Destroys table and data |
| `TRUNCATE` | Empties table |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `UPDATE … SET` (no WHERE) | Overwrites all rows |
| `ALTER TABLE DROP COLUMN` | Irreversible schema change |
| `ALTER TABLE DROP CONSTRAINT` | Removes integrity constraint |
| `DROP SCHEMA` | Destroys entire schema |
| `DROP DATABASE` | Destroys entire database |
| `GRANT ALL` | Grants unrestricted privileges |
| `USING (true)` | Grants all-row read access |
| `WITH CHECK (true)` | Allows any write |

**Invariant checks:**
- `read_only` must be `true` in the generator result.
- `applied` must be `false` in the generator result.
- Generated SQL must not contain known secret patterns.

**Verdicts:**

| Verdict | Condition | Exit code |
|---|---|---|
| `PASS ✓` | All blocks safe, zero TODOs, no invariant violation | 0 |
| `WARNING ⚠` | Has TODO blocks (migration incomplete, needs human edits) | 0 |
| `BLOCKED ✗` | Any blocked block, or any invariant violation | 1 |

A `BLOCKED` verdict means the proposed migration must not be applied.
A `WARNING` verdict means the migration is incomplete — TODO blocks must be
resolved by a human before application.
A `PASS` verdict means all generated blocks are structurally safe to review
and apply after human validation.

**Note:** `WARNING` exits with code 0 intentionally. The chain is expected to
produce TODO blocks whenever AEOS cannot automatically fix a finding. This is
normal and not a failure — it signals work remaining for the engineer.

---

## Commands

```bash
# Full chain — text output
aeos supabase rls inspect  --path <project>
aeos supabase rls plan     --path <project>
aeos supabase rls generate --path <project>
aeos supabase rls review   --path <project>

# JSON output (for scripting or CI)
aeos supabase rls inspect  --path <project> --json
aeos supabase rls plan     --path <project> --json
aeos supabase rls generate --path <project> --json
aeos supabase rls review   --path <project> --json

# Include MEDIUM priority actions (default: CRITICAL + HIGH only)
aeos supabase rls generate --path <project> --include-medium
aeos supabase rls review   --path <project> --include-medium

# Export proposed SQL to a file (Sprint 2Y)
aeos supabase rls generate --path <project> --output <file>

# Export even when TODO blocks remain (WARNING verdict)
aeos supabase rls generate --path <project> --output <file> --force-warning

# Overwrite an existing output file
aeos supabase rls generate --path <project> --output <file> --overwrite
```

All commands accept `--path .` to target the current directory.

### `--output` export rules

The `--output` flag runs `generate` then `review` automatically and writes the
file only if the verdict permits:

| Verdict | Without flags | With `--force-warning` |
|---|---|---|
| `PASS` | Writes file ✅ | Writes file ✅ |
| `WARNING` | Refuses ✗ | Writes file ✅ |
| `BLOCKED` | Refuses ✗ | Refuses ✗ |

If the output file already exists, `--overwrite` is required.
The written file embeds: AEOS header, date, verdict, `read_only: true`,
`applied: false`, summary, warnings, TODO list, and the proposed SQL.
No migration is applied. No database connection is opened.

---

## Recommended Workflow

```
1. Run inspect   → identify all RLS weaknesses
2. Run plan      → understand priorities and riskiest tables
3. Run generate  → get the SQL proposal
4. Read the SQL  → review every block manually
5. Run review    → verify no dangerous pattern was generated
6. Edit TODOs    → resolve manual blocks with project knowledge
7. Run tests     → validate access for all user roles on a staging database
8. Apply         → execute the SQL on the target database (outside AEOS)
9. Verify        → confirm policies in Supabase dashboard or via SQL query
```

Steps 1–6 are local, read-only, and safe to run at any time.
Steps 7–9 are performed by the engineer, outside AEOS, after human validation.

---

## Validated Example: ma-mairie-digitale

Results from a real Supabase project (multi-tenant civic platform, 27 tables):

| Step | Result |
|---|---|
| Migrations scanned | 8 |
| Tables detected | 27 / 27 with RLS enabled |
| Policies detected | 74 |
| Findings | 67 (CRITICAL: 3 · HIGH: 50 · MEDIUM: 14) |
| Plan actions | 67 total |
| Generated blocks | 38 (auto: 25 · TODO: 13) |
| Review verdict | **WARNING ⚠** |
| Safe blocks | 25 |
| TODO blocks | 13 |
| Blocked blocks | 0 |
| `read_only` | `true` |
| `applied` | `false` |
| Secrets found | `[]` |
| Files modified in client project | **0** |
| Migrations applied | **0** |

The three CRITICAL findings were `SELECT_TOO_PERMISSIVE` policies on `budget_entries`,
`budget_projets`, and `personnel` — all exposing sensitive municipal data to any
authenticated user regardless of commune. These were correctly flagged as TODO blocks
(requiring human review before narrowing SELECT scope) rather than auto-applied fixes.

---

## What AEOS Does

- Parses SQL migrations locally without a database connection.
- Detects RLS weaknesses with static analysis.
- Generates a prioritized remediation plan.
- Proposes idempotent SQL fixes (`DROP POLICY IF EXISTS` + `CREATE POLICY`).
- Classifies uncertain fixes as TODO blocks with commented-out proposals.
- Detects dangerous patterns in generated SQL.
- Enforces `read_only` and `applied` invariants in code and in tests.
- Supports text and JSON output for human review and CI integration.

## What AEOS Does Not Do (Yet)

- Apply any migration to any database.
- Connect to Supabase or any remote service.
- Read `.env` files or access secrets.
- Write any file to the client project.
- Validate SQL syntax against a live schema.
- Run integration tests against a staging database.
- Export the proposed SQL to a versioned migration file.

---

## Current Limitations

**Tenant column detection is heuristic.**
AEOS scans existing policies for known column names (`commune_id`, `tenant_id`,
`org_id`, `organization_id`, `team_id`). If the project uses a non-standard column
name, AEOS may miss the tenant scope or generate a subquery with the wrong column.
Always verify the generated `WITH CHECK` expressions before applying.

**`INSERT_NO_WITH_CHECK` without a detectable pattern → TODO.**
When an INSERT policy has no `WITH CHECK` and AEOS cannot determine the correct
ownership constraint from the policy body, it emits a TODO block. This is intentional
and conservative — a wrong `WITH CHECK` can silently lock users out.

**`SELECT_TOO_PERMISSIVE` → always TODO.**
Narrowing SELECT scope changes who can read data. AEOS never auto-applies this
because the business intent (intentional public read vs. accidental over-permission)
cannot be inferred from SQL alone. The engineer must decide.

**One level of nested parentheses.**
The `has_role(auth.uid(), 'agent'::app_role)` pattern is correctly handled.
Deeper nesting (rare in practice) may not be detected.

**No DELETE policy generation.**
`NO_DELETE_POLICY` findings are reported but not auto-fixed. DELETE policies require
understanding the business rules around moderation and self-deletion that vary per table.

---

## Proposed Next Steps

### Sprint 2Y — RLS Export ✅ (delivered)

`aeos supabase rls generate --path <project> --output <file>`

Implemented as an option on the existing `generate` command (not a separate command).
Runs generate → review → writes file conditionally based on verdict.
Supports `--force-warning` and `--overwrite`. Never applies anything.

### Sprint 2Z — RLS Test Plan

`aeos supabase rls test-plan --path <project>`

Generate a structured test plan in Markdown or JSON: one test case per block,
with pre-condition, action, and expected result. Designed to be executed manually
or fed into a test framework against a staging database.

### Sprint 3A — RLS Apply Gate

`aeos supabase rls apply --path <project> --confirm`

Apply the reviewed and exported migration to a target database.
Requires explicit `--confirm` flag.
Requires a prior successful `review` with `PASS` or `WARNING` verdict and all TODOs resolved.
Runs inside a transaction and rolls back on any error.
Never runs on production without an explicit `--env production --confirm` double gate.
