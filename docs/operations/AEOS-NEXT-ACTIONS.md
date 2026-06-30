# AEOS Next Actions

**Version :** 2026-06-30  
**Auteur :** AEOS Operations  
**Statut :** Document vivant — à mettre à jour après chaque session de travail

---

## 1. État actuel

| Élément | État |
|---|---|
| Branche `main` | `b4464dc` — Sprint 5A-2 mergé (PR #46) |
| CI | Verte (1420 tests) |
| AEOS CLI | `reclaim harden`, `reclaim recovery plan`, `memory list`, `memory show`, `memory compare`, `memory timeline`, `build plan`, `build scaffold` |
| Memory Write | Sprint 3F — mergé, stable |
| Memory Read CLI | Sprint 3G — mergé dans main (PR #36) |
| Memory Compare | Sprint 3H — mergé dans main (PR #38) |
| Memory Timeline | Sprint 3I — mergé dans main (PR #40) |
| Build Rail MVP | Sprint 4A — mergé dans main (PR #41) |
| Build Scaffold MVP | Sprint 4B — mergé dans main (PR #42) |
| Build Scaffold Validation | Sprint 4B-1 — mergé dans main (PR #43) |
| Recovery Plan MVP | Sprint 5A — **mergé dans main** (PR #44 + #45) |
| Recovery Real-World Validation | Sprint 5A-2 — **mergé dans main** (PR #46) |
| Total Sovereign Recovery Vision | Sprint 5B — **en cours** (branch `sprint5b/total-sovereign-recovery-vision`) |
| `ma-mairie-digitale` governance | Sprint 5A (client) — PR #2 mergé dans main · PR #3 open (fix Lovable disconnect task) |
| `.env` | Non lu, non tracké, non copié |

---

## 2. Chaîne de commandes disponible dans main

```
aeos reclaim harden          --path <project> --memory-dir <dir>               →  audit + MemoryRecord
aeos reclaim recovery plan   --path <project> [--json] [--output <file>]       →  plan de récupération (read-only)
aeos memory list             --memory-dir <dir>                                 →  liste tous les records
aeos memory show             --memory-dir <dir> --record <id>                   →  affiche un record
aeos memory compare          --memory-dir <dir> --left <id> --right <id>        →  compare deux records
aeos memory timeline         --memory-dir <dir> --project <name>                →  timeline du projet
aeos build plan              --name <name> --type <type> --stack <stack>        →  plan d'architecture (read-only)
aeos build scaffold          --name <name> --type <type> --stack <stack> --output <dir>  →  scaffold governance
```

Tous les modes `--json` sont disponibles. `reclaim recovery plan` et `build plan` sont read-only.
Sprint 5A (`reclaim recovery plan`) est sur la branche `sprint5a/reclaim-recovery-plan` — PR en attente.

---

## 3. Roadmap Sprint 5B — 5I

> Priorité immédiate : construire le modèle standard de reprise totale avant toute migration réelle.

La vision Total Sovereign Recovery (Sprint 5B) pose la doctrine. Les sprints suivants l'implémentent progressivement.

### Sprint 5B — Total Sovereign Recovery Vision (en cours)

**Objectif :** Mettre à jour la documentation stratégique AEOS pour intégrer la vision Total Sovereign Recovery, le modèle agentique, les niveaux d'action, et le stage model complet.

**Documents mis à jour :** `AEOS-PRODUCT-VISION.md`, `AEOS-PRODUCT-RAILS-AND-AGENTS.md`, `AEOS-RECLAIM-RECOVERY.md`, `AEOS-NEXT-ACTIONS.md`, `AEOS-SPRINT-LOG.md`

---

### Sprint 5C — Total Recovery Stage Model

**Objectif :** Implémenter le modèle de stages comme structure de données AEOS.

- `src/aeos/reclaim/stages.py` — `RecoveryStage`, `StageResult`, `StagePrecondition`
- `aeos reclaim stage status --path <project>` — état de chaque stage pour un projet
- Liaison avec MemoryRecord : chaque stage completed crée un record
- Tests : 20+ tests unitaires

---

### Sprint 5D — Project Recover Orchestrator

**Objectif :** Orchestrateur de reprise — exécute les stages dans l'ordre avec gates humains.

- `aeos recover --path <project> [--stage <stage_name>]` — lance un stage de récupération
- Gate humain avant chaque action (Level 3+)
- Evidence produite après chaque stage
- MemoryRecord créé et timeline mise à jour

---

### Sprint 5E — Governance PR Generator

**Objectif :** Générer automatiquement les fichiers de gouvernance stage_1 sous forme de PR.

- `aeos recover governance --path <project> --output <dir>` — génère les 7 fichiers
- Basé sur le résultat de `reclaim recovery plan`
- `--dry-run` pour prévisualisation sans écriture
- Tests : 15+ tests unitaires

---

### Sprint 5F — Local AI Development Policy Engine

**Objectif :** Moteur de politique IA locale — configurer, valider et appliquer la politique IA d'un projet.

- `aeos ai policy check --path <project>` — vérifie la conformité avec la politique IA
- `aeos ai policy generate --path <project>` — génère docs/AI-DEVELOPMENT-POLICY.md
- Validation du contexte avant envoi (filtrage des secrets, PII, données sensibles)
- Tests : 15+ tests unitaires

---

### Sprint 5G — Migration Readiness Plan

**Objectif :** Générer un plan de migration complet (stage_7) avec backup, dry-run et rollback.

- `aeos migrate plan --path <project> --from <source> --to <target>` — plan read-only
- Vérification des préconditions (backup, portabilité, tests)
- Rollback path documenté automatiquement
- Tests : 15+ tests unitaires

---

### Sprint 5H — Multi-Project Sovereign Recovery Validation

**Objectif :** Valider la chaîne complète de reprise sur plusieurs projets clients.

- Exécution de stage_0 à stage_4 sur au moins 2 projets distincts
- Comparaison before/after via `aeos memory compare`
- Documentation dans `docs/features/AEOS-RECLAIM-RECOVERY.md`

---

### Sprint 5I — AEOS Local Server / UI Contract

**Objectif :** Définir le contrat d'interface pour l'interface graphique AEOS future.

L'interface graphique permettra de :
1. Coller l'URL d'un repository
2. Choisir Express (automatique) ou Expert (stage par stage)
3. Lancer le Sovereignty Recovery
4. Visualiser la roadmap des PRs
5. Préparer les PRs avec review humaine
6. Continuer le développement avec l'IA locale

Ce sprint documente le contrat API/UI sans implémenter le serveur.

---

## 4. Règles permanentes — ne pas déroger

- **Ne pas lancer `apply`** sans gate humain explicite.
- **Ne pas automatiser les corrections** sans revue intermédiaire.
- **Garder les outputs dans `/tmp`** pour les tests réels avant d'écrire dans le repo.
- **`ma-mairie-digitale` reste untouched** sauf instruction explicite.
- **Ne jamais lire `.env`** ni afficher de secrets.
- **Proposer avant d'agir** : tout plan doit être validé avant exécution.

---

## 5. Standard agent startup prompt

Tout agent (Claude Code, Codex, Antigravity, ou autre) reprenant le travail sur AEOS doit commencer par lire ces documents dans cet ordre :

```
Before doing any work on AEOS, read:

* docs/strategy/AEOS-PRODUCT-VISION.md
* docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md
* docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md
* docs/operations/AEOS-CTO-HANDOFF.md
* docs/operations/AEOS-SPRINT-LOG.md
* docs/operations/AEOS-NEXT-ACTIONS.md

Then:

* summarize the current state
* identify the active sprint
* propose a plan before modifying files
* never read .env
* never display secrets
* never touch client projects unless explicitly instructed
* never apply fixes without a gate
```

---

## 6. Prochaine séquence recommandée

```bash
# 1. Valider la chaîne complète sur un vrai audit
uv run aeos reclaim harden \
  --path ~/aeos-client-audits/ma-mairie-digitale \
  --output /tmp/ma-mairie-report.md \
  --memory-dir /tmp/aeos-memory

# 2. Lister les records
uv run aeos memory list --memory-dir /tmp/aeos-memory

# 3. Afficher le record en détail
uv run aeos memory show \
  --memory-dir /tmp/aeos-memory \
  --record <record_id_from_list>

# 4. Valider en JSON
uv run aeos memory list --memory-dir /tmp/aeos-memory --json
uv run aeos memory show \
  --memory-dir /tmp/aeos-memory \
  --record <record_id> \
  --json

# 5. Démarrer Sprint 3H avec le CTO
# → aeos memory compare
```

---

## 7. Historique des mises à jour

| Date | Mise à jour |
|---|---|
| 2026-06-29 | Création initiale — état post-sprint3f, memory layer mergé |
| 2026-06-29 | Sprint 3G livré — Memory Read CLI (list + show), 28 tests |
| 2026-06-29 | Sprint 3G-1 — documentation usage Memory CLI, prochains sprints 3H/3I/4A |
| 2026-06-29 | Sprint 3H — Memory Compare livré (26 tests, `aeos memory compare`) |
| 2026-06-30 | Sprint 3I — Memory Timeline livré (22 tests, `aeos memory timeline`) |
| 2026-06-30 | Sprint 4A — Build Rail MVP livré (18 tests, `aeos build plan`) |
| 2026-06-30 | Sprint 4B — Build Scaffold MVP livré (16 tests, `aeos build scaffold`) |
| 2026-06-30 | Sprint 5A — Recovery Plan MVP mergé (22 tests, PR #44 + #45) |
| 2026-06-30 | Sprint 5A-2 — Real-World Validation mergée (PR #46), 1420 tests |
| 2026-06-30 | Sprint 5B — Total Sovereign Recovery Vision lancé — doctrine, stage model, agentic model |
