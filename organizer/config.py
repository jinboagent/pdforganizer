"""Configuration loading, validation and defaults."""
import json
import os

DEFAULTS = {
    "input_folder": ".",
    "output_folder": None,          # None = same as input_folder
    "recursive": False,
    "ignore": [],
    "rename_files": True,
    "dry_run": False,
    "nested": False,
    "subfolder_by": "none",         # none | first_letter
    "uncategorized_folder": "uncategorized",
    "work_folder": ".pdf_organizer_cache",
    "workers": 8,
    "extract_timeout_sec": 45,
    "max_pages": 3,
    "reports": {
        "enabled": True,
        "rename_report": "rename_report.txt",
        "manifest": "folder_manifest.txt",
        "summary": "summary.txt",
    },
    "classifier": {
        "min_score": 2.0,
        "min_margin": 0.5,
        "custom_categories": [],
        "disable_categories": [],
    },
    "log_file": "organize_log.json",
}


def load_config(path=None, overrides=None):
    """Load config from JSON file, apply CLI overrides, validate, fill defaults."""
    cfg = json.loads(json.dumps(DEFAULTS))  # deep copy
    if path:
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        _deep_update(cfg, user)
    if overrides:
        _deep_update(cfg, overrides)

    if not os.path.isdir(cfg["input_folder"]):
        raise SystemExit(f"input_folder does not exist: {cfg['input_folder']}")
    if cfg["output_folder"] is None:
        cfg["output_folder"] = cfg["input_folder"]
    if not os.path.isdir(cfg["output_folder"]):
        os.makedirs(cfg["output_folder"], exist_ok=True)
    if cfg["subfolder_by"] not in ("none", "first_letter"):
        raise SystemExit("subfolder_by must be 'none' or 'first_letter'")
    if cfg["subfolder_by"] != "none" and not cfg["nested"]:
        raise SystemExit("subfolder_by requires nested: true")
    cfg["_input_abs"] = os.path.abspath(cfg["input_folder"])
    cfg["_output_abs"] = os.path.abspath(cfg["output_folder"])
    return cfg


def _deep_update(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
