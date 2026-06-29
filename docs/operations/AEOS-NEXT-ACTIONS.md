# AEOS Next Actions

**Version :** 2026-06-29  
**Auteur :** AEOS Operations  
**Statut :** Document vivant — à mettre à jour après chaque session de travail

---

## 1. État actuel

| Élément | État |
|---|---|
| Branche `main` | Propre, à jour avec `origin/main` — commit `4e6c06c` |
| CI | Verte (Quality Gate pass — 1316 tests) |
| AEOS CLI | Fonctionnel — `aeos reclaim harden`, `aeos memory list`, `aeos memory show` |
| Memory Write | Sprint 3F — mergé, stable |
| Memory Read CLI | Sprint 3G — **mergé** dans main (PR #36) |
| Memory Usage Docs | Sprint 3G-1 — en cours |
| `ma-mairie-digitale` | Untouched — projet client intact |
| `.env` | Non lu, non tracké, non copié |

---

## 2. Chaîne Memory disponible dans main

```
aeos reclaim harden --path <project> --memory-dir <dir>   →  crée un MemoryRecord JSON
aeos memory list   --memory-dir <dir>                      →  liste tous les records
aeos memory show   --memory-dir <dir> --record <id>        →  affiche un record en détail
```

Tous les modes `--json` sont disponibles. Tout est read-only. Aucun secret. Aucune DB.

---

## 3. Prochains sprints recommandés

### Priorité 1 — Sprint 3H : Memory Compare (recommandé)

**Objectif :** Comparer deux records pour mesurer la progression entre deux audits.

```bash
aeos memory compare --memory-dir <dir> --record-a <id> --record-b <id>
```

Affiche :
- delta des findings (critical, important, manual, generated)
- changement de status (ERROR → WARNING, etc.)
- delta de control_level
- évolution du remediation_summary

Sans modifier aucun fichier. Read-only.

---

### Priorité 2 — Sprint 3I : Memory Timeline

**Objectif :** Visualiser l'évolution d'un projet dans le temps à partir de plusieurs records.

```bash
aeos memory timeline --memory-dir <dir> --project <project_name>
```

Affiche une vue chronologique de tous les records pour un même projet :
date · status · critical · control_level.

---

### Priorité 3 — Sprint 4A : Build Rail MVP

**Objectif :** Démarrer le rail Build — scaffolding de projets AEOS-native.

Premier jalon :
```bash
aeos build scaffold --name <project> --type python
```

Génère un projet Python AEOS-native avec :
`pyproject.toml`, `src/`, `tests/`, `docs/`, `.gitignore`, `aeos.toml`, CI skeleton.

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
