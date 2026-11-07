#!/usr/bin/env python3
"""Test program for pdf_organizer.

Creates its own fixture PDFs in a temporary directory and exercises every
stage of the pipeline: extraction, classification, renaming, planning,
moves, collisions, nesting, ignore lists, dry-run, undo and reports.

Run:  python tests/test_organizer.py
Exit code 0 = all tests passed.
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymupdf

from organizer.config import load_config
from organizer.extract import find_pdfs, extract_all
from organizer.classify import build_rule_set, classify
from organizer.rename import new_name_for, name_kind
from organizer.executor import build_plan, target_paths, apply_plan, write_log, undo, resolve_undo
from organizer.report import write_reports

# ---------------------------------------------------------------- framework

TESTS = []
FAILURES = []


def test(fn):
    TESTS.append(fn)
    return fn


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------- fixtures

IEEE_PAPER = (
    "IEEE TRANSACTIONS ON SPEECH AND AUDIO PROCESSING, VOL. 13, NO. 6, NOVEMBER 2005\n\n"
    "ACOUSTIC ECHO CANCELLATION AND DOUBLETALK DETECTION\n"
    "FOR HANDS-FREE TELEPHONY SYSTEMS\n\n"
    "Abstract—This paper presents an acoustic echo canceller with robust\n"
    "doubletalk detection for hands-free telephony systems.\n"
)
NOISE_PAPER = (
    "SINGLE-CHANNEL NOISE REDUCTION AND SPEECH ENHANCEMENT\n"
    "WITH A WIENER FILTER APPROACH\n\n"
    "Abstract—We propose a noise reduction system that estimates the noise\n"
    "PSD and enhances noisy speech with minimum mean-square error estimation.\n"
)
DANISH_BILL = (
    "Norlys Energi A/S\nOver Baekken 6, 9000 Aalborg\n\n"
    "Regning - Forbrugsopgorelse for el og varme\n"
    "Beloeb at betale: 1.234,56 kr.\nForfaldsdato: 01-03-2026\n"
)
CPP_BOOK = (
    "Effective C++ Programming\n"
    "Chapter 1: Accustoming Yourself to C++\n\n"
    "This chapter covers const, references, the STL and template\n"
    "metaprogramming basics for the C++ language.\n"
)
CJK_BOOK = (
    "深入理解C++11：C++ 11新特性解析与应用\n\n"
    "本书详细讲解移动语义、右值引用、lambda表达式等新特性。\n"
)
BLA_BOOK = "A boring text about nothing in particular. " * 20


def make_pdf(path, text, meta_title=None):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 555, 800), text, fontsize=11)
    if meta_title is not None:
        doc.set_metadata({"title": meta_title})
    doc.save(path)
    doc.close()


def build_fixtures(root):
    inp = os.path.join(root, "input")
    os.makedirs(inp)
    make_pdf(os.path.join(inp, "12345.pdf"), IEEE_PAPER)                       # numeric -> rename from title
    make_pdf(os.path.join(inp, "6789.pdf"), NOISE_PAPER)                       # numeric -> rename from title
    make_pdf(os.path.join(inp, "regning April.pdf"), DANISH_BILL)              # meaningful-ish name, bill content
    make_pdf(os.path.join(inp, "effective_cpp_notes.pdf"), CPP_BOOK)           # meaningful name -> keep
    make_pdf(os.path.join(inp, "深入理解C++11.pdf"), CJK_BOOK)                  # CJK name -> keep
    make_pdf(os.path.join(inp, "readme.pdf"), BLA_BOOK)                        # generic name, no topic -> uncategorized
    with open(os.path.join(inp, "broken.pdf"), "wb") as f:                     # corrupt file
        f.write(b"%PDF-1.4 this is not really a pdf\n\x00\x01garbage")
    priv = os.path.join(inp, "private")
    os.makedirs(priv)
    make_pdf(os.path.join(priv, "secret.pdf"), NOISE_PAPER)                    # must be ignored
    return inp


def base_cfg(inp, out=None, **over):
    os.makedirs(out or inp, exist_ok=True)
    c = {"input_folder": inp, "output_folder": out or inp, "work_folder": None}
    c.update(over)
    return load_config(None, c)


# ---------------------------------------------------------------- tests

@test
def test_config_validation():
    with tempfile.TemporaryDirectory() as root:
        try:
            load_config(None, {"input_folder": os.path.join(root, "nope")})
            check(False, "missing input_folder must raise")
        except SystemExit:
            pass
        inp = os.path.join(root, "in")
        os.makedirs(inp)
        try:
            load_config(None, {"input_folder": inp, "subfolder_by": "bogus"})
            check(False, "bad subfolder_by must raise")
        except SystemExit:
            pass
        cfg = load_config(None, {"input_folder": inp})
        check(cfg["output_folder"] == inp, "output defaults to input")


@test
def test_name_kind():
    check(name_kind("12345.pdf") != "ok", "numeric detection")
    check(name_kind("Pre6389.pdf") != "ok", "code detection")
    check(name_kind("readme.pdf") == "generic", "generic detection")
    check(name_kind("深入理解C++11.pdf") == "ok", "CJK names are meaningful")
    check(name_kind("My Paper About Echo.pdf") == "ok", "real title is meaningful")


@test
def test_extraction_and_cache(tmp=None):
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, work_folder=os.path.join(root, "cache"))
        pdfs = find_pdfs(cfg)
        check(len(pdfs) == 7, f"expected 7 pdfs (private ignored), got {len(pdfs)}")
        recs = extract_all(pdfs, cfg)
        iee = recs[os.path.join(inp, "12345.pdf")]
        check(iee["text"] and "ECHO CANCELLATION" in iee["text"].upper(), "text extracted")
        broken = recs[os.path.join(inp, "broken.pdf")]
        check(broken.get("err"), "corrupt pdf flagged with err")
        # second call is served from cache
        recs2 = extract_all(pdfs, cfg)
        check(recs2[os.path.join(inp, "12345.pdf")]["pages"] == 1, "cached record returned")


@test
def test_classification():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        rs = build_rule_set(cfg)
        expect = {
            "12345.pdf": "echo_cancellation",
            "6789.pdf": "noise_reduction",
            "regning April.pdf": "bills_utilities",
            "effective_cpp_notes.pdf": "programming_cpp",
            "深入理解C++11.pdf": "programming_cpp",
            "readme.pdf": None,           # no topic -> unclassifiable
            "broken.pdf": None,
        }
        for fn, want in expect.items():
            cat, _sc, _top = classify(recs[os.path.join(inp, fn)], rs, cfg)
            check(cat == want, f"{fn}: expected {want}, got {cat}")


@test
def test_rename_from_content():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        rs = build_rule_set(cfg)
        # numeric + clear title -> renamed
        n1 = new_name_for(recs[os.path.join(inp, "12345.pdf")])
        check(n1 is not None and "echo cancellation" in n1.lower(),
              f"numeric file renamed from title, got {n1!r}")
        check("ieee transactions" not in n1.lower(), "venue header must not become the title")
        # meaningful names untouched
        for keep in ("effective_cpp_notes.pdf", "深入理解C++11.pdf", "regning April.pdf"):
            check(new_name_for(recs[os.path.join(inp, keep)]) is None, f"{keep} must keep its name")
        # corrupt file cannot be renamed
        check(new_name_for(recs[os.path.join(inp, "broken.pdf")]) is None, "corrupt file not renamed")


@test
def test_plan_apply_undo_separate_output():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(root, "sorted")
        cfg = base_cfg(inp, out, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        applied, errors, log = apply_plan(ops, cfg)
        check(not errors and len(applied) == 7, f"7 moved, errors={errors}")
        check(not [f for f in os.listdir(inp) if f.lower().endswith('.pdf')], "input emptied")
        outfiles = []
        for d, _, fs in os.walk(out):
            outfiles += [os.path.join(d, f) for f in fs if f.lower().endswith(".pdf")]
        check(len(outfiles) == 7, "all files in output")
        echo_dir = os.path.join(out, "echo_cancellation")
        check(os.path.isdir(echo_dir) and len(os.listdir(echo_dir)) == 1, "echo pdf grouped")
        logp = write_log(log, cfg)
        check(logp and os.path.exists(logp), "undo log written")
        write_reports(ops, cfg)
        for r in ("rename_report.txt", "folder_manifest.txt", "summary.txt"):
            check(os.path.exists(os.path.join(out, r)), f"report {r} written")
        # undo restores everything
        undone, skipped = undo(logp)
        check(undone == 7 and skipped == 0, f"undo restored 7, got {undone}/{skipped}")
        check(len([f for f in os.listdir(inp) if f.lower().endswith('.pdf')]) == 7, "input restored")
        out_left = [f for d, _, fs in os.walk(out) for f in fs if f.lower().endswith('.pdf')]
        check(not out_left, "output emptied after undo")


@test
def test_collision_suffix():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(root, "sorted")
        cfg = base_cfg(inp, out, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = build_plan(recs, cfg, build_rule_set(cfg), None, None)
        # force a collision: two files, same category, same planned name
        picked = [o for o in ops if o["cat"] == "uncategorized"][:2] or ops[:2]
        for o in picked[:2]:
            o["cat"], o["name"] = "collide_me", "SAME TITLE.pdf"
        ops = target_paths(ops, cfg)
        dsts = [os.path.basename(o["dst"]) for o in picked[:2]]
        check(len({d.lower() for d in dsts}) == len(dsts), f"collision names unique: {dsts}")
        applied, errors, _ = apply_plan(ops, cfg)
        check(not errors, f"collision apply ok: {errors}")


@test
def test_dry_run_moves_nothing():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, dry_run=True, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        applied, errors, log = apply_plan(ops, cfg)
        check(not errors and applied, "dry-run produced a plan")
        check(len([f for f in os.listdir(inp) if f.lower().endswith('.pdf')]) == 7,
              "dry-run left all files in place")
        check(not write_log(log, cfg), "no undo log on dry-run")


@test
def test_nested_first_letter():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(root, "sorted")
        cfg = base_cfg(inp, out, nested=True, subfolder_by="first_letter",
                       work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        applied, errors, _ = apply_plan(ops, cfg)
        check(not errors, f"nested apply: {errors}")
        echo = os.path.join(out, "echo_cancellation")
        subs = [d for d in os.listdir(echo) if os.path.isdir(os.path.join(echo, d))]
        check(subs and subs[0].upper().startswith("A"), f"echo file under A/, got {subs}")


@test
def test_ignore_and_recursive():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, work_folder=os.path.join(root, "cache"))
        cfg["ignore"] = ["private"]
        pdfs = find_pdfs(cfg)
        check(all("private" not in p for p in pdfs), "private folder ignored")
        cfg["recursive"] = True
        pdfs = find_pdfs(cfg)
        check(all("private" not in p for p in pdfs), "private still ignored when recursive")
        check(len(pdfs) == 7, f"recursive without ignore finds 7, got {len(pdfs)}")
        cfg["recursive"] = False
        cfg["ignore"] = []
        pdfs = find_pdfs(cfg)
        check(len(pdfs) == 7, f"non-recursive flat scan, got {len(pdfs)}")


@test
def test_undo_auto_discovery():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(root, "sorted")
        cfg = base_cfg(inp, out, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        _applied, _errors, log = apply_plan(ops, cfg)
        logp = write_log(log, cfg)
        check(logp and os.path.exists(logp), "log written")
        # auto-discovery finds the log via the output folder, no explicit path
        found = resolve_undo("auto", cfg)
        check(os.path.samefile(found, logp), f"auto-discovered {found}")
        undone, skipped = undo(found)
        check(undone == 7 and skipped == 0, f"undo via discovery restored 7, got {undone}")


@test
def test_recursive_prunes_output_and_cache():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(inp, "sorted_out")            # output INSIDE input
        cache = os.path.join(inp, ".cache")
        os.makedirs(out, exist_ok=True)
        make_pdf(os.path.join(out, "decoy.pdf"), NOISE_PAPER)
        cfg = base_cfg(inp, out, recursive=True, work_folder=cache)
        recs = extract_all(find_pdfs(cfg), cfg)
        check(all("sorted_out" not in p for p in recs), "decoy in output folder not scanned")
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        applied, errors, _ = apply_plan(ops, cfg)
        check(not errors and applied, "run completed with output nested inside input")
        # after the run, a rescan must not pick up the moved files or the cache
        found = find_pdfs(cfg)
        check(found == [], f"recursive rescan prunes output+cache, got {found}")
        # without pruning (output outside input) the moved files are visible
        cfg2 = base_cfg(inp, os.path.join(root, "elsewhere"), recursive=True,
                        work_folder=os.path.join(root, "c2"))
        found2 = find_pdfs(cfg2)
        check(all("sorted_out" in p for p in found2), f"all 7+1 visible: {len(found2)}")


@test
def test_custom_category_priority():
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        cfg = base_cfg(inp, work_folder=os.path.join(root, "cache"))
        cfg["classifier"]["custom_categories"] = [
            {"name": "my_echo_shelf", "keywords": ["doubletalk detection"]}]
        rs = build_rule_set(cfg)
        recs = extract_all(find_pdfs(cfg), cfg)
        cat, _s, _t = classify(recs[os.path.join(inp, "12345.pdf")], rs, cfg)
        check(cat == "my_echo_shelf", f"custom category wins, got {cat}")
        # disable it -> falls back to echo_cancellation
        cfg["classifier"]["disable_categories"] = ["my_echo_shelf"]
        rs2 = build_rule_set(cfg)
        cat2, _s2, _t2 = classify(recs[os.path.join(inp, "12345.pdf")], rs2, cfg)
        check(cat2 == "echo_cancellation", f"disabled category falls back, got {cat2}")


@test
def test_standard_schemes():
    from organizer.rules import DEFAULT_RULES
    from organizer.schemes import LCC_MAP, ARXIV_MAP, standard_codes, lcc_label, LCC_TOP
    cats = [c for c, *_ in DEFAULT_RULES]
    missing = [c for c in cats if c not in LCC_MAP]
    check(not missing, f"every built-in category has an LCC entry, missing: {missing}")
    stale = [c for c in ARXIV_MAP if c not in cats]
    check(not stale, f"ARXIV_MAP has no stale keys, stale: {stale}")
    check(all(c in cats for c in LCC_MAP), "LCC_MAP has no stale keys")
    check(all(letter in LCC_TOP for letter in LCC_MAP.values() if letter),
          "every used LCC letter has a label")
    check(standard_codes("echo_cancellation") == ("T", "eess.AS"), "echo -> T/eess.AS")
    check(lcc_label("echo_cancellation") == "T - Technology", "LCC label rendered")
    check(standard_codes("bills_utilities") == ("", ""),
          "personal/practical documents have no standard class")
    check(standard_codes("unknown_category") == ("", ""), "unknown categories map to ('', '')")
    # the summary report carries the code columns
    with tempfile.TemporaryDirectory() as root:
        inp = build_fixtures(root)
        out = os.path.join(root, "sorted")
        cfg = base_cfg(inp, out, work_folder=os.path.join(root, "cache"))
        recs = extract_all(find_pdfs(cfg), cfg)
        ops = target_paths(build_plan(recs, cfg, build_rule_set(cfg), None, None), cfg)
        write_reports(ops, cfg)
        summary = open(os.path.join(out, "summary.txt"), encoding="utf-8").read()
        check("LCC" in summary and "arXiv" in summary, "summary has standard-code columns")
        check("eess." in summary, "summary shows an arXiv code")


def main():
    only = sys.argv[1:] or None
    for fn in TESTS:
        if only and fn.__name__ not in only:
            continue
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            FAILURES.append(fn.__name__)
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print()
    if FAILURES:
        print(f"{len(FAILURES)} test(s) FAILED: {', '.join(FAILURES)}")
        sys.exit(1)
    print(f"All {len(TESTS)} tests passed.")


if __name__ == "__main__":
    main()
