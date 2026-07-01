# AEOS Workspace Doctor

**Sprint:** MVP-UX-4
**Status:** SHIPPED

---

## Summary

`aeos workspace doctor` runs a full local health check of the AEOS workspace.
It diagnoses every layer — home directory, registry integrity, per-project
directories, and the generated workspace — and reports an overall status of
`OK`, `WARNING`, or `ERROR`.

Purely read-only. No files written. No network. No secrets. No `.env`.

---

## Usage

```sh
aeos workspace doctor [--output-dir <dir>]
```

`--output-dir` defaults to `$TMPDIR/aeos-workspace-demo`.

---

## Example output — all OK

```
AEOS Workspace Doctor

  [OK]       AEOS home                         /Users/you/.aeos
  [OK]       Registry                          /Users/you/.aeos/projects.json
  [OK]       Registry readable                 valid JSON · 1 project(s)
  [OK]       Registry flags                    local_only=true  ·  read_only=true
  [OK]       Projects registered               1 project
  [OK]       [ma-mairie-digitale] memory_dir   /tmp/.../memory  ✓
  [OK]       [ma-mairie-digitale] flags        local_only=true  ·  read_only=true
  [OK]       Workspace index                   /tmp/aeos-workspace-demo/index.html

Overall:           OK

Suggested next:    aeos workspace open --path /tmp/aeos-workspace-demo/index.html

  read_only: true  ·  applied: false
```

## Example output — WARNING (workspace not generated)

```
AEOS Workspace Doctor

  [OK]       AEOS home                         /Users/you/.aeos
  [OK]       Registry                          /Users/you/.aeos/projects.json
  [OK]       Registry readable                 valid JSON · 1 project(s)
  [OK]       Registry flags                    local_only=true  ·  read_only=true
  [OK]       Projects registered               1 project
  [OK]       [ma-mairie-digitale] memory_dir   /tmp/.../memory  ✓
  [OK]       [ma-mairie-digitale] flags        local_only=true  ·  read_only=true
  [WARNING]  Workspace index                   /tmp/aeos-workspace-demo/index.html  (not found)

Overall:           WARNING

Suggested next:    aeos workspace demo --output-dir /tmp/aeos-workspace-demo

  read_only: true  ·  applied: false
```

## Example output — ERROR (no registry)

```
AEOS Workspace Doctor

  [ERROR]    AEOS home                         /Users/you/.aeos  (not found — run: aeos workspace init)
  [ERROR]    Registry                          /Users/you/.aeos/projects.json  (not found — run: aeos workspace init)

Overall:           ERROR

Suggested next:    aeos workspace init

  read_only: true  ·  applied: false
```

Exit code is `1` when `Overall` is `ERROR`, `0` otherwise.

---

## Checks performed

| # | Check | OK | WARNING | ERROR |
|---|-------|----|---------|-------|
| 1 | AEOS home exists | dir present | — | dir absent |
| 2 | Registry exists | file present | — | file absent |
| 3 | Registry readable JSON | valid JSON | — | parse error |
| 4 | Registry flags | local_only + read_only = true | either false | — |
| 5 | Projects registered | ≥1 project | 0 projects | — |
| 6a | `[proj]` memory_dir | dir exists | — | dir missing |
| 6b | `[proj]` evidence_dir | dir exists | dir missing | — |
| 6c | `[proj]` flags | both true | either false | — |
| 7 | Workspace index.html | file exists | file missing | — |

---

## Exit codes

| Exit code | Meaning |
|-----------|---------|
| `0` | Overall OK or WARNING — no action required to read the workspace |
| `1` | Overall ERROR — run the suggested command to fix |

---

## Implementation

| File | Role |
|------|------|
| `src/aeos/workspace/doctor.py` | Library: `CheckItem`, `DoctorResult`, `workspace_doctor()` |
| `src/aeos/workspace/__init__.py` | Re-exports |
| `src/aeos/cli.py` | CLI command `workspace doctor` |
| `tests/unit/test_workspace_doctor.py` | Unit tests (library + CLI) |

---

## Safety guarantees

| Guarantee | Detail |
|-----------|--------|
| No `.env` read | Not imported anywhere in the doctor path |
| No secrets shown | Only filesystem paths, counts, and boolean flags |
| No client project mutation | Zero write operations |
| No network call | Pure local filesystem checks |
| No AI call | Deterministic Python logic |
| No migration applied | `applied: false` in every output |
| Registry never modified | `load_registry()` only — `save_registry()` never called |

---

## Recommended usage pattern

```sh
# After any environment change, run doctor to verify state:
aeos workspace doctor

# Full first-run sequence:
aeos workspace init      # create ~/.aeos if absent
aeos workspace doctor    # verify environment
aeos project register \  # add a project
  --name my-project \
  --memory-dir /path/to/memory
aeos workspace demo      # generate workspace
aeos workspace open      # open in browser
```
