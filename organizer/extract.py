"""Extraction driver: runs the worker per PDF with a hard timeout, in parallel."""
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_extract_worker.py")


def find_pdfs(cfg):
    """All PDFs under input_folder (optionally recursive), minus ignored entries."""
    root = cfg["_input_abs"]
    ignore = cfg.get("ignore", [])
    pdfs = []
    if cfg.get("recursive"):
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root)
            # filter ignored directories in-place
            dirnames[:] = [d for d in dirnames if not _ignored(os.path.join(rel_dir, d) if rel_dir != '.' else d, ignore)]
            for fn in filenames:
                if fn.lower().endswith(".pdf"):
                    rel = os.path.join(rel_dir, fn) if rel_dir != "." else fn
                    if not _ignored(rel, ignore):
                        pdfs.append(os.path.join(dirpath, fn))
    else:
        for fn in os.listdir(root):
            p = os.path.join(root, fn)
            if os.path.isfile(p) and fn.lower().endswith(".pdf") and not _ignored(fn, ignore):
                pdfs.append(p)
    return sorted(pdfs)


def _ignored(rel_path, patterns):
    rel = rel_path.replace("\\", "/")
    parts = rel.split("/")
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat + "/*") or any(fnmatch.fnmatch(part, pat) for part in parts):
            return True
    return False


def extract_all(paths, cfg):
    """Extract text/meta for each PDF; returns {abs_path: record}. Resumable via cache."""
    cache_dir = cfg["work_folder"]
    os.makedirs(cache_dir, exist_ok=True)
    index_path = os.path.join(cache_dir, "index.jsonl")
    done = {}
    if os.path.exists(index_path):
        for line in open(index_path, "r", encoding="utf-8"):
            try:
                d = json.loads(line)
                done[d["file"]] = d
            except Exception:
                pass
    todo = [p for p in paths if p not in done]
    print(f"PDFs found: {len(paths)}  (cached: {len(paths) - len(todo)}, to extract: {len(todo)})")
    if todo:
        timeout = cfg["extract_timeout_sec"]
        workers = cfg["workers"]

        def run(path):
            h = hashlib.md5(path.encode("utf-8")).hexdigest()
            out = os.path.join(cache_dir, f"{h}.json")
            if os.path.exists(out) and os.path.getsize(out) > 2:
                return path, "cached"
            try:
                subprocess.run([sys.executable, WORKER, path, out, str(cfg["max_pages"])],
                               timeout=timeout, capture_output=True)
                return path, "ok" if os.path.exists(out) else "no_output"
            except subprocess.TimeoutExpired:
                return path, "timeout"
            except Exception as e:
                return path, f"err:{type(e).__name__}"

        n_ok = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(run, p): p for p in todo}
            for i, fut in enumerate(as_completed(futs)):
                _, st = fut.result()
                n_ok += st in ("ok", "cached")
                if (i + 1) % 200 == 0:
                    print(f"  extracted {i + 1}/{len(todo)}")
        # read fresh records
        for p in todo:
            h = hashlib.md5(p.encode("utf-8")).hexdigest()
            out = os.path.join(cache_dir, f"{h}.json")
            if os.path.exists(out):
                try:
                    done[p] = json.load(open(out, encoding="utf-8"))
                except Exception:
                    done[p] = {"file": p, "pages": 0, "err": "bad_cache", "meta": "", "text": ""}
        with open(index_path, "w", encoding="utf-8") as f:
            for p in paths:
                if p in done:
                    f.write(json.dumps(done[p], ensure_ascii=False) + "\n")
    return done
