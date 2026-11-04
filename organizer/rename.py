"""Content-based renaming: decide whether a filename is meaningless, and if so
derive a clean name from metadata / first-page text."""
import os
import re

FORBIDDEN = '<>:"/\\|?*'
GENERIC_WORDS = {
    'overview', 'report', 'notes', 'chapter', 'document', 'page', 'result', 'test',
    'bench', 'hand', 'pattern', 'reference', 'guide', 'toc', 'untitled', 'scan',
    'image', 'file', 'final', 'draft', 'print', 'template', 'sample', 'paper',
    'slides', 'lecture', 'exercise', 'solution', 'book', 'readme', 'fulltext',
    'download', 'output', 'figure', 'abstract', 'contents', 'index', 'master',
    'thesis', 'manual', 'info', 'noname', 'pdf',
}
MOJ_STRICT = re.compile(r'[\u2500-\u257f\u0080-\u009f\u0000-\u001f\u007f]|[¡¢£¤¥¦§¨«¬¯±²³´µ¶¸¹º»¼½¾¿×÷]')
CJK = re.compile(r'[\u4e00-\u9fff]')

META_BAD = re.compile(
    r'(?i)^(microsoft (word|powerpoint)|print preview|untitled|no title|title|'
    r'getstart|ebook ?\d+|contents page|'
    r'\d+(\.\d+)?$|'
    r'.*\.(doc|docx|rtf|ppt|dvi|indd|tex|md|jsp|vp|book|prj)$|'
    r'draft\.dvi|p\.dvi|master\.dvi|bookfinal|'
    r'doi:\S+|isbn \S+)')

LINE_SKIP = re.compile(
    r'(?i)^\s*('
    r'see discussions,.*|stats,.*|and author profiles.*|'
    r'https?://\S+.*|arxiv:\S+.*|\d{1,3}\s*$|'
    r'downloaded (from|by).*|'
    r'international telecommunication union.*|telecommunication standardization sector.*|'
    r'audio engineering society (convention|conference) paper.*|'
    r'convention paper \d+.*|reprinted from.*|'
    r'ieee transactions on.*|proceedings of the ieee.*|'
    r'\s*ieee\b.{0,60}$|\u00a9.{0,80}|vol(ume)?\.?\s*\d+.*|no\.?\s*\d+.*|pp\.\s*\d+.*|'
    r'journal of the audio engineering society.*|journal of the acoustical society.*|'
    r'microsoft word.*|microsoft powerpoint.*|print preview.*|'
    r'.*\.(doc|docx|rtf|ppt|dvi|indd|tex|md|ps|pdf|book|prj|vp|cnf)\s*$|'
    r'\s*$)')

CAPS_RUN = re.compile(r"(?:[A-Z][A-Z0-9''’&,.:/+()°\- ]{1,} ){2,}[A-Z][A-Z0-9''’&,.:/+()°\- ]{1,}")


def name_kind(filename):
    """'ok' when the name looks meaningful, else the reason it is not."""
    stem = os.path.splitext(filename)[0].strip()
    if not stem:
        return 'empty'
    if MOJ_STRICT.search(stem):
        return 'mojibake'
    if len(CJK.findall(stem)) >= 3:
        return 'ok'                     # meaningful CJK title
    digits = sum(c.isdigit() for c in stem)
    if digits >= 2 and digits >= len(stem) * 0.5:
        return 'numeric'
    if len(stem) <= 14 and re.fullmatch(r'[A-Za-z]{1,6}\d[\w\-_%]*', stem):
        return 'code'
    if len(stem) <= 3:
        return 'tiny'
    words = [w for w in re.findall(r'[A-Za-zÀ-ÿæøåÆØÅ]{4,}', stem)]
    if not words:
        return 'no_real_words'
    if all(w.lower() in GENERIC_WORDS for w in words):
        return 'generic'
    return 'ok'


def sanitize(s):
    s = re.sub(r'[\x00-\x1f\x7f\x80-\x9f\u2028\u2029]', ' ', s)
    m = re.search(r'[\u2500-\u257f]|[¡¢£¤¥¦§¨ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿×÷]', s)
    if m:
        s = s[:m.start()]
    s = re.sub(r'\s+', ' ', s).strip(' .,-–—:;')
    for c in FORBIDDEN:
        s = s.replace(c, ' ')
    s = re.sub(r'\s+', ' ', s).strip(' .')
    if len(s) > 80:
        cut = s[:80]
        sp = cut.rfind(' ')
        s = (cut[:sp] if sp > 40 else cut).rstrip(' .,;:-')
    return s


def _good_meta(meta):
    if not meta or len(meta) < 12 or META_BAD.search(meta):
        return False
    return sum(c.isalpha() for c in meta) >= 8


def _title_from_lines(text):
    lines = [re.sub(r'\s+', ' ', l).strip(' .,:;-–—_|') for l in (text or '').split('\n')]
    cands = []
    for l in lines[:40]:
        if not l:
            if cands:
                break
            continue
        if LINE_SKIP.match(l) or MOJ_STRICT.search(l):
            if cands:
                break
            continue
        cands.append(l)
        if len(cands) >= 3:
            break
    if not cands:
        return ''
    t = cands[0]
    if len(cands) > 1 and (t.isupper() or len(t) < 45) and not t.endswith('.'):
        t2 = cands[1]
        if len(t2) < 70:
            t = t + ' ' + t2
    if len(t) < 8 or len(t) > 150:
        return ''
    return t


def _title_from_flat(text):
    t = re.sub(r'\s+', ' ', (text or '')[:1500])
    for b in ('audio engineering society convention paper', 'microsoft word -', 'print preview -'):
        t = t.replace(b, ' ')
    m = re.search(r'researchgate\.net/publication/\d+\s+(.{15,130}?)(?:\s{2,}|\.\s|\bAbstract\b)', t)
    if m:
        return m.group(1)
    m = CAPS_RUN.search(t)
    if m and len(m.group()) >= 15:
        return m.group()
    m = re.search(r'arxiv:\S+.*?\d+\s+(.{15,110}?)(?:\.\s|Abstract)', t)
    if m:
        return m.group(1)
    m = re.match(r'\s*(.{20,140}?)(?:\.\s|\bAbstract\b|\bIntroduction\b|,\s*.{0,40}\b(University|Institute|Department)\b)', t)
    if m and not MOJ_STRICT.search(m.group(1)):
        return m.group(1)
    return ''


def decode_mojibake(stem):
    """Try to recover a garbled (GBK shown as cp437/latin-1) filename."""
    if not any(ord(c) > 127 for c in stem):
        return ''
    for enc in ('cp437', 'latin-1'):
        try:
            d = stem.encode(enc, errors='strict').decode('gbk')
            if CJK.search(d):
                return d
        except Exception:
            pass
    return ''


VENUE_TELL = re.compile(
    r'(?i)(ieee transactions|proceedings of the ieee|journal of the (audio|acoustical)|'
    r'international conference on|symposium on|workshop on|vol(ume)?\.?\s*\d+,?\s+no\.?\s*\d+)')


def new_name_for(rec):
    """Return a clean new filename (with .pdf) from content, or None to keep."""
    fn = os.path.basename(rec["file"])
    stem = os.path.splitext(fn)[0]
    if name_kind(fn) == 'ok':
        return None
    cands = []
    meta = (rec.get("meta") or "").strip()
    if _good_meta(meta) and not VENUE_TELL.search(meta):
        cands.append(sanitize(meta))
    tl = _title_from_lines(rec.get("text"))
    if tl and sum(c.isalpha() for c in tl) >= 8 and not VENUE_TELL.search(tl):
        cands.append(sanitize(tl))
    tf = _title_from_flat(rec.get("text"))
    if tf and not VENUE_TELL.search(tf):
        cands.append(sanitize(tf))
    if not _any_text(rec) or not cands:
        d = decode_mojibake(stem)
        if d:
            cands.append(sanitize(d))
    cands = [c for c in cands if c and len(c) >= 6 and c.lower() != stem.lower()]
    if not cands:
        return None
    best = max(cands, key=len)
    return best + ".pdf"


def _any_text(rec):
    return (rec.get("text") or "").strip() or (rec.get("meta") or "").strip()
