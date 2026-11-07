# pdf_organizer — Usage Guide

**Languages**: [English](USAGE.md) · [中文](USAGE.zh-CN.md) · [Español](USAGE.es.md)

A practical, step-by-step companion to the [README](README.md) (reference) and
[SPECIFICATION](SPECIFICATION.md) (formal details). This page is about *how you
actually drive the tool* day to day.

---

## 1. What it does, in one breath

Point it at a folder of PDFs. It reads the first pages of every file, figures out
what each document is about, gives the no-name files (`12345.pdf`, `scan_final.pdf`,
garbled text) their real titles, and sorts everything into topic folders like
`noise_reduction/`, `programming_python/`, `bills_utilities/`. Nothing is deleted,
every move is logged, and the whole run can be undone.

## 2. The 5-minute start

```bash
pip install pymupdf

# step 1 — look before you leap (nothing is moved):
python pdf_organizer.py --input "D:\Messy PDFs" --dry-run

# step 2 — read the plan it printed (also saved to .pdf_organizer_cache/plan_preview.txt)

# step 3 — do it for real:
python pdf_organizer.py --input "D:\Messy PDFs"

# step 4 — regret it? one command puts everything back:
python pdf_organizer.py --undo
```

That's the whole loop. The rest of this guide is about doing it *well*.

## 3. The recommended safety workflow

For a first run on an important folder:

1. **Copy, don't risk.** Either run with a separate output folder
   (`--input IN --output OUT` leaves `IN` untouched), or take a backup. Or trust
   `--undo` — it is exact and tested, but backups are cheaper than regrets.
2. **Dry-run first.** Check the category table. Expect *some* files in
   `uncategorized` — that's the tool being honest, not broken (see §7).
3. **Run for real.** Note the printed `Undo log:` path.
4. **Inspect the results** in `rename_report.txt` (old → new names) and
   `folder_manifest.txt` (where everything went).
5. **Iterate.** Files in the wrong category? Add a custom category or adjust
   thresholds (§6), then run again — the extraction cache makes re-runs fast, and
   only *misplaced* files move the second time.

## 4. Everyday scenarios

### "My PDFs are a huge flat pile — organize them in place"

```bash
python pdf_organizer.py --input "E:\papers" --dry-run
python pdf_organizer.py --input "E:\papers"
```

Input and output are the same folder by default: the pile becomes topic folders,
bad names become real titles.

### "Sort copies into a library folder, keep my originals and their names"

```bash
python pdf_organizer.py --input "C:\Users\me\Downloads" --output "D:\library" --no-rename --recursive
```

### "My Downloads folder has stuff I never want touched"

```bash
python pdf_organizer.py --input "D:\In" --output "D:\Out" --recursive --ignore private receipts_*
```

(Or put the same patterns in `config.json` under `"ignore"`.)

### "I have 20,000 PDFs and folders would get unwieldy"

```bash
python pdf_organizer.py --input "E:\big" --nested
```

Each category folder is split by first letter: `noise_reduction/A/`, `noise_reduction/B/`…

### "My field has topics the tool doesn't know"

```json
{
  "input_folder": "E:\\thesis_chapters",
  "classifier": {
    "custom_categories": [
      { "name": "bicycle_dynamics",
        "keywords": ["bicycle dynamics", "wheel gyroscopic"],
        "weak_keywords": ["bicycle"] }
    ],
    "disable_categories": ["danish_education"]
  }
}
```

```bash
python pdf_organizer.py --config myconfig.json
```

Custom categories win ties against built-ins. See all active ones with:

```bash
python pdf_organizer.py --list-categories
```

### "I keep adding PDFs to the folder"

Just re-run the same command. Extraction is cached, so only the new files are
read, and only *they* move. The tool also never re-shuffles its own results —
recursive scans skip the output folder and cache automatically.

### "I only want the renaming, not the folders" (or vice versa)

- Rename but keep everything in one place: not a job for this tool (it always groups).
- Group without renaming: `--no-rename`.

## 5. Reading the output

| File | What it tells you |
|---|---|
| console | Category plan before the run; moved/error counts after |
| `rename_report.txt` | Every renamed file: old name → new name, grouped by folder |
| `folder_manifest.txt` | The complete final layout — where every single PDF ended up |
| `summary.txt` | Per-category counts, plus each category's Library of Congress (LCC) top class and arXiv subject area — standard human knowledge classification codes |
| `organize_log.json` | Machine-readable move journal (used by `--undo`) |
| `.pdf_organizer_cache/` | Extraction cache + `plan_preview.txt` from dry-runs. Safe to delete. |

## 6. Tuning the classifier

- **Too many files in `uncategorized`?** Lower the evidence bar:
  `"classifier": { "min_score": 1.5, "min_margin": 0.3 }`. Or add custom
  categories for your topics. Or raise `max_pages` (default 3) so more text is read.
- **Files landing in the wrong category?** Raise `min_margin` (e.g. `1.0`) so only
  clear winners are assigned, and check which category is "stealing" them in
  `folder_manifest.txt`; add a more specific custom category — custom categories
  are checked before built-ins.
- **A category you'll never need is grabbing files?** Disable it:
  `"classifier": { "disable_categories": ["fiction"] }`.

## 7. Troubleshooting

| Symptom | Explanation & fix |
|---|---|
| Many files in `uncategorized/` | Scanned/image-only PDFs have no text to read (no OCR); or first pages lack topic keywords. See §6. |
| A file wasn't renamed | Its name was already judged meaningful, or no confident title was found in the text. Rename manually — the tool never touches names it isn't sure about. |
| `broken.pdf` style file landed in `uncategorized/` | Corrupt or password-protected; still moved, can't be read. Fix the file, re-run. |
| "File in use" errors on Windows | A viewer has the file open. Close it and re-run — cached extraction makes retries cheap. |
| Re-ran and nothing happened | Everything was already sorted; the plan is empty. That's success, not failure. |
| Undo says "No organize_log.json found" | Pass the path explicitly: `--undo "D:\Out\organize_log.json"` — the log lives in the **output** folder of the run. |

## 8. Good habits

- One folder, one purpose: don't point `--recursive` at a general-purpose folder
  (like your whole user profile) — you'll organize things you didn't mean to.
- Prefer a config file over long CLI lines; keep one per project
  (`python pdf_organizer.py --config library.json`).
- Re-run after big additions instead of hoarding new files: incremental runs are
  cheap because of the cache.
- Scripted/CI use: the process exits with code 1 if any file failed to move, so
  failures are detectable without parsing output. Use `--verbose` for per-category
  detail in logs.

## 9. Where to go deeper

- [README.md](README.md) — full option reference and the built-in category list
- [SPECIFICATION.md](SPECIFICATION.md) — how the classifier scores, data formats, guarantees
- `organizer/rules.py` — the category patterns themselves, if you want to fork the scheme
- `organizer/schemes.py` — the LCC / arXiv standard-classification codes per category
