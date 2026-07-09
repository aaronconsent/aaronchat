#!/usr/bin/env python3
"""Static site generator for stats.lakelivingston.aaron.chat.

The product: a business owner lands here, finds THEIR business, sees exactly
how they score against the local competition, and gets a ranked playbook of
what to fix first. "Here's the data, here's what to do with it."

Data flow:
    data/site.yaml + data/methodology.yaml + data/exclusions.yaml
    data/contractors_master.csv          (from discovery/output/, committed)
    data/trades/<key>.yaml               (optional, hand-authored insights)
                        │
                        ▼
    docs/index.html                      home — explainer + global search
    docs/<trade>/index.html              trade report — hero, playbook,
                                         leaderboard, searchable roster
    docs/biz/<slug>/index.html           per-business scorecard (the page
                                         you text a contractor)
    docs/methodology/index.html          how scoring works
    docs/search-index.json               client-side search index
    docs/social-quotables.json           feed for the aaron.chat social engine
    docs/style.css, CNAME, robots.txt, sitemap.xml

Run: python3 scripts/build.py
"""
import csv
import datetime as dt
import html
import json
import os
import re
import shutil
import statistics
import sys

import yaml


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(ROOT, "assets")
TEMPLATES = os.path.join(ROOT, "templates")
CSV_PATH = os.path.join(DATA, "contractors_master.csv")


# ---------- tiny helpers ----------

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def read(path):
    with open(path) as f:
        return f.read()


def write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(body)


def e(s):
    return html.escape("" if s is None else str(s), quote=True)


def _to_int(v):
    try: return int(float(v))
    except (TypeError, ValueError): return None


def _to_float(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def _to_bool_int(v):
    if v in (True, 1, "1", "True", "true", "yes", "Yes", "YES"): return 1
    return 0


def _load_json_col(v):
    if not v:
        return []
    try:
        d = json.loads(v)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def slugify(s):
    s = (s or "").lower()
    s = re.sub(r"['’]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "business"


def _norm_city(s):
    return (s or "").strip().lower().replace(".", "")


# ---------- exclusions ----------

def load_exclusions():
    path = os.path.join(DATA, "exclusions.yaml")
    if not os.path.exists(path):
        return None
    return load_yaml(path)


def is_excluded(row, ex):
    """True if this row is junk (retail / attraction / auto / etc.)."""
    if not ex:
        return False
    cat = (row.get("category") or "").strip()
    cat_l = cat.lower()
    name_l = (row.get("name") or "").lower()

    if cat in (ex.get("keep_exact") or []):
        return False
    for tok in ex.get("drop_category_contains") or []:
        if tok in cat_l:
            return True
    if cat in (ex.get("drop_category_exact") or []):
        return True
    for tok in ex.get("drop_name_contains") or []:
        if tok in name_l:
            return True
    if row.get("place_id") in set(ex.get("drop_place_ids") or []):
        return True
    return False


# ---------- CSV loader ----------

def load_contractors(site):
    """Return (by_trade_slug dict, all_businesses list). Filters junk +
    non-service-area rows, tags is_local, assigns unique URL slugs."""
    local_towns = {_norm_city(t) for t in
                   (site.get("service_area") or {}).get("towns") or []}
    valid_counties = set(site.get("county_keys") or [])
    ex = load_exclusions()

    by_trade = {}
    all_biz = {}
    slug_taken = {}
    dropped = 0

    if not os.path.exists(CSV_PATH):
        print(f"[warn] {CSV_PATH} missing — pages will render empty.")
        return {}, []

    with open(CSV_PATH) as f:
        for row in csv.DictReader(f):
            counties = set(_load_json_col(row.get("county_keys_seen")))
            if valid_counties and not (counties & valid_counties):
                continue
            if is_excluded(row, ex):
                dropped += 1
                continue
            trades = _load_json_col(row.get("trades"))
            pid = row.get("place_id")
            slug = slugify(row.get("name"))
            if slug in slug_taken and slug_taken[slug] != pid:
                slug = f"{slug}-{(pid or 'x')[-6:].lower()}"
            slug_taken[slug] = pid

            company = {
                "place_id":     pid,
                "slug":         slug,
                "name":         row.get("name"),
                "city":         row.get("city"),
                "state":        row.get("state"),
                "phone":        row.get("phone"),
                "site":         row.get("site"),
                "rating":       _to_float(row.get("rating")),
                "reviews":      _to_int(row.get("reviews")),
                "verified":     _to_bool_int(row.get("verified")),
                "photos_count": _to_int(row.get("photos_count")),
                "full_address": row.get("full_address"),
                "category":     row.get("category"),
                "trades":       trades,
                "county_keys":  sorted(counties),
                "is_local":     _norm_city(row.get("city")) in local_towns,
            }
            all_biz[pid] = company
            for slug_t in trades:
                by_trade.setdefault(slug_t, []).append(company)

    print(f"[load] {len(all_biz)} businesses kept, {dropped} junk rows excluded")
    return by_trade, list(all_biz.values())


# ---------- scoring: single source of truth ----------

FACTOR_META = [
    # key, label, how it's judged
    ("has_website",    "Working website",        "Yes/No — the `site` field on your Google listing"),
    ("gbp_claimed",    "Claimed Google profile", "Yes/No — listing verified by the owner"),
    ("reviews_volume", "Review volume",          "Scaled — full points at 50+ Google reviews"),
    ("avg_rating",     "Star rating",            "Full points at ★4.5+, partial at ★4.0+"),
    ("photos_count",   "Listing photos",         "Scaled — full points at 20+ photos"),
    ("phone_present",  "Phone on listing",       "Yes/No — tap-to-call number present"),
]


def score_breakdown(c, methodology):
    """Return (total:int, band:dict, factors:[{key,label,earned,max,ok,detail}])."""
    w = methodology["presence_score"]["weights"]
    rc = c.get("reviews") or 0
    ar = c.get("rating") or 0
    pc = c.get("photos_count") or 0
    has_site = bool((c.get("site") or "").strip())
    has_phone = bool((c.get("phone") or "").strip())
    claimed = c.get("verified") == 1

    factors = []

    def add(key, label, earned, mx, ok, detail):
        factors.append({"key": key, "label": label, "earned": round(earned, 1),
                        "max": mx, "ok": ok, "detail": detail})

    add("has_website", "Working website",
        w["has_website"] if has_site else 0, w["has_website"], has_site,
        "Website linked on your listing" if has_site else "No website on your Google listing")
    add("gbp_claimed", "Claimed Google profile",
        w["gbp_claimed"] if claimed else 0, w["gbp_claimed"], claimed,
        "Profile is claimed" if claimed else "Listing is unclaimed — anyone can suggest edits")
    rv = min(1.0, rc / 50.0) * w["reviews_volume"]
    add("reviews_volume", "Review volume", rv, w["reviews_volume"], rc >= 50,
        f"{rc} Google reviews" + ("" if rc >= 50 else f" — full points at 50"))
    if ar >= 4.5:
        ap, ok = w["avg_rating"], True
    elif ar >= 4.0:
        ap, ok = w["avg_rating"] * 0.6, False
    else:
        ap, ok = 0, False
    add("avg_rating", "Star rating", ap, w["avg_rating"], ok,
        f"★ {ar}" if ar else "No rating yet")
    pp = min(1.0, pc / 20.0) * w["photos_count"]
    add("photos_count", "Listing photos", pp, w["photos_count"], pc >= 20,
        f"{pc} photos" + ("" if pc >= 20 else " — full points at 20"))
    add("phone_present", "Phone on listing",
        w["phone_present"] if has_phone else 0, w["phone_present"], has_phone,
        "Tap-to-call number present" if has_phone else "No phone number on the listing")

    total = int(round(sum(f["earned"] for f in factors)))
    band = next(b for b in methodology["presence_score"]["bands"] if total >= b["min"])
    return total, band, factors


def compute_presence_score(c, methodology):
    total, band, _ = score_breakdown(c, methodology)
    return total, band


# ---------- fix playbook copy (per factor) ----------

def factor_fix(key, c, trade_ctx):
    """Actionable fix text for a factor the business is losing points on."""
    rc = c.get("reviews") or 0
    pc = c.get("photos_count") or 0
    ar = c.get("rating") or 0
    top3_med = trade_ctx.get("top3_median_reviews")
    if key == "has_website":
        return ("Get a real website — even one page",
                "A single page with your phone number, the towns you serve, and "
                "5 photos of finished work beats no site every time. Homeowners "
                "searching from a phone skip businesses without one. This is the "
                "single biggest point gain available to you.")
    if key == "gbp_claimed":
        return ("Claim your Google Business Profile (15 minutes, free)",
                "Go to google.com/business, search your business name, and claim "
                "it. Until you do, you can't respond to reviews, fix wrong hours, "
                "or add photos — and Google ranks unclaimed listings lower.")
    if key == "reviews_volume":
        need_full = max(0, 50 - rc)
        line = (f"You have {rc} review{'s' if rc != 1 else ''}. Getting to 50 earns "
                f"full points here.")
        if top3_med:
            line += (f" The local top-3 median is {top3_med:,} — that's the medal "
                     f"bar in your trade.")
        return ("Build a review engine",
                line + " The play: text every customer a direct review link the "
                "day you finish the job. Businesses that ask get reviews; "
                "businesses that don't, don't.")
    if key == "avg_rating":
        if ar and ar < 4.0:
            return ("Repair your rating",
                    f"At ★ {ar}, you're below the trust threshold most homeowners "
                    "filter by. Respond publicly to every negative review, fix the "
                    "recurring complaint, and bury old reviews with fresh 5-stars "
                    "from happy customers.")
        return ("Push your rating past ★ 4.5",
                f"You're at ★ {ar} — close to the ★ 4.5 line where full points "
                "kick in. A steady stream of new 5-star reviews moves the "
                "average faster than you'd think when volume is low.")
    if key == "photos_count":
        need = max(0, 20 - pc)
        return ("Post photos of real jobs",
                f"You have {pc} photo{'s' if pc != 1 else ''}; 20+ earns full "
                f"points. Before/after shots from your phone are enough — "
                "listings with fresh photos get dramatically more calls, and "
                "it costs nothing.")
    if key == "phone_present":
        return ("Add your phone number to the listing",
                "Your Google listing has no tap-to-call number. Most local "
                "service searches end in a phone call — right now yours can't.")
    return ("", "")


# ---------- template render ----------

def render_base(*, title, description, canonical, content, crumbs, site,
                methodology, jsonld, asset_root=".", built_at=None):
    tpl = read(os.path.join(TEMPLATES, "base.html"))
    ctx = {
        "title": e(title), "description": e(description),
        "canonical": canonical, "content": content, "crumbs": crumbs,
        "site": {k: (e(v) if isinstance(v, str) else v) for k, v in site.items()},
        "methodology": methodology,
        "jsonld": json.dumps(jsonld, separators=(",", ":")),
        "asset_root": asset_root,
        "built_at": built_at or dt.datetime.utcnow().strftime("%Y-%m-%d"),
    }
    for k, v in ctx.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                tpl = tpl.replace("{{ " + f"{k}.{sk}" + " }}", str(sv or ""))
        else:
            tpl = tpl.replace("{{ " + k + " }}", str(v))
            tpl = tpl.replace("{{ " + k + "|safe }}", str(v))
    return tpl


def render_crumbs(items):
    parts = []
    for i, (label, href) in enumerate(items):
        if href and i < len(items) - 1:
            parts.append(f'<a href="{e(href)}">{e(label)}</a>')
        else:
            parts.append(e(label))
    return f'<nav class="crumbs">{" &rsaquo; ".join(parts)}</nav>'


# ---------- home ----------

def render_home(site, trades_data, methodology, built_at):
    total_biz = len({c["place_id"] for t in trades_data for c in t["companies"]})
    total_local = len({c["place_id"] for t in trades_data for c in t["companies"] if c["is_local"]})

    cards = []
    for t in trades_data:
        top1 = t["top3"][0] if t["top3"] else None
        n1_med = int(statistics.median([c.get("reviews") or 0 for c in t["top3"]])) if t["top3"] else 0
        cards.append(f'''
          <a class="trade-card" href="/{e(t["meta"]["key"])}/">
            <div class="icon">{e(t["meta"]["icon"])}</div>
            <h2>{e(t["meta"]["name"])}</h2>
            <p class="tagline">{e(t["meta"]["tagline"])}</p>
            <div class="metrics">
              <div class="metric"><span class="n">{t["n_local"]}</span><span class="l">local</span></div>
              <div class="metric"><span class="n">{n1_med or "—"}</span><span class="l">#1 median</span></div>
              <div class="metric"><span class="n">{(top1 or {}).get("reviews") or "—"}</span><span class="l">top reviews</span></div>
            </div>
          </a>''')

    content = f'''
      <header class="masthead">
        <p class="eyebrow">Free competitive scorecards · updated weekly</p>
        <h1>How does your business stack up around Lake Livingston?</h1>
        <p class="tagline">We track {total_local:,} local service businesses across {len(trades_data)} trades
        in Polk, Walker, and San Jacinto counties — websites, reviews, ratings, claimed listings.
        Find your business, see your scorecard, and get the exact moves that put you in the top 3.</p>
        <div class="weekly-stamp">Built {built_at} · {total_biz:,} businesses tracked</div>
      </header>

      <section class="finder">
        <p class="section-title">Find your business</p>
        <input id="global-search" type="search" placeholder="Type your business name… (e.g. JNJ Plumbing)" autocomplete="off">
        <div id="global-results"></div>
      </section>

      <section>
        <p class="section-title">Or browse by trade <span class="count">{len(trades_data)} tracked</span></p>
        <div class="trade-grid">{"".join(cards)}</div>
      </section>

      <section class="how-it-works">
        <p class="section-title">How this works</p>
        <ol class="steps-list">
          <li><b>We collect public data weekly</b> — Google Business Profile signals for every service business that shows up in Polk, Walker, or San Jacinto county searches.</li>
          <li><b>Every business gets a Presence Score (0–100)</b> — website, claimed listing, review volume, rating, photos, phone. <a href="/methodology/">Full methodology here</a>.</li>
          <li><b>Your scorecard shows the gaps</b> — exactly which points you're leaving on the table, ranked by impact, with the specific fix for each.</li>
        </ol>
        <p class="attribution">{e(site["attribution"])}</p>
      </section>

      <script>
      (function() {{
        var input = document.getElementById("global-search");
        var out = document.getElementById("global-results");
        var index = null;
        function load(cb) {{
          if (index) return cb();
          fetch("/search-index.json").then(function(r){{return r.json();}})
            .then(function(d) {{ index = d; cb(); }});
        }}
        input.addEventListener("input", function() {{
          var q = input.value.trim().toLowerCase();
          if (q.length < 2) {{ out.innerHTML = ""; return; }}
          load(function() {{
            var hits = index.filter(function(b) {{
              return b.n.toLowerCase().indexOf(q) !== -1;
            }}).slice(0, 12);
            out.innerHTML = hits.length
              ? hits.map(function(b) {{
                  return '<a class="hit" href="/biz/' + b.s + '/"><b>' + b.n + '</b>' +
                         '<span>' + (b.c || "") + ' · score ' + b.p + '/100</span></a>';
                }}).join("")
              : '<p class="no-hit">No match — we may not have picked your business up yet. Email hello@aaron.chat and we\\'ll add you to the next weekly build.</p>';
          }});
        }});
      }})();
      </script>
    '''
    jsonld = {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": site["name"], "url": f"https://{site['domain']}/",
        "publisher": {"@type": "Organization", "name": site["publisher"],
                       "url": site["publisher_url"]},
        "inLanguage": "en-US",
    }
    return render_base(
        title=site["name"], description=site["tagline"], canonical="/",
        content=content, crumbs="",
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root=".", built_at=built_at)


# ---------- trade playbook (auto-generated from local stats) ----------

def build_trade_playbook(name, locals_ranked, top3):
    """Numbered 'here's the data → here's the move' steps from real stats."""
    if not locals_ranked:
        return ""
    n = len(locals_ranked)
    no_site = sum(1 for c in locals_ranked if not (c.get("site") or "").strip())
    unclaimed = sum(1 for c in locals_ranked if c.get("verified") != 1)
    low_rev = sum(1 for c in locals_ranked if (c.get("reviews") or 0) < 10)
    low_photos = sum(1 for c in locals_ranked if (c.get("photos_count") or 0) < 20)
    med_rev = int(statistics.median([(c.get("reviews") or 0) for c in locals_ranked]))
    top3_med = int(statistics.median([c.get("reviews") or 0 for c in top3])) if top3 else None

    steps = []
    if unclaimed:
        steps.append((
            f"Claim your Google Business Profile — {unclaimed} of {n} local shops haven't",
            f"That's {round(100*unclaimed/n)}% of your competition running unclaimed listings. "
            "Claiming yours takes 15 minutes, costs nothing, and immediately puts you ahead of "
            "every one of them in Google's eyes."))
    if no_site:
        steps.append((
            f"Get a website — {no_site} of {n} local shops don't have one",
            f"{round(100*no_site/n)}% of your local competitors are invisible to a homeowner "
            "comparing options on their phone. Even a one-pager with your phone, towns served, "
            "and job photos captures the customers they're losing."))
    steps.append((
        f"Out-review the median — the local median is just {med_rev} reviews",
        (f"Half your competitors have {med_rev} or fewer reviews. " if med_rev else "Most of your competitors have almost no reviews. ")
        + (f"The top-3 bar is {top3_med:,}. " if top3_med else "")
        + f"With {low_rev} of {n} shops under 10 reviews, a simple ask-every-customer habit "
        "moves you up the rankings faster in this trade than almost anywhere else."))
    if low_photos:
        steps.append((
            f"Post job photos — {low_photos} of {n} local shops have fewer than 20",
            "Google feeds photo-rich listings into Maps results more often. Phone photos of "
            "finished work, uploaded weekly, is a zero-cost ranking lever most of this market ignores."))
    steps.append((
        "Respond to every review — good and bad",
        "Response rate is a trust signal homeowners actually read, and almost nobody in this "
        "market does it consistently. Two sentences per review is enough."))

    items = "".join(
        f'<li><b>{e(h)}</b><span class="desc">{e(b)}</span></li>'
        for h, b in steps[:5])
    return f'''
      <section class="playbook">
        <p class="section-title">The playbook — what to do with this data</p>
        <ol class="playbook-list">{items}</ol>
      </section>
    '''


# ---------- trade page ----------

def render_trade(trade_meta, trade_yaml, companies_with_scores, methodology,
                 site, built_at):
    trade_yaml = trade_yaml or {}
    key = trade_meta["key"]
    name = trade_meta["name"]

    ranked = sorted(companies_with_scores,
                    key=lambda x: (-x["_score"], -(x.get("reviews") or 0)))
    min_medal = methodology["leaderboard"]["min_reviews_for_medal"]
    local_pool = [c for c in ranked if c.get("is_local")
                   and (c.get("reviews") or 0) >= min_medal]
    top3 = local_pool[:methodology["leaderboard"]["medal_count"]]
    locals_ranked = [c for c in ranked if c.get("is_local")]
    regionals_ranked = [c for c in ranked if not c.get("is_local")]

    # --- #1 bar ---
    n1_cfg = dict(trade_yaml.get("number_one_bar") or {})
    if top3:
        auto_reviews = int(statistics.median([c.get("reviews") or 0 for c in top3]))
        auto_rating = round(min(c.get("rating") or 0 for c in top3), 1)
        auto_web = all(bool((c.get("site") or "").strip()) for c in top3)
    else:
        auto_reviews = auto_rating = auto_web = None
    def resolve(k, auto_val):
        v = n1_cfg.get(k)
        return auto_val if v == "auto" else v
    n1 = {
        "reviews_median": resolve("reviews_median", auto_reviews),
        "avg_rating_min": resolve("avg_rating_min", auto_rating),
        "website_required": resolve("website_required", auto_web),
        "response_within_hours": n1_cfg.get("response_within_hours"),
        "same_day_service": n1_cfg.get("same_day_service"),
        "summary": n1_cfg.get("summary") or "",
    }
    hero_pieces = []
    if n1["reviews_median"] is not None:
        hero_pieces.append(f'<div class="stat"><span class="n">{n1["reviews_median"]}</span><span class="l">reviews (median)</span></div>')
    if n1["avg_rating_min"] is not None:
        hero_pieces.append(f'<div class="stat"><span class="n">{n1["avg_rating_min"]}</span><span class="l">★ min</span></div>')
    if n1["response_within_hours"] is not None:
        hero_pieces.append(f'<div class="stat"><span class="n">{n1["response_within_hours"]}</span><span class="l">hr response</span></div>')
    if n1["website_required"] is not None:
        hero_pieces.append(f'<div class="stat"><span class="n">{"YES" if n1["website_required"] else "no"}</span><span class="l">website req</span></div>')
    if n1["same_day_service"] is not None:
        hero_pieces.append(f'<div class="stat"><span class="n">{"YES" if n1["same_day_service"] else "no"}</span><span class="l">same-day</span></div>')
    summary_lines = n1["summary"].strip().split("\n") if n1["summary"] else []
    summary_first = summary_lines[0] if summary_lines else \
        f"Top-3 {name} in the Lake Livingston area median {n1['reviews_median'] or '—'} reviews at ★ {n1['avg_rating_min'] or '—'}+."
    summary_rest = " ".join(summary_lines[1:]) if len(summary_lines) > 1 else ""
    hero = f'''
      <section class="number-one-bar">
        <h2>What it takes to be #1</h2>
        <p class="headline">{e(summary_first)}</p>
        <div class="stat-row">{"".join(hero_pieces) or '<p style="color:#7d6a58;padding:8px">Not enough verified data yet.</p>'}</div>
        {("<p>" + e(summary_rest) + "</p>") if summary_rest else ""}
      </section>
    '''

    # --- market snapshot (locals) ---
    snapshot = ""
    subset = locals_ranked or ranked
    if subset:
        n = len(subset)
        with_site = sum(1 for c in subset if (c.get("site") or "").strip())
        low_rev = sum(1 for c in subset if (c.get("reviews") or 0) < 10)
        unclaimed = sum(1 for c in subset if c.get("verified") != 1)
        ratings = [c.get("rating") for c in subset if isinstance(c.get("rating"), (int, float))]
        avg = round(statistics.mean(ratings), 2) if ratings else "—"
        snapshot = f'''
          <p class="section-title">Market snapshot <span class="count">local businesses</span></p>
          <ul class="snapshot">
            <li><b>{n}</b> {e(name.lower())} tracked in the Lake Livingston service area</li>
            <li><b>{with_site}</b> ({round(100*with_site/n)}%) have a working website — {n-with_site} do not</li>
            <li><b>{low_rev}</b> ({round(100*low_rev/n)}%) have fewer than 10 reviews on Google</li>
            <li><b>{unclaimed}</b> ({round(100*unclaimed/n)}%) have not claimed their Google Business Profile</li>
            <li>Average rating across the roster: <b>★ {avg}</b></li>
          </ul>
        '''

    playbook = build_trade_playbook(name, locals_ranked, top3)

    # --- leaderboard ---
    leaderboard = ""
    if top3:
        medal_cards = []
        labels = ["Gold · #1", "Silver · #2", "Bronze · #3"]
        for i, c in enumerate(top3):
            quick = " · ".join(x for x in [
                f'{c.get("reviews")} reviews' if c.get("reviews") is not None else None,
                f'★ {c.get("rating")}' if c.get("rating") is not None else None,
                c.get("city")] if x)
            medal_cards.append(f'''
              <article class="medal-card rank-{i+1}">
                <span class="medal">{labels[i]}</span>
                <h3><a href="/biz/{e(c["slug"])}/">{e(c["name"])}</a></h3>
                <span class="score">Presence {c["_score"]}/100 · {e(quick)}</span>
                <p class="quick"><a href="/biz/{e(c["slug"])}/">Full scorecard →</a></p>
              </article>''')
        leaderboard = f'''
          <p class="section-title">Leaderboard <span class="count">top {len(top3)} local by presence score</span></p>
          <div class="leaderboard">{"".join(medal_cards)}</div>
        '''

    # --- searchable rosters ---
    def roster_table(title, count_label, subset):
        if not subset:
            return ""
        rows = []
        for i, c in enumerate(subset):
            band = c["_band"]
            site_cell = "✓" if c.get("site") else "—"
            rows.append(f'''
              <tr data-name="{e((c.get("name") or "").lower())}">
                <td class="num">{i+1}</td>
                <td class="name"><a href="/biz/{e(c["slug"])}/">{e(c["name"])}</a></td>
                <td>{e(c.get("city",""))}</td>
                <td class="num">{c["_score"]}</td>
                <td class="num">{c.get("reviews") if c.get("reviews") is not None else "—"}</td>
                <td class="num">{c.get("rating") if c.get("rating") is not None else "—"}</td>
                <td>{site_cell}</td>
                <td><span class="band" style="background:{band['color']}">{e(band['label'])}</span></td>
              </tr>''')
        return f'''
          <p class="section-title">{title} <span class="count">{count_label}</span></p>
          <div class="company-table-wrap">
            <table class="company-table searchable">
              <thead><tr>
                <th>#</th><th>Company</th><th>Town</th><th>Score</th>
                <th>Reviews</th><th>★</th><th>Site</th><th>Band</th>
              </tr></thead>
              <tbody>{"".join(rows)}</tbody>
            </table>
          </div>
        '''

    search_box = ""
    if locals_ranked or regionals_ranked:
        search_box = '''
          <div class="finder trade-finder">
            <input class="roster-search" type="search"
                   placeholder="Find your business in this list…" autocomplete="off">
          </div>
          <script>
          (function(){
            var inp = document.querySelector(".roster-search");
            if (!inp) return;
            inp.addEventListener("input", function() {
              var q = inp.value.trim().toLowerCase();
              document.querySelectorAll("table.searchable tbody tr").forEach(function(tr) {
                tr.style.display = (!q || tr.dataset.name.indexOf(q) !== -1) ? "" : "none";
              });
            });
          })();
          </script>
        '''

    roster = (roster_table("Local roster",
                            f"{len(locals_ranked)} in the service area — click any name for its scorecard",
                            locals_ranked) +
              roster_table("Regional roster",
                            f"{len(regionals_ranked)} serving the area from Houston / Conroe / elsewhere",
                            regionals_ranked))

    # --- insights ---
    insight_cards = []
    for ins in trade_yaml.get("insights") or []:
        klass = f"insight kind-{ins.get('kind','note')}"
        insight_cards.append(f'''
          <article class="{klass}">
            <span class="kind">{e(ins.get("kind","note"))}</span>
            <h4>{e(ins.get("headline",""))}</h4>
            <p>{e(ins.get("body",""))}</p>
          </article>''')
    insights = ""
    if insight_cards:
        insights = f'''
          <p class="section-title">This week's findings <span class="count">{len(insight_cards)}</span></p>
          <div class="insights">{"".join(insight_cards)}</div>
        '''

    service_area_note = (trade_yaml.get("service_area_note") or
                         f"Serving the Lake Livingston communities of Polk, Walker, and San Jacinto counties.")

    content = f'''
      <header class="masthead">
        <p class="eyebrow">Trade report · updated weekly</p>
        <h1>{e(name)} around Lake Livingston</h1>
        <p class="tagline">{e(service_area_note)}</p>
        <div class="weekly-stamp">Built {built_at} · {len(locals_ranked)} local · {len(regionals_ranked)} regional</div>
      </header>
      {hero}
      {snapshot}
      {playbook}
      {leaderboard}
      {search_box}
      {roster}
      {insights}
    '''
    jsonld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": f"{name} around Lake Livingston · Weekly report",
        "datePublished": built_at,
        "publisher": {"@type": "Organization", "name": site["publisher"],
                       "url": site["publisher_url"]},
        "url": f"https://{site['domain']}/{key}/",
    }
    crumbs = render_crumbs([("Home", "/"), (name, None)])
    return render_base(
        title=f"{name} around Lake Livingston",
        description=service_area_note,
        canonical=f"/{key}/",
        content=content, crumbs=crumbs,
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root="..", built_at=built_at)


# ---------- per-business scorecard ----------

def render_scorecard(c, methodology, site, trade_contexts, built_at):
    total, band, factors = score_breakdown(c, methodology)

    # factor table
    factor_rows = "".join(f'''
      <tr class="{'ok' if f['ok'] else 'miss'}">
        <td class="fl">{'✓' if f['ok'] else '✗'}</td>
        <td class="name">{e(f["label"])}</td>
        <td>{e(f["detail"])}</td>
        <td class="num">{f["earned"]:g} / {f["max"]}</td>
      </tr>''' for f in factors)

    # opportunities: biggest point gaps first
    primary_trade = None
    for t in c.get("trades") or []:
        if t in trade_contexts:
            primary_trade = trade_contexts[t]
            break
    tctx = primary_trade or {}
    opps = sorted([f for f in factors if f["max"] - f["earned"] >= 1],
                  key=lambda f: -(f["max"] - f["earned"]))
    opp_cards = []
    for i, f in enumerate(opps[:3], 1):
        gain = round(f["max"] - f["earned"])
        head, body = factor_fix(f["key"], c, tctx)
        opp_cards.append(f'''
          <article class="opp">
            <div class="opp-head">
              <span class="opp-rank">Fix #{i}</span>
              <span class="opp-gain">+{gain} pts</span>
            </div>
            <h4>{e(head)}</h4>
            <p>{e(body)}</p>
          </article>''')
    opportunities = ""
    if opp_cards:
        new_total = min(100, total + sum(round(f["max"] - f["earned"]) for f in opps[:3]))
        opportunities = f'''
          <p class="section-title">Your biggest opportunities <span class="count">ranked by point gain</span></p>
          <div class="opps">{"".join(opp_cards)}</div>
          <p class="opp-summary">Close these {len(opp_cards)} gaps and your score goes from
          <b>{total}</b> to roughly <b>{new_total}</b> — {'that’s "' + e(next(b for b in methodology["presence_score"]["bands"] if new_total >= b["min"])["label"]) + '" territory' if new_total > total else 'keep going'}.</p>
        '''
    else:
        opportunities = '''
          <p class="section-title">Your biggest opportunities</p>
          <p class="opp-summary">Full marks across the board — you're running this trade's
          best-practice playbook already. Defend the lead: keep review velocity up and
          photos fresh.</p>
        '''

    # benchmarks per trade
    bench_rows = []
    for t in c.get("trades") or []:
        ctx = trade_contexts.get(t)
        if not ctx:
            continue
        rank_str = "—"
        if c.get("is_local") and c["place_id"] in ctx["local_rank_by_pid"]:
            rank_str = f'#{ctx["local_rank_by_pid"][c["place_id"]]} of {ctx["n_local"]}'
        bench_rows.append(f'''
          <tr>
            <td class="name"><a href="/{e(ctx["key"])}/">{e(ctx["name"])}</a></td>
            <td class="num">{rank_str}</td>
            <td class="num">{ctx["median_reviews"]}</td>
            <td class="num">{ctx["top3_median_reviews"] or "—"}</td>
          </tr>''')
    benchmarks = ""
    if bench_rows:
        benchmarks = f'''
          <p class="section-title">Where you rank</p>
          <div class="company-table-wrap">
            <table class="company-table">
              <thead><tr><th>Trade</th><th>Your local rank</th><th>Local median reviews</th><th>Top-3 median</th></tr></thead>
              <tbody>{"".join(bench_rows)}</tbody>
            </table>
          </div>
        '''

    quick_facts = " · ".join(x for x in [
        e(c.get("city") or ""),
        f'★ {c.get("rating")}' if c.get("rating") else None,
        f'{c.get("reviews")} reviews' if c.get("reviews") is not None else None,
        e(c.get("category") or "")] if x)

    content = f'''
      <header class="masthead scorecard-head">
        <p class="eyebrow">Business scorecard · public data · updated weekly</p>
        <h1>{e(c["name"])}</h1>
        <p class="tagline">{quick_facts}</p>
        <div class="score-hero">
          <div class="score-dial" style="border-color:{band['color']}">
            <span class="score-n">{total}</span>
            <span class="score-d">/100</span>
          </div>
          <div class="score-band">
            <span class="band big" style="background:{band['color']}">{e(band['label'])}</span>
            <p>Presence Score — how findable and trustworthy this business looks
            to a homeowner searching Google right now. <a href="/methodology/">How scoring works →</a></p>
          </div>
        </div>
        <div class="weekly-stamp">Built {built_at}</div>
      </header>

      <p class="section-title">Score breakdown</p>
      <div class="company-table-wrap">
        <table class="company-table factor-table">
          <thead><tr><th></th><th>Factor</th><th>What we found</th><th>Points</th></tr></thead>
          <tbody>{factor_rows}</tbody>
        </table>
      </div>

      {opportunities}
      {benchmarks}

      <div class="scorecard-cta">
        <p>This scorecard is built from public Google data and refreshed weekly.
        Something wrong? Email <a href="mailto:hello@aaron.chat">hello@aaron.chat</a> and we'll fix it in the next build.</p>
        <p class="cta-line">Want these gaps closed for you? That's literally what we do —
        <a href="{e(site["publisher_url"])}">Hey Aaron! Marketing</a>.</p>
      </div>
    '''
    jsonld = {
        "@context": "https://schema.org", "@type": "WebPage",
        "name": f"{c['name']} — Lake Livingston service pro scorecard",
        "url": f"https://{site['domain']}/biz/{c['slug']}/",
        "datePublished": built_at,
        "about": {"@type": "LocalBusiness", "name": c["name"],
                   "address": c.get("full_address") or c.get("city") or ""},
        "publisher": {"@type": "Organization", "name": site["publisher"],
                       "url": site["publisher_url"]},
    }
    first_trade = (c.get("trades") or [None])[0]
    crumb_trade = None
    for t in c.get("trades") or []:
        if t in trade_contexts:
            crumb_trade = trade_contexts[t]
            break
    crumbs = render_crumbs(
        [("Home", "/")] +
        ([(crumb_trade["name"], f"/{crumb_trade['key']}/")] if crumb_trade else []) +
        [(c["name"], None)])
    return render_base(
        title=f"{c['name']} scorecard",
        description=f"How {c['name']} stacks up against Lake Livingston-area competitors — presence score, review benchmarks, and the exact fixes that move the ranking.",
        canonical=f"/biz/{c['slug']}/",
        content=content, crumbs=crumbs,
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root="../..", built_at=built_at)


# ---------- methodology page ----------

def render_methodology(site, methodology, built_at):
    w = methodology["presence_score"]["weights"]
    weight_rows = "".join(f'''
      <tr>
        <td class="name">{e(label)}</td>
        <td class="num">{w[key]}</td>
        <td>{e(how)}</td>
      </tr>''' for key, label, how in FACTOR_META)
    band_rows = "".join(f'''
      <tr>
        <td><span class="band" style="background:{b["color"]}">{e(b["label"])}</span></td>
        <td class="num">{b["min"]}+</td>
      </tr>''' for b in methodology["presence_score"]["bands"])
    excluded = "".join(f"<li>{e(x)}</li>" for x in methodology.get("excluded") or [])

    content = f'''
      <header class="masthead">
        <p class="eyebrow">Methodology · v{e(methodology["version"])}</p>
        <h1>How the Presence Score works</h1>
        <p class="tagline">Every business gets a 0–100 score from six public signals on its
        Google Business Profile. Same formula for everyone — including businesses we work with.</p>
        <div class="weekly-stamp">Built {built_at}</div>
      </header>

      <p class="section-title">The six factors</p>
      <div class="company-table-wrap">
        <table class="company-table">
          <thead><tr><th>Factor</th><th>Max points</th><th>How it's judged</th></tr></thead>
          <tbody>{weight_rows}</tbody>
        </table>
      </div>

      <p class="section-title">Score bands</p>
      <div class="company-table-wrap">
        <table class="company-table">
          <thead><tr><th>Band</th><th>Score</th></tr></thead>
          <tbody>{band_rows}</tbody>
        </table>
      </div>

      <p class="section-title">Where the data comes from</p>
      <p>Business data is captured weekly from Google Maps via the Outscraper API across
      Polk, Walker, and San Jacinto counties, deduplicated by Google place ID, and filtered
      to service businesses (we exclude retail stores, attractions, and other non-service
      listings that Google's category matching sometimes surfaces).</p>

      <p class="section-title">What we deliberately don't track</p>
      <ul class="snapshot">{excluded}</ul>

      <p class="section-title">Local vs regional</p>
      <p>The leaderboards and "what it takes to be #1" numbers only count businesses based
      in the Lake Livingston service-area towns. Houston- and Conroe-based shops that serve
      the area appear in the regional roster but don't hold medals — a Lake Livingston
      shop shouldn't be benchmarked against an 11,000-review metro operation.</p>
    '''
    jsonld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": "How the Lake Livingston Presence Score works",
        "datePublished": built_at,
        "publisher": {"@type": "Organization", "name": site["publisher"],
                       "url": site["publisher_url"]},
        "url": f"https://{site['domain']}/methodology/",
    }
    crumbs = render_crumbs([("Home", "/"), ("Methodology", None)])
    return render_base(
        title="Methodology — how the Presence Score works",
        description="The 0-100 scoring formula behind every Lake Livingston service-pro scorecard.",
        canonical="/methodology/",
        content=content, crumbs=crumbs,
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root="..", built_at=built_at)


# ---------- social feed ----------

def build_social_feed(trades_data, site):
    quotables = []
    for t in trades_data:
        for ins in (t.get("yaml") or {}).get("insights") or []:
            if ins.get("social_ready"):
                quotables.append({
                    "trade": t["meta"]["key"],
                    "kind": ins.get("kind"),
                    "headline": ins.get("headline"),
                    "body": (ins.get("body") or "").strip(),
                    "link": f"https://{site['domain']}/{t['meta']['key']}/",
                })
    return {
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "site": site["domain"],
        "quotables": quotables,
    }


# ---------- main ----------

def main():
    site = load_yaml(os.path.join(DATA, "site.yaml"))
    methodology = load_yaml(os.path.join(DATA, "methodology.yaml"))
    built_at = dt.datetime.utcnow().strftime("%Y-%m-%d")
    contractors_by_slug, all_biz = load_contractors(site)

    trades_data = []
    trade_contexts = {}
    for t in site["trades"]:
        yaml_path = os.path.join(DATA, "trades", f"{t['key']}.yaml")
        trade_yaml = load_yaml(yaml_path) if os.path.exists(yaml_path) else None
        companies = contractors_by_slug.get(t["discovery_slug"], [])
        scored = []
        for c in companies:
            score, band = compute_presence_score(c, methodology)
            scored.append({**c, "_score": score, "_band": band})
        scored.sort(key=lambda x: (-x["_score"], -(x.get("reviews") or 0)))
        min_medal = methodology["leaderboard"]["min_reviews_for_medal"]
        locals_ranked = [c for c in scored if c.get("is_local")]
        top3 = [c for c in locals_ranked if (c.get("reviews") or 0) >= min_medal][:3]

        trades_data.append({
            "meta": t, "yaml": trade_yaml, "companies": scored, "top3": top3,
            "n_local": len(locals_ranked),
            "n_regional": len(scored) - len(locals_ranked),
        })
        trade_contexts[t["discovery_slug"]] = {
            "key": t["key"], "name": t["name"],
            "n_local": len(locals_ranked),
            "median_reviews": int(statistics.median([(c.get("reviews") or 0) for c in locals_ranked])) if locals_ranked else 0,
            "top3_median_reviews": int(statistics.median([c.get("reviews") or 0 for c in top3])) if top3 else None,
            "local_rank_by_pid": {c["place_id"]: i + 1 for i, c in enumerate(locals_ranked)},
        }

    # Clean docs/
    if os.path.exists(DOCS):
        for name in os.listdir(DOCS):
            full = os.path.join(DOCS, name)
            if os.path.isdir(full): shutil.rmtree(full)
            else: os.remove(full)
    os.makedirs(DOCS, exist_ok=True)

    # Pages
    write(os.path.join(DOCS, "index.html"),
          render_home(site, trades_data, methodology, built_at))
    for t in trades_data:
        write(os.path.join(DOCS, t["meta"]["key"], "index.html"),
              render_trade(t["meta"], t["yaml"], t["companies"], methodology,
                            site, built_at))
    write(os.path.join(DOCS, "methodology", "index.html"),
          render_methodology(site, methodology, built_at))

    # Scorecards — one per unique business appearing in any roster
    seen = set()
    n_cards = 0
    for t in trades_data:
        for c in t["companies"]:
            if c["place_id"] in seen:
                continue
            seen.add(c["place_id"])
            write(os.path.join(DOCS, "biz", c["slug"], "index.html"),
                  render_scorecard(c, methodology, site, trade_contexts, built_at))
            n_cards += 1

    # Search index (name, city, slug, score)
    index = []
    seen2 = set()
    for t in trades_data:
        for c in t["companies"]:
            if c["place_id"] in seen2:
                continue
            seen2.add(c["place_id"])
            index.append({"n": c["name"], "c": c.get("city") or "",
                          "s": c["slug"], "p": c["_score"]})
    index.sort(key=lambda x: x["n"] or "")
    write(os.path.join(DOCS, "search-index.json"),
          json.dumps(index, separators=(",", ":"), ensure_ascii=False))

    # Assets + plumbing
    shutil.copy(os.path.join(ASSETS, "style.css"), os.path.join(DOCS, "style.css"))
    write(os.path.join(DOCS, "CNAME"), site["domain"] + "\n")
    urls = ([f"https://{site['domain']}/",
             f"https://{site['domain']}/methodology/"] +
            [f"https://{site['domain']}/{t['meta']['key']}/" for t in trades_data] +
            [f"https://{site['domain']}/biz/{b['s']}/" for b in index])
    write(os.path.join(DOCS, "robots.txt"),
          f"User-agent: *\nAllow: /\nSitemap: https://{site['domain']}/sitemap.xml\n")
    write(os.path.join(DOCS, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{u}</loc><lastmod>{built_at}</lastmod></url>\n" for u in urls) +
          '</urlset>\n')
    write(os.path.join(DOCS, "social-quotables.json"),
          json.dumps(build_social_feed(trades_data, site), indent=2))

    print(f"[build] {len(trades_data)} trade pages + {n_cards} scorecards "
          f"+ home + methodology → {DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
