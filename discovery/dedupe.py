"""Dedupe raw Outscraper JSON into master CSV + SQLite + market summary.

Runs after scrape.py. Reads every output/raw/*.json (each carries the batch
metadata so we know which query surfaced which record), dedupes by place_id,
and emits three artifacts:

    output/contractors_master.csv    — every unique business, all kept fields
    output/contractors.db            — SQLite w/ D1-compatible schema
    output/summary.md                — per-county × per-trade market gaps
"""
import csv
import glob
import json
import os
import sqlite3
from collections import defaultdict
from typing import Iterable

import config


# ---------------------------------------------------------------------------
# Raw file loading
# ---------------------------------------------------------------------------

def list_raw_files():
    return sorted(glob.glob(os.path.join(config.RAW_DIR, "*.json")))


def _iter_business_rows(raw_paths):
    """Yield (business_dict, batch_meta_for_the_query_that_returned_it) tuples.

    Outscraper's async response for google_maps_search is a list-of-lists:
    one inner list per query in the batch, containing business dicts.
    """
    for path in raw_paths:
        with open(path) as f:
            payload = json.load(f)
        batch_meta = payload.get("batch_meta") or []
        response = payload.get("response") or []
        for query_i, sublist in enumerate(response):
            if not isinstance(sublist, list):
                continue
            meta = batch_meta[query_i] if query_i < len(batch_meta) else {}
            for biz in sublist:
                if not isinstance(biz, dict):
                    continue
                yield biz, meta


# ---------------------------------------------------------------------------
# Field extraction — Outscraper field names vary slightly across versions
# ---------------------------------------------------------------------------

def _pick(d, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _extract(biz):
    """Normalize a business dict → the columns we keep."""
    return {
        "place_id":        _pick(biz, "place_id", "google_id"),
        "google_id":       _pick(biz, "google_id", "place_id"),
        "name":            _pick(biz, "name", "title"),
        "full_address":    _pick(biz, "full_address", "address"),
        "city":            _pick(biz, "city"),
        "state":           _pick(biz, "state"),
        "postal_code":     _pick(biz, "postal_code", "zip", "zipcode"),
        "phone":           _pick(biz, "phone", "phone_1", "phone_number"),
        "site":            _pick(biz, "site", "website"),
        "category":        _pick(biz, "category", "type"),
        "subtypes":        _pick(biz, "subtypes", "categories"),
        "rating":          _float(_pick(biz, "rating")),
        "reviews":         _int(_pick(biz, "reviews", "reviews_count")),
        "latitude":        _float(_pick(biz, "latitude", "lat")),
        "longitude":       _float(_pick(biz, "longitude", "lng", "lon")),
        "business_status": _pick(biz, "business_status"),
        "verified":        _pick(biz, "verified", "claimed"),
        "photos_count":    _int(_pick(biz, "photos_count", "photos")),
        "working_hours":   _pick(biz, "working_hours", "hours"),
    }


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

# Google Maps' geographic disambiguation is imperfect. A search for
# "plumber in Huntsville TX" happily returns results in Huntsville AL, Onalaska
# WI, Riverside CA, Livingston NJ, Oakhurst CA, and Goodrich MI (all towns
# that share names with our target East Texas cities). Filter every record
# to Texas. Kept as a set so operators can extend later.
ACCEPTED_STATES = {"Texas", "TX", "texas", "tx"}


def _is_texas(rec):
    """True if this business is in Texas. Falls back to address suffix if the
    `state` field is empty (Outscraper sometimes returns state as null)."""
    state = (rec.get("state") or "").strip()
    if state in ACCEPTED_STATES:
        return True
    if not state:
        # Check the address for a ", TX " or " TX " marker
        addr = (rec.get("full_address") or "")
        if ", TX " in addr or addr.endswith(" TX") or ", Texas " in addr:
            return True
        return False
    return False


def dedupe_records(raw_paths):
    """Walk every raw file, key by place_id, merge trades[] + queries_matched[]."""
    by_id = {}
    dropped_non_tx = 0
    for biz, meta in _iter_business_rows(raw_paths):
        rec = _extract(biz)
        pid = rec["place_id"] or rec["google_id"]
        if not pid:
            continue          # unindexable — drop
        if not _is_texas(rec):
            dropped_non_tx += 1
            continue          # cross-state contamination — drop
        rec["place_id"] = pid

        trade_slug = meta.get("trade_slug", "")
        trade_term = meta.get("trade_term", "")
        query = meta.get("query", "")
        county_key = meta.get("county_key", "")

        if pid not in by_id:
            rec["trades"] = set()
            rec["queries_matched"] = set()
            rec["county_keys_seen"] = set()
            by_id[pid] = rec
        else:
            # Merge — prefer existing non-null values; fill any nulls from the new copy
            existing = by_id[pid]
            for k, v in rec.items():
                if existing.get(k) in (None, "") and v not in (None, ""):
                    existing[k] = v

        if trade_slug:
            by_id[pid]["trades"].add(trade_slug)
        if query:
            by_id[pid]["queries_matched"].add(query)
        if county_key:
            by_id[pid]["county_keys_seen"].add(county_key)

    # Freeze sets → sorted lists (stable output)
    for rec in by_id.values():
        rec["trades"] = sorted(rec["trades"])
        rec["queries_matched"] = sorted(rec["queries_matched"])
        rec["county_keys_seen"] = sorted(rec["county_keys_seen"])
    if dropped_non_tx:
        print(f"[dedupe] dropped {dropped_non_tx} cross-state rows "
              f"(matches for our search-term cities that live in other US states)")
    return list(by_id.values())


# ---------------------------------------------------------------------------
# Output — CSV
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "place_id", "google_id", "name", "full_address", "city", "state", "postal_code",
    "phone", "site", "category", "subtypes", "rating", "reviews",
    "latitude", "longitude", "business_status", "verified", "photos_count",
    "working_hours", "trades", "queries_matched", "county_keys_seen",
]


def write_csv(records, path=None):
    path = path or config.MASTER_CSV
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for rec in records:
            row = dict(rec)
            for k in ("trades", "queries_matched", "county_keys_seen", "subtypes",
                      "working_hours"):
                if isinstance(row.get(k), (list, dict, set)):
                    row[k] = json.dumps(sorted(row[k]) if isinstance(row[k], set) else row[k],
                                        ensure_ascii=False)
            w.writerow(row)
    return path


# ---------------------------------------------------------------------------
# Output — SQLite (D1-compatible: TEXT / INTEGER / REAL only)
# ---------------------------------------------------------------------------

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS contractors (
  place_id         TEXT PRIMARY KEY,
  google_id        TEXT,
  name             TEXT,
  full_address     TEXT,
  city             TEXT,
  state            TEXT,
  zip              TEXT,
  phone            TEXT,
  site             TEXT,
  category         TEXT,
  subtypes         TEXT,       -- JSON array as text
  rating           REAL,
  reviews          INTEGER,
  latitude         REAL,
  longitude        REAL,
  business_status  TEXT,
  verified         INTEGER,    -- 0/1
  photos_count     INTEGER,
  working_hours    TEXT,       -- JSON as text
  trades           TEXT,       -- JSON array as text
  queries_matched  TEXT,       -- JSON array as text
  county_keys      TEXT,       -- JSON array as text
  first_seen_at    TEXT,
  last_seen_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_contractors_city   ON contractors(city);
CREATE INDEX IF NOT EXISTS idx_contractors_state  ON contractors(state);
CREATE INDEX IF NOT EXISTS idx_contractors_rating ON contractors(rating);
"""


def _norm_verified(v):
    if v in (True, "true", "True", 1, "1", "yes"):
        return 1
    if v in (False, "false", "False", 0, "0", "no"):
        return 0
    return None


def _json_col(v):
    if v is None:
        return None
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def write_sqlite(records, path=None):
    path = path or config.SQLITE_DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(SQL_SCHEMA)

    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows = []
    for rec in records:
        rows.append((
            rec.get("place_id"),
            rec.get("google_id"),
            rec.get("name"),
            rec.get("full_address"),
            rec.get("city"),
            rec.get("state"),
            rec.get("postal_code"),
            rec.get("phone"),
            rec.get("site"),
            rec.get("category"),
            _json_col(rec.get("subtypes")),
            rec.get("rating"),
            rec.get("reviews"),
            rec.get("latitude"),
            rec.get("longitude"),
            rec.get("business_status"),
            _norm_verified(rec.get("verified")),
            rec.get("photos_count"),
            _json_col(rec.get("working_hours")),
            _json_col(rec.get("trades")),
            _json_col(rec.get("queries_matched")),
            _json_col(rec.get("county_keys_seen")),
            now_iso,
            now_iso,
        ))
    con.executemany(
        """INSERT INTO contractors
           (place_id, google_id, name, full_address, city, state, zip, phone, site,
            category, subtypes, rating, reviews, latitude, longitude, business_status,
            verified, photos_count, working_hours, trades, queries_matched, county_keys,
            first_seen_at, last_seen_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    con.commit()
    con.close()
    return path


# ---------------------------------------------------------------------------
# Output — market summary
# ---------------------------------------------------------------------------

TRADE_NAME = {t["slug"]: t["name"] for t in config.TRADES}
COUNTY_NAME = {c["key"]: c["name"] for c in config.COUNTIES}


def _summary_rows(records):
    """Group records by (county_key, trade_slug). A record appears in every
    (county, trade) cell it matched — that's the desired denormalized view for
    a market summary."""
    cells = defaultdict(list)
    for rec in records:
        counties = rec.get("county_keys_seen") or []
        trades = rec.get("trades") or []
        for cty in counties:
            for tr in trades:
                cells[(cty, tr)].append(rec)
    return cells


def _band_counts(recs):
    n = len(recs)
    with_site = sum(1 for r in recs if r.get("site"))
    low_rev = sum(1 for r in recs if (r.get("reviews") or 0) < 10)
    unclaimed = sum(1 for r in recs if _norm_verified(r.get("verified")) != 1)
    ratings = [r.get("rating") for r in recs if isinstance(r.get("rating"), (int, float))]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    top3 = sorted(recs, key=lambda r: (r.get("reviews") or 0), reverse=True)[:3]
    return {
        "n": n,
        "with_site": with_site,
        "low_rev": low_rev,
        "unclaimed": unclaimed,
        "avg_rating": avg_rating,
        "top3": top3,
    }


def write_summary(records, path=None):
    path = path or config.SUMMARY_MD
    cells = _summary_rows(records)

    lines = [
        "# East Texas contractor discovery — market summary",
        "",
        f"**Total unique businesses (deduped):** {len(records)}",
        f"**Trades tracked:** {len(config.TRADES)}",
        f"**Counties tracked:** {', '.join(c['name'] for c in config.COUNTIES)}",
        "",
        "Every cell below counts a business in every (county × trade) it matched. "
        "A shop that showed up as both `plumber` and `general_contractor` is counted "
        "in both — that's usually a real signal, not noise.",
        "",
    ]

    for county in config.COUNTIES:
        lines.append(f"## {county['name']}")
        lines.append("")
        lines.append("| Trade | Businesses | With site | <10 reviews | Unclaimed | Avg ★ | Top 3 by reviews |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for trade in config.TRADES:
            recs = cells.get((county["key"], trade["slug"]), [])
            if not recs:
                lines.append(f"| {trade['name']} | 0 | — | — | — | — | _(none found)_ |")
                continue
            b = _band_counts(recs)
            top3_str = " · ".join(
                f"{r.get('name') or '—'} ({r.get('reviews') or 0})" for r in b["top3"]
            ) or "—"
            lines.append(
                f"| {trade['name']} | {b['n']} | {b['with_site']} | {b['low_rev']} | "
                f"{b['unclaimed']} | {b['avg_rating'] or '—'} | {top3_str} |"
            )
        lines.append("")

    # Cross-county rollup: gap headlines the product team can quote
    lines.append("## Cross-county gap headlines")
    lines.append("")
    total_by_trade = defaultdict(lambda: {"n": 0, "with_site": 0, "low_rev": 0, "unclaimed": 0})
    for trade in config.TRADES:
        for county in config.COUNTIES:
            recs = cells.get((county["key"], trade["slug"]), [])
            if not recs:
                continue
            b = _band_counts(recs)
            t = total_by_trade[trade["slug"]]
            t["n"] += b["n"]
            t["with_site"] += b["with_site"]
            t["low_rev"] += b["low_rev"]
            t["unclaimed"] += b["unclaimed"]

    lines.append("| Trade | Total | No-website % | <10 reviews % | Unclaimed % |")
    lines.append("|---|---:|---:|---:|---:|")
    for slug in [t["slug"] for t in config.TRADES]:
        t = total_by_trade.get(slug)
        if not t or t["n"] == 0:
            lines.append(f"| {TRADE_NAME[slug]} | 0 | — | — | — |")
            continue
        n = t["n"]
        no_site_pct   = round(100 * (n - t["with_site"]) / n)
        low_rev_pct   = round(100 * t["low_rev"] / n)
        unclaimed_pct = round(100 * t["unclaimed"] / n)
        lines.append(
            f"| {TRADE_NAME[slug]} | {n} | {no_site_pct}% | {low_rev_pct}% | {unclaimed_pct}% |"
        )

    lines.append("")
    lines.append(f"_Generated by discovery/dedupe.py._")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def build_all(raw_paths=None):
    raw_paths = raw_paths or list_raw_files()
    records = dedupe_records(raw_paths)
    write_csv(records)
    write_sqlite(records)
    write_summary(records)
    print(f"[dedupe] {len(records)} unique businesses from "
          f"{sum(1 for _ in raw_paths)} raw file(s)")
    return records


if __name__ == "__main__":
    build_all()
