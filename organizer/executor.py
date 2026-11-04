"""Executor: build the move/rename plan, apply it (or dry-run), write the undo log."""
import json
import os
import shutil


def build_plan(records, cfg, rule_set, classify_fn, rename_fn):
    """records: {abs_path: rec}. Returns list of ops dicts."""
    from .classify import classify
    from .rename import new_name_for

    ops = []
    for path in sorted(records):
        rec = records[path]
        cat, sc, top = classify(rec, rule_set, cfg)
        if cat is None:
            cat = cfg["uncategorized_folder"]
        new_name = os.path.basename(path)
        if cfg.get("rename_files"):
            cand = new_name_for(rec)
            if cand:
                new_name = cand
        ops.append({"src": path, "cat": cat, "name": new_name,
                    "old_name": os.path.basename(path), "score": round(sc, 2), "top": top,
                    "err": rec.get("err")})
    return ops


def target_paths(ops, cfg):
    """Resolve final destination per op, handling nesting and collisions."""
    used = {}
    out_root = cfg["_output_abs"]
    nested = cfg.get("nested")
    sub_by = cfg.get("subfolder_by", "none")
    for op in ops:
        cat = op["cat"]
        sub = ""
        if nested and sub_by == "first_letter":
            c = op["name"][0].upper()
            sub = c if c.isalpha() else "0-9"
        dstdir = os.path.join(out_root, cat, sub) if (nested and sub) else os.path.join(out_root, cat)
        name = op["name"]
        stem, ext = os.path.splitext(name)
        key = dstdir.lower()
        i = 2
        while (key, name.lower()) in used:
            name = f"{stem} ({i}){ext}"
            i += 1
        used[(key, name.lower())] = True
        op["dst"] = os.path.join(dstdir, name)
    return ops


def apply_plan(ops, cfg):
    """Move files. Returns (applied, errors, log_entries)."""
    applied, errors, log = [], [], []
    dry = cfg.get("dry_run")
    for op in ops:
        src, dst = op["src"], op["dst"]
        if os.path.normpath(src) == os.path.normpath(dst):
            continue
        if dry:
            applied.append(op)
            log.append({"src": src, "dst": dst})
            continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                raise OSError(f"destination exists: {dst}")
            shutil.move(src, dst)
            applied.append(op)
            log.append({"src": src, "dst": dst})
        except OSError as e:
            errors.append(f"{src} -> {dst}: {e}")
    return applied, errors, log


def write_log(log, cfg):
    if not cfg.get("dry_run") and cfg.get("log_file"):
        p = os.path.join(cfg["_output_abs"], cfg["log_file"])
        with open(p, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=1)
        return p
    return None


def resolve_undo(spec, cfg=None):
    """Return the path to an undo log.

    spec may be an explicit path, or 'auto'/None to search the output folder,
    the input folder and the current working directory for the log file.
    """
    if spec and spec != "auto":
        if os.path.exists(spec):
            return spec
        raise SystemExit(f"undo log not found: {spec}")
    candidates = []
    if cfg:
        names = [cfg.get("log_file") or "organize_log.json"]
        for d in (cfg.get("_output_abs"), cfg.get("_input_abs")):
            if d:
                candidates += [os.path.join(d, n) for n in names]
    candidates.append(os.path.join(os.getcwd(), "organize_log.json"))
    for c in candidates:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "No organize_log.json found next to the input/output folder or in the\n"
        "current directory. Pass the path explicitly:\n"
        '  python pdf_organizer.py --undo "path/to/organize_log.json"')


def undo(log_path):
    """Reverse a previous run using its organize_log.json."""
    log = json.load(open(log_path, "r", encoding="utf-8"))
    undone, skipped = 0, 0
    for entry in reversed(log):
        src, dst = entry["src"], entry["dst"]
        if not os.path.exists(dst):
            skipped += 1
            continue
        os.makedirs(os.path.dirname(src) or ".", exist_ok=True)
        if os.path.exists(src):
            skipped += 1
            continue
        shutil.move(dst, src)
        undone += 1
    # remove folders left empty
    folders = {os.path.dirname(e["dst"]) for e in log}
    for d in sorted(folders, key=len, reverse=True):
        try:
            if d and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
        except OSError:
            pass
    return undone, skipped
