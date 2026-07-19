#!/usr/bin/env python3
"""Build data/lookup-index.json for the report-card diagnose flow.

Per business we bundle name/grade/city/slug/domain/rating/reviews, the real
report card (parsed from the grading engine's biz page), the in-area rank, the
#1 shop in the trade, AND a `fomo` block: trade-wide market averages, modeled
lead/cost/revenue projections, the climb-path to C/B/A with the plan needed, and
the tactics the top shops use that this shop doesn't.

MODEL constants below are TUNABLE — the lead/cost/revenue figures are transparent
projections (clearly labeled "est." in the UI), everything else is real data.
Run: python3 scripts/build_lookup.py  (re-run when the grading data updates).
"""
import os, csv, json, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = os.path.join(ROOT, "stats-lakelivingston")
SEARCH = os.path.join(STATS, "docs/search-index.json")
CSVF = os.path.join(STATS, "data/contractors_master.csv")
BIZ = os.path.join(STATS, "docs/biz")
OUT = os.path.join(ROOT, "data/lookup-index.json")

# ---- MODEL (tunable projection assumptions) -------------------------------
# Estimated monthly leads for a shop = REV_K * reviews + SCORE_K * score, clamped.
REV_K, SCORE_K, LEADS_MIN, LEADS_MAX = 0.11, 0.22, 3, 80
CLOSE_RATE = 0.30                 # leads -> booked jobs
# Estimated cost per booked job falls as the grade rises.
CPJ_BASE, CPJ_SLOPE, CPJ_MIN, CPJ_MAX = 225, 1.6, 60, 225
SOCIAL_BENCH = 4                  # market avg social posts / month (benchmark)
# Average booked-job value by trade (rough industry benchmarks, USD).
AVG_JOB = {
    "hvac": 500, "plumber": 375, "electrician": 325, "roofing": 9000,
    "general_contractor": 6000, "pool_service": 275, "fencing": 3800,
    "tree_service": 950, "pressure_washing": 300, "lawn_care": 160,
    "septic": 700, "concrete": 4500, "pest_control": 130, "garage_door": 480,
    "handyman": 300, "painter": 2500, "flooring": 3500, "_default": 450,
}
# Which plan / cost / timeline gets a shop to each grade tier (>= score).
PATH = [
    {"g": "C", "pts": 50, "plan": "Enrolled", "mo": 300, "time": "4–6 weeks"},
    {"g": "B", "pts": 72, "plan": "Honor Roll", "mo": 600, "time": "about 3 months"},
    {"g": "A", "pts": 90, "plan": "Top of Class", "mo": 1200, "time": "about 6 months"},
]
# trade token -> the grading site's ranked-list page slug
TRADE_SLUG = {
    "electrician": "electricians", "plumber": "plumbers", "hvac": "hvac",
    "roofing": "roofing", "general_contractor": "general-contractor",
    "pool_service": "pool-service", "fencing": "fencing", "tree_service": "tree-service",
    "pressure_washing": "pressure-washing", "lawn_care": "lawn-care", "septic": "septic",
    "concrete": "concrete", "pest_control": "pest-control", "garage_door": "garage-door",
    "painter": "painters", "gutters": "gutters", "appliance": "appliance-repair",
    "appliance_repair": "appliance-repair",
}
# rubric subject -> (short key, "what the top shops do" action)
FACTORS = [
    ("Working website", "site", "Run a real, fast website"),
    ("Claimed Google profile", "claimed", "Claim & optimize their Google profile"),
    ("Review volume", "reviews", "Ask every customer for a review"),
    ("Star rating", "rating", "Protect a 4.5★-plus rating"),
    ("Listing photos", "photos", "Post 20+ real job photos"),
    ("Phone on listing", "phone", "Show a tap-to-call number"),
]


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def norm_domain(s):
    if not s:
        return ""
    s = re.sub(r"^https?://", "", s.strip().lower())
    s = re.sub(r"^www\.", "", s)
    return s.split("/")[0].split("?")[0].strip()


def trade_token(s):
    m = re.search(r"[a-z_]+", (s or "").lower())
    return m.group(0) if m else ""


def num(s, d=0):
    try:
        return float(re.sub(r"[^0-9.]", "", str(s)))
    except Exception:
        return d


def _txt(s):
    s = re.sub(r"<[^>]+>", "", s).replace("&thinsp;", "")
    s = html.unescape(s)
    s = re.sub(r"[    ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_biz(slug):
    fn = os.path.join(BIZ, slug, "index.html")
    if not os.path.isfile(fn):
        return None, None
    h = open(fn, encoding="utf-8").read()
    rk = None
    rm = re.search(r'Class rank</span><span class="rc-fill">#(\d+) of (\d+) (?:local )?([^<]+)</span>', h)
    if rm:
        rk = [int(rm.group(1)), int(rm.group(2)), rm.group(3).strip()]
    m = re.search(r'<table class="rc-subjects">.*?</table>', h, re.S)
    if not m:
        return None, rk
    rows, total = [], None
    for cls, body in re.findall(r"<tr class=\"([^\"]+)\">(.*?)</tr>", m.group(0), re.S):
        def cell(k):
            mm = re.search(r'class="' + k + r'[^"]*"[^>]*>(.*?)</td>', body, re.S)
            return _txt(mm.group(1)) if mm else ""
        grade = re.search(r'class="grade-[^"]*"[^>]*>(.*?)</span>', body, re.S)
        row = [cell("subj"), cell("found"), cell("num").replace(" / ", "/"), _txt(grade.group(1)) if grade else ""]
        if cls == "rc-total":
            total = row
        else:
            rows.append(row + [cls])
    if not rows:
        return None, rk
    plain = _txt(re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S))
    cm = re.search(r"\bComments\b\s+(.*?)\s+(?:Prepared by|Print this|Class averages|$)", plain)
    rc = {"rows": rows, "cmt": (re.sub(r"\s+", " ", cm.group(1)).strip()[:360] if cm else "")}
    if total:
        rc["tot"] = [total[1], total[2], total[3]]
    return rc, rk


def passes(rc):
    """Set of factor keys this shop already does well (status ok)."""
    out = set()
    if not rc:
        return out
    subj_key = {s: k for s, k, _ in FACTORS}
    for r in rc.get("rows", []):
        k = subj_key.get(r[0])
        if k and r[4] == "ok":
            out.add(k)
    return out


def est_leads(reviews, score):
    v = round(REV_K * reviews + SCORE_K * score)
    return int(max(LEADS_MIN, min(LEADS_MAX, v)))


def est_cpj(score):
    v = round(CPJ_BASE - CPJ_SLOPE * score)
    return int(max(CPJ_MIN, min(CPJ_MAX, v)))


def main():
    by_name = {}
    with open(CSVF, newline="") as f:
        for row in csv.DictReader(f):
            nn = norm_name(row.get("name"))
            if not nn:
                continue
            by_name.setdefault(nn, {
                "d": norm_domain(row.get("site")), "r": row.get("rating") or "",
                "rv": row.get("reviews") or "", "tr": trade_token(row.get("trades")),
                "ph": int(num(row.get("photos_count"))),
            })

    idx = json.load(open(SEARCH))
    out = []
    for x in idx:
        e = by_name.get(norm_name(x.get("n")), {})
        rc, rk = parse_biz(x.get("s"))
        rec = {
            "n": x.get("n"), "nn": norm_name(x.get("n")), "g": x.get("g"), "c": x.get("c"),
            "s": x.get("s"), "d": e.get("d", ""), "r": e.get("r", ""), "rv": e.get("rv", ""),
            "ph": e.get("ph", 0), "p": x.get("p") or 0, "tr": e.get("tr", ""),
        }
        if rc:
            rec["rc"] = rc
        if rk:
            rec["rk"] = rk
        out.append(rec)

    # ---- per-trade aggregates over IN-AREA (ranked) shops -----------------
    trades = {}
    for r in out:
        if r.get("rk") and r["tr"]:
            trades.setdefault(r["tr"], []).append(r)

    stats = {}
    for tr, shops in trades.items():
        shops_sorted = sorted(shops, key=lambda s: s.get("p") or 0, reverse=True)
        top5 = shops_sorted[:5]
        n = len(shops)
        site_ct = sum(1 for s in shops if "site" in passes(s.get("rc")))
        # how many of the top 5 do each factor
        top5_pass = {}
        for _, k, _a in FACTORS:
            top5_pass[k] = sum(1 for s in top5 if k in passes(s.get("rc")))
        leader = shops_sorted[0]
        stats[tr] = {
            "n": n,
            "pctSite": round(100 * site_ct / n) if n else 0,
            "avgRev": round(sum(num(s["rv"]) for s in shops) / n) if n else 0,
            "avgPh": round(sum(s["ph"] for s in shops) / n) if n else 0,
            "top5Rev": round(sum(num(s["rv"]) for s in top5) / len(top5)) if top5 else 0,
            "top5Pass": top5_pass,
            "leaderRev": num(leader["rv"]), "leaderScore": leader.get("p") or 0,
            "ldN": leader["n"], "ldG": leader["g"], "ldRv": leader["rv"],
        }

    # ---- attach the fomo block to every shop that has a trade stat --------
    carded = 0
    for r in out:
        st = stats.get(r["tr"])
        if not st:
            continue
        carded += 1
        score = r.get("p") or 0
        reviews = num(r["rv"])
        job = AVG_JOB.get(r["tr"], AVG_JOB["_default"])
        leadsYou = est_leads(reviews, score)
        leadsTop = est_leads(st["leaderRev"], st["leaderScore"])
        missed_jobs = max(0, leadsTop - leadsYou) * CLOSE_RATE
        missed_rev = int(round(missed_jobs * job / 100.0) * 100)
        cpjYou, cpjTop = est_cpj(score), est_cpj(max(score, 92))
        cplYou, cplTop = int(round(cpjYou * CLOSE_RATE)), int(round(cpjTop * CLOSE_RATE))
        new_jobs = max(2, int(round(max(0, leadsTop - leadsYou) * CLOSE_RATE)))
        mine = passes(r.get("rc"))
        tactics = []
        for subj, k, action in FACTORS:
            if st["top5Pass"].get(k, 0) >= 3 and k not in mine:
                tactics.append(action)
        tactics.append("Post fresh photos & updates every week")  # social gap
        tactics = tactics[:5]
        path = [p for p in PATH if p["pts"] > score]
        if not path:  # already an A / A+
            path = [{"g": "A+", "pts": 96, "plan": "Top of Class", "mo": 1200, "time": "ongoing"}]
        target = path[-1]
        r["fomo"] = {
            "n": st["n"], "pctSite": st["pctSite"], "avgRev": st["avgRev"],
            "avgPh": st["avgPh"], "top5Rev": st["top5Rev"],
            "yourRev": int(reviews), "yourPh": r["ph"],
            "leadsYou": leadsYou, "leadsTop": leadsTop,
            "cpjYou": cpjYou, "cpjTop": cpjTop, "cplYou": cplYou, "cplTop": cplTop,
            "missed": missed_rev, "job": job, "social": SOCIAL_BENCH,
            "path": path, "tactics": tactics,
            "trslug": TRADE_SLUG.get(r["tr"], ""),
            "deal": {"mo": target["mo"], "plan": target["plan"], "jobs": new_jobs, "cpl": cplTop},
        }
        if st["ldN"] != r["n"]:
            r["fomo"]["ldn"] = st["ldN"]
            r["fomo"]["ldg"] = st["ldG"]
            r["fomo"]["ldrv"] = int(num(st["ldRv"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    kb = os.path.getsize(OUT) // 1024
    print(f"wrote {len(out)} businesses ({kb} KB); {len(stats)} trades, {carded} with fomo blocks")


if __name__ == "__main__":
    main()
