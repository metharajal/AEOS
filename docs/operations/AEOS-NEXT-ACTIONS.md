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
| AEOS CLI | Fonctionnel (`aeos --version`, `aeos reclaim harden`, `aeos memory`) |
| Workstation doc | Présente (`docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md`) |
| Memory Layer MVP | Mergé dans main — à consolider |
| `ma-mairie-digitale` | Untouched — projet client intact |
| `.env` | Non lu, non tracké, non copié |

---

## 2. Point d'attention immédiat

### Commit `7139b77` — Memory Layer MVP

```
7139b77  feat(memory): add Memory Layer MVP — local-first diagnostic record store
```

Fichiers ajoutés dans ce commit :

```
src/aeos/memory/__init__.py
src/aeos/memory/models.py
src/aeos/memory/store.py
tests/unit/test_memory_store.py   (573 lignes)
docs/features/AEOS-MEMORY-LAYER.md
```

**Ce commit est déjà dans `main`** (mergé via PR #33).

**Actions à vérifier :**

- [ ] Lire `docs/features/AEOS-MEMORY-LAYER.md` pour comprendre la spec
- [ ] Lancer `pytest tests/unit/test_memory_store.py` pour valider les tests
- [ ] Lancer `ruff check src/aeos/memory/` pour vérifier la qualité
- [ ] Lancer `mypy src/aeos/memory/` pour vérifier les types
- [ ] Vérifier si `aeos memory` est exposé dans `src/aeos/cli.py`

---

## 3. Priorités par ordre

### Priorité 1 — Consolider Memory Layer

Le Memory Layer MVP est mergé mais pas encore validé en détail.

1. Inspecter `7139b77` : `git show 7139b77 --stat`
2. Lire la spec : `docs/features/AEOS-MEMORY-LAYER.md`
3. Valider les tests : `pytest tests/unit/test_memory_store.py -v`
4. Vérifier la qualité : `ruff check src/aeos/memory/` et `mypy src/aeos/memory/`
5. Vérifier l'intégration CLI : `aeos memory --help`
6. Décider : consolider tel quel, corriger, ou étendre

### Priorité 2 — CLI memory (si Memory Layer stable)

Seulement après validation du Memory Layer :

- Ajouter `aeos memory list` — lister les enregistrements
- Ajouter `aeos memory search` — rechercher dans la mémoire
- Ajouter `aeos memory export` — exporter la mémoire locale

### Priorité 3 — Documentation Memory Layer

- Compléter `docs/features/AEOS-MEMORY-LAYER.md` si incomplet
- Ajouter des exemples d'usage dans le sprint log

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
* docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md

Then:

* summarize the current state
* identify the active sprint
* confirm the active branch and its sync status with origin/main
* propose a plan before modifying files
* wait for human validation if the change is sensitive
* never read .env
* never display secrets
* never touch client projects unless explicitly instructed
* never apply fixes without a gate
* never apply migrations or contact a database without explicit instruction
```

Le workflow multi-agent complet est documenté dans `docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md`.
Ce document définit les rôles de ChatGPT, Claude Code, Codex, l'IA locale et Antigravity,
ainsi que le protocole obligatoire avant chaque tâche agent.

---

## 6. Prochaine séquence recommandée

```bash
# 1. Inspecter le commit Memory Layer
cd ~/Development/AEOS
git show 7139b77 --stat

# 2. Lire la spec Memory Layer
# docs/features/AEOS-MEMORY-LAYER.md

# 3. Valider les tests
source .venv/bin/activate
pytest tests/unit/test_memory_store.py -v

# 4. Vérifier la qualité
ruff check src/aeos/memory/
mypy src/aeos/memory/

# 5. Vérifier l'intégration CLI
uv run aeos memory --help

# 6. Décider du prochain sprint avec le CTO
# → consolidation, correction, ou extension CLI memory
```

---

## 7. Historique des mises à jour

| Date | Mise à jour |
|---|---|
| 2026-06-29 | Création initiale — état post-sprint3f, memory layer mergé |
| 2026-06-29 | Ajout du workflow multi-agent (sprint3f3) — `AEOS-MULTI-AGENT-WORKFLOW.md` créé |
