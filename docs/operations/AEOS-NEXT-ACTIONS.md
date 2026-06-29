# AEOS Next Actions

**Version :** 2026-06-29  
**Auteur :** AEOS Operations  
**Statut :** Document vivant — à mettre à jour après chaque session de travail

---

## 1. État actuel

| Élément | État |
|---|---|
| Branche `main` | Propre, à jour avec `origin/main` |
| CI | Verte (Quality Gate pass) |
| AEOS CLI | Fonctionnel — `aeos reclaim harden`, `aeos memory list`, `aeos memory show` |
| Workstation doc | Présente (`docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md`) |
| Memory Layer MVP | Mergé dans main — validé, lu par CLI |
| Memory Read CLI | **Sprint 3G livré** — `aeos memory list` + `aeos memory show` |
| `ma-mairie-digitale` | Untouched — projet client intact |
| `.env` | Non lu, non tracké, non copié |

---

## 2. Sprint actif — sprint3g/memory-read-cli (livré)

### Livraisons sprint3g

```
src/aeos/memory/models.py        — MemoryRecordSummary, MemoryListResult
src/aeos/memory/store.py         — list_records(), load_record(), find_record_path()
src/aeos/memory/__init__.py      — exports publics mis à jour
src/aeos/cli.py                  — aeos memory list, aeos memory show
tests/unit/test_memory_cli.py    — 28 tests unitaires
docs/features/AEOS-MEMORY-LAYER.md — section Memory Read CLI + limites + next steps
```

**Commandes livrées :**

```bash
aeos memory list --memory-dir /tmp/aeos-memory
aeos memory list --memory-dir /tmp/aeos-memory --json
aeos memory show --memory-dir /tmp/aeos-memory --record <record_id>
aeos memory show --memory-dir /tmp/aeos-memory --record <record_id> --json
```

---

## 3. Priorités par ordre

### Priorité 1 — Merger sprint3g dans main

La PR sprint3g/memory-read-cli est prête à merger.
Vérifier la CI puis merger.

### Priorité 2 — Memory pour les autres rails

Après stabilisation du read CLI :

- Wirer `aeos security check --memory-dir` → écrire des MemoryRecord pour le rail Security
- Wirer `aeos supabase check --memory-dir` → écrire des MemoryRecord pour le rail Supabase

### Priorité 3 — Compare / Diff

- Comparer deux records successifs pour un même projet
- `aeos memory diff --memory-dir <dir> --record-a <id> --record-b <id>`

### Priorité 4 — Validation humaine

- Permettre à l'humain de marquer un record comme validé
- `aeos memory validate --memory-dir <dir> --record <id>`
- `aeos memory note --memory-dir <dir> --record <id> --text "note"`

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
# 1. Merger sprint3g
gh pr merge <pr_number> --squash

# 2. Vérifier le CLI après merge
uv run aeos memory list --help
uv run aeos memory show --help

# 3. Tester sur un vrai audit
uv run aeos reclaim harden --path ~/aeos-client-audits/ma-mairie-digitale \
  --memory-dir /tmp/aeos-memory-test
uv run aeos memory list --memory-dir /tmp/aeos-memory-test
uv run aeos memory show --memory-dir /tmp/aeos-memory-test \
  --record <record_id_from_list>

# 4. Décider du prochain sprint avec le CTO
# → memory diff, ou rails supplémentaires, ou validation humaine
```

---

## 7. Historique des mises à jour

| Date | Mise à jour |
|---|---|
| 2026-06-29 | Création initiale — état post-sprint3f, memory layer mergé |
| 2026-06-29 | Sprint 3G livré — Memory Read CLI (list + show), 28 tests |
