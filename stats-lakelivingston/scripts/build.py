#!/usr/bin/env python3
"""Static site generator for stats.lakelivingston.aaron.chat.

Data flow:
    data/site.yaml + data/methodology.yaml
    data/contractors_master.csv          (from discovery/output/, committed)
    data/trades/<key>.yaml               (optional, hand-authored insights)
                        │
                        ▼
                    docs/*.html + docs/style.css + docs/CNAME
                    docs/social-quotables.json
                    docs/robots.txt + docs/sitemap.xml

Run: python3 scripts/build.py
"""
import csv
import datetime as dt
import html
import json
import os
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


# ---------- helpers ----------

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
    """CSV round-trips write True/False as strings; also handles 0/1/'yes'/'no'."""
    if v in (True, 1, "1", "True", "true", "yes", "Yes", "YES"): return 1
    if v in (False, 0, "0", "False", "false", "no", "No", "NO", "", None): return 0
    return 0


def _load_json_col(v):
    """CSV JSON columns come in as strings like '["polk","walker"]'."""
    if v is None or v == "":
        return []
    try:
        d = json.loads(v)
        return d if isinstance(d, list) else []
    except Exception:
        return []


# ---------- CSV loader ----------

def _norm_city(s):
    return (s or "").strip().lower().replace(".", "")


def load_contractors(site):
    """Return {discovery_slug: [company_dict, ...]} filtered to site.county_keys.

    Adds `is_local` (True if the business's city matches one of the towns in
    site.service_area.towns). Locals are what drive the leaderboard + #1 bar;
    regionals stay in the roster with a badge so users know these shops
    serve the area from Houston/Conroe/etc.
    """
    local_towns = {_norm_city(t) for t in
                   (site.get("service_area") or {}).get("towns") or []}
    if not os.path.exists(CSV_PATH):
        print(f"[warn] {CSV_PATH} not found — trade pages will render empty. "
              f"Copy discovery/output/contractors_master.csv into data/.")
        return {}
    valid_counties = set(site.get("county_keys") or [])
    by_trade = {}
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            counties = set(_load_json_col(row.get("county_keys_seen")))
            if valid_counties and not (counties & valid_counties):
                continue
            trades = _load_json_col(row.get("trades"))
            company = {
                "place_id":       row.get("place_id"),
                "name":           row.get("name"),
                "city":           row.get("city"),
                "state":          row.get("state"),
                "phone":          row.get("phone"),
                "site":           row.get("site"),
                "rating":         _to_float(row.get("rating")),
                "reviews":        _to_int(row.get("reviews")),
                "verified":       _to_bool_int(row.get("verified")),
                "photos_count":   _to_int(row.get("photos_count")),
                "full_address":   row.get("full_address"),
                "latitude":       _to_float(row.get("latitude")),
                "longitude":      _to_float(row.get("longitude")),
                "trades":         trades,
                "county_keys":    sorted(counties),
                "is_local":       _norm_city(row.get("city")) in local_towns,
            }
            for slug in trades:
                by_trade.setdefault(slug, []).append(company)
    return by_trade


# ---------- score computation ----------

def compute_presence_score(c, methodology):
    """Rebalanced weights (v0.2) using Outscraper-only fields. Sum = 100."""
    w = methodology["presence_score"]["weights"]
    s = 0.0
    if (c.get("site") or "").strip():   s += w["has_website"]
    if c.get("verified") == 1:          s += w["gbp_claimed"]
    rc = c.get("reviews") or 0
    s += min(1.0, rc / 50.0) * w["reviews_volume"]
    ar = c.get("rating") or 0
    if ar >= 4.5:    s += w["avg_rating"]
    elif ar >= 4.0:  s += w["avg_rating"] * 0.6
    pc = c.get("photos_count") or 0
    s += min(1.0, pc / 20.0) * w["photos_count"]
    if (c.get("phone") or "").strip():  s += w["phone_present"]
    score = int(round(s))
    band = next(b for b in methodology["presence_score"]["bands"] if score >= b["min"])
    return score, band


# ---------- #1 bar auto-compute ----------

def _resolve_number_one_bar(configured, top3, all_companies):
    """Return the final number_one_bar dict, filling `auto` values from top-3."""
    cfg = dict(configured or {})
    if top3:
        auto_reviews = int(statistics.median([c.get("reviews") or 0 for c in top3]))
        auto_rating = round(min(c.get("rating") or 0 for c in top3), 1)
        auto_web = all(bool((c.get("site") or "").strip()) for c in top3)
    else:
        auto_reviews = auto_rating = auto_web = None

    def resolve(key, auto_val):
        v = cfg.get(key)
        return auto_val if v == "auto" else v

    return {
        "reviews_median":       resolve("reviews_median", auto_reviews),
        "avg_rating_min":       resolve("avg_rating_min", auto_rating),
        "website_required":     resolve("website_required", auto_web),
        "response_within_hours": cfg.get("response_within_hours"),
        "same_day_service":     cfg.get("same_day_service"),
        "summary":              cfg.get("summary") or "",
    }


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
    """trades_data = list of {trade_meta, companies, top3}."""
    total_verified = sum(len(t["companies"]) for t in trades_data)

    cards = []
    for t in trades_data:
        top1 = t["top3"][0] if t["top3"] else None
        top1_reviews = (top1 or {}).get("reviews") or 0
        n1_reviews_median = 0
        if t["top3"]:
            n1_reviews_median = int(statistics.median([c.get("reviews") or 0 for c in t["top3"]]))
        cards.append(f'''
          <a class="trade-card" href="/{e(t["meta"]["key"])}/">
            <div class="icon">{e(t["meta"]["icon"])}</div>
            <h2>{e(t["meta"]["name"])}</h2>
            <p class="tagline">{e(t["meta"]["tagline"])}</p>
            <div class="metrics">
              <div class="metric"><span class="n">{t["n_local"]}</span><span class="l">local</span></div>
              <div class="metric"><span class="n">{n1_reviews_median or "—"}</span><span class="l">#1 median</span></div>
              <div class="metric"><span class="n">{top1_reviews or "—"}</span><span class="l">top reviews</span></div>
            </div>
          </a>''')

    content = f'''
      <header class="masthead">
        <p class="eyebrow">Weekly research report</p>
        <h1>{e(site["name"])}</h1>
        <p class="tagline">{e(site["tagline"])}</p>
        <div class="weekly-stamp">Built {built_at} · {total_verified:,} businesses tracked · {len(trades_data)} trades</div>
      </header>
      <section>
        <p class="section-title">Trades tracked <span class="count">{len(trades_data)} live</span></p>
        <div class="trade-grid">{"".join(cards)}</div>
      </section>
      <section>
        <p class="section-title">How this is put together</p>
        <p>{e(site["attribution"])}</p>
      </section>
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
        asset_root=".", built_at=built_at,
    )


# ---------- trade page ----------

def render_trade(trade_meta, trade_yaml, companies_with_scores, methodology,
                 site, built_at):
    """Render one trade page. trade_yaml can be None (all defaults)."""
    trade_yaml = trade_yaml or {}
    key = trade_meta["key"]
    name = trade_meta["name"]

    # Rank
    ranked = sorted(companies_with_scores,
                    key=lambda x: (-x["_score"], -(x.get("reviews") or 0)))
    min_medal_reviews = methodology["leaderboard"]["min_reviews_for_medal"]
    # Medal only businesses IN the service area — regionals don't count as
    # "the top plumber in Lake Livingston" even if they surface in search.
    local_pool = [c for c in ranked if c.get("is_local")
                   and (c.get("reviews") or 0) >= min_medal_reviews]
    top3 = local_pool[:methodology["leaderboard"]["medal_count"]]
    locals_ranked = [c for c in ranked if c.get("is_local")]
    regionals_ranked = [c for c in ranked if not c.get("is_local")]

    # #1 bar
    n1 = _resolve_number_one_bar(trade_yaml.get("number_one_bar"), top3, ranked)
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

    summary_first_line = n1["summary"].strip().split("\n")[0] if n1["summary"] else \
        f"Top-3 {name} in the Lake Livingston area median {n1['reviews_median'] or '—'} reviews at ★ {n1['avg_rating_min'] or '—'}+."
    summary_rest = " ".join(n1["summary"].strip().split("\n")[1:]) if n1["summary"] else ""

    hero = f'''
      <section class="number-one-bar">
        <h2>What it takes to be #1</h2>
        <p class="headline">{e(summary_first_line)}</p>
        <div class="stat-row">{"".join(hero_pieces) or '<p style="color:#7d6a58;padding:8px">Not enough top-3 data yet — verify more rows.</p>'}</div>
        {("<p>" + e(summary_rest) + "</p>") if summary_rest else ""}
      </section>
    '''

    # Leaderboard
    leaderboard = ""
    if top3:
        medal_cards = []
        medal_labels = ["Gold · #1", "Silver · #2", "Bronze · #3"]
        for i, c in enumerate(top3):
            score = c["_score"]
            quick_parts = []
            if c.get("reviews") is not None:
                quick_parts.append(f'{c["reviews"]} reviews')
            if c.get("rating") is not None:
                quick_parts.append(f'★ {c["rating"]}')
            if c.get("city"):
                quick_parts.append(c["city"])
            quick = " · ".join(quick_parts)
            site_line = ""
            if c.get("site"):
                site_line = f'<a href="{e(c["site"])}" target="_blank" rel="noopener nofollow">Website ↗</a>'
            elif c.get("phone"):
                site_line = f'<span class="no-site">No website — phone {e(c["phone"])}</span>'
            medal_cards.append(f'''
              <article class="medal-card rank-{i+1}">
                <span class="medal">{medal_labels[i]}</span>
                <h3>{e(c["name"])}</h3>
                <span class="score">Presence {score}/100 · {e(quick)}</span>
                <p class="quick">{site_line}</p>
              </article>''')
        leaderboard = f'''
          <p class="section-title">Leaderboard <span class="count">Top {len(top3)} by presence score</span></p>
          <div class="leaderboard">{"".join(medal_cards)}</div>
        '''

    # Roster — two tables: locals first, regionals second
    def _roster_table(section_title, section_count, subset):
        if not subset:
            return ""
        rows = []
        for i, c in enumerate(subset):
            band = c["_band"]
            site_cell = f'<a href="{e(c["site"])}" target="_blank" rel="noopener nofollow">✓</a>' if c.get("site") else "—"
            rows.append(f'''
              <tr>
                <td class="num">{i+1}</td>
                <td class="name">{e(c["name"])}</td>
                <td>{e(c.get("city",""))}</td>
                <td class="num">{c["_score"]}</td>
                <td class="num">{c.get("reviews") if c.get("reviews") is not None else "—"}</td>
                <td class="num">{c.get("rating") if c.get("rating") is not None else "—"}</td>
                <td>{site_cell}</td>
                <td><span class="band" style="background:{band['color']}">{e(band['label'])}</span></td>
              </tr>''')
        return f'''
          <p class="section-title">{section_title} <span class="count">{section_count}</span></p>
          <div class="company-table-wrap">
            <table class="company-table">
              <thead><tr>
                <th>#</th><th>Company</th><th>Town</th><th>Score</th>
                <th>Reviews</th><th>★</th><th>Site</th><th>Band</th>
              </tr></thead>
              <tbody>{"".join(rows)}</tbody>
            </table>
          </div>
        '''
    roster = (
        _roster_table("Local roster", f"{len(locals_ranked)} in the Lake Livingston service area", locals_ranked) +
        _roster_table("Regional roster", f"{len(regionals_ranked)} shops serving the area from Houston / Conroe / elsewhere", regionals_ranked)
    )

    # Market snapshot mini-table — LOCAL businesses only (the real market gap)
    snapshot = ""
    subset = locals_ranked if locals_ranked else ranked
    if subset:
        n = len(subset)
        with_site = sum(1 for c in subset if (c.get("site") or "").strip())
        low_rev = sum(1 for c in subset if (c.get("reviews") or 0) < 10)
        unclaimed = sum(1 for c in subset if c.get("verified") != 1)
        avg = round(statistics.mean(c.get("rating") for c in subset
                                     if isinstance(c.get("rating"), (int, float))), 2) \
              if any(isinstance(c.get("rating"), (int, float)) for c in subset) else "—"
        scope = "local" if locals_ranked else "surfaced"
        snapshot = f'''
          <p class="section-title">Market snapshot <span class="count">{scope} businesses</span></p>
          <ul class="snapshot">
            <li><b>{n}</b> {name.lower()} tracked in the Lake Livingston service area</li>
            <li><b>{with_site}</b> ({round(100*with_site/n)}%) have a working website — {n-with_site} do not</li>
            <li><b>{low_rev}</b> ({round(100*low_rev/n)}%) have fewer than 10 reviews on Google</li>
            <li><b>{unclaimed}</b> ({round(100*unclaimed/n)}%) have not claimed their Google Business Profile</li>
            <li>Average rating across the roster: <b>★ {avg}</b></li>
          </ul>
        '''

    # Insights
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
                         f"Serving {', '.join(site.get('service_area',{}).get('towns',[])[:5])} and the surrounding lake communities.")

    content = f'''
      <header class="masthead">
        <p class="eyebrow">Trade report · updated weekly</p>
        <h1>{e(name)} around Lake Livingston</h1>
        <p class="tagline">{e(service_area_note)}</p>
        <div class="weekly-stamp">Built {built_at} · {len(locals_ranked)} local · {len(regionals_ranked)} regional</div>
      </header>
      {hero}
      {snapshot}
      {leaderboard}
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
        asset_root="..", built_at=built_at,
    )


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
    contractors_by_slug = load_contractors(site)

    trades_data = []
    for t in site["trades"]:
        yaml_path = os.path.join(DATA, "trades", f"{t['key']}.yaml")
        trade_yaml = load_yaml(yaml_path) if os.path.exists(yaml_path) else None

        companies = contractors_by_slug.get(t["discovery_slug"], [])
        scored = []
        for c in companies:
            score, band = compute_presence_score(c, methodology)
            scored.append({**c, "_score": score, "_band": band})
        scored.sort(key=lambda x: (-x["_score"], -(x.get("reviews") or 0)))
        min_medal_reviews = methodology["leaderboard"]["min_reviews_for_medal"]
        local_top3 = [c for c in scored if c.get("is_local")
                       and (c.get("reviews") or 0) >= min_medal_reviews][:3]

        trades_data.append({
            "meta": t, "yaml": trade_yaml, "companies": scored, "top3": local_top3,
            "n_local": sum(1 for c in scored if c.get("is_local")),
            "n_regional": sum(1 for c in scored if not c.get("is_local")),
        })

    # Clean docs/
    if os.path.exists(DOCS):
        for name in os.listdir(DOCS):
            full = os.path.join(DOCS, name)
            if os.path.isdir(full): shutil.rmtree(full)
            else: os.remove(full)
    os.makedirs(DOCS, exist_ok=True)

    write(os.path.join(DOCS, "index.html"),
          render_home(site, trades_data, methodology, built_at))
    for t in trades_data:
        write(os.path.join(DOCS, t["meta"]["key"], "index.html"),
              render_trade(t["meta"], t["yaml"], t["companies"], methodology,
                            site, built_at))

    shutil.copy(os.path.join(ASSETS, "style.css"), os.path.join(DOCS, "style.css"))
    write(os.path.join(DOCS, "CNAME"), site["domain"] + "\n")

    urls = [f"https://{site['domain']}/"] + \
           [f"https://{site['domain']}/{t['meta']['key']}/" for t in trades_data]
    write(os.path.join(DOCS, "robots.txt"),
          f"User-agent: *\nAllow: /\nSitemap: https://{site['domain']}/sitemap.xml\n")
    write(os.path.join(DOCS, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{u}</loc><lastmod>{built_at}</lastmod></url>\n" for u in urls) +
          '</urlset>\n')

    write(os.path.join(DOCS, "social-quotables.json"),
          json.dumps(build_social_feed(trades_data, site), indent=2))

    total = sum(len(t["companies"]) for t in trades_data)
    print(f"[build] wrote {len(trades_data) + 1} pages, "
          f"{total:,} business rows across {len(trades_data)} trades → {DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
