"""One-PDF extraction worker. Run as a subprocess so a pathological PDF
cannot hang the whole pipeline (hard timeout enforced by the parent).

Usage: python _extract_worker.py <pdf_path> <out_json> [max_pages]
"""
import sys, os, json


def main():
    path, out = sys.argv[1], sys.argv[2]
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    rec = {"file": path, "pages": 0, "size": 0, "err": None, "meta": "", "text": ""}
    try:
        rec["size"] = os.path.getsize(path)
    except OSError:
        pass
    try:
        import pymupdf
        doc = pymupdf.open(path)
        if doc.needs_pass:
            try:
                doc.authenticate("")
            except Exception:
                rec["err"] = "password"
        rec["pages"] = doc.page_count
        try:
            m = doc.metadata or {}
            rec["meta"] = str(m.get("title") or "")[:300]
        except Exception:
            pass
        chunks = []
        for i in range(min(max_pages, doc.page_count)):
            try:
                t = doc[i].get_text("text")
            except Exception:
                t = ""
            chunks.append(t)
            if sum(len(c) for c in chunks) > 4000:
                break
        rec["text"] = "\n".join(chunks)[:4000]
        doc.close()
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {str(e)[:120]}"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
