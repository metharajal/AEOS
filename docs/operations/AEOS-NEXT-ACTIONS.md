# AEOS Next Actions

**Version :** 2026-06-29  
**Auteur :** AEOS Operations  
**Statut :** Document vivant — à mettre à jour après chaque session de travail

---

## 1. État actuel

| Élément | État |
|---|---|
| Branche `main` | `8410c28` — Sprint 3I mergé (PR #40) |
| CI | Verte (1382 tests — sprint 4A local) |
| AEOS CLI | `reclaim harden`, `memory list`, `memory show`, `memory compare`, `memory timeline`, `build plan` |
| Memory Write | Sprint 3F — mergé, stable |
| Memory Read CLI | Sprint 3G — mergé dans main (PR #36) |
| Memory Compare | Sprint 3H — mergé dans main (PR #38) |
| Memory Compare Validation | Sprint 3H-1 — mergé dans main (PR #39) |
| Memory Timeline | Sprint 3I — mergé dans main (PR #40) |
| Build Rail MVP | Sprint 4A — **en attente de merge** (branch `sprint4a/build-rail-mvp`) |
| `ma-mairie-digitale` | Untouched — projet client intact |
| `.env` | Non lu, non tracké, non copié |

---

## 2. Chaîne de commandes disponible dans main

```
aeos reclaim harden  --path <project> --memory-dir <dir>               →  crée un MemoryRecord
aeos memory list     --memory-dir <dir>                                 →  liste tous les records
aeos memory show     --memory-dir <dir> --record <id>                   →  affiche un record
aeos memory compare  --memory-dir <dir> --left <id> --right <id>        →  compare deux records
aeos memory timeline --memory-dir <dir> --project <name>                →  timeline du projet
aeos build plan      --name <name> --type <type> --stack <stack>        →  plan d'architecture
```

Tous les modes `--json` sont disponibles. Tout est read-only. Aucun secret. Aucune DB.
Sprint 4A (`build plan`) est sur la branche `sprint4a/build-rail-mvp` — PR en attente.

---

## 3. Prochains sprints recommandés

### Priorité 1 — Sprint 3H : Memory Compare (DONE)

**Statut :** Livré et mergé — PR #38 (`401d485`).

---

### Priorité 2 — Sprint 3I : Memory Timeline (DONE)

**Statut :** Livré — branch `sprint3i/memory-timeline-mvp`, PR en attente de merge.

```bash
aeos memory timeline --memory-dir <dir> --project <name> [--json]
```

---

### Priorité 3 — Sprint 4A : Build Rail MVP (DONE)

**Statut :** Livré — branch `sprint4a/build-rail-mvp`, PR en attente de merge.

```bash
aeos build plan --name <project> --type <type> --stack <stack> [--json]
```

Types : `web-app` · `api` · `internal-tool`
Stacks : `nextjs-supabase` · `nextjs-postgres` · `fastapi-postgres` · `generic`

### Priorité 4 — Sprint 4B : Build Scaffold MVP

**Objectif :** Générer la structure de dossiers et fichiers governance pour un
nouveau projet AEOS-native.

```bash
aeos build scaffold --name <project> --type <type> --stack <stack>
```

Génère dans un dossier vide : folder structure, governance files, .env.example,
.gitignore, README.md, ARCHITECTURE.md, docs/DECISIONS.md.

---

### Horizon — autres priorités mémoire

| Sprint | Objectif |
|---|---|
| Memory pour Security/Supabase | Wirer `--memory-dir` sur les autres rails |
| Memory validate | `aeos memory validate --record <id>` — marquer comme validé humainement |
| Memory note | `aeos memory note --record <id> --text "..."` — annoter un record |
| Memory search | Recherche dans les records par field ou texte libre |

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
