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
