# AEOS Reclaim Recovery Plan

**Version :** Sprint 5A — 2026-06-30
**Statut :** MVP livré — `aeos reclaim recovery plan` disponible
**Rail :** Reclaim

---

## 1. Rôle de la commande

`aeos reclaim recovery plan` génère un **plan de récupération complet** pour un projet existant.

Le plan couvre 13 sections, est entièrement **read-only** (aucun fichier modifié, aucune base de données contactée, aucun secret lu), et peut être exporté en Markdown ou JSON.

> **Récupérer ne signifie pas corriger immédiatement.**
> Récupérer signifie comprendre l'état réel, identifier les blocages critiques, et définir un chemin de retour au contrôle.

---

## 2. Usage

```bash
aeos reclaim recovery plan --path <path>
aeos reclaim recovery plan --path <path> --json
aeos reclaim recovery plan --path <path> --output recovery.md
aeos reclaim recovery plan --path <path> --output recovery.md --overwrite
```

### Options

| Option | Description |
|---|---|
| `--path` / `-p` | Chemin vers le projet à analyser (défaut : `.`) |
| `--json` | Sortie JSON au lieu de texte |
| `--output` / `-o` | Exporter le plan complet en Markdown dans ce fichier |
| `--overwrite` | Écraser le fichier `--output` s'il existe déjà |

---

## 3. Sections du plan (13)

| Section | Contenu |
|---|---|
| 1. Project Identity | Chemin, nom, générateurs et providers détectés |
| 2. Current Architecture | Frontend, backend, database, auth, deployment, portabilité |
| 3. Control Status | Secrets, exposition, source control, portabilité |
| 4. Security Recovery | Blocages immédiats, exposition des secrets, .gitignore, .env.example |
| 5. Sovereignty Recovery | Dépendances externes, risques de portabilité, options de sortie |
| 6. Database and RLS Recovery | Supabase détecté, verdict RLS, fixes auto, revue manuelle |
| 7. Governance Recovery | Présence aeos.toml, DECISIONS.md, SECURITY.md, SOVEREIGNTY.md |
| 8. Testing and CI Recovery | Répertoire de tests, CI quality gate |
| 9. Local AI Development Policy | Ce que l'IA locale peut faire, ce qui nécessite une approbation humaine |
| 10. Frontier AI Escalation Rules | Ce qui ne doit jamais être envoyé à une IA frontière |
| 11. Recovery PR Roadmap | 7+ PRs ordonnées avec priorité et prérequis |
| 12. Development Continuation Backlog | 6 catégories : stabilisation, sécurité, architecture, tests, DX, produit |
| 13. Recommended Next Action | Action suivante recommandée issue de l'audit harden |

---

## 4. Sortie texte

```
── Recovery Plan ───────────────────────────────────
  Path:    /path/to/project
  Project: project-name
  Status:  WARNING

── Current Architecture ────────────────────────────
  Frontend:    partial
  Backend:     likely_external
  Database:    partial
  Deployment:  likely_external
  Portability: partial

── Control Status ──────────────────────────────────
  Secrets:         local
  Secrets exposure:none
  Source control:  git_present
  Portability:     partial

── Security Recovery ───────────────────────────────
  Status:           WARNING
  Secret exposure:  none
  No immediate security blockers.

── Sovereignty Recovery ────────────────────────────
  Status: WARNING
  External deps (1): supabase (database, auth)

── Database Recovery ───────────────────────────────
  Supabase detected:  yes
  RLS verdict:        WARNING
  Auto-generated:     3
  Manual review:      2

── Governance Recovery ─────────────────────────────
  aeos.toml                missing
  docs/DECISIONS.md        missing
  docs/SECURITY.md         missing
  docs/SOVEREIGNTY.md      missing

── Testing and CI ──────────────────────────────────
  Tests:      missing
  CI gate:    missing

── Local AI Policy ─────────────────────────────────
  Can do:              8 tasks by default
  Needs approval:      7 actions
  Never send frontier: 7 types

── Frontier AI Rules ───────────────────────────────
  ✗ Never send secrets or credentials to frontier AI
  ✗ Never send .env or environment files
  ✗ Never send customer data or PII
  … and 3 more rules

── Recovery PR Roadmap (7 PRs) ─────────────────────
  PR 1  [high    ] Stabilize secrets and environment policy
  PR 2  [high    ] Add governance documentation (after PR 1)
  PR 3  [high    ] Harden database and RLS (after PR 1)
  PR 4  [medium  ] Add smoke tests (after PR 2)
  PR 5  [medium  ] Add CI quality gate (after PR 4)
  PR 6  [medium  ] Improve portability (after PR 2)
  PR 7  [low     ] Prepare AI-assisted development workflow (after PR 2)

── Backlog (6 categories) ──────────────────────────
  stabilization            3 items
  security                 5 items
  architecture             4 items
  testing                  5 items
  developer_experience     5 items
  product_continuation     5 items

── Recommended Next Action ─────────────────────────
  → Run aeos security check

Read-only — no files modified, no migration applied, no database connection.
  read_only: true  ·  applied: false
  → Use --output to export the full Markdown recovery plan.
```

---

## 5. Sortie JSON (`--json`)

```json
{
  "command": "reclaim recovery plan",
  "read_only": true,
  "applied": false,
  "project_path": "/path/to/project",
  "project_name": "project-name",
  "status": "WARNING",
  "current_architecture": {
    "frontend": "partial",
    "backend": "likely_external",
    "database": "partial",
    "auth": "likely_external",
    "deployment": "likely_external",
    "portability": "partial",
    "detected_generators": [],
    "detected_providers": ["supabase"],
    "missing_docs": ["ARCHITECTURE.md", "docs/DECISIONS.md"]
  },
  "control_status": {
    "secrets": "local",
    "secrets_exposure": "none",
    "source_control": "git_present",
    "database": "partial",
    "deployment": "likely_external",
    "portability": "partial"
  },
  "security_recovery": { "...": "..." },
  "sovereignty_recovery": { "...": "..." },
  "database_recovery": { "...": "..." },
  "governance_recovery": { "...": "..." },
  "testing_ci_recovery": { "...": "..." },
  "local_ai_policy": {
    "can_do": ["..."],
    "requires_human_approval": ["..."],
    "may_require_frontier": ["..."],
    "must_never_send_to_frontier": ["..."]
  },
  "frontier_ai_rules": [
    { "rule": "Never send secrets or credentials to frontier AI", "reason": "..." }
  ],
  "recovery_pr_roadmap": [
    {
      "pr_number": 1,
      "title": "Stabilize secrets and environment policy",
      "goal": "...",
      "tasks": ["..."],
      "priority": "high",
      "prerequisite": null
    }
  ],
  "development_continuation_backlog": [
    { "name": "stabilization", "items": ["..."] }
  ],
  "recommended_next_action": "Run aeos security check"
}
```

---

## 6. Export Markdown (`--output`)

```bash
aeos reclaim recovery plan --path ./my-project --output docs/RECOVERY-PLAN.md
# Recovery plan written to: docs/RECOVERY-PLAN.md
# Status:  WARNING
# PRs:     7 in roadmap
#   read_only: true  ·  applied: false
```

- Le fichier est refusé s'il existe déjà sans `--overwrite`.
- Le Markdown contient les 13 sections avec tableaux, listes de tâches GitHub (`- [ ]`), et un footer de sécurité.
- Footer : `No correction has been applied. This plan is read-only.`

---

## 7. Recovery PR Roadmap (détail)

| PR | Titre | Priorité | Prérequis |
|---|---|---|---|
| PR 1 | Stabilize secrets and environment policy | critical/high | — |
| PR 2 | Add governance documentation | high | PR 1 |
| PR 3 | Harden database and RLS / Document database architecture | high/medium | PR 1 |
| PR 4 | Add smoke tests | medium | PR 2 |
| PR 5 | Add CI quality gate | medium | PR 4 |
| PR 6 | Improve portability | medium/low | PR 2 |
| PR 7 | Prepare AI-assisted development workflow | low | PR 2 |

PR 1 est marquée `critical` si des secrets sont exposés (`secrets_exposure = "confirmed"`).
PR 3 est adaptée selon la présence de Supabase.

---

## 8. Local AI Policy (résumé)

| Catégorie | Count MVP |
|---|---|
| Peut faire par défaut | 8 actions |
| Nécessite approbation humaine | 7 actions |
| Peut nécessiter IA frontière | 4 cas |
| Ne jamais envoyer à l'IA frontière | 7 types |

**Ne jamais envoyer** inclut : fichiers `.env`, connection strings, données clients (PII), dumps de base de données, API keys, tokens de session.

---

## 9. Garanties read-only

| Garantie | Statut |
|---|---|
| Aucun fichier modifié dans le projet audité | ✓ |
| Aucune base de données contactée | ✓ |
| Aucun `.env` lu | ✓ |
| Aucun secret affiché | ✓ |
| Aucun appel réseau | ✓ |
| Aucun appel IA externe | ✓ |
| Aucune migration appliquée | ✓ |
| `read_only: true` dans la sortie JSON | ✓ |
| `applied: false` dans la sortie JSON | ✓ |

---

## 10. Architecture interne

```
src/aeos/reclaim/
  recovery.py          — RecoveryPlan, LocalAIPolicy, FrontierAIRule,
                         RecoveryPRRoadmapItem, RecoveryBacklogCategory,
                         build_recovery_plan(), recovery_plan_to_dict(),
                         build_recovery_markdown()
  __init__.py          — exports publics

src/aeos/cli.py        — commande aeos reclaim recovery plan

tests/unit/
  test_reclaim_recovery.py  — 22 tests
```

### Public API

```python
from aeos.reclaim import (
    RecoveryPlan,
    LocalAIPolicy,
    FrontierAIRule,
    RecoveryPRRoadmapItem,
    RecoveryBacklogCategory,
    build_recovery_plan,
    recovery_plan_to_dict,
    build_recovery_markdown,
)

plan = build_recovery_plan(Path("./my-project"))
md = build_recovery_markdown(plan)
data = recovery_plan_to_dict(plan)
```

---

## 11. Chaîne de commandes recommandée

```bash
# 1. Inspecter le projet
aeos reclaim inspect --path ./my-project

# 2. Durcir et auditer
aeos reclaim harden --path ./my-project

# 3. Générer le plan de récupération
aeos reclaim recovery plan --path ./my-project --output docs/RECOVERY-PLAN.md

# 4. Suivre l'avancement
aeos memory timeline --path ./my-project
```

---

## 12. Validation réelle — ma-mairie-digitale (Sprint 5A-2)

Validation exécutée le 2026-06-30 dans `/tmp` uniquement, sans toucher `ma-mairie-digitale`.

### Commande utilisée

```bash
uv run aeos reclaim recovery plan \
  --path ~/aeos-client-audits/ma-mairie-digitale \
  --output /tmp/ma-mairie-digitale-recovery-plan.md
```

### Résultats obtenus

```
Recovery plan written to: /tmp/ma-mairie-digitale-recovery-plan.md
Status:  ERROR
PRs:     7 in roadmap
  read_only: true  ·  applied: false
```

### Contenu du plan (sections clés)

| Section | Valeur |
|---|---|
| Status | `ERROR` |
| Generator détecté | `lovable` |
| Provider détecté | `supabase` |
| Secrets exposure | `confirmed` |
| Portability | `weak` |
| Source control | `git_present` |
| `.gitignore` protects `.env` | `yes` |
| `.env.example` | `yes` |
| Exit options | 3 (stay / own Supabase Cloud / self-hosted) |
| PRs in roadmap | 7 |
| Taille du fichier | 9.4 K |

### Vérifications de sécurité

| Vérification | Résultat |
|---|---|
| Output dans `/tmp` uniquement | ✓ |
| `ma-mairie-digitale` untouched — `git status` clean | ✓ |
| AEOS repo clean après exécution | ✓ |
| Aucune connexion base de données | ✓ |
| Aucune migration appliquée | ✓ |
| Aucun secret affiché | ✓ |
| `read_only: true` · `applied: false` confirmés | ✓ |
| `uv run pytest` → 1420 passed | ✓ |

---

## 13. Total Recovery Scope

`aeos reclaim recovery plan` is the entry point to a larger arc. AEOS can accompany a project through the full recovery — from audit to sovereign operation.

**AEOS does not stop at scanning a project.** AEOS accompanies until the project is:

- understood (architecture documented, stack mapped, unknown zones identified);
- secured (secrets rotated, .gitignore verified, .env.example complete);
- governed (DECISIONS.md, SECURITY.md, SOVEREIGNTY.md, aeos.toml in place);
- tested (smoke tests added, test baseline established);
- CI-gated (quality gate pipeline active, branch protection on main);
- locally runnable (local run documented, Supabase local configured);
- portable (Dockerfile present, migrations versioned, deployment reversible);
- migratable if necessary (backup, dry-run, rollback, human gate);
- operable with local AI continuation (local model configured, AI workflow established).

### Migration rules

AEOS can accompany migrations — but never silently.

| Rule | Enforcement |
|---|---|
| No automatic apply | Every migration step requires explicit human confirmation before execution |
| Backup mandatory | No migration step executes without a verified backup |
| Dry-run mandatory | Migration SQL or script is validated in dry-run before live execution |
| Rollback plan mandatory | A defined rollback path exists before any destructive step is applied |
| Human validation explicit | Human reviews the plan, confirms the dry-run result, approves the apply |
| Post-migration tests | Tests run after migration before declaring success |
| MemoryRecord after operation | A memory record is created: backup status, dry-run result, tests passed, human gate |
| No sensitive data to frontier AI | Migration plans and SQL proposals are generated locally — never sent to frontier AI |

---

## 14. Local AI First Development Continuation

Once a project is recovered, development continues with local AI by default.

| Rule | Description |
|---|---|
| **Local AI by default** | All routine engineering tasks (code review, test generation, refactoring, documentation) use local models |
| **Frontier by exception** | Frontier AI is used only when local AI is demonstrably insufficient, with explicit human approval |
| **Filtered context** | Context sent to any AI is filtered: no secrets, no credentials, no sensitive data |
| **Never `.env`** | Environment files are never passed to any AI, local or frontier |
| **Never secrets** | API keys, tokens, passwords, connection strings are never in AI context |
| **Never customer data** | PII, financial data, health data, citizen data are never in AI context |
| **Never sensitive DB dumps** | Database exports containing real data are never in AI context |
| **Human validation before external send** | If any frontier escalation is considered, human reviews the filtered context before it is sent |

This policy applies permanently — during recovery, during continuation, and during operation. It is not a phase-specific rule. It is a permanent invariant.

---

## 15. Recovery Evidence

Every recovery step must produce verifiable evidence. Evidence is the proof that recovery is real, not claimed.

| Evidence type | What it proves |
|---|---|
| **Files added** | New governance or infrastructure files are present and committed in the repo |
| **Tests passed** | The change did not break existing functionality |
| **PR created or merged** | The change was reviewed and human-approved before landing on main |
| **Risk reduced** | The AEOS audit shows improvement (status, critical count, control level) |
| **MemoryRecord created** | AEOS recorded the event with date, project name, and findings |
| **Timeline updated** | `aeos memory timeline` shows measurable progression between audits |
| **Human validation recorded** | An ADR or PR comment documents who validated what and when |
| **Rollback documented** | If a destructive step was applied, the rollback path is documented in writing |

> Evidence is not optional. A recovery step without evidence is not a recovery step — it is a guess.

The complete evidence chain for a recovery stage:

```
aeos reclaim harden → MemoryRecord (before)
[recovery actions applied in PR]
aeos reclaim harden → MemoryRecord (after)
aeos memory compare --left <before> --right <after>  → delta
aeos memory timeline --project <name>                → progression
```

---

## 16. Recovery Stage Model (Sprint 5C)

Le modèle de stages implémente le registre Python des 10 étapes du Total Sovereign Recovery Arc.
Implémenté dans `src/aeos/reclaim/stages.py`. Read-only. Aucune mutation. Aucune exécution.

### Structure d'un stage

```python
@dataclass
class RecoveryStage:
    id: str                        # ex. "stage_0_baseline"
    name: str                      # ex. "Baseline Assessment"
    objective: str
    prerequisites: list[str]       # IDs des stages requis avant ce stage
    actions: list[str]             # commandes ou tâches concrètes
    risks: list[str]               # risques identifiés
    expected_evidence: list[str]   # preuves attendues à la fin du stage
    human_gate: str                # décision humaine requise
    rollback_path: str | None      # chemin de rollback (None si aucun)
    memory_record_type: str        # type de MemoryRecord créé en fin de stage
    allowed_agents: list[str]      # agents autorisés pour ce stage
```

### Les 10 stages

| Stage | Nom | Prérequis |
|-------|-----|-----------|
| `stage_0_baseline` | Baseline Assessment | — |
| `stage_1_governance` | Governance Documentation | stage_0 |
| `stage_2_secrets_env` | Secrets and Environment Policy | stage_1 |
| `stage_3_database_rls` | Database and RLS Hardening | stage_2 |
| `stage_4_tests_ci` | Tests and CI Gate | stage_1 |
| `stage_5_local_run` | Local Run | stage_1 |
| `stage_6_portability` | Portability | stage_5 |
| `stage_7_migration_readiness` | Migration Readiness | stage_6 |
| `stage_8_local_ai_continuation` | Local AI Continuation | stage_4 |
| `stage_9_sovereign_operating_mode` | Sovereign Operating Mode | stage_0, 1, 2, 4 |

### Commandes CLI

```bash
# Lister tous les stages
aeos reclaim stage list
aeos reclaim stage list --json

# Afficher le détail d'un stage
aeos reclaim stage show --id stage_0_baseline
aeos reclaim stage show --id stage_7_migration_readiness --json
```

### API Python

```python
from aeos.reclaim import (
    RecoveryStage,
    get_recovery_stages,
    get_stage_by_id,
    recovery_stage_to_dict,
)

stages = get_recovery_stages()        # list[RecoveryStage] — 10 stages
stage = get_stage_by_id("stage_0_baseline")  # RecoveryStage | None
d = recovery_stage_to_dict(stage)    # dict[str, object] — JSON-serializable
```

### Garanties read-only

- Aucun fichier modifié, aucune base de données contactée, aucun secret lu.
- Les commandes CLI retournent toujours `read_only: true · applied: false`.
- Aucun stage ne s'exécute — le modèle documente uniquement, il ne pilote pas.

---

## 17. Recovery Planner (Sprint 5D)

Le Recovery Planner transforme le registre des 10 stages en un plan structuré selon les stages déjà complétés.
Implémenté dans `src/aeos/reclaim/planner.py`. Read-only. Aucune mutation. Aucune exécution. Aucun write MemoryRecord.

### Concept

Entrée : une liste d'IDs de stages complétés (`done_ids`)
Sortie : `StagedRecoveryPlan` — chaque stage classé `done | ready | blocked`, avec la prochaine action recommandée.

### Modèles

```python
@dataclass
class StageAssessment:
    stage_id: str
    stage_name: str
    status: str                      # "done" | "ready" | "blocked"
    missing_prerequisites: list[str] # [] si done ou ready
    recommended_first_action: str    # actions[0] si ready/blocked, "" si done
    human_gate: str
    memory_record_type: str

@dataclass
class StagedRecoveryPlan:
    project_path: str
    read_only: bool                  # toujours True
    applied: bool                    # toujours False
    stages_done: list[str]
    stages_ready: list[str]
    stages_blocked: list[str]
    recommended_sequence: list[str]  # done → ready → blocked
    next_stage_id: str | None
    next_action: str | None
    items: list[StageAssessment]
    total: int                       # toujours 10
```

### Logique de statut

| Condition | Statut |
|-----------|--------|
| `stage.id` dans `done_ids` | `done` |
| Tous les prérequis dans `done_ids`, stage non complété | `ready` |
| Au moins un prérequis absent de `done_ids` | `blocked` |

### Commandes CLI

```bash
# Projet vierge (tous les stages pending)
aeos reclaim stage plan

# Projet partiellement avancé
aeos reclaim stage plan --done stage_0_baseline,stage_1_governance

# Sortie JSON
aeos reclaim stage plan --done stage_0_baseline --json

# ID inconnu → exit 1
aeos reclaim stage plan --done stage_99_fake   # Error: unknown stage ID
```

### Sortie texte (exemple avec stage_0 complété)

```
── Staged Recovery Plan ────────────────────────────────────────────────
  Done: 1  ·  Ready: 1  ·  Blocked: 8  ·  read_only: true  ·  applied: false

  DONE
    ✓ stage_0_baseline                           Baseline Assessment

  READY
    → stage_1_governance                         Governance Documentation
      First action: Create ARCHITECTURE.md

  BLOCKED
    ✗ stage_2_secrets_env                        [needs: stage_1_governance]
    ...

  Next stage:  stage_1_governance
  Next action: Create ARCHITECTURE.md

  read_only: true  ·  applied: false
```

### API Python

```python
from aeos.reclaim import (
    StageAssessment,
    StagedRecoveryPlan,
    assess_stage,
    build_staged_recovery_plan,
    staged_plan_to_dict,
    validate_done_ids,
)

# Valider les IDs avant de planifier
unknown = validate_done_ids(["stage_0_baseline", "stage_99_fake"])
# → ["stage_99_fake"]

# Construire le plan
plan = build_staged_recovery_plan(
    done_ids=["stage_0_baseline", "stage_1_governance"],
    project_path="/path/to/project",
)

# Sérialiser
d = staged_plan_to_dict(plan)  # dict[str, object] — JSON-serializable
```

### Garanties read-only

- Aucun accès filesystem.
- Aucune base de données contactée.
- Aucun secret lu ou affiché.
- Aucun MemoryRecord créé ou modifié.
- Sortie toujours `read_only: true · applied: false`.
- `validate_done_ids` rejette tout ID inconnu → exit 1 en CLI.

---

## Voir aussi

- [`docs/features/AEOS-RECLAIM-HARDEN.md`](AEOS-RECLAIM-HARDEN.md)
- [`docs/features/AEOS-BUILD-RAIL.md`](AEOS-BUILD-RAIL.md)
- [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](../strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md)
- [`docs/strategy/AEOS-PRODUCT-VISION.md`](../strategy/AEOS-PRODUCT-VISION.md) — section 14 : Total Sovereign Recovery
