# AEOS Architecture

**Version:** 1.0.0
**Status:** Living Document
**Date:** 2026-06-30
**Governed by:** [CONSTITUTION.md](CONSTITUTION.md) §5.3

---

## 1. Identity

AEOS is a **sovereign software continuity platform** — a local-first, open-source-first, AI-local-first engineering operating system for creating, reclaiming, modernizing, migrating, evolving, and operating digital products with AI.

AEOS is not a code generator. It is not an AI wrapper. It is the governance layer above AI tools, cloud platforms, and legacy systems that ensures software ownership, portability, and sovereignty.

---

## 2. Core Doctrine

```
AEOS Core guarantees.
AEOS Agents reason.
AEOS Memory learns.
Humans validate.
```

**Absolute invariants (code-enforced):**

- `read_only: true` — all inspection commands are non-destructive by default
- `applied: false` — no action is applied without explicit human gate
- No secret exposure — values never appear in output, logs, or transmitted context
- No silent frontier escalation — `require_human_approval = true` stops and asks
- No destructive action without gate — Level 4 required
- No autonomous production change — explicit human confirmation at Level 4

---

## 3. Eight Core Capabilities

AEOS is defined by eight permanent capabilities (CONSTITUTION §1.4):

| Capability | Description |
|---|---|
| **Discover** | Inspect and map project structure, dependencies, providers, and risks |
| **Assess** | Classify findings, score sovereignty and security, produce evidence |
| **Recover** | Restore control: governance, secrets, RLS, tests, portability |
| **Transform** | Move from one architecture to another: controlled, tested, reversible |
| **Continue** | Resume development with AI assistance under sovereignty constraints |
| **Govern** | Enforce standards, manage decisions, maintain architecture documentation |
| **Operate** | Continuous audit, drift detection, periodic reports, memory timeline |
| **Learn** | Accumulate validated knowledge across audits, tests, and decisions |

---

## 4. Ten Platform Engines

AEOS implements capabilities through ten engines (CONSTITUTION §1.5). Each engine is infra-independent and composable:

| Engine | Capability(ies) | Location |
|---|---|---|
| **Discovery Engine** | Discover | `src/aeos/reclaim/inspector.py` |
| **Assessment Engine** | Assess | `src/aeos/reclaim/inspector.py`, `src/aeos/supabase/` |
| **Recovery Engine** | Recover | `src/aeos/reclaim/recovery.py`, `src/aeos/reclaim/planner.py` |
| **Transformation Engine** | Transform | `src/aeos/reclaim/stages.py` (stage_7) |
| **Continuation Engine** | Continue | `src/aeos/build/` |
| **Governance Engine** | Govern | `src/aeos/build/planner.py` |
| **Operations Engine** | Operate | `src/aeos/reclaim/stages.py` (stage_9) |
| **Memory Engine** | Learn | `src/aeos/memory/` |
| **Evidence Engine** | Assess, Recover | `src/aeos/reclaim/evidence.py` |
| **AI Routing Engine** | All | `src/aeos/ai/router.py` |

The engine catalog evolves through the Standards process. The engine-based architecture principle is constitutional.

---

## 5. Nine Product Rails

Rails are user-facing delivery paths that combine multiple capabilities and engines:

| Rail | Maps to Capability | Status |
|---|---|---|
| Build Rail | Continue, Govern | MVP — `aeos build plan`, `aeos build scaffold` |
| Reclaim Rail | Discover, Assess, Recover | Production — `aeos reclaim inspect`, `aeos reclaim harden`, `aeos reclaim recovery plan` |
| Modernize Rail | Discover, Assess, Transform | Planned |
| Migrate Rail | Transform, Recover | Planned |
| Operate Rail | Operate, Assess | Planned |
| Security Rail | Assess, Govern | Partial — `aeos security check`, `aeos supabase rls harden` |
| Sovereignty Rail | Assess, Govern | Partial — `aeos sovereignty check` |
| Agents Rail | All | Evolving — cross-cutting |
| Memory Rail | Learn | Production — `aeos memory list`, `aeos memory show`, `aeos memory compare`, `aeos memory timeline` |

---

## 6. Four Platform Interfaces

(CONSTITUTION §1.7)

| Interface | Role | Status |
|---|---|---|
| **CLI** | Primary interface — authoritative definition of correct behavior | Production |
| **API** | Programmatic access — mirrors CLI semantics | Planned |
| **Workspace** | Integrated GUI for guided recovery and operation | Planned |
| **Agents** | Autonomous task execution within human-gated boundaries | Evolving |

When behavior differs between interfaces, CLI defines correct behavior.

---

## 7. Source Module Structure

```
src/aeos/
├── cli.py                          # Typer CLI — primary entry point
├── version.py
├── ai/
│   ├── router.py                   # AI Routing Engine — local-first, frontier by exception
│   ├── local.py                    # Local AI provider (Ollama)
│   ├── frontier.py                 # Frontier AI provider (OpenAI-compatible)
│   ├── config.py                   # AI configuration parsing
│   └── doctor.py                   # Local runtime health check
├── build/
│   ├── planner.py                  # BuildPlan, stack selection
│   └── scaffold.py                 # Governance file scaffolding
├── generators/
│   ├── base.py                     # Base generator contract
│   ├── basic.py                    # Basic file generators
│   └── python.py                   # Python project generators
├── memory/
│   ├── models.py                   # MemoryRecord, MemoryRecordSummary
│   ├── store.py                    # Local read/write, no cloud sync
│   ├── compare.py                  # Diff between two records
│   └── timeline.py                 # Project audit history
├── onboarding/
│   └── checker.py                  # Onboarding state verification
├── project/
│   └── inspector.py                # General project inspection
├── providers/
│   └── supabase/
│       ├── checker.py              # Supabase-specific analysis
│       └── rls/
│           ├── inspector.py        # RLS policy inspection
│           ├── hardener.py         # RLS hardening proposals
│           ├── generator.py        # RLS SQL generation
│           ├── planner.py          # RLS remediation planning
│           └── reviewer.py         # RLS policy review
├── reclaim/
│   ├── inspector.py                # Discovery + Assessment engines
│   ├── hardener.py                 # Security and sovereignty checks
│   ├── recovery.py                 # Recovery plan generation
│   ├── planner.py                  # Staged recovery planning
│   ├── stages.py                   # Ten recovery stages definition
│   └── evidence.py                 # Evidence Engine
├── report/
│   └── generator.py                # Report generation
├── security/
│   └── checker.py                  # Secret detection (names only, never values)
└── sovereignty/
    └── checker.py                  # External dependency audit
```

**Conventions (CONSTITUTION §5.1):**

- `from __future__ import annotations` in every module
- `@dataclass` with `field(default_factory=list)` for mutable defaults
- All outputs are read-only data structures — no side effects without explicit gates
- `MemoryRecord`: safe serializable snapshot, never contains secret values
- `EvidenceReport`: evidence from caller-declared confirmed indices — never auto-detected

---

## 8. Three Level Systems

AEOS uses three orthogonal level systems (CONSTITUTION §1.6). They are not interchangeable:

### Action Levels (0–5) — operation authorization

| Level | Name | Human gate |
|---|---|---|
| 0 | Diagnose | None — fully autonomous read-only |
| 1 | Plan | Human reviews before proceeding |
| 2 | Prepare | Human reviews output before merge |
| 3 | Propose PR | Human merges the PR |
| 4 | Execute with approval | Explicit confirmation required |
| 5 | Operate continuously | Human reviews periodic reports |

All current CLI commands operate at Level 0–3.

### Project Maturity (weak → sovereign) — project recovery state

`weak` → `partial` → `controlled` → `portable` → `sovereign`

Measures how controlled, governed, and portable a project is.

### Sovereignty Levels (1–5) — cloud infrastructure dependency

1 — Controlled Productivity · 2 — Personal Cloud Control · 3 — Managed Open Source · 4 — Self-Hosted · 5 — Full Sovereign Stack

Measures the degree of independence from external cloud providers.

---

## 9. Ten Recovery Stages

The standard recovery arc for an AI-generated or fragile project:

```
stage_0_baseline           →  understand current state
stage_1_governance         →  create governance baseline
stage_2_secrets_env        →  stabilize secrets and environment
stage_3_database_rls       →  harden database access
stage_4_tests_ci           →  establish test baseline and CI gate
stage_5_local_run          →  make project runnable locally
stage_6_portability        →  achieve full portability
stage_7_migration_readiness →  assess and prepare migration
stage_8_local_ai_continuation → enable local-AI-first development
stage_9_sovereign_operating_mode → maintain sovereignty over time
```

Stages 0 and 1 are always mandatory. Stage 7 is entered only on explicit human decision to migrate.

---

## 10. AI Routing Architecture

```
ask_ai(prompt, config, provider="local")
    → "local"    → Ollama / local endpoint (default)
    → "frontier" → OpenAI-compatible (require_human_approval checked)
    → "auto"     → tries local first;
                   if require_human_approval=True and local fails → raises error
                   (never silently escalates to frontier)
```

**AI policy invariants:**

- Local AI by default
- Frontier AI by exception — explicit provider="frontier" only
- `require_human_approval = true` — stops and asks, never silently escalates
- No `.env` values, secrets, or sensitive data in any AI context
- All frontier calls logged

---

## 11. Quality Gates

Non-negotiable (CONSTITUTION §5.2):

```
ruff check .          # linting and style
mypy src              # strict type checking
pytest                # 1400+ tests
```

All three must pass before any merge. CI gate enforces this.

---

## 12. Standards Hierarchy

```
MANIFESTO.md           (supreme — immutable)
  └── CONSTITUTION.md  (identity and invariants)
        ├── governance/standards/   (implementation standards)
        │     └── governance/playbooks/  (operational procedures)
        │           └── governance/adr/  (architecture decisions)
        ├── governance/dec/         (ratified platform decisions)
        └── governance/rfc/         (proposals — not decisions)
```

---

## See Also

- [MANIFESTO.md](MANIFESTO.md) — supreme document, immutable
- [CONSTITUTION.md](CONSTITUTION.md) — identity, invariants, and governance
- [docs/DECISIONS.md](docs/DECISIONS.md) — decision log
- [docs/SECURITY.md](docs/SECURITY.md) — security policy
- [docs/SOVEREIGNTY.md](docs/SOVEREIGNTY.md) — sovereignty posture
- [docs/AI-DEVELOPMENT-POLICY.md](docs/AI-DEVELOPMENT-POLICY.md) — AI usage policy
- [docs/strategy/AEOS-PRODUCT-VISION.md](docs/strategy/AEOS-PRODUCT-VISION.md) — strategic vision
- [docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md](docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md) — rails and agents matrix
