#!/usr/bin/env python3
"""Static site generator for stats.lakelivingston.aaron.chat.

Reads YAML from data/, renders HTML into docs/ using tiny string templates
(no Jinja dep — keeps the deploy simple). Output structure:

    docs/
      index.html                        home page (trade grid)
      plumbers/index.html               per-trade page
      hvac/index.html
      electricians/index.html
      style.css                         copied from assets/
      CNAME                             stats.lakelivingston.aaron.chat
      social-quotables.json             machine-readable feed for aaron.chat
      robots.txt
      sitemap.xml

Run: python3 scripts/build.py
"""
import datetime as dt
import html
import json
import os
import shutil
import sys

import yaml


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(ROOT, "assets")
TEMPLATES = os.path.join(ROOT, "templates")


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
    return html.escape(s or "", quote=True)


def render_base(*, title, description, canonical, content, crumbs, site, methodology,
                jsonld, asset_root=".", built_at=None):
    tpl = read(os.path.join(TEMPLATES, "base.html"))
    ctx = {
        "title":       e(title),
        "description": e(description),
        "canonical":   canonical,
        "content":     content,
        "crumbs":      crumbs,
        "site":        {k: (e(v) if isinstance(v, str) else v) for k, v in site.items()},
        "methodology": methodology,
        "jsonld":      json.dumps(jsonld, separators=(",", ":")),
        "asset_root":  asset_root,
        "built_at":    built_at or dt.datetime.utcnow().strftime("%Y-%m-%d"),
    }
    # Tiny mustache-ish rendering (no external Jinja)
    for k, v in ctx.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                tpl = tpl.replace("{{ " + f"{k}.{sk}" + " }}", str(sv or ""))
        else:
            tpl = tpl.replace("{{ " + k + " }}", str(v))
            tpl = tpl.replace("{{ " + k + "|safe }}", str(v))
    return tpl


# ---------- score computation ----------

def compute_presence_score(company, methodology):
    """Return (score:int|None, band:dict|None). None if the row is unverified."""
    if (company.get("research_status") or "template") == "template":
        return None, None
    w = methodology["presence_score"]["weights"]
    s = 0.0
    if company.get("website"):                    s += w["website"]
    if company.get("website_https"):              s += w["website_https"]
    if company.get("mobile_friendly"):            s += w["mobile_friendly"]
    if company.get("gbp_claimed"):                s += w["gbp_claimed"]
    rc = company.get("reviews_count") or 0
    s += min(w["gbp_reviews_count"], w["gbp_reviews_count"] * min(1.0, rc / 47.0))
    ar = company.get("avg_rating") or 0
    if ar >= 4.5:                                  s += w["gbp_avg_rating"]
    elif ar >= 4.0:                                s += w["gbp_avg_rating"] * 0.5
    # review_recency (naive): if last_review_iso is within 60 days
    lri = company.get("last_review_iso")
    if lri:
        try:
            when = dt.datetime.fromisoformat(lri.replace("Z", "+00:00"))
            days = (dt.datetime.utcnow().replace(tzinfo=when.tzinfo) - when).days
            if days <= 60: s += w["review_recency"]
        except Exception:
            pass
    if company.get("website_phone_click"):        s += w["website_phone_click"]
    if company.get("website_service_area"):       s += w["website_service_area"]
    if company.get("schema_localbusiness"):       s += w["schema_localbusiness"]
    if company.get("social_presence"):            s += w["social_presence"]
    score = int(round(s))
    band = next(b for b in methodology["presence_score"]["bands"] if score >= b["min"])
    return score, band


# ---------- page renderers ----------

def render_crumbs(items):
    parts = []
    for i, (label, href) in enumerate(items):
        if href and i < len(items) - 1:
            parts.append(f'<a href="{e(href)}">{e(label)}</a>')
        else:
            parts.append(e(label))
    return f'<nav class="crumbs">{" &rsaquo; ".join(parts)}</nav>'


def render_home(site, trades, methodology, built_at):
    """Home page: masthead + trade grid + methodology strip."""
    cards = []
    for t in trades:
        key = t["key"]
        data = t["data"]
        status = t["status"]
        n_companies = len([c for c in (data.get("companies") or [])
                           if (c.get("research_status") or "template") != "template"])
        n_all = len(data.get("companies") or [])
        n1 = (data.get("number_one_bar") or {}).get("reviews_median")
        klass = "trade-card" + (" draft" if status == "draft" else "")
        href = f"/{key}/"
        cards.append(f'''
          <a class="{klass}" href="{e(href)}">
            <div class="icon">{e(t["icon"])}</div>
            <h2>{e(t["name"])}</h2>
            <p class="tagline">{e(t["tagline"])}</p>
            <div class="metrics">
              <div class="metric"><span class="n">{n_all}</span><span class="l">tracked</span></div>
              <div class="metric"><span class="n">{n_companies}</span><span class="l">verified</span></div>
              <div class="metric"><span class="n">{n1 or "—"}</span><span class="l">#1 reviews</span></div>
            </div>
          </a>''')
    content = f'''
      <header class="masthead">
        <p class="eyebrow">Weekly research report</p>
        <h1>{e(site["name"])}</h1>
        <p class="tagline">{e(site["tagline"])}</p>
        <div class="weekly-stamp">Built {built_at}</div>
      </header>
      <section>
        <p class="section-title">Trades tracked <span class="count">{len(trades)} in rotation</span></p>
        <div class="trade-grid">{"".join(cards)}</div>
      </section>
      <section>
        <p class="section-title">How this is put together</p>
        <p>{e(site["attribution"])}</p>
      </section>
    '''
    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site["name"],
        "url": f"https://{site['domain']}/",
        "publisher": {"@type": "Organization", "name": site["publisher"], "url": site["publisher_url"]},
        "inLanguage": "en-US",
    }
    return render_base(
        title=site["name"],
        description=site["tagline"],
        canonical="/",
        content=content,
        crumbs="",
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root=".", built_at=built_at,
    )


def render_trade(trade_key, data, site, methodology, built_at):
    """Per-trade page: hero, leaderboard, roster table, insights."""
    companies = data.get("companies") or []
    verified = []
    for c in companies:
        score, band = compute_presence_score(c, methodology)
        if score is not None:
            verified.append({**c, "_score": score, "_band": band})
    verified.sort(key=lambda x: (-x["_score"], -(x.get("reviews_count") or 0)))
    top3 = verified[:methodology["leaderboard"]["medal_count"]]
    template_rows = [c for c in companies
                     if (c.get("research_status") or "template") == "template"]

    # --- hero "what it takes to be #1" ---
    n1 = data.get("number_one_bar") or {}
    stat_row = ""
    stats_pairs = [
        ("reviews_median",       "reviews (median)"),
        ("avg_rating_min",       "★ min"),
        ("response_within_hours","hr response"),
    ]
    for k, label in stats_pairs:
        v = n1.get(k)
        stat_row += f'<div class="stat"><span class="n">{v if v not in (None,"") else "—"}</span><span class="l">{e(label)}</span></div>'
    if n1.get("website_required") is not None:
        stat_row += f'<div class="stat"><span class="n">{"YES" if n1["website_required"] else "no"}</span><span class="l">website req</span></div>'
    if n1.get("same_day_service") is not None:
        stat_row += f'<div class="stat"><span class="n">{"YES" if n1["same_day_service"] else "no"}</span><span class="l">same-day</span></div>'
    hero = f'''
      <section class="number-one-bar">
        <h2>What it takes to be #1</h2>
        <p class="headline">{e(n1.get("summary","").split(chr(10))[0] if n1.get("summary") else "Awaiting research.")}</p>
        <div class="stat-row">{stat_row}</div>
        <p>{e(_rest_of_paragraph(n1.get("summary","")))}</p>
      </section>
    '''

    # --- leaderboard ---
    if top3:
        medals = []
        medal_labels = ["Gold · #1", "Silver · #2", "Bronze · #3"]
        for i, c in enumerate(top3):
            medals.append(f'''
              <article class="medal-card rank-{i+1}">
                <span class="medal">{medal_labels[i]}</span>
                <h3>{e(c["name"])}</h3>
                <span class="score">Presence {c["_score"]}/100 · {c.get("reviews_count") or 0} reviews · ★ {c.get("avg_rating") or "—"}</span>
                <p class="quick">{e((c.get("summary") or "")[:180])}</p>
              </article>''')
        leaderboard = f'''
          <p class="section-title">Leaderboard <span class="count">Top {len(top3)} by presence score</span></p>
          <div class="leaderboard">{"".join(medals)}</div>
        '''
    else:
        leaderboard = ""

    # --- roster table ---
    if verified:
        rows = []
        for i, c in enumerate(verified):
            rows.append(f'''
              <tr>
                <td class="num">{i+1}</td>
                <td class="name">{e(c["name"])}</td>
                <td>{e(c.get("address",""))}</td>
                <td class="num">{c["_score"]}</td>
                <td class="num">{c.get("reviews_count") or "—"}</td>
                <td class="num">{c.get("avg_rating") or "—"}</td>
                <td>{"✓" if c.get("website") else "—"}</td>
                <td><span class="band" style="background:{c["_band"]["color"]}">{e(c["_band"]["label"])}</span></td>
              </tr>''')
        roster = f'''
          <p class="section-title">Full roster <span class="count">{len(verified)} verified</span></p>
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
    else:
        roster = ""

    # --- template / gaps ---
    if template_rows:
        tmpl_names = "".join(f'<li>{e(c["name"])}</li>' for c in template_rows[:20])
        gaps = f'''
          <div class="template-note">
            <b>Research queue.</b> {len(template_rows)} placeholder rows are waiting for verified data.
            They do NOT appear in the leaderboard or public roster above. Next weekly build fills these in:
            <ul style="margin:8px 0 0 18px;padding:0">{tmpl_names}</ul>
          </div>
        '''
    else:
        gaps = ""

    # --- insights ---
    insight_cards = []
    for ins in data.get("insights") or []:
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

    # --- assemble ---
    content = f'''
      <header class="masthead">
        <p class="eyebrow">Trade report · updated weekly</p>
        <h1>{e(data["name"])} around Lake Livingston</h1>
        <p class="tagline">{e(data.get("service_area_note",""))}</p>
        <div class="weekly-stamp">Built {built_at}</div>
      </header>
      {hero}
      {leaderboard}
      {roster}
      {gaps}
      {insights}
    '''

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"{data['name']} around Lake Livingston · Weekly report",
        "datePublished": built_at,
        "publisher": {"@type": "Organization", "name": site["publisher"], "url": site["publisher_url"]},
        "url": f"https://{site['domain']}/{trade_key}/",
    }

    crumbs = render_crumbs([("Home", "/"), (data["name"], None)])
    return render_base(
        title=f"{data['name']} around Lake Livingston",
        description=data.get("service_area_note",""),
        canonical=f"/{trade_key}/",
        content=content,
        crumbs=crumbs,
        site=site, methodology=methodology, jsonld=jsonld,
        asset_root="..", built_at=built_at,
    )


def _rest_of_paragraph(text):
    lines = (text or "").split("\n")
    return " ".join(lines[1:]).strip() if len(lines) > 1 else ""


# ---------- social feed ----------

def build_social_feed(trades, site):
    """Emit machine-readable quotables for the aaron.chat social pipeline."""
    quotables = []
    for t in trades:
        for ins in t["data"].get("insights") or []:
            if ins.get("social_ready"):
                quotables.append({
                    "trade": t["key"],
                    "kind": ins.get("kind"),
                    "headline": ins.get("headline"),
                    "body": (ins.get("body") or "").strip(),
                    "link": f"https://{site['domain']}/{t['key']}/",
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

    trades = []
    for t in site["trades"]:
        path = os.path.join(DATA, "trades", f"{t['key']}.yaml")
        trades.append({**t, "data": load_yaml(path)})

    # Clean output
    if os.path.exists(DOCS):
        for name in os.listdir(DOCS):
            full = os.path.join(DOCS, name)
            if os.path.isdir(full): shutil.rmtree(full)
            else: os.remove(full)
    os.makedirs(DOCS, exist_ok=True)

    # Render pages
    write(os.path.join(DOCS, "index.html"),
          render_home(site, trades, methodology, built_at))
    for t in trades:
        write(os.path.join(DOCS, t["key"], "index.html"),
              render_trade(t["key"], t["data"], site, methodology, built_at))

    # Assets
    shutil.copy(os.path.join(ASSETS, "style.css"), os.path.join(DOCS, "style.css"))

    # CNAME (GitHub Pages custom domain)
    write(os.path.join(DOCS, "CNAME"), site["domain"] + "\n")

    # robots + sitemap
    urls = [f"https://{site['domain']}/"] + [f"https://{site['domain']}/{t['key']}/" for t in trades]
    write(os.path.join(DOCS, "robots.txt"),
          f"User-agent: *\nAllow: /\nSitemap: https://{site['domain']}/sitemap.xml\n")
    write(os.path.join(DOCS, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"  <url><loc>{u}</loc><lastmod>{built_at}</lastmod></url>\n" for u in urls) +
          '</urlset>\n')

    # Social quotables feed
    write(os.path.join(DOCS, "social-quotables.json"),
          json.dumps(build_social_feed(trades, site), indent=2))

    print(f"[build] wrote {len(trades) + 1} pages + assets → {DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
