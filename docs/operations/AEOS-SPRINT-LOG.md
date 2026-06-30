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

**PR / Commit :** PR #41 — mergé dans main (`6c5c598`)
**Statut :** DONE — 1382 tests passés
**Validation :** `uv run pytest` → 1382 passed. `aeos build plan` fonctionnel.

---

## Sprint 4B — Build Scaffold MVP

**Objectif :** Ajouter `aeos build scaffold` pour générer un squelette minimal de
gouvernance dans un dossier output explicitement fourni.
Première commande write d'AEOS (`read_only: false`, `applied: true`).
Aucun code applicatif généré. Aucun npm/pnpm/uv/docker lancé.

**Livraisons :**

- `src/aeos/build/scaffold.py` — `BuildScaffoldResult`, `ScaffoldedFile`,
  `scaffold_build_project()`, `render_scaffold_files()`, `ensure_safe_output_directory()`,
  `scaffold_result_to_dict()`
- `src/aeos/build/__init__.py` — exports mis à jour (scaffold)
- `src/aeos/cli.py` — sous-commande `build scaffold`
- `tests/unit/test_build_scaffold.py` — 16 tests unitaires
- `docs/features/AEOS-BUILD-RAIL.md` — Section 7 Build Scaffold ajoutée

**Commandes ajoutées :**

```bash
aeos build scaffold --name <project> --type <type> --stack <stack> --output <dir>
aeos build scaffold --name <project> --type <type> --stack <stack> --output <dir> --force
aeos build scaffold --name <project> --type <type> --stack <stack> --output <dir> --json
```

**Fichiers générés (8) :**

```
README.md · ARCHITECTURE.md · .env.example · .gitignore · aeos.toml
docs/DECISIONS.md · docs/SECURITY.md · docs/SOVEREIGNTY.md
```

**Garanties write :**
Écriture uniquement dans `--output` · Aucun `.env` créé · Aucune valeur secrète ·
`read_only: false` · `applied: true` · Aucun appel réseau · Aucun appel IA externe ·
`--output` non vide sans `--force` → refus avec message d'erreur clair.

**PR / Commit :** PR #42 — mergé dans main (`a7afee4`)
**Statut :** DONE — 1398 tests passés
**Validation :** `uv run pytest` → 1398 passed. `aeos build scaffold` fonctionnel.

---

## Sprint 4B-1 — Build Scaffold Real-World Validation

**Objectif :** Valider en conditions réelles la commande `aeos build scaffold`
dans `/tmp`, sans toucher aucun projet client.

**Commande exécutée :**

```bash
uv run aeos build scaffold \
  --name civic-portal \
  --type web-app \
  --stack nextjs-supabase \
  --output /tmp/aeos-build-civic-portal
```

**Output utilisé :** `/tmp/aeos-build-civic-portal` — hors du projet AEOS et hors de `ma-mairie-digitale`.

**Vérifications effectuées :**

| Vérification | Résultat |
|---|---|
| 8 fichiers créés dans `--output` uniquement | ✓ |
| `.gitignore` protège `.env` / `.env.*` / `!.env.example` | ✓ |
| `.env.example` — placeholders uniquement, aucun secret réel | ✓ |
| `aeos.toml` — `local_first = true`, `human_approval_required = true` | ✓ |
| Mode `--json` — `read_only: false`, `applied: true`, JSON valide | ✓ |
| Refus sur dossier non vide sans `--force` — exit code 1, message clair | ✓ |
| Aucun fichier écrit hors `--output` | ✓ |
| Aucune application complète générée | ✓ |
| Aucun appel réseau | ✓ |
| Aucun secret affiché | ✓ |
| Aucun projet client touché | ✓ |
| `uv run pytest` → 1398 passed | ✓ |

**Garanties confirmées :**
`read_only: false` · `applied: true` · output-confined · aucun secret ·
aucun réseau · aucun code applicatif · `ma-mairie-digitale` intact.

**Livraisons :**
- `docs/features/AEOS-BUILD-RAIL.md` — Section 11 Real-World Validation ajoutée
- `docs/operations/AEOS-SPRINT-LOG.md` — entrée Sprint 4B-1

**PR / Commit :** Sprint 4B-1 — branch `sprint4b1/build-scaffold-real-validation`
**Statut :** DONE
**Validation :** Validation réelle exécutée, tous les checks verts, repo clean.

---

## Sprint 5A — Reclaim Recovery Plan

**Objectif :** Ajouter `aeos reclaim recovery plan` — plan de récupération complet
pour un projet existant, en lecture seule.

**Commande ajoutée :** `aeos reclaim recovery plan [--path] [--json] [--output] [--overwrite]`

**13 sections couvertes :**
1. Project Identity
2. Current Architecture (frontend, backend, database, auth, deployment, portabilité)
3. Control Status (secrets, exposition, source control, portabilité)
4. Security Recovery (blocages immédiats, gitignore, .env.example)
5. Sovereignty Recovery (dépendances externes, risques, exit strategy)
6. Database and RLS Recovery (Supabase, RLS verdict, fixes auto, revue manuelle)
7. Governance Recovery (aeos.toml, DECISIONS, SECURITY, SOVEREIGNTY)
8. Testing and CI Recovery
9. Local AI Development Policy (8 can_do, 7 requires_approval, 7 never_send)
10. Frontier AI Escalation Rules (6 règles)
11. Recovery PR Roadmap (7+ PRs avec priorité et prérequis)
12. Development Continuation Backlog (6 catégories)
13. Recommended Next Action

**Fichiers ajoutés / modifiés :**
- `src/aeos/reclaim/recovery.py` — nouveau module (RecoveryPlan + 5 dataclasses + builders)
- `src/aeos/reclaim/__init__.py` — exports recovery ajoutés
- `src/aeos/cli.py` — commande `aeos reclaim recovery plan` ajoutée
- `tests/unit/test_reclaim_recovery.py` — 22 tests
- `docs/features/AEOS-RECLAIM-RECOVERY.md` — documentation

**Garanties read-only :**
Aucun fichier modifié dans le projet audité · Aucune base de données contactée ·
Aucun `.env` lu · Aucun secret affiché · Aucun appel réseau · Aucun appel IA externe ·
`read_only: true` · `applied: false`

**PR / Commit :** PR #44 + PR #45 — mergés dans main (`3ecbea9`)
**Statut :** DONE — 1420 tests passés
**Validation :** `uv run pytest` → 1420 passed. `aeos reclaim recovery plan` fonctionnel.

---

## Sprint 5A-2 — Reclaim Recovery Real-World Validation

**Objectif :** Valider en conditions réelles la commande `aeos reclaim recovery plan`
sur `ma-mairie-digitale`, output dans `/tmp` uniquement.

**Commande exécutée :**

```bash
uv run aeos reclaim recovery plan \
  --path ~/aeos-client-audits/ma-mairie-digitale \
  --output /tmp/ma-mairie-digitale-recovery-plan.md
```

**Output utilisé :** `/tmp/ma-mairie-digitale-recovery-plan.md` (9.4K) —
hors du projet AEOS et hors de `ma-mairie-digitale`.

**Résultats obtenus :**

| Champ | Valeur |
|---|---|
| Status | `ERROR` |
| Generator détecté | `lovable` |
| Provider détecté | `supabase` |
| Secrets exposure | `confirmed` |
| Portability | `weak` |
| Source control | `git_present` |
| `.gitignore` protects `.env` | `yes` |
| `.env.example` | `yes` |
| PRs in roadmap | 7 |

**Vérifications de sécurité :**

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

**Livraisons :**
- `docs/features/AEOS-RECLAIM-RECOVERY.md` — Section 12 Real-World Validation ajoutée
- `docs/operations/AEOS-SPRINT-LOG.md` — entrée Sprint 5A-2

**PR / Commit :** branch `sprint5a2/reclaim-recovery-real-validation`
**Statut :** DONE
**Validation :** Validation réelle exécutée, tous les checks verts, repos propres.

---

## Sprint 5B — Total Sovereign Recovery Vision

**Objectif :** Élargir la vision AEOS de "reclaim audit/recovery plan" vers une doctrine complète de reprise totale souveraine.

**Ce sprint ne modifie aucun code Python. Documentation stratégique uniquement.**

### Vision élargie

La vision AEOS passe de :
> "AEOS audite et génère un plan de récupération"

vers :
> "AEOS accompagne un client depuis un projet généré, fragile ou dépendant jusqu'à un logiciel maîtrisé, sécurisé, migrable si nécessaire, maintenable, exploitable et développable dans la durée avec IA locale en priorité et IA frontière seulement par exception."

### Doctrine centrale (confirmée)

```
AEOS Core guarantees.
AEOS Agents reason.
AEOS Memory learns.
Humans validate.

AEOS is not a chatbot.
AEOS is not a blind autonomous agent.
AEOS is a controlled agentic operating system for sovereign software recovery, continuation, and operation.
```

### Ce qui a été ajouté

**`docs/strategy/AEOS-PRODUCT-VISION.md` — section 14 : Total Sovereign Recovery**

- Promesse : *From generated prototype to sovereign software. / De prototype généré à logiciel souverain maîtrisé.*
- Full recovery arc (12 phases : compréhension → secrets → architecture → gouvernance → RLS → tests → CI → local run → portabilité → migration → IA locale → exploitation souveraine)
- Souveraineté progressive : `weak → partial → controlled → portable → sovereign`
- 8 dimensions de souveraineté : code, data, secret, deployment, architecture, AI, knowledge, operational
- Doctrine agentique réaffirmée : AEOS n'est pas un agent autonome sans contrôle

**`docs/strategy/AEOS-PRODUCT-RAILS-AND-AGENTS.md` — sections 8, 9, 10**

- Reclaim → Recover → Continue : l'arc de reprise standard documenté
- Clarification : Reclaim / Recover / Continue / Migration / Operate
- Section 8 : Agentic Operating Model — 12 agents AEOS avec scope et rails
- Section 9 : AEOS Action Levels (Level 0–5) — du diagnostic vers l'exploitation continue
- Section 10 : Total Recovery Stage Model — 10 stages avec 9 dimensions chacun :
  - objectif, préconditions, actions, risques, preuves attendues, gates humains, rollback, MemoryRecord, agents
- Mapping stage → agents

**`docs/features/AEOS-RECLAIM-RECOVERY.md` — sections 13, 14, 15**

- Section 13 : Total Recovery Scope — migration rules (8 règles non négociables)
- Section 14 : Local AI First Development Continuation (8 règles permanentes)
- Section 15 : Recovery Evidence — 8 types de preuves + chaîne complète de mesure

**`docs/operations/AEOS-NEXT-ACTIONS.md`**

- État mis à jour (main = `b4464dc`, 1420 tests, Sprint 5A mergé)
- Roadmap Sprint 5B → 5I documentée
- Sprint 5I : contrat UI — Paste URL / Express or Expert / Run Sovereignty Recovery / View roadmap / Prepare PRs / Continue with local AI

**`docs/operations/AEOS-SPRINT-LOG.md`**

- Cette entrée

### Ce qui reste inchangé

- Tous les rails existants (Build, Reclaim, Modernize, Migrate, Operate, Security, Sovereignty, Agents, Memory)
- Toutes les commandes CLI existantes
- Toutes les garanties read-only
- La doctrine local-first / open-source-first / AI-local-first
- Les 1420 tests

### Invariants maintenus

- Ne pas réduire AEOS à Reclaim
- Ne pas présenter AEOS comme un agent autonome sans contrôle
- Ne pas affaiblir les rails déjà documentés
- Ne pas modifier le code Python ni les tests

**Fichiers modifiés :** 5 (documentation uniquement)
**Lignes ajoutées :** ~400
**Commandes CLI ajoutées :** 0
**Tests ajoutés :** 0
**Statut :** DONE (documentation) — implémentation dans Sprints 5C–5I

**PR / Commit :** branch `sprint5b/total-sovereign-recovery-vision`
**Validation :** `uv run ruff check .` · `uv run mypy src` · `uv run pytest` — tous verts (aucun code modifié)

---

## Sprint 5C — Total Recovery Stage Model

**Date :** 2026-06-29 → 2026-06-30
**Branche :** `sprint5c/total-recovery-stage-model`
**Objectif :** Implémenter en Python le registre des 10 stages du Total Sovereign Recovery Arc.

### Ce qui a été ajouté

**Python (read-only, aucune mutation) :**

- `src/aeos/reclaim/stages.py` — `RecoveryStage` dataclass (11 champs), `get_recovery_stages()` (10 stages complets), `get_stage_by_id()`, `recovery_stage_to_dict()`
- `src/aeos/reclaim/__init__.py` — 4 nouveaux imports et exports dans `__all__` (RUF022 trié)
- `src/aeos/cli.py` — sous-app `reclaim stage` avec 2 commandes :
  - `aeos reclaim stage list [--json]`
  - `aeos reclaim stage show --id <stage_id> [--json]`

**Tests :**

- `tests/unit/test_reclaim_stages.py` — 45 tests couvrant : registry (10 stages, IDs uniques, ordre), dataclass (tous les champs), `get_stage_by_id`, `recovery_stage_to_dict`, CLI `stage list`, CLI `stage show`

**Documentation :**

- `docs/features/AEOS-RECLAIM-RECOVERY.md` — section 16 : Recovery Stage Model (structure, 10 stages, CLI, API Python, garanties read-only)
- `docs/operations/AEOS-SPRINT-LOG.md` — cette entrée

### Périmètre strict respecté

| Dans le scope | Hors scope |
|---------------|------------|
| Modèles Python typés | Orchestrateur ou exécution de stages |
| Registry des 10 stages | Mutation des MemoryRecords existants |
| CLI read-only list/show | Modification du modèle Memory |
| Tests unitaires | Appel réseau ou secret |
| Documentation minimale | Liaison MemoryRecord réelle |

### Invariants maintenus

- `read_only: true · applied: false` présent dans toutes les sorties CLI
- Aucun stage ne s'exécute — le modèle documente uniquement
- Aucun `.env` lu, aucune base de données contactée, aucun secret affiché
- Tous les checks verts : `ruff`, `mypy`, `pytest`

**Fichiers modifiés :** 5 (3 Python + 2 docs)
**Lignes ajoutées :** ~500
**Commandes CLI ajoutées :** 2 (`stage list`, `stage show`)
**Tests ajoutés :** 45
**Statut :** DONE

**PR / Commit :** branch `sprint5c/total-recovery-stage-model`
**Validation :** `uv run ruff check .` · `uv run mypy src` · `uv run pytest` — tous verts
