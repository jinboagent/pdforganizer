#!/usr/bin/env python3
"""pdf_organizer - extract, classify, rename and group PDF files by content.

Usage:
  python pdf_organizer.py --config myconfig.json
  python pdf_organizer.py --input E:\\pdfs                          # same folder in/out
  python pdf_organizer.py --input E:\\pdfs --output E:\\sorted --no-rename
  python pdf_organizer.py --input E:\\pdfs --dry-run               # plan only
  python pdf_organizer.py --undo E:\\pdfs\\organize_log.json       # revert a run
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from organizer.config import load_config
from organizer.extract import find_pdfs, extract_all
from organizer.classify import build_rule_set
from organizer.executor import build_plan, target_paths, apply_plan, write_log, undo
from organizer.report import write_reports


def main():
    ap = argparse.ArgumentParser(description="Organize PDF files by content.")
    ap.add_argument("--config", help="JSON config file (see config.example.json)")
    ap.add_argument("--input", dest="input_folder", help="input folder (default: config or '.')")
    ap.add_argument("--output", dest="output_folder", help="output folder (default: same as input)")
    ap.add_argument("--dry-run", action="store_true", help="show the plan without moving anything")
    ap.add_argument("--no-rename", action="store_true", help="keep current filenames, only group")
    ap.add_argument("--recursive", action="store_true", help="scan subfolders of the input folder")
    ap.add_argument("--nested", action="store_true", help="allow subfolders inside category folders")
    ap.add_argument("--ignore", nargs="*", default=None,
                    help="glob patterns of folders/files to skip (e.g. 'private' '*_backup')")
    ap.add_argument("--workers", type=int, default=None, help="parallel extraction workers")
    ap.add_argument("--undo", metavar="LOG", help="undo a previous run using its organize_log.json")
    args = ap.parse_args()

    if args.undo:
        undone, skipped = undo(args.undo)
        print(f"Undone: {undone} files restored, {skipped} skipped")
        return

    overrides = {}
    if args.input_folder:
        overrides["input_folder"] = args.input_folder
    if args.output_folder:
        overrides["output_folder"] = args.output_folder
    if args.dry_run:
        overrides["dry_run"] = True
    if args.no_rename:
        overrides["rename_files"] = False
    if args.recursive:
        overrides["recursive"] = True
    if args.nested:
        overrides["nested"] = True
    if args.ignore is not None:
        overrides["ignore"] = args.ignore
    if args.workers:
        overrides["workers"] = args.workers

    cfg = load_config(args.config, overrides or None)

    print(f"Input : {cfg['_input_abs']}")
    print(f"Output: {cfg['_output_abs']}{'  (dry-run)' if cfg['dry_run'] else ''}")

    # 1. find + extract
    pdfs = find_pdfs(cfg)
    if not pdfs:
        print("No PDF files found (check input_folder / ignore / recursive).")
        return
    records = extract_all(pdfs, cfg)

    # 2. classify + rename plan
    rule_set = build_rule_set(cfg)
    ops = build_plan(records, cfg, rule_set, None, None)
    ops = target_paths(ops, cfg)

    # 3. preview / apply
    cnt = collections.Counter(op["cat"] for op in ops)
    print(f"\nPlan for {len(ops)} PDFs across {len(cnt)} categories:")
    for cat, n in cnt.most_common():
        print(f"  {cat:<32}{n:>6}")
    ren = sum(1 for op in ops if op["old_name"].lower() != os.path.basename(op["dst"]).lower())
    print(f"\nRenames: {ren}" if cfg["rename_files"] else "\nRenames: disabled (--no-rename)")

    if cfg["dry_run"]:
        preview = os.path.join(cfg["work_folder"], "plan_preview.txt")
        os.makedirs(cfg["work_folder"], exist_ok=True)
        with open(preview, "w", encoding="utf-8") as fh:
            for op in sorted(ops, key=lambda o: (o["cat"], o["dst"].lower())):
                fh.write(f"{op['src']}  ->  {op['dst']}\n")
        print(f"Dry-run: nothing was moved. Full plan written to {preview}")
        return

    applied, errors, log = apply_plan(ops, cfg)
    print(f"\nMoved: {len(applied)}  Errors: {len(errors)}")
    for e in errors[:10]:
        print("  !", e)

    logp = write_log(log, cfg)
    if logp:
        print(f"Undo log: {logp}  (revert with --undo \"{logp}\")")

    # 4. reports
    write_reports(ops, cfg)
    if cfg.get("reports", {}).get("enabled", True):
        print("Reports written: rename_report.txt, folder_manifest.txt, summary.txt")
    print("Done.")


if __name__ == "__main__":
    main()
