#!/usr/bin/env python3
"""Build data/lookup-index.json for the report-card diagnose flow.

Joins the grading engine's search-index.json (name, grade, city, slug) with
contractors_master.csv (domain, rating, reviews) so the site's /api/lookup can
match a business by domain OR company name and return its live report card.
Run: python3 scripts/build_lookup.py  (re-run when the grading data updates).
"""
import os, csv, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH = os.path.join(ROOT, "stats-lakelivingston/docs/search-index.json")
CSVF = os.path.join(ROOT, "stats-lakelivingston/data/contractors_master.csv")
OUT = os.path.join(ROOT, "data/lookup-index.json")


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def norm_domain(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s)
    s = s.split("/")[0].split("?")[0].strip()
    return s


def main():
    # name -> {domain, rating, reviews, trades} from the master CSV
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
    out = []
    matched = 0
    for x in idx:
        nn = norm_name(x.get("n"))
        extra = by_name.get(nn, {})
        if extra:
            matched += 1
        out.append({
            "n": x.get("n"),          # display name
            "nn": nn,                 # normalized name (search)
            "g": x.get("g"),          # grade
            "c": x.get("c"),          # city
            "s": x.get("s"),          # slug (biz card)
            "d": extra.get("d", ""),  # domain
            "r": extra.get("r", ""),  # rating
            "rv": extra.get("rv", ""),# reviews
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    size = os.path.getsize(OUT)
    print(f"wrote {len(out)} businesses to {OUT} ({size//1024} KB); "
          f"{matched} joined a domain/rating from the CSV")


if __name__ == "__main__":
    main()
