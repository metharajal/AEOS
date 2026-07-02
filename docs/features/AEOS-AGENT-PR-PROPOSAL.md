# AEOS Agent PR Proposal

**Sprint:** MVP-AGENTS-4
**Status:** SHIPPED

---

## Summary

MVP-AGENTS-4 adds `aeos agent pr-proposal` — a deterministic, read-only command that
generates a structured 14-section PR proposal from the local project registry and
`MemoryRecord` history.

No LLM. No network. No .env. No registry mutation. `read_only: true · applied: false`.

---

## CLI

```bash
# Terminal summary (default)
aeos agent pr-proposal --project <name>

# Write full Markdown proposal to file
aeos agent pr-proposal --project <name> --output /tmp/aeos-pr-proposal.md

# Machine-readable JSON
aeos agent pr-proposal --project <name> --json

# Custom registry path
aeos agent pr-proposal --project <name> --registry ~/.aeos/projects.json
```

---

## 14-section proposal

| # | Section | Source |
|---|---------|--------|
| 1 | Title | Decision rules on critical/generated/important findings |
| 2 | Objective | Derived from finding counts and production-readiness |
| 3 | Why This PR Now | Reasons from MemoryRecord aggregates |
| 4 | Recommended Scope | Actions matched to risk level |
| 5 | Out of Scope | Always includes production deploy, credential rotation |
| 6 | Likely Files | Provider-aware (supabase/, docs/governance/) |
| 7 | Safety Constraints | Fixed list — no secrets, no prod migration |
| 8 | Suggested Implementation Steps | Numbered, project-name-scoped |
| 9 | Validation Commands | git status + aeos agent plan + evidence pack |
| 10 | Human Approval Checklist | No secrets, no prod migration, CTO sign-off |
| 11 | Risks | Derived from control_level, finding counts |
| 12 | Rollback Notes | Always: git revert, aeos workspace demo --overwrite |
| 13 | Evidence References | Record count, finding aggregates, latest record ID |
| 14 | Final Statement | "No changes were applied. This is a proposal only." |

---

## Title decision rules

Priority cascade (first match wins):

1. `critical > 0` → `"security: validate RLS hardening and resolve {N} critical finding(s) for {project}"`
2. `generated > 0` (no critical) → `"security: stage {N} SQL hardening block(s) and validate {project} on staging"`
3. `important > 0` (no critical, no generated) → `"security: address {N} important finding(s) and staging validation for {project}"`
4. `control_level == "weak"` → `"governance: strengthen project control and document sovereignty policy for {project}"`
5. `not production_ready` → `"security: resolve remaining production blockers for {project}"`
6. all OK → `"docs: release readiness review for {project}"`

---

## Files

| File | Role |
|------|------|
| `src/aeos/agent/pr_proposal.py` | Core: `PRProposal` dataclass, 10 `_build_*` helpers, `generate_pr_proposal()`, 3 renderers |
| `src/aeos/agent/__init__.py` | Exports `PRProposal`, `generate_pr_proposal` |
| `src/aeos/cli.py` | `@agent_app.command("pr-proposal")` — added at end of file |
| `tests/unit/test_agent_pr_proposal.py` | 42 unit tests: library, renderers, CLI, safety invariants |

---

## Safety invariants

- `read_only: true` always in all output modes
- `applied: false` always
- `human_validation_required: true` always
- Final statement: `"No changes were applied. This is a proposal only."`
- Registry: read-only (mtime unchanged after any call)
- Memory dir: read-only (no new files written)
- No LLM references in any generated field
- Production migration always in `out_of_scope`
- Credential rotation always in `out_of_scope`

---

## PRProposal dataclass

```python
@dataclass
class PRProposal:
    project_name: str
    generated_at: str
    agent_mode: str
    title: str
    objective: str
    why_now: list[str]
    recommended_scope: list[str]
    out_of_scope: list[str]
    likely_files: list[str]
    safety_constraints: list[str]
    implementation_steps: list[str]
    validation_commands: list[str]
    approval_checklist: list[str]
    risks: list[str]
    rollback_notes: list[str]
    evidence_references: dict[str, object]
    read_only: bool = True
    applied: bool = False
    human_validation_required: bool = True
    final_statement: str = field(
        default="No changes were applied. This is a proposal only."
    )
```
