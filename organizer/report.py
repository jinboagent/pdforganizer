"""Human-readable reports: rename report, folder manifest, summary."""
import collections
import os
from datetime import date


def write_reports(ops, cfg):
    rcfg = cfg.get("reports", {})
    if not rcfg.get("enabled", True) or cfg.get("dry_run"):
        return
    out = cfg["_output_abs"]
    today = date.today().isoformat()
    total = len(ops)
    renames = [op for op in ops if op["old_name"].lower() != os.path.basename(op["dst"]).lower()]

    # rename report
    p = os.path.join(out, rcfg.get("rename_report", "rename_report.txt"))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("PDF RENAME REPORT - old name -> new name\n")
        fh.write(f"Generated: {today} | Folder: {out}\n")
        fh.write(f"Files renamed: {len(renames)} of {total}\n")
        fh.write("=" * 110 + "\n")
        by_cat = collections.defaultdict(list)
        for op in renames:
            by_cat[op["cat"]].append((op["old_name"], os.path.basename(op["dst"])))
        for cat in sorted(by_cat):
            fh.write(f"\n### {cat}/  ({len(by_cat[cat])} renames)\n\n")
            fh.write(f'{"OLD NAME":<56} ->  NEW NAME\n')
            fh.write("-" * 130 + "\n")
            for o, n in sorted(by_cat[cat], key=lambda x: x[0].lower()):
                fh.write(f"{o:<56} ->  {n}\n")

    # manifest
    p = os.path.join(out, rcfg.get("manifest", "folder_manifest.txt"))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("FOLDER MANIFEST - final location of every PDF\n")
        fh.write(f"Generated: {today} | Output folder: {out}\n")
        fh.write("=" * 110 + "\n")
        by_cat = collections.defaultdict(list)
        for op in ops:
            by_cat[op["cat"]].append(op["dst"])
        for cat in sorted(by_cat):
            fh.write(f"\n### {cat}/  ({len(by_cat[cat])} files)\n")
            for d in sorted(by_cat[cat], key=str.lower):
                fh.write(f"  {os.path.relpath(d, os.path.join(out, cat))}\n")

    # summary
    p = os.path.join(out, rcfg.get("summary", "summary.txt"))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("PDF ORGANIZATION SUMMARY\n")
        fh.write(f"Folder: {out} | Total PDFs: {total} | Date: {today}\n\n")
        fh.write("PDFs were classified by content (text + metadata extracted from the first\n")
        fh.write("pages; see README). Files with meaningless names were renamed from their\n")
        fh.write("content. Files are grouped into category folders.\n\n")
        fh.write("See rename_report.txt and folder_manifest.txt for details.\n\n")
        fh.write("CATEGORY                            FILES\n")
        fh.write("-" * 44 + "\n")
        cnt = collections.Counter(op["cat"] for op in ops)
        for cat, n in cnt.most_common():
            fh.write(f"{cat:<36}{n:>6}\n")
        fh.write(f'{"TOTAL":<36}{sum(cnt.values()):>6}\n')
