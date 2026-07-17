"""Static config for the East Texas contractor discovery pipeline.

Everything the operator might tune (geo, trades, rate limits, output paths)
lives here so scrape.py + dedupe.py stay code-only.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
RAW_DIR = os.path.join(OUT_DIR, "raw")           # per-task JSON responses
TASK_LOG = os.path.join(OUT_DIR, "task_log.jsonl")
MASTER_CSV = os.path.join(OUT_DIR, "contractors_master.csv")
SQLITE_DB = os.path.join(OUT_DIR, "contractors.db")
SUMMARY_MD = os.path.join(OUT_DIR, "summary.md")


# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------
# Both county- and city-level queries — dedupe handles the overlap.
COUNTIES = [
    {"key": "polk",        "name": "Polk County, TX",        "geo": "Polk County TX"},
    {"key": "walker",      "name": "Walker County, TX",      "geo": "Walker County TX"},
    {"key": "san_jacinto", "name": "San Jacinto County, TX", "geo": "San Jacinto County TX"},
    # Expansion corridor (approved 2026-07): Montgomery-corridor + Trinity county
    {"key": "trinity",     "name": "Trinity County, TX",     "geo": "Trinity County TX"},
]

CITIES = [
    # Polk County
    {"key": "livingston",   "county_key": "polk",        "geo": "Livingston TX"},
    {"key": "onalaska",     "county_key": "polk",        "geo": "Onalaska TX"},
    {"key": "corrigan",     "county_key": "polk",        "geo": "Corrigan TX"},
    {"key": "goodrich",     "county_key": "polk",        "geo": "Goodrich TX"},
    {"key": "leggett",      "county_key": "polk",        "geo": "Leggett TX"},
    # Walker County
    {"key": "huntsville",   "county_key": "walker",      "geo": "Huntsville TX"},
    {"key": "new_waverly",  "county_key": "walker",      "geo": "New Waverly TX"},
    {"key": "riverside",    "county_key": "walker",      "geo": "Riverside TX"},
    # San Jacinto County
    {"key": "coldspring",   "county_key": "san_jacinto", "geo": "Coldspring TX"},
    {"key": "shepherd",     "county_key": "san_jacinto", "geo": "Shepherd TX"},
    {"key": "point_blank",  "county_key": "san_jacinto", "geo": "Point Blank TX"},
    {"key": "oakhurst",     "county_key": "san_jacinto", "geo": "Oakhurst TX"},
    # Expansion corridor (approved 2026-07). Montgomery-corridor towns keyed to
    # a synthetic 'corridor' county for reporting; Trinity towns to trinity.
    {"key": "conroe",       "county_key": "corridor",    "geo": "Conroe TX"},
    {"key": "willis",       "county_key": "corridor",    "geo": "Willis TX"},
    {"key": "montgomery",   "county_key": "corridor",    "geo": "Montgomery TX"},
    {"key": "cleveland",    "county_key": "corridor",    "geo": "Cleveland TX"},
    {"key": "trinity_town", "county_key": "trinity",     "geo": "Trinity TX"},
    {"key": "groveton",     "county_key": "trinity",     "geo": "Groveton TX"},
]


def geo_terms():
    """Every geo string we search, keyed by (level, key, county_key)."""
    out = []
    for c in COUNTIES:
        out.append({"level": "county", "key": c["key"], "county_key": c["key"], "geo": c["geo"]})
    for c in CITIES:
        out.append({"level": "city", "key": c["key"], "county_key": c["county_key"], "geo": c["geo"]})
    return out


# ---------------------------------------------------------------------------
# Trades — 17 total. Each maps to one or more Google Maps search terms.
# The slug is what we store on the record so the trades[] column stays stable
# even if we tweak the search string later.
# ---------------------------------------------------------------------------
TRADES = [
    {"slug": "plumber",           "name": "Plumber",             "terms": ["plumber"]},
    {"slug": "roofing",           "name": "Roofing Contractor",  "terms": ["roofing contractor"]},
    {"slug": "hvac",              "name": "HVAC + AC Service",   "terms": ["HVAC contractor", "air conditioning repair"]},
    {"slug": "electrician",       "name": "Electrician",         "terms": ["electrician"]},
    {"slug": "garage_door",       "name": "Garage Door Repair",  "terms": ["garage door repair"]},
    {"slug": "pest_control",      "name": "Pest Control",        "terms": ["pest control"]},
    {"slug": "lawn_care",         "name": "Lawn Care / Landscape","terms": ["lawn care", "landscaping"]},
    {"slug": "tree_service",      "name": "Tree Service",        "terms": ["tree service"]},
    {"slug": "fencing",           "name": "Fence Contractor",    "terms": ["fence contractor"]},
    {"slug": "concrete",          "name": "Concrete Contractor", "terms": ["concrete contractor"]},
    {"slug": "painter",           "name": "Painter",             "terms": ["painter"]},
    {"slug": "pool_service",      "name": "Pool Service",        "terms": ["pool service", "pool cleaning"]},
    {"slug": "septic",            "name": "Septic System Svc",   "terms": ["septic system service"]},
    {"slug": "gutter",            "name": "Gutter Service",      "terms": ["gutter service"]},
    {"slug": "pressure_washing",  "name": "Pressure Washing",    "terms": ["pressure washing"]},
    {"slug": "appliance_repair",  "name": "Appliance Repair",    "terms": ["appliance repair"]},
    {"slug": "general_contractor","name": "General Contractor",  "terms": ["general contractor", "remodeling"]},
]


# ---------------------------------------------------------------------------
# Scrape params
# ---------------------------------------------------------------------------
LIMIT_PER_QUERY = 100
REGION = "US"
LANGUAGE = "en"

QUERIES_PER_TASK = 12                    # Outscraper allows a list of queries per task
POLL_INTERVAL_SEC = 15
POLL_MAX_TRIES = 80                      # 80 × 15s = 20 min per task
SUBMIT_DELAY_SEC = 5                     # sleep between task submissions

# Cost estimate — Outscraper google_maps_search bills per returned record.
COST_PER_1000_RECORDS_USD = 3.0
EXPECTED_RECORDS_PER_QUERY_RURAL = 15    # rural counties; most queries << 100


# ---------------------------------------------------------------------------
# Fields to keep from every Outscraper business record.
# ---------------------------------------------------------------------------
KEEP_FIELDS = [
    "place_id", "google_id", "name", "full_address", "city", "state", "postal_code",
    "phone", "site", "category", "subtypes", "rating", "reviews",
    "latitude", "longitude", "business_status", "verified", "photos_count",
    "working_hours",
]


def build_queries():
    """Return a list of query dicts:
       {"query": str, "trade_slug": str, "trade_term": str, "geo_level": str,
        "geo_key": str, "county_key": str}
    """
    queries = []
    geos = geo_terms()
    for trade in TRADES:
        for term in trade["terms"]:
            for g in geos:
                queries.append({
                    "query": f"{term} in {g['geo']}",
                    "trade_slug": trade["slug"],
                    "trade_term": term,
                    "geo_level": g["level"],
                    "geo_key": g["key"],
                    "county_key": g["county_key"],
                })
    return queries


def cost_estimate(n_queries):
    est_records = n_queries * EXPECTED_RECORDS_PER_QUERY_RURAL
    est_usd = est_records / 1000.0 * COST_PER_1000_RECORDS_USD
    return est_records, est_usd
