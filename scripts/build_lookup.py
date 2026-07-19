#!/usr/bin/env python3
"""Build data/lookup-index.json for the report-card diagnose flow.

Per business we bundle: name/grade/city/slug, domain+rating+reviews (from the
master CSV), the real report card (parsed from the grading engine's biz page),
the in-area competitive rank ("#39 of 50 local electricians"), the trade + score,
and the #1 shop in that trade — everything the FOMO step needs.
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


def trade_token(s):
    m = re.search(r"[a-z_]+", (s or "").lower())
    return m.group(0) if m else ""


def _txt(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&thinsp;", "")
    s = html.unescape(s)
    s = re.sub(r"[    ]", "", s)  # thin / narrow / nbsp spaces only
    return re.sub(r"\s+", " ", s).strip()


def parse_biz(slug):
    """Return (report_card_dict, rank_tuple) from a business's biz page."""
    fn = os.path.join(BIZ, slug, "index.html")
    if not os.path.isfile(fn):
        return None, None
    h = open(fn, encoding="utf-8").read()
    # ---- rank ----
    rk = None
    rm = re.search(r'Class rank</span><span class="rc-fill">#(\d+) of (\d+) (?:local )?([^<]+)</span>', h)
    if rm:
        rk = [int(rm.group(1)), int(rm.group(2)), rm.group(3).strip()]
    # ---- report card ----
    m = re.search(r'<table class="rc-subjects">.*?</table>', h, re.S)
    if not m:
        return None, rk
    rows, total = [], None
    for cls, body in re.findall(r"<tr class=\"([^\"]+)\">(.*?)</tr>", m.group(0), re.S):
        def cell(k, tag="td"):
            mm = re.search(r'class="' + k + r'[^"]*"[^>]*>(.*?)</' + tag + r'>', body, re.S)
            return _txt(mm.group(1)) if mm else ""
        row = [cell("subj"), cell("found"), cell("num").replace(" / ", "/"),
               (re.search(r'class="grade-[^"]*"[^>]*>(.*?)</span>', body, re.S) or [None, ""])[1]]
        row[3] = _txt(row[3])
        if cls == "rc-total":
            total = row
        else:
            rows.append(row + [cls])
    if not rows:
        return None, rk
    plain = _txt(re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S))
    cmt = ""
    cm = re.search(r"\bComments\b\s+(.*?)\s+(?:Prepared by|Print this|Class averages|$)", plain)
    if cm:
        cmt = re.sub(r"\s+", " ", cm.group(1)).strip()[:360]
    rc = {"rows": rows, "cmt": cmt}
    if total:
        rc["tot"] = [total[1], total[2], total[3]]
    return rc, rk


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
                "tr": trade_token(row.get("trades")),
            })

    idx = json.load(open(SEARCH))
    out = []
    for x in idx:
        nn = norm_name(x.get("n"))
        extra = by_name.get(nn, {})
        rc, rk = parse_biz(x.get("s"))
        rec = {
            "n": x.get("n"), "nn": nn, "g": x.get("g"), "c": x.get("c"),
            "s": x.get("s"), "d": extra.get("d", ""),
            "r": extra.get("r", ""), "rv": extra.get("rv", ""),
            "p": x.get("p"), "tr": extra.get("tr", ""),
        }
        if rc:
            rec["rc"] = rc
        if rk:
            rec["rk"] = rk
        out.append(rec)

    # trade leaders: among in-area (ranked) shops, the #1 of each trade
    leaders = {}
    for r in out:
        if r.get("rk") and r["tr"]:
            cur = leaders.get(r["tr"])
            if not cur or (r.get("p") or 0) > (cur.get("p") or 0):
                leaders[r["tr"]] = r
    ranked_ct = sum(1 for r in out if r.get("rk"))
    for r in out:
        L = leaders.get(r["tr"])
        if L and L["n"] != r["n"]:
            r["ld"] = {"n": L["n"], "g": L["g"], "rv": L["rv"]}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    kb = os.path.getsize(OUT) // 1024
    print(f"wrote {len(out)} businesses ({kb} KB); {ranked_ct} ranked in-area, "
          f"{len(leaders)} trade leaders")


if __name__ == "__main__":
    main()
