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

## Voir aussi

- [`docs/features/AEOS-RECLAIM-HARDEN.md`](AEOS-RECLAIM-HARDEN.md)
- [`docs/features/AEOS-BUILD-RAIL.md`](AEOS-BUILD-RAIL.md)
- [`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`](../strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md)
