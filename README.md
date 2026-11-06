# pdf_organizer

**Languages**: [English](README.md) · [中文](README.zh-CN.md) · [Español](README.es.md)

Organize a folder of PDF files **by their content**: the tool extracts text from the
first pages of every PDF, classifies each document into a topic category, optionally
renames files whose names are meaningless (numbers, codes, garbled text) to their
actual headline/title, and moves everything into category subfolders.

It was developed and battle-tested on a 10,500-PDF mixed corpus (research papers,
technical books, manuals, bills, exam papers, fiction, in English/Chinese/Danish).

## What it does

1. **Extract** — for every PDF it pulls the metadata title and the text of the first
   pages (default 3). Each file is extracted in its own subprocess with a hard
   timeout, so one broken or encrypted PDF cannot stall the run. Results are cached,
   so re-runs are fast.
2. **Classify** — a keyword-scoring engine scores every file against ~55 topic
   categories. Evidence in the filename and title-zone counts more than evidence in
   the body text; case-sensitive acronyms (HRTF, FIR, ADC …) are matched exactly.
   Files that match nothing (or match several categories equally) go to an
   `uncategorized` folder instead of being guessed.
3. **Rename** (optional) — filenames that are pure numbers/codes/garble are replaced
   by the document's real title, taken from metadata or extracted from the first-page
   layout (headline lines, ALL-CAPS title runs, arXiv/ResearchGate title patterns).
   Filenames that are already meaningful are never touched. Chinese filenames are
   recognized as meaningful and kept.
4. **Group** — files are moved into one folder per category. By default the structure
   is **flat** (no subfolders inside category folders).
5. **Report** — three reports are written into the output folder:
   `rename_report.txt` (old → new name), `folder_manifest.txt` (final layout),
   `summary.txt` (per-category counts).

Nothing is ever deleted. Every move is written to `organize_log.json`, and a run can
be fully reverted with `--undo`.

## Requirements

- Python 3.9+
- [PyMuPDF](https://pymupdf.readthedocs.io/)

```bash
pip install -r requirements.txt
```

Documentation: **[USAGE.md](USAGE.md)** is the practical step-by-step guide;
[README.md](README.md) (this file) is the option reference;
[SPECIFICATION.md](SPECIFICATION.md) has the formal details.

Tests: `python tests/test_organizer.py` (self-contained, generates its own fixtures).

## Quick start

```bash
# organize a folder in place (input = output), with renaming
python pdf_organizer.py --input "E:\my_pdfs"

# see what WOULD happen first — nothing is moved
python pdf_organizer.py --input "E:\my_pdfs" --dry-run

# only group into folders, do not rename any file
python pdf_organizer.py --input "E:\my_pdfs" --no-rename

# revert the last run — the log is found automatically
python pdf_organizer.py --undo

# see every active category
python pdf_organizer.py --list-categories
```

Extra CLI flags: `--verbose` (per-category move counts + example renames),
`--version`. The process exits with code 1 if any file failed to move.

With a config file (recommended for the full set of options):

```bash
cp config.example.json myconfig.json   # edit it, then:
python pdf_organizer.py --config myconfig.json
```

## Configuration options

| Option (JSON) | CLI flag | Default | Meaning |
|---|---|---|---|
| `input_folder` | `--input` | `.` | Folder containing the PDFs to organize. |
| `output_folder` | `--output` | same as input | Where category subfolders are created. **By default input and output are the same folder**, i.e. files are reorganized in place. Set a different folder to keep the input untouched. |
| `recursive` | `--recursive` | `false` | Also scan subfolders of the input folder. The output folder and the extraction cache are **never** descended into, even when they live inside the input folder. |
| `ignore` | `--ignore a b …` | `[]` | Glob patterns for folders/files to skip, e.g. `["private", "*_backup", "invoices"]`. Matches any path part or relative path. |
| `rename_files` | `--no-rename` to disable | `true` | Rename meaningless filenames to the document's title. `false` = keep all current names, only group into folders. |
| `dry_run` | `--dry-run` | `false` | Compute and print the full plan (also saved to `.pdf_organizer_cache/plan_preview.txt`) without moving anything. |
| `nested` | `--nested` | `false` | Allow subfolders **inside** category folders (see `subfolder_by`). |
| `subfolder_by` | — | `"none"` | `"none"` = flat category folders. `"first_letter"` (needs `nested: true`) = split each category into `A/ … Z/` subfolders. |
| `uncategorized_folder` | — | `uncategorized` | Folder name for files that could not be classified. |
| `work_folder` | — | `.pdf_organizer_cache` | Cache directory for extraction results (enables fast re-runs). |
| `workers` | `--workers N` | `8` | Parallel extraction subprocesses. |
| `extract_timeout_sec` | — | `45` | Hard timeout per PDF during extraction. |
| `max_pages` | — | `3` | Pages of text extracted per PDF. |
| `log_file` | — | `organize_log.json` | Undo log written to the output folder (set `null` to disable). |
| `reports.enabled` | — | `true` | Write the three report files. |
| `reports.rename_report` / `reports.manifest` / `reports.summary` | — | `rename_report.txt` / `folder_manifest.txt` / `summary.txt` | Report filenames (relative to output folder). |
| `classifier.min_score` | — | `2.0` | Minimum evidence score to accept a category. |
| `classifier.min_margin` | — | `0.5` | Required gap between the best and second-best category; smaller = more decisive, larger = more files left uncategorized. |
| `classifier.custom_categories` | — | `[]` | Your own categories, checked **before** the built-ins. Example below. |
| `classifier.disable_categories` | — | `[]` | Built-in category names to switch off (their files fall through to other categories or `uncategorized`). |

## Examples

### 1. Reorganize in place (what this tool was built for)

```json
{
  "input_folder": "E:\\pdf_regroup",
  "output_folder": "E:\\pdf_regroup",
  "rename_files": true
}
```

Input and output are the same folder: the flat pile of PDFs becomes a set of topic
folders, badly-named files get their real titles.

### 2. Separate output folder, keep names, ignore some folders

```json
{
  "input_folder": "C:\\Users\\me\\Downloads",
  "output_folder": "D:\\library",
  "rename_files": false,
  "recursive": true,
  "ignore": ["*.tmp", "family_photos", "invoices_*"]
}
```

Reads PDFs from Downloads *and its subfolders*, skips anything matching the ignore
patterns, sorts copies into `D:\library\<category>\` without renaming, and leaves the
Downloads folder untouched.

### 3. Big collections: nested subfolders by first letter

```json
{
  "input_folder": "E:\\papers",
  "nested": true,
  "subfolder_by": "first_letter"
}
```

Produces `E:\papers\noise_reduction\A\`, `…\B\`, … so no single folder contains
thousands of files.

### 4. Custom categories

```json
{
  "input_folder": "E:\\work_docs",
  "classifier": {
    "custom_categories": [
      { "name": "company_reports",
        "keywords": ["acme corp", "quarterly report", "ACME-202"],
        "weak_keywords": ["acme"] }
    ]
  }
}
```

Files mentioning "acme corp" etc. land in a `company_reports` folder before the
built-in categories are even considered.

### 5. Dry-run first (recommended)

```bash
python pdf_organizer.py --input "E:\my_pdfs" --dry-run
# inspect .pdf_organizer_cache/plan_preview.txt, then:
python pdf_organizer.py --input "E:\my_pdfs"
```

### 6. Undo a run

```bash
python pdf_organizer.py --undo              # finds organize_log.json automatically
# or explicitly:
python pdf_organizer.py --undo "E:\my_pdfs\organize_log.json"
```

Restores every file to its original path and removes folders the run created.

## Built-in categories

Documents/admin: `travel_bookings`, `certificates_ids`, `insurance_pension`,
`bank_tax`, `bills_utilities`, `contracts_agreements`, `misc_admin`.

Audio & speech: `noise_reduction`, `echo_cancellation`, `adaptive_filtering`,
`beamforming`, `spatial_audio`, `room_acoustics`, `loudspeakers`,
`microphones_transducers`, `hearing_aids_audiology`, `audio_coding`, `music_audio`,
`audio_measurement`, `audio_production_broadcast`, `audio_converters_interfaces`,
`audio_effects_reverb`, `audio_equalization`, `audio_general`,
`speech_recognition`, `speech_synthesis`, `speech_analysis`.

Math/DSP: `machine_learning`, `statistics_probability`, `optimization`,
`mathematics_reference`, `dsp_general`, `filter_design`, `estimation_tracking`.

Computing: `programming_python`, `programming_cpp`, `programming_java`,
`programming_other`, `software_engineering`, `operating_systems`, `networking`,
`databases`, `web_dev`, `embedded`, `rf_microwave`, `circuits`, `video_image`.

Other: `career_interview`, `danish_education`, `writing_media`, `fiction`,
`self_help`, `finance_accounting`, `product_manuals`, `misc_reading`.

Rename or remove any of these via `classifier.custom_categories` /
`classifier.disable_categories` — or edit `organizer/rules.py` directly.

## Notes & limitations

- Classification is keyword-evidence based: it is fast and fully offline, but a
  document whose first pages contain no recognizable topic keywords will end up in
  `uncategorized` (tune `min_score` / `min_margin`, or add a custom category).
- Scanned/image-only PDFs have no extractable text; they are grouped by filename
  evidence only.
- Corrupt or password-protected PDFs are still moved (to `uncategorized`) but cannot
  be renamed from content.
- Moves within one drive are instant; across drives files are copied then removed.
- The extraction cache (`.pdf_organizer_cache/`) can be deleted safely; it will be
  rebuilt on the next run.

## Layout

```
pdf_organizer/
├── pdf_organizer.py        # CLI entry point
├── config.example.json     # documented default config
├── requirements.txt
├── USAGE.md                # practical step-by-step usage guide
├── USAGE.zh-CN.md          # usage guide (Chinese)
├── USAGE.es.md             # usage guide (Spanish)
├── README.zh-CN.md         # this reference (Chinese)
├── README.es.md            # this reference (Spanish)
├── SPECIFICATION.md        # software specification (requirements, algorithms, formats)
├── tests/
│   └── test_organizer.py   # self-contained test program
└── organizer/
    ├── config.py           # config loading/validation
    ├── rules.py            # built-in category scheme
    ├── extract.py          # parallel, timeout-protected extraction driver
    ├── _extract_worker.py  # per-PDF extraction subprocess
    ├── classify.py         # scoring classifier
    ├── rename.py           # meaningless-name detection + title extraction
    ├── executor.py         # plan/apply/undo
    └── report.py           # the three report files
```
