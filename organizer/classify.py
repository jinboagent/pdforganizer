"""Rule-based content classifier with title-zone weighting."""
import os
import re

from . import rules as R

BOILER = [
    re.compile(r'_*\s*audio engineering society convention paper[^.]{0,240}\.?', re.I | re.S),
    re.compile(r'see discussions, stats, and author profiles for this publication at[^.]{0,200}\.?', re.I | re.S),
    re.compile(r'microsoft word - \S{0,80}\.(doc|docx|rtf)\b', re.I),
    re.compile(r'ieee transactions on [a-z &,]{2,60}(vol(ume)?\.?\s*\d+.{0,60})?', re.I),
    re.compile(r'journal of the (audio engineering|acoustical) society[^.]{0,80}\.?', re.I),
    re.compile(r'proceedings of the ieee[^.]{0,80}\.?', re.I),
]
MOJ = re.compile(r'[\u2500-\u257f\u0080-\u009f\u0000-\u001f\u007f]|[¡¢£¤¥¦§¨«¬¯±²³´µ¶¸¹º»¼½¾¿×÷]')


def build_rule_set(cfg):
    """(category, strong, weak, bonus) list: custom categories first with a
    priority bonus so they win ties against built-ins; defaults minus disabled."""
    ccfg = cfg.get("classifier", {})
    disable = set(ccfg.get("disable_categories", []))
    out = []
    for c in ccfg.get("custom_categories", []):
        name = c.get("name", "").strip()
        kws = [re.escape(k) for k in c.get("keywords", []) if k.strip()]
        weak = [re.escape(k) for k in c.get("weak_keywords", []) if k.strip()]
        if name and kws and name not in disable:
            out.append((name, kws, weak, 2.0))
    for cat, strong, weak in R.DEFAULT_RULES:
        if cat not in disable:
            out.append((cat, strong, weak, 0.0))
    return out


def zones(rec):
    fn = os.path.basename(rec["file"])
    head = MOJ.sub(" ", (rec.get("text") or "")[:400])
    for b in BOILER:
        head = b.sub(" ", head)
    title = (fn + " " + (rec.get("meta") or "") + " " + head[:350]).lower()
    body = ((rec.get("text") or "")[350:]).lower()
    case_zone = fn + " " + (rec.get("meta") or "") + " " + head
    return fn.lower(), title, body, case_zone


def score(rec, cat, strongs, weaks):
    fl, tl, bl, case_zone = zones(rec)
    s = 0.0
    for p in strongs:
        if re.search(p, fl, re.I):
            s += 4.5
        elif re.search(p, tl, re.I):
            s += 3.0
        elif re.search(p, bl, re.I):
            s += 1.0
    for p in weaks:
        if re.search(p, fl, re.I):
            s += 2.7
        elif re.search(p, tl, re.I):
            s += 1.2
        elif re.search(p, bl, re.I):
            s += 0.35
    for p in R.CASE_SENSITIVE.get(cat, []):
        if re.search(p, case_zone):
            s += 4.5
        elif re.search(p, rec.get("text") or ""):
            s += 1.0
    return s


def classify(rec, rule_set, cfg):
    """Returns (category, score, top3). Category None when unclassifiable."""
    ccfg = cfg.get("classifier", {})
    min_score = ccfg.get("min_score", 2.0)
    min_margin = ccfg.get("min_margin", 0.5)
    scores = {}
    for cat, strongs, weaks, bonus in rule_set:
        s = score(rec, cat, strongs, weaks) + bonus
        if s > 0:
            scores[cat] = s
    if not scores:
        return None, 0.0, []
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best, bs = ranked[0]
    margin = bs - (ranked[1][1] if len(ranked) > 1 else 0)
    top = [[c, round(v, 2)] for c, v in ranked[:3]]
    if bs >= min_score and margin >= min_margin:
        return best, bs, top
    return None, bs, top   # ambiguous -> uncategorized
