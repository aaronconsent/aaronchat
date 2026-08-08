#!/usr/bin/env python3
"""Build /work/ — the "Real Work" hub (three-tier proof system).
Owns work/index.html (build_portfolio.py owns the per-project detail pages).

Tiers, per real-work-strategy.md:
  A. Your trade   — G4 Electric (live build) + a playbook card per remaining trade
  B. Built local  — Texas client builds + labeled portfolio builds (real screenshots)
  C. Big leagues  — Jurassic Quest / Monarx / Consent Resolve / Booked Job (dark band)

Honesty architecture: badges never blur categories; a fixed verified outcome
(Jurassic 3,500, Dosey 600+) shows a "verified" stamp, never the live chip; the
live chip only ever means "pulled right now". Live [data-live] rows hydrate from
STATS_ENDPOINT (brand/real-work.js) and COLLAPSE when absent — no fake stats ship.
Run: python3 scripts/build_real_work.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
VER = re.search(r"ha\.css\?v=(\d+)", IDX).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]
PIXEL = IDX[IDX.index('<!-- Meta Pixel -->'):IDX.index('</script>', IDX.index('<!-- Meta Pixel -->')) + len('</script>')]

PHONE = '<svg><use href="#i-phone"/></svg>'

# ---- Tier A: the 17-trade filter. Electrician = the live G4 build; the rest are playbooks. ----
TRADES = [
    ("hvac", "HVAC &amp; AC", "hvac-marketing"),
    ("plumbers", "Plumbers", "plumber-marketing"),
    ("electricians", "Electricians", "electrician-marketing"),
    ("roofers", "Roofers", "roofer-marketing"),
    ("remodelers", "Remodelers &amp; GCs", "remodeler-marketing"),
    ("fence", "Fence", "fence-marketing"),
    ("concrete", "Concrete", "concrete-marketing"),
    ("lawn", "Lawn &amp; landscape", "lawn-care-marketing"),
    ("tree", "Tree services", "tree-service-marketing"),
    ("septic", "Septic", "septic-marketing"),
    ("pressure", "Pressure washing", "pressure-washing-marketing"),
    ("pool", "Pool service", "pool-service-marketing"),
    ("garage", "Garage door", "garage-door-marketing"),
    ("gutters", "Gutters", "gutter-marketing"),
    ("pest", "Pest control", "pest-control-marketing"),
    ("painters", "Painters", "painter-marketing"),
    ("appliance", "Appliance repair", "appliance-repair-marketing"),
]

# playbook lead-take per non-electrician trade (Mike-voice, from the content matrix)
PLAYBOOKS = {
    "hvac": ("The two-season machine",
             "A campaign calendar that flips from AC to heat <b>before demand does</b>, a maintenance list that fills the October dip, and a call button built for the 11pm breakdown."),
    "plumbers": ("The burst-pipe sprint",
                 "When a pipe lets go, nobody reads a website. <b>I build for the ten-second decision:</b> call-first pages, ads aimed at people who need you now, and a water-heater page for the biggest ticket in the trade."),
    "roofers": ("The storm ticket",
                "When hail hits, the phone has to ring inside 48 hours. <b>Surge pages, ads that switch on with the weather,</b> and the &ldquo;actually local&rdquo; review wall that beats the out-of-town chasers."),
    "remodelers": ("The portfolio that closes",
                   "Your photos should be doing the selling. <b>A gallery organized by room and budget band,</b> plus a form that screens tire-kickers before you ever drive out for the estimate."),
    "fence": ("The linear-foot quote",
              "An instant estimate calculator that captures the lead while they&rsquo;re curious &mdash; <b>kills the &ldquo;call for pricing&rdquo; friction</b> &mdash; backed by a wood-vs-metal guide that owns the trade&rsquo;s #1 search."),
    "concrete": ("The before/after proof",
                 "Concrete sells on pictures. <b>Tear-out-to-finish galleries, a square-footage quote calculator,</b> and neighborhood targeting &mdash; because one new driveway sells three more on the same street."),
    "lawn": ("The route-density play",
             "Every new yard on a street you already run is nearly pure margin. <b>Neighborhood targeting plus set-and-forget mowing plans</b> with card-on-file signup &mdash; recurring revenue, not one-off cuts."),
    "tree": ("The storm cleanup surge",
             "When limbs come down across the county, the crew they find first wins. <b>Surge pages and a photo-estimate form</b> &mdash; the homeowner texts a picture, you quote before the saws cool."),
    "septic": ("The pump-out clock",
               "Septic runs on a 3&ndash;5 year cycle, which means <b>the customer list is the business.</b> The reminder machine, the realtor-inspection pipeline East Texas closings run on, and the aerobic-vs-conventional guide homeowners actually search."),
    "pressure": ("The satisfying split-screen",
                 "Half-clean-driveway video is the most scroll-stopping content on this whole list. <b>Reels plus &ldquo;on your street Tuesday&rdquo; neighborhood offers</b> &mdash; and a published bundle menu so nobody has to call for a price."),
    "pool": ("The weekly route",
             "The whole economic model is recurring service. <b>Route-dense cleaning plans with online signup,</b> green-to-clean transformation reels, and same-day equipment-repair positioning for the dead-pump call."),
    "garage": ("The local vs. 1-800 fight",
               "Your real competitor is a national call center with a fake local listing. <b>The plan is legitimacy:</b> published price ranges, honest spring-repair education, and review velocity they can&rsquo;t fake."),
    "gutters": ("The first-big-rain push",
                "Clogs announce themselves in fall and storm season, and that&rsquo;s when the campaign fires. <b>Honest gutter-guard education</b> that ranks and gets quoted, plus referral positioning alongside the roofers and washers you already know."),
    "pest": ("The quarterly plan",
             "This is a subscription business in work boots. <b>Market the plan, not the visit</b> &mdash; a month-by-month East Texas bug calendar for content, and automated review requests off your high visit frequency."),
    "painters": ("The room-by-room wall",
                 "A before/after portfolio with color callouts, <b>a free color consult as the lead magnet,</b> and an inside-in-winter / outside-in-summer calendar that smooths the season."),
    "appliance": ("The brand + model page",
                  "&ldquo;Samsung washer repair Livingston&rdquo; is how this trade is actually searched, so <b>I build for it</b> &mdash; brand-and-model pages, a plainly-stated same-day slot, and a fix-or-toss guide the AI answers quote."),
}

# ---- Tier B / C metadata overlay (keyed by _projects_data slug) ----
# badge: client | portfolio | mine | role ; verified = a real fixed number (no live chip)
META = {
    # Tier B — built local
    "dosey-doe": dict(tier="B", badge="client", tag="Live music venue", h3="600+ shows, promoted",
        loc="Dosey Doe &middot; The Woodlands, TX", verified=("600+", "shows promoted"),
        problem="A legendary hall with a relentless calendar: every show needs an event page, a Facebook Event, and a social push &mdash; every week, all year.",
        foryou="the same always-on social engine, pointed at your jobs instead of concerts."),
    "deuces-wild-poker": dict(tier="B", badge="client", tag="Poker club", h3="Found, and filling seats",
        loc="Deuces Wild Poker Club &middot; Huntsville, TX", live=("deuceswild.web.visits_30d", "Site visits &middot; 30d"),
        problem="A local club that lives or dies on people finding it and showing up. A self-owned site plus local SEO does the finding.",
        foryou="the same local-search work that puts a Huntsville club on the map puts a Huntsville plumber there too."),
    "br-productions": dict(tier="B", badge="client", tag="CNC machine shop", h3="Thirty years, finally online right",
        loc="B&amp;R Productions &middot; Texas, since 1994",
        problem="Three decades of machining reputation stuck on a slow, rented page-builder with broken images and a dead contact form.",
        foryou="if your site&rsquo;s on a page-builder subscription that&rsquo;s slow and rented, this is the way out."),
    "lakeside-ink-threadz": dict(tier="B", badge="client", tag="Embroidery &amp; DTF", h3="The home-based storefront",
        loc="Lakeside Ink &amp; Threadz &middot; Onalaska, TX",
        problem="No storefront and no walk-ins means the website has to be the shop window for the whole lake.",
        foryou="work-from-the-truck trades have the exact same problem &mdash; the site is the storefront."),
    "first-byte": dict(tier="B", badge="client", tag="Marketing agency", h3="The agency&rsquo;s agency",
        loc="First Byte &middot; The Woodlands, TX",
        problem="When another agency needs their own migration and local SEO done right, they don&rsquo;t do it in-house &mdash; they call me.",
        foryou="you&rsquo;re getting the guy other marketers hire."),
    "polk-county-golf-carts": dict(tier="B", badge="portfolio", tag="Local retail + tool", h3="The neighborhood fleet",
        loc="Polk County Golf Carts &middot; my own build, Livingston TX", live=("pcgc.web.visits_30d", "Site visits &middot; 30d"),
        problem="A demonstration build, run for real: everybody on the lake needs a cart, so the whole site &mdash; plus a private rental-booking tool &mdash; points at the communities that ride them.",
        foryou="this is what I build when nobody&rsquo;s paying me. Imagine what you get when somebody is."),
    "midwest-cnc": dict(tier="B", badge="portfolio", tag="Industrial", h3="The shop floor, online",
        loc="Midwest CNC Services &middot; my own build", live=("midwestcnc.web.visits_30d", "Site visits &middot; 30d"),
        problem="Off a page-builder subscription and onto fast hosting &mdash; loads quicker, costs less, ranks better. A working demonstration of the migration playbook.",
        foryou="the migration I&rsquo;d run for your shop, proven on my own dime first."),
    # Tier C — big leagues
    "jurassic-quest": dict(tier="C", role="Growth &amp; platform", num=("3,500", "abandoned ticket sales recovered"),
        blurb="A cart-recovery system on Universe.com for North America&rsquo;s biggest touring dinosaur show &mdash; won back 3,500 sales that were already walking out the door."),
    "monarx": dict(tier="C", role="Past role &middot; CMO",
        blurb="Ran marketing for a security SaaS protecting millions of websites. That&rsquo;s where the &ldquo;track everything&rdquo; habit comes from."),
    "consent-resolve": dict(tier="C", role="My company &middot; co-founder &amp; CMO",
        blurb="A visitor-ID SaaS built for contractors. I don&rsquo;t just market to the trades &mdash; I build software for them."),
    "booked-job": dict(tier="C", role="My brand &middot; AI automation",
        blurb="An autonomous content brand that runs itself &mdash; the same automation that keeps client marketing moving while you&rsquo;re on a roof."),
}

import importlib.util
spec = importlib.util.spec_from_file_location("_projects_data", os.path.join(ROOT, "scripts", "_projects_data.py"))
_pd = importlib.util.module_from_spec(spec); spec.loader.exec_module(_pd)
PROJECTS = {p["slug"]: p for p in _pd.PROJECTS}


def frame(slug, shot, domain):
    return (f'<div class="rw-frame"><div class="rw-chrome"><i></i><i></i><i></i>'
            f'<span class="rw-url">{domain}</span></div>'
            f'<div class="rw-shot"><img src="/brand/media/portfolio/{shot}" '
            f'alt="{H.unescape(PROJECTS[slug]["name"])} website, built by Hey Aaron!" '
            f'width="1280" height="800" loading="lazy" decoding="async"></div></div>')


def live_rows(m):
    if m.get("verified"):
        n, l = m["verified"]
        return (f'<div class="rw-rows"><div class="rw-row"><span class="rw-k">{l}</span>'
                f'<span class="rw-dots"></span><span class="rw-v">{n}<span class="rw-verified">verified</span></span></div></div>')
    if m.get("live"):
        key, l = m["live"]
        return (f'<div class="rw-rows" data-property><div class="rw-row"><span class="rw-k">{l}</span>'
                f'<span class="rw-dots"></span><span class="rw-v"><span data-live="{key}">&ndash;</span>'
                f'<span class="rw-mini-live">live</span></span></div></div>')
    return ""


def domain(url):
    return re.sub(r"^https?://", "", url).rstrip("/")


def card_live(slug):
    p = PROJECTS[slug]
    return f'''    <article class="rw-card" data-trade="electricians">
      {frame(slug, p["shot"], domain(p["url"]))}
      <div class="rw-body">
        <div class="rw-tagrow"><span class="rw-tag">Electrician</span><span class="rw-badge client">&#9679; Client build</span></div>
        <h3>The map-pack takeover</h3>
        <div class="rw-loc">G4 Electric &middot; a trade like yours</div>
        <p class="rw-problem">Great electricians, invisible on Google. The shops winning the panel-upgrade and EV-charger searches weren&rsquo;t better &mdash; they just showed up first.</p>
        {live_rows(dict(live=("g4.gbp.calls_30d","Google profile calls &middot; 30d")))}
        <div class="rw-links">
          <a href="{p['url']}" target="_blank" rel="noopener">Visit the live site &rarr;</a>
          <a class="rw-quiet" href="/work/{slug}/">Read the story &rarr;</a>
        </div>
      </div>
    </article>'''


def card_playbook(key, label, slug):
    title, plan = PLAYBOOKS[key]
    return f'''    <article class="rw-card rw-play" data-trade="{key}">
      <div class="rw-body">
        <div class="rw-tagrow"><span class="rw-tag">{label}</span><span class="rw-badge play">Playbook</span></div>
        <h3>{title}</h3>
        <p class="rw-plan">{plan}</p>
        <div class="rw-links"><a class="rw-quiet" href="/{slug}/">See the full plan &rarr;</a></div>
      </div>
    </article>'''


def card_local(slug):
    p, m = PROJECTS[slug], META[slug]
    badge = {"client": '<span class="rw-badge client">&#9679; Client build</span>',
             "portfolio": '<span class="rw-badge portfolio">Portfolio build</span>'}[m["badge"]]
    return f'''      <article class="rw-card">
        {frame(slug, p["shot"], domain(p["url"]))}
        <div class="rw-body">
          <div class="rw-tagrow"><span class="rw-tag">{m["tag"]}</span>{badge}</div>
          <h3>{m["h3"]}</h3>
          <div class="rw-loc">{m["loc"]}</div>
          <p class="rw-problem">{m["problem"]}</p>
          <p class="rw-foryou"><b>For your shop:</b> {m["foryou"]}</p>
          {live_rows(m)}
          <div class="rw-links">
            <a href="{p['url']}" target="_blank" rel="noopener">Visit the live site &rarr;</a>
            <a class="rw-quiet" href="/work/{slug}/">Read the story &rarr;</a>
          </div>
        </div>
      </article>'''


def card_big(slug):
    p, m = PROJECTS[slug], META[slug]
    num = f'<div class="rw-bignum">{m["num"][0]}<small>{m["num"][1]}</small></div>' if m.get("num") else ""
    return f'''      <div class="rw-bigcard">
        <div class="rw-role">{m["role"]}</div>
        <div class="rw-brand">{p["name"]}</div>
        <p>{m["blurb"]}</p>
        {num}
        <a href="{p['url']}" target="_blank" rel="noopener">{domain(p['url'])} &rarr;</a>
      </div>'''


# ---- assemble Tier A grid: G4 live card first, then a playbook per remaining trade ----
tier_a = [card_live("g4-electric")]
for key, label, slug in TRADES:
    if key == "electricians":
        continue
    tier_a.append(card_playbook(key, label, slug))
TIER_A = "\n".join(tier_a)

chips = '<button class="rw-chip" data-trade="all" aria-pressed="true">All trades</button>\n'
chips += "\n".join(f'<button class="rw-chip" data-trade="{k}" aria-pressed="false">{l}</button>' for k, l, _ in TRADES)

LOCAL_ORDER = ["dosey-doe", "deuces-wild-poker", "br-productions", "lakeside-ink-threadz",
               "first-byte", "polk-county-golf-carts", "midwest-cnc"]
TIER_B = "\n".join(card_local(s) for s in LOCAL_ORDER)
BIG_ORDER = ["jurassic-quest", "monarx", "consent-resolve", "booked-job"]
TIER_C = "\n".join(card_big(s) for s in BIG_ORDER)

SCHEMA = ('<script type="application/ld+json">' + H.escape(
    '{"@context":"https://schema.org","@type":"CollectionPage","name":"Real work — Hey Aaron! Marketing",'
    '"url":"https://aaron.chat/work/","about":"Live websites and marketing systems built by Aaron Phillips for contractors and local businesses across Texas.",'
    '"breadcrumb":{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://aaron.chat/"},{"@type":"ListItem","position":2,"name":"Real work","item":"https://aaron.chat/work/"}]}}',
    quote=False) + '</script>')

title = "Real work — live sites &amp; the numbers behind them | Hey Aaron! Marketing"
desc = ("Every site here is one I built or run — East Texas shops, a national dinosaur tour, my own "
        "software companies. Real work, real screenshots, click through and check any one of them.")

BODY = f'''
<div class="page-hero"><div class="wrap">
  <span class="caps">Real work</span>
  <h1>Live sites. Real businesses. Go&nbsp;check.</h1>
  <p>Every site on this page is one I built or run &mdash; East&nbsp;Texas shops, a national dinosaur tour,
  my own software companies. Not screenshots of someone else&rsquo;s work, not case-study fan fiction.
  <b>Tap any card and poke around</b> &mdash; that&rsquo;s the best proof I can give you.</p>
  <div class="hero-cta"><a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="realwork-hero">{PHONE}Call me: 713-384-8985</a>
  <span class="rw-aside">You get Aaron, not a sales rep.</span></div>
</div></div>

<section class="rw-stats" aria-label="Portfolio at a glance"><div class="wrap">
  <div class="rw-stats-grid">
    <div class="rw-stat"><div class="rw-n">12</div><div class="rw-d">sites &amp; systems I&rsquo;ve built</div></div>
    <div class="rw-stat"><div class="rw-n">17</div><div class="rw-d">trades I build for</div></div>
    <div class="rw-stat"><div class="rw-n">20+</div><div class="rw-d">years running marketing</div></div>
    <div class="rw-stat"><div class="rw-n">3,500</div><div class="rw-d">ticket sales recovered for Jurassic Quest <span class="rw-verified">verified</span></div></div>
  </div>
  <p class="rw-pulled">Every site here is live. Tap any card and go check it yourself &mdash; that&rsquo;s the whole point.</p>
</div></section>

<!-- TIER A: YOUR TRADE -->
<section class="sec" id="trades"><div class="wrap">
  <div class="rw-head"><span class="caps">Start here</span><h2>Your trade</h2>
  <p>Pick your trade. If there&rsquo;s a live build, you&rsquo;ll see it. If there isn&rsquo;t one yet, you&rsquo;ll see exactly what I&rsquo;d build for you &mdash; and the slot&rsquo;s open.</p></div>
  <div class="rw-chips" role="group" aria-label="Filter by trade">
    {chips}
  </div>
  <div class="rw-grid" id="rw-grid">
{TIER_A}
  </div>
  <div class="rw-empty" id="rw-empty">
    <h3>No <span id="rw-empty-trade">shop</span> on this page yet.</h3>
    <p>That&rsquo;s an opening, not bad news. <b>First one in gets me</b> &mdash; month to month, $0 setup, you call and I answer &mdash; and this slot with your name on it.</p>
    <a class="btn btn-call" href="tel:+17133848985" data-cta-location="realwork-empty">{PHONE}Call Aaron: 713-384-8985</a>
  </div>
</div></section>

<!-- TIER B: BUILT LOCAL -->
<section class="sec rw-local" id="local"><div class="wrap">
  <div class="rw-head"><span class="caps">Around here</span><h2>Built local</h2>
  <p>Texas businesses I build and run &mdash; same wiring, same phone-first thinking I put on trade sites. Two are my own demonstration builds, and they&rsquo;re labeled that way.</p></div>
  <div class="rw-grid">
{TIER_B}
  </div>
</div></section>

<!-- TIER C: THE BIG LEAGUES -->
<section class="rw-big" id="big"><div class="wrap">
  <div class="rw-head"><span class="caps">Where the firepower comes from</span><h2>The big-league work</h2>
  <p>Twenty years running marketing at the top of tech &mdash; and I still do. This is the caliber of machine now pointed at East Texas trucks.</p></div>
  <div class="rw-biggrid">
{TIER_C}
  </div>
  <p class="rw-kicker"><b>Why this matters to you:</b> the shops beating you online aren&rsquo;t smarter &mdash; they just have better wiring. You&rsquo;re hiring the guy who built that wiring for companies you&rsquo;ve heard of, month to month, for $500.</p>
</div></section>

<section class="sec final"><div class="wrap center reveal">
  <h2>Ready when you are.</h2>
  <p class="lede">Ten minutes, no pitch, no contract. Tell me your trade and where the phone&rsquo;s quiet.</p>
  <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="realwork-final">{PHONE}Call Aaron: 713-384-8985</a>
  <p class="rw-fire">If I&rsquo;m not booking you jobs, fire me.</p>
</div></section>

<script src="/brand/real-work.js?v={VER}" defer></script>
'''

PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{title}</title>
<meta name="description" content="{H.escape(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="https://aaron.chat/work/">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{H.escape(desc)}">
<meta property="og:url" content="https://aaron.chat/work/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
{SCHEMA}
{PIXEL}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{HEADER}
<main id="main">
{BODY}
</main>
{TAIL}
</body>
</html>
'''

out = os.path.join(ROOT, "work")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(PAGE)
print(f"real-work: wrote /work/index.html (v={VER}) — Tier A {len(tier_a)} cards, B {len(LOCAL_ORDER)}, C {len(BIG_ORDER)}")
