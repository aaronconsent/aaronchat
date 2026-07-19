#!/usr/bin/env python3
"""Build data/lookup-index.json for the report-card diagnose flow.

Joins the grading engine's search-index.json (name, grade, city, slug) with
contractors_master.csv (domain, rating, reviews) AND parses each business's
real report card out of stats-lakelivingston/docs/biz/<slug>/index.html so the
site can render the full card inline (no need to send visitors off-site).
Run: python3 scripts/build_lookup.py  (re-run when the grading data updates).
"""
import os, csv, json, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = os.path.join(ROOT, "stats-lakelivingston")
SEARCH = os.path.join(STATS, "docs/search-index.json")
CSVF = os.path.join(STATS, "data/contractors_master.csv")
BIZ = os.path.join(STATS, "docs/biz")
OUT = os.path.join(ROOT, "data/lookup-index.json")


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def norm_domain(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s)
    return s.split("/")[0].split("?")[0].strip()


def _txt(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&thinsp;", "").replace(" ", "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()


def parse_rc(slug):
    """Parse the real report card from the grading engine's biz page."""
    fn = os.path.join(BIZ, slug, "index.html")
    if not os.path.isfile(fn):
        return None
    h = open(fn, encoding="utf-8").read()
    m = re.search(r'<table class="rc-subjects">.*?</table>', h, re.S)
    if not m:
        return None
    table = m.group(0)
    rows, total = [], None
    for tr in re.findall(r"<tr class=\"([^\"]+)\">(.*?)</tr>", table, re.S):
        cls, body = tr
        subj = re.search(r'class="subj"[^>]*>(.*?)</td>', body, re.S)
        found = re.search(r'class="found"[^>]*>(.*?)</td>', body, re.S)
        num = re.search(r'class="num"[^>]*>(.*?)</td>', body, re.S)
        grade = re.search(r'class="grade-[^"]*"[^>]*>(.*?)</span>', body, re.S)
        row = [
            _txt(subj.group(1)) if subj else "",
            _txt(found.group(1)) if found else "",
            _txt(num.group(1)).replace(" / ", "/") if num else "",
            _txt(grade.group(1)) if grade else "",
        ]
        if cls == "rc-total":
            total = row  # [label, "Overall", pts, grade] -> subj is "Overall", found is label
        else:
            rows.append(row + [cls])  # +status class (ok / miss / ...)
    if not rows:
        return None
    # class rank + comment (plain text scrape; whitespace already collapsed)
    plain = _txt(re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S))
    rank = ""
    rm = re.search(r"Class rank\s+(.*?)\s+Google standing", plain)
    if rm:
        rank = rm.group(1).strip()
    cmt = ""
    cm = re.search(r"\bComments\b\s+(.*?)\s+(?:Prepared by|Print this|Class averages|$)", plain)
    if cm:
        cmt = re.sub(r"\s+", " ", cm.group(1)).strip()[:360]
    out = {"rows": rows, "rank": rank, "cmt": cmt}
    if total:
        # total row: subj="Overall", found=label (e.g. Category Leader), num=pts, grade
        out["tot"] = [total[1], total[2], total[3]]
    return out


def main():
    by_name = {}
    with open(CSVF, newline="") as f:
        for row in csv.DictReader(f):
            nn = norm_name(row.get("name"))
            if not nn:
                continue
            by_name.setdefault(nn, {
                "d": norm_domain(row.get("site")),
                "r": row.get("rating") or "",
                "rv": row.get("reviews") or "",
            })

    idx = json.load(open(SEARCH))
    out, matched, carded = [], 0, 0
    for x in idx:
        nn = norm_name(x.get("n"))
        extra = by_name.get(nn, {})
        if extra:
            matched += 1
        rc = parse_rc(x.get("s"))
        if rc:
            carded += 1
        rec = {
            "n": x.get("n"), "nn": nn, "g": x.get("g"), "c": x.get("c"),
            "s": x.get("s"), "d": extra.get("d", ""),
            "r": extra.get("r", ""), "rv": extra.get("rv", ""),
        }
        if rc:
            rec["rc"] = rc
        out.append(rec)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    kb = os.path.getsize(OUT) // 1024
    print(f"wrote {len(out)} businesses to {OUT} ({kb} KB); "
          f"{matched} with domain/rating, {carded} with full report cards")


if __name__ == "__main__":
    main()
