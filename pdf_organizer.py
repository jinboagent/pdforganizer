#!/usr/bin/env python3
"""pdf_organizer - extract, classify, rename and group PDF files by content.

Usage:
  python pdf_organizer.py --config myconfig.json
  python pdf_organizer.py --input E:\\pdfs                          # same folder in/out
  python pdf_organizer.py --input E:\\pdfs --output E:\\sorted --no-rename
  python pdf_organizer.py --input E:\\pdfs --dry-run               # plan only
  python pdf_organizer.py --undo                                   # auto-find the log
  python pdf_organizer.py --undo E:\\pdfs\\organize_log.json       # explicit log
  python pdf_organizer.py --list-categories                        # show categories
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from organizer import __version__
from organizer.config import load_config, DEFAULTS
from organizer.extract import find_pdfs, extract_all
from organizer.classify import build_rule_set
from organizer.executor import build_plan, target_paths, apply_plan, write_log, undo, resolve_undo
from organizer.report import write_reports


def _minimal_cfg(config_path, classifier_only=True):
    """Load config without requiring a valid input folder (for undo/list)."""
    over = {"input_folder": "."}
    try:
        return load_config(config_path, over)
    except SystemExit:
        cfg = json.loads(json.dumps(DEFAULTS))
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                user = json.load(f)
            for k in ("log_file", "classifier"):
                if k in user:
                    cfg[k] = user[k]
        return cfg


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
    ap.add_argument("--verbose", action="store_true", help="print per-category results and example renames")
    ap.add_argument("--list-categories", action="store_true",
                    help="print all active categories and exit")
    ap.add_argument("--version", action="version", version=f"pdf_organizer {__version__}")
    ap.add_argument("--undo", nargs="?", const="auto", default=None, metavar="LOG",
                    help="undo a previous run; without a path the log is auto-discovered")
    args = ap.parse_args()

    if args.list_categories:
        from organizer.schemes import standard_codes, lcc_label
        cfg = _minimal_cfg(args.config)
        rs = build_rule_set(cfg)
        custom = {c["name"] for c in cfg.get("classifier", {}).get("custom_categories", [])}
        print(f"{len(rs)} active categories (custom first, then built-ins).")
        print("LCC = Library of Congress top class; arXiv = arXiv subject area.\n")
        width = max(len(c) for c, *_ in rs) + 2
        print(f"{'CATEGORY':<{width}}{'LCC':<21}arXiv")
        print("-" * (width + 31))
        for c, *_ in rs:
            tag = "  (custom)" if c in custom else ""
            lcc = lcc_label(c) or "-"
            print(f"{c + tag:<{width}}{lcc:<21}{standard_codes(c)[1] or '-'}")
        return

    if args.undo:
        cfg = None
        try:
            over = {}
            if args.input_folder:
                over["input_folder"] = args.input_folder
            if args.output_folder:
                over["output_folder"] = args.output_folder
            cfg = load_config(args.config, over or None)
        except SystemExit:
            cfg = _minimal_cfg(args.config)
        logp = resolve_undo(args.undo, cfg)
        undone, skipped = undo(logp)
        print(f"Undone: {undone} files restored, {skipped} skipped  (log: {logp})")
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

    if args.verbose:
        vc = collections.Counter(op["cat"] for op in applied if
                                 os.path.normpath(op["src"]) != os.path.normpath(op["dst"]))
        if vc:
            print("\nMoved per category:")
            for cat, n in vc.most_common():
                print(f"  {cat:<32}{n:>6}")
        examples = [op for op in applied
                    if op["old_name"].lower() != os.path.basename(op["dst"]).lower()][:8]
        if examples:
            print("\nExample renames:")
            for op in examples:
                print(f"  {op['old_name'][:48]:<50} -> {os.path.basename(op['dst'])[:60]}")

    logp = write_log(log, cfg)
    if logp:
        print(f"\nUndo log: {logp}\nRevert with:  python pdf_organizer.py --undo \"{logp}\"")

    # 4. reports
    write_reports(ops, cfg)
    if cfg.get("reports", {}).get("enabled", True):
        print("Reports written: rename_report.txt, folder_manifest.txt, summary.txt")
    print("Done.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
