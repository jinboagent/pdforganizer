# pdf_organizer — Software Specification

Version 1.0 · October 2026

## 1. Introduction

### 1.1 Purpose
`pdf_organizer` organizes a folder of PDF files **by content**: it extracts text and
metadata from each PDF, classifies the document into a topic category, optionally
renames files whose names do not reflect their content, and moves every file into a
category subfolder. It produces human-readable reports and is fully reversible.

### 1.2 Scope
In scope: local, offline processing of PDF files on Windows/Linux/macOS.
Out of scope: OCR of scanned images, network services, duplicate detection,
non-PDF documents.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| record | One PDF's extraction result: `{file, pages, size, err, meta, text}` |
| title zone | filename + metadata title + first ~350 chars of page text (lowercased); the highest-value evidence region |
| strong / weak pattern | Keyword regex carrying high / low classification weight |
| op | One planned operation: `{src, cat, name, dst, old_name, score, top, err}` |
| uncategorized | Destination for files without a confident category |

## 2. System overview

```
            config.json / CLI flags
                    │
                    ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ 1. FIND  │→ │2. EXTRACT│→ │3. CLASSIFY│→ │4. PLAN   │→ │5. APPLY  │
  │ scan     │  │ per-PDF  │  │ score vs │  │ rename + │  │ move     │
  │ pdfs,    │  │ subprocess│ │ categories│  │ target + │  │ (or dry- │
  │ apply    │  │ + timeout │ │ (rules)  │  │ collision│  │  run)    │
  │ ignore   │  │ + cache   │  │          │  │          │  │          │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘
                                                                 ▼
                                                    6. REPORTS + undo log
```

Stages 2 and 5 are resumable/idempotent: extraction results are cached on disk, and
the move log enables `--undo`.

## 3. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | The tool shall scan an input folder for `*.pdf` files (case-insensitive), optionally recursing into subfolders (`recursive`). |
| FR-2 | The tool shall skip any file or folder matching a glob in `ignore` (matched against any path part and the relative path). |
| FR-3 | For each PDF the tool shall extract: page count, file size, metadata title, and the text of the first `max_pages` pages (truncated at 4,000 chars). |
| FR-4 | Extraction shall run one PDF per subprocess with a hard timeout (`extract_timeout_sec`); failures shall be recorded, never crash the run. |
| FR-5 | Extraction results shall be cached under `work_folder`; a re-run shall reuse cached records without re-reading PDFs. |
| FR-6 | The tool shall assign each PDF exactly one category from the configured rule set; ambiguous or unmatched files shall go to `uncategorized_folder` rather than being guessed. |
| FR-7 | Categories shall be extensible: user-defined categories (`classifier.custom_categories`) shall be evaluated with priority over built-ins, and built-ins shall be disableable by name. |
| FR-8 | When `rename_files` is true, files whose current name is meaningless (numeric, code-like, generic, garbled/mojibake, empty) shall be renamed to a title derived from content. Meaningful names — including CJK names — shall never be changed. |
| FR-9 | Renaming shall never pick a venue/header line (IEEE transactions, journal headers, "Microsoft Word – …") as the title. |
| FR-10 | Renamed/moved files shall never overwrite existing files; collisions shall receive ` (2)`, ` (3)` … suffixes. |
| FR-11 | Destination folders shall be flat by default; with `nested: true` and `subfolder_by: "first_letter"` each category folder shall contain letter subfolders (`A/…Z/`, `0-9/`). |
| FR-12 | When `output_folder` differs from `input_folder` the input folder shall be left untouched (files are moved/copied out); when equal, files are reorganized in place. |
| FR-13 | `dry_run` shall compute and persist the full plan (`plan_preview.txt`) without modifying any file. |
| FR-14 | Every executed move shall be recorded in `organize_log.json`; `--undo <log>` shall restore every file to its source path and remove folders emptied by the undo. |
| FR-15 | After an applied run the tool shall write `rename_report.txt` (old → new name), `folder_manifest.txt` (final layout) and `summary.txt` (per-category counts). |
| FR-16 | Moves shall work within one drive (rename) and across drives (copy + delete). |

## 4. Module specification

### 4.1 `organizer/config.py`
Loads defaults → JSON file → CLI overrides (deepest wins), validates
(input exists; `subfolder_by ∈ {none, first_letter}`; `subfolder_by ≠ none` requires
`nested`), resolves `output_folder = input_folder` when unset, and attaches absolute
paths `_input_abs` / `_output_abs`.

### 4.2 `organizer/extract.py` (+ `_extract_worker.py`)
- `find_pdfs(cfg)` — implements FR-1/FR-2.
- `extract_all(paths, cfg)` — implements FR-3/4/5. One ThreadPool dispatches one
  `subprocess` per PDF running `_extract_worker.py`; each writes a JSON result named
  by MD5 of the path. `index.jsonl` maps the current set of paths to cached records.

### 4.3 `organizer/rules.py`
Data only: `DEFAULT_RULES` (ordered `[category, strong-patterns, weak-patterns]`,
~55 categories) and `CASE_SENSITIVE` (exact-case acronyms per category, e.g. `HRTF`,
`FIR`, `ADC`, to prevent substring false hits such as `ILD` inside "build").

### 4.4 `organizer/classify.py`
- `build_rule_set(cfg)` — custom categories first with `bonus = 2.0` (FR-7);
  built-ins minus disabled.
- `zones(rec)` — builds the lowercased title zone (filename + meta + first 400 chars
  of text with venue boilerplate stripped), the body zone, and an original-case zone.
- `score(rec, cat, strongs, weaks)` — case-insensitive evidence matching:
  strong in filename **4.5** / title zone **3.0** / body **1.0**; weak
  **2.7 / 1.2 / 0.35**; case-sensitive acronym in case zone **4.5** / body **1.0**.
- `classify(rec, rule_set, cfg)` — accepts the best category when
  `score ≥ min_score` **and** `score − runner-up ≥ min_margin`; otherwise returns
  `None` (→ uncategorized).

### 4.5 `organizer/rename.py`
- `name_kind(filename)` — classifies the current name as `ok` or the reason it is
  not (`numeric`, `code`, `generic`, `tiny`, `mojibake`, `no_real_words`).
  ≥3 CJK characters ⇒ `ok`.
- Title candidates, in priority order: clean metadata title → headline lines of page 1
  (skipping venue/boilerplate lines via `LINE_SKIP`) → flat-text title (ALL-CAPS runs,
  arXiv/ResearchGate patterns, first sentence) → GBK mojibake decoding of the old
  name. Candidates matching `VENUE_TELL` are rejected (FR-9).
- `sanitize` removes control characters, Windows-forbidden characters `<>:"/\|?*`,
  collapses whitespace, truncates to 80 chars on a word boundary.
- `new_name_for(rec)` returns the longest surviving candidate or `None` (keep name).

### 4.6 `organizer/executor.py`
- `build_plan` — one op per record: category (FR-6) + new name (FR-8).
- `target_paths` — resolves `output/<cat>[/<letter>]/<name>` with collision suffixes (FR-10/11).
- `apply_plan` — no-op per file when src == dst; creates target dirs; refuses to
  overwrite; `shutil.move` (FR-12/16). Dry-run records but does not touch disk (FR-13).
- `write_log` / `undo` — the full move journal and its exact reverse (FR-14).

### 4.7 `organizer/report.py` — implements FR-15.
### 4.8 `pdf_organizer.py` — CLI: argument parsing, orchestration, plan preview,
progress output. `--undo` bypasses the pipeline entirely.

## 5. Configuration reference

See `config.example.json` and the README option table for the complete, documented
schema (input/output folders, recursive, ignore, rename_files, dry_run, nested,
subfolder_by, uncategorized_folder, work_folder, workers, extract_timeout_sec,
max_pages, log_file, reports.{enabled, rename_report, manifest, summary},
classifier.{min_score, min_margin, custom_categories, disable_categories}).
Unknown keys are ignored; CLI flags override JSON values.

## 6. Data formats

**Cache record** (JSON, per PDF and mirrored in `index.jsonl`):
`{file, pages, size, err, meta, text}`.

**`organize_log.json`**: array of `{"src": <abs path>, "dst": <abs path>}` in
execution order; undo processes it in reverse.

**Reports**: plain UTF-8 text; `rename_report.txt` groups `old -> new` per category;
`folder_manifest.txt` lists every final path per category; `summary.txt` has the
per-category count table.

## 7. Error handling

| Condition | Behaviour |
|---|---|
| Corrupt / non-PDF file | Extraction error recorded; file still classified (filename evidence only) and moved, never renamed from content |
| Password-protected PDF | Empty-password auth attempted; on failure treated like corrupt |
| Extraction exceeds timeout | Worker killed; recorded as timeout; treated like corrupt |
| Destination file already exists | ` (n)` suffix applied; apply aborts that file with an error entry (never overwrites) |
| Destination exists unexpectedly at apply time | File skipped, reported in errors |
| File locked by another process (Windows) | Move fails with OSError, listed in errors, run continues |
| Bad config (missing input, invalid option) | `SystemExit` with a clear message before any file is touched |

## 8. Non-functional requirements

- **Safety** — no deletion; dry-run; undo log; refuse-overwrite semantics.
- **Robustness** — per-file process isolation; one bad PDF cannot stall or crash a run.
- **Performance** — parallel extraction (`workers`, default 8); on-disk cache makes
  re-runs near-instant; ~10,500 PDFs extract in under a minute on a desktop PC.
- **Portability** — Python 3.9+, PyMuPDF; Windows/Linux/macOS; cross-drive output supported.
- **Determinism** — same inputs + config ⇒ same plan (sorted paths, stable suffixing).

## 9. Test coverage

`tests/test_organizer.py` (run: `python tests/test_organizer.py`, exit 0 = pass)
creates its own fixture PDFs (IEEE-style paper, noise-reduction paper, Danish bill,
C++ book, CJK-titled book, topic-less document, corrupt file, ignored subfolder)
and verifies:

| Test | Requirements exercised |
|---|---|
| `test_config_validation` | config defaults (output = input), rejection of missing input / bad `subfolder_by` |
| `test_name_kind` | FR-8 name-meaningfulness detection incl. CJK |
| `test_extraction_and_cache` | FR-1..5 (count, text, corrupt flag, cache reuse) |
| `test_classification` | FR-6 (5 documents → expected categories; no-topic → uncategorized) |
| `test_rename_from_content` | FR-8/9 (numeric → real title; venue header rejected; meaningful/CJK/corrupt untouched) |
| `test_plan_apply_undo_separate_output` | FR-12/14/15/16 (separate output, moves, reports, full undo) |
| `test_collision_suffix` | FR-10 |
| `test_dry_run_moves_nothing` | FR-13 |
| `test_nested_first_letter` | FR-11 |
| `test_ignore_and_recursive` | FR-1/2 |
| `test_custom_category_priority` | FR-7 (custom wins, disabled falls back) |

## 10. Known limitations & future work

- Keyword-evidence classification only (no ML model): documents whose first pages
  lack recognizable keywords land in `uncategorized`; tuning via custom categories,
  `min_score`/`min_margin`, or editing `rules.py`.
- Scanned/image-only PDFs yield no text (no OCR); they classify on filename only.
- Titles are taken from page 1; heavily formatted covers may defeat line extraction.
- The rename step does not transliterate scripts (CJK titles are preserved as-is).
- Future: optional OCR stage; embedding-based classification; duplicate detection;
  per-category custom rename templates.
