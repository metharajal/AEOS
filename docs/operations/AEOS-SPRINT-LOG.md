# AEOS Sprint Log

**Version :** 2026-06-29  
**Auteur :** AEOS Operations  
**Statut :** Document vivant — à mettre à jour après chaque sprint

---

## Conventions

| Champ | Description |
|---|---|
| **Objectif** | Ce que le sprint devait accomplir |
| **Commandes ajoutées** | Nouvelles commandes CLI ou fonctionnalités |
| **PR / Commit** | Référence GitHub si connue |
| **Statut** | `DONE`, `PARTIAL`, `ABANDONED` |
| **Validation** | Critère principal de succès |

---

## Sprint 0 — Fondations AEOS

**Objectif :** Créer la structure de base du projet AEOS.

- Structure repo : `src/aeos/`, `tests/`, `docs/`
- `pyproject.toml`, `uv`, `.python-version`
- Premier `aeos --version`

**Commandes ajoutées :** `aeos --version`  
**Statut :** DONE  
**Validation :** `uv run aeos --version` retourne une version.

---

## Sprint 1 — Inspect

**Objectif :** Ajouter la commande `aeos inspect` pour auditer un projet.

- Détection de fichiers sensibles (`.env`, secrets en clair)
- Détection de dépendances outdated
- Rapport d'audit en sortie console

**Commandes ajoutées :** `aeos inspect`  
**Statut :** DONE  
**Validation :** `aeos inspect` retourne un rapport d'audit sur `ma-mairie-digitale`.

---

## Sprint 2A-2R — AI Config, Security, Sovereignty, Report, Reclaim Intelligence

**Objectif :** Itérations successives sur les rails Security et Reclaim.

- Configuration des modèles IA locaux
- Détection RLS manquante sur Supabase
- Rapport de souveraineté (dépendances cloud, vendor lock-in)
- Premiers résultats Reclaim avec scoring de sécurité

**Statut :** DONE  
**Validation :** Rapport complet généré sur `ma-mairie-digitale`.

---

## Sprint 2T — RLS Inspector

**Objectif :** Inspecter les politiques RLS d'une base Supabase.

- Détection des tables sans RLS activé
- Détection des tables avec RLS activé mais sans politique définie
- Rapport structuré par table

**Commandes ajoutées :** `aeos supabase rls inspect`  
**Statut :** DONE  
**Validation :** Rapport RLS généré pour `ma-mairie-digitale`.

---

## Sprint 2U — RLS Plan Advisor

**Objectif :** Générer un plan de correction RLS à partir du rapport d'inspection.

- Recommandations par table (activer RLS, ajouter politique, revoir politique)
- Priorisation par niveau de risque

**Commandes ajoutées :** `aeos supabase rls plan`  
**Statut :** DONE  
**Validation :** Plan RLS généré et lisible sans connexion Supabase.

---

## Sprint 2V — RLS Migration Generator

**Objectif :** Générer les fichiers de migration SQL pour corriger le RLS.

- Génération de SQL `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- Génération de politiques `CREATE POLICY`
- Fichiers de migration compatibles Supabase CLI

**Commandes ajoutées :** `aeos supabase rls generate`  
**Statut :** DONE  
**Validation :** Fichiers SQL générés et syntaxiquement corrects.

---

## Sprint 2W — RLS Review Gate

**Objectif :** Ajouter une gate de validation avant d'appliquer les migrations RLS.

- Affichage du diff avant apply
- Confirmation utilisateur requise
- Blocage de l'apply si gate refusée

**Commandes ajoutées :** `aeos supabase rls review`  
**Statut :** DONE  
**Validation :** Gate affichée, apply bloqué sans confirmation.

---

## Sprint 2Y — RLS generate --output

**Objectif :** Ajouter l'option `--output` à `rls generate` pour écrire dans un fichier.

- `--output <path>` écrit le SQL dans un fichier au lieu de stdout
- Compatible avec `/tmp` pour tests sans modifier le repo

**Commandes ajoutées :** `aeos supabase rls generate --output <path>`  
**Statut :** DONE  
**Validation :** Fichier SQL généré dans `/tmp`, repo non modifié.

---

## Sprint 2Z — supabase rls harden

**Objectif :** Commande tout-en-un pour inspecter, planifier et générer les corrections RLS.

- Orchestre : inspect → plan → generate
- Produit un rapport consolidé
- `--output` disponible

**Commandes ajoutées :** `aeos supabase rls harden`  
**Statut :** DONE  
**Validation :** Rapport complet généré en une commande.

---

## Sprint 3A — reclaim harden

**Objectif :** Créer la commande `aeos reclaim harden` comme point d'entrée principal du rail Reclaim.

- Audit complet du projet cible
- Génération d'un plan de remédiation
- Intégration de l'inspection RLS si Supabase détecté

**Commandes ajoutées :** `aeos reclaim harden`  
**Statut :** DONE  
**Validation :** `aeos reclaim harden --project ~/aeos-client-audits/ma-mairie-digitale` produit un rapport.

---

## Sprint 3B — docs reclaim harden

**Objectif :** Documenter la commande `aeos reclaim harden`.

- Création de `docs/features/AEOS-RECLAIM-HARDEN.md`
- Exemples d'usage, options, sorties attendues

**PR / Commit :** PR #30  
**Statut :** DONE  
**Validation :** Document présent dans `docs/features/`.

---

## Sprint 3C — reclaim harden --output

**Objectif :** Ajouter l'option `--output` à `aeos reclaim harden`.

- Écrit le rapport dans un fichier au lieu de stdout
- Permet la revue avant intégration dans le repo

**Commandes ajoutées :** `aeos reclaim harden --output <path>`  
**PR / Commit :** `6534140` / `26444d1`  
**Statut :** DONE  
**Validation :** Rapport écrit dans `/tmp/reclaim-report.md`, repo non modifié.

---

## Sprint 3D — Product Rails and Agents Vision

**Objectif :** Documenter la vision produit complète : rails, agents, positionnement.

- `docs/strategy/AEOS-PRODUCT-VISION.md`
- `docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md`
- Positionnement vs Lovable
- Rails : Build, Reclaim, Modernize, Migrate, Operate, Security, Sovereignty, Agents, Memory

**PR / Commit :** PR #31 — `9e04258`  
**Statut :** DONE  
**Validation :** Documents stratégiques présents dans `docs/strategy/`.

---

## Sprint 3E — Remediation Plan

**Objectif :** Enrichir la sortie de `aeos reclaim harden` avec un plan de remédiation structuré.

- Sections : critique, élevé, moyen, faible
- Actions concrètes par finding
- Ordre de priorité recommandé

**PR / Commit :** PR #32 — `aa4d5d6`  
**Statut :** DONE  
**Validation :** Plan de remédiation inclus dans le rapport `harden`.

---

## Sprint 3F — Memory Layer MVP

**Objectif :** Ajouter un système de mémoire local-first pour stocker les diagnostics AEOS.

- `src/aeos/memory/store.py` — store SQLite local
- `src/aeos/memory/models.py` — modèles Pydantic
- `src/aeos/memory/__init__.py`
- `tests/unit/test_memory_store.py` — 573 lignes de tests
- `docs/features/AEOS-MEMORY-LAYER.md` — spec fonctionnelle

**PR / Commit :** Mergé dans PR #33 — `7139b77`  
**Statut :** DONE (MVP mergé — à consolider)  
**Validation :** `pytest tests/unit/test_memory_store.py` passe.

---

## Sprint 3F-0 — AI Mac Workstation Setup

**Objectif :** Documenter la reconstruction complète d'une workstation Mac pour AEOS.

- `docs/operations/AEOS-AI-MAC-WORKSTATION-SETUP.md`
- 14 sections : système, Python, Node, Docker, IA locale, cloud CLIs, reprise AEOS, clients, sécurité, validation, inventaire, troubleshooting
- Inventaire du Mac actuel (installé / absent / optionnel)
- Troubleshooting : ancien workspace AI-Foundation-Kit, `.venv` cassé, prompt shell, `__pycache__`

**PR / Commit :** PR #33 — `5f2c1ed`  
**Statut :** DONE  
**Validation :** Document présent dans `docs/operations/`, CI verte, mergé dans main.

---

## Sprint 3F-1 — CTO Handoff and Continuity Notes

**Objectif :** Documenter le protocole de reprise AEOS pour assurer la continuité entre sessions et entre agents.

- `docs/operations/AEOS-CTO-HANDOFF.md` — vision, doctrine, rails, rôles agents, règles de sécurité, état actuel
- Document vivant, à mettre à jour à chaque décision structurante

**PR / Commit :** PR #34 — `1f2f6f5`  
**Statut :** DONE  
**Validation :** Document présent dans `docs/operations/`, CI verte, mergé dans main.

---

## Sprint 3F-3 — Multi-Agent Operating Model

**Objectif :** Documenter comment AEOS doit être développé avec plusieurs IA sans perdre la continuité, la sécurité ni la souveraineté.

- `docs/operations/AEOS-MULTI-AGENT-WORKFLOW.md` — rôles ChatGPT, Claude Code, Codex, IA locale, Antigravity
- Protocole obligatoire avant chaque tâche agent (7 documents à lire)
- Règles interdites non négociables
- Checks obligatoires avant PR
- Modèle opérationnel : "ChatGPT conseille. Le repo se souvient. Claude Code exécute. Codex travaille en parallèle. L'IA locale protège. Antigravity expérimente. GitHub prouve. L'humain valide."

**PR / Commit :** PR #35 — `fee7187`  
**Statut :** DONE  
**Validation :** Document présent dans `docs/operations/`, CI verte, mergé dans main.

---

## Sprint 3G — Memory Read CLI

**Objectif :** Ajouter les commandes de lecture mémoire pour compléter la chaîne :
`reclaim harden → MemoryRecord → memory list → memory show`

**Livraisons :**

- `src/aeos/memory/models.py` — `MemoryRecordSummary`, `MemoryListResult`
- `src/aeos/memory/store.py` — `list_records()`, `load_record()`, `find_record_path()`
- `src/aeos/memory/__init__.py` — exports publics mis à jour
- `src/aeos/cli.py` — sous-commande `memory` avec `list` et `show`
- `tests/unit/test_memory_cli.py` — 28 tests unitaires

**Commandes ajoutées :**

```bash
aeos memory list --memory-dir <dir>
aeos memory list --memory-dir <dir> --json
aeos memory show --memory-dir <dir> --record <record_id>
aeos memory show --memory-dir <dir> --record <record_id> --json
```

**PR / Commit :** PR #36 — commit `f5dc4ff`, merge `4e6c06c`  
**Statut :** DONE — mergé dans main, CI verte, 1316 tests passés  
**Validation :** `uv run pytest` → 1316 passed. `aeos memory list` et `aeos memory show` fonctionnels.

---

## Sprint 3G-1 — Memory CLI Usage Documentation

**Objectif :** Documenter proprement la chaîne Memory complète disponible dans AEOS.

- `docs/features/AEOS-MEMORY-LAYER.md` — guide d'usage end-to-end, garanties, limites, API mise à jour
- `docs/operations/AEOS-SPRINT-LOG.md` — entrées sprint 3F-1, 3F-3, 3G ajoutées
- `docs/operations/AEOS-NEXT-ACTIONS.md` — priorités mises à jour (3H, 3I, 4A)

**PR / Commit :** PR #37 — mergé dans main (`a8f7e51`)
**Statut :** DONE
**Validation :** Documentation disponible dans `docs/features/AEOS-MEMORY-LAYER.md`.

---

## Sprint 3H — Memory Compare

**Objectif :** Ajouter `aeos memory compare` pour comparer deux MemoryRecords et mesurer la progression entre deux audits.

**Livraisons :**

- `src/aeos/memory/compare.py` — `MemoryCompareDelta`, `MemoryCompareResult`, `compare_records()`, `load_record_reference()`, `compute_trend()`
- `src/aeos/memory/__init__.py` — exports mis à jour
- `src/aeos/cli.py` — sous-commande `memory compare`
- `tests/unit/test_memory_compare.py` — 26 tests unitaires
- `docs/features/AEOS-MEMORY-LAYER.md` — Section 10 Memory Compare ajoutée

**Commandes ajoutées :**

```bash
aeos memory compare --memory-dir <dir> --left <record_id_or_path> --right <record_id_or_path>
aeos memory compare --memory-dir <dir> --left <id> --right <id> --json
```

Synthesis categories : `improved` | `degraded` | `unchanged` | `mixed` | `incompatible`.
`--left` / `--right` acceptent un record_id ou un chemin JSON direct.

**PR / Commit :** PR #38 — mergé dans main (`401d485`)
**Statut :** DONE — 1342 tests passés
**Validation :** `uv run pytest` → 1342 passed. `aeos memory compare` fonctionnel.

---

## Sprint 3H-1 — Memory Compare Real-World Validation

**Objectif :** Valider en conditions réelles la chaîne Memory complète sur `ma-mairie-digitale`
sans modifier le projet client.

**Projet utilisé :** `~/aeos-client-audits/ma-mairie-digitale` — ouvert en lecture seule uniquement.

**Dossier mémoire temporaire :** `/tmp/aeos-memory-compare-validation` — hors du projet client.

**Séquence exécutée :**

1. `aeos reclaim harden --memory-dir /tmp/aeos-memory-compare-validation` → record #1
2. `aeos reclaim harden --memory-dir /tmp/aeos-memory-compare-validation` → record #2
3. `aeos memory list --memory-dir /tmp/aeos-memory-compare-validation` → 2 records listés
4. `aeos memory show --record ma-mairie-digitale-20260629T214040-087abc8d` → OK
5. `aeos memory show --record ma-mairie-digitale-20260629T214048-da25f672` → OK
6. `aeos memory compare --left <id1> --right <id2>` → `Synthesis: unchanged` (7 champs)
7. `aeos memory compare --left <id1> --right <id2> --json` → JSON valide

**Records comparés :**

| Rôle | Record ID |
|---|---|
| Left (1er audit) | `ma-mairie-digitale-20260629T214040-087abc8d` |
| Right (2ème audit) | `ma-mairie-digitale-20260629T214048-da25f672` |

**Résultat compare :** `synthesis: unchanged` — tous les 7 champs identiques.
Comportement attendu : deux audits consécutifs du même projet non modifié.

**Garanties confirmées :**
- `ma-mairie-digitale` : `git status` clean avant et après — aucune modification
- Aucune connexion base de données
- Aucune migration lancée
- Aucun `.env` lu
- Aucun secret affiché
- Fichiers mémoire dans `/tmp` uniquement, hors du projet client
- `read_only: true` · `applied: false` dans les deux records

**Livraisons :**
- `docs/features/AEOS-MEMORY-LAYER.md` — Section 11 : Real-World Validation Scenario

**PR / Commit :** PR #39 — mergé dans main (`f7ed7e9`)
**Statut :** DONE
**Validation :** Chaîne complète exécutée, résultat `unchanged` confirmé, repos propres.

---

## Sprint 3I — Memory Timeline MVP

**Objectif :** Ajouter `aeos memory timeline --memory-dir <dir> --project <name>` pour
afficher la timeline chronologique de tous les MemoryRecords d'un projet.

**Livraisons :**

- `src/aeos/memory/timeline.py` — `MemoryTimelineEntry`, `MemoryTimelineResult`,
  `MemoryTimelineSynthesis`, `load_project_records()`, `build_timeline()`,
  `compute_timeline_synthesis()`, `timeline_to_dict()`
- `src/aeos/memory/__init__.py` — exports mis à jour
- `src/aeos/cli.py` — sous-commande `memory timeline`
- `tests/unit/test_memory_timeline.py` — 22 tests unitaires
- `docs/features/AEOS-MEMORY-LAYER.md` — Section 11 Memory Timeline ajoutée

**Commandes ajoutées :**

```bash
aeos memory timeline --memory-dir <dir> --project <project_name>
aeos memory timeline --memory-dir <dir> --project <project_name> --json
```

Synthesis : `improved` | `degraded` | `unchanged` | `insufficient_data`.
Colonnes affichées : date, record_id, status, control_level, critical, important, manual, generated.

**PR / Commit :** Sprint 3I — branch `sprint3i/memory-timeline-mvp`
**Statut :** DONE — 1364 tests passés
**Validation :** `uv run pytest` → 1364 passed. `aeos memory timeline` fonctionnel.

---

## Sprint 4A — Build Rail MVP

**Objectif :** Ajouter le premier MVP du rail Build dans AEOS.
Commande : `aeos build plan --name <name> --type <type> --stack <stack>`.
Produit un plan d'architecture structuré en texte et JSON. Read-only.

**Livraisons :**

- `src/aeos/build/__init__.py` — module Build Rail, exports publics
- `src/aeos/build/planner.py` — `BuildPlan`, `create_build_plan()`,
  `build_plan_to_dict()`, `validate_project_type()`, `validate_stack()`
- `src/aeos/cli.py` — sous-commande `build plan` + Typer `build_app`
- `tests/unit/test_build_planner.py` — 18 tests unitaires
- `docs/features/AEOS-BUILD-RAIL.md` — documentation complète du rail Build
- `docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md` — section Build Rail mise à jour

**Commandes ajoutées :**

```bash
aeos build plan --name <project> --type <type> --stack <stack>
aeos build plan --name <project> --type <type> --stack <stack> --json
```

Types : `web-app` · `api` · `internal-tool`
Stacks : `nextjs-supabase` · `nextjs-postgres` · `fastapi-postgres` · `generic`

**Sections du plan généré :**
Project Identity · Architecture Summary · Folder Structure · Governance Files ·
Security Baseline · Sovereignty Baseline · Testing Baseline · Deployment Baseline ·
Recommended Next Steps.

**Garanties :**
`read_only: true` · `applied: false` · Aucun projet créé · Aucun secret · Aucun
appel réseau · Aucun appel IA externe.

**PR / Commit :** Sprint 4A — branch `sprint4a/build-rail-mvp`
**Statut :** DONE — 1382 tests passés
**Validation :** `uv run pytest` → 1382 passed. `aeos build plan` fonctionnel.
