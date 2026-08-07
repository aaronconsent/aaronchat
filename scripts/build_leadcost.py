#!/usr/bin/env python3
"""Generate the lead-cost calculator table + the /stats page from one source of truth.

Reads:  scripts/_leadcost_data.json   (per-trade, per-channel value+tier+source, seeds)
Writes: - the LC_BENCH object inside _worker.js (between the // <LC_BENCH> markers)
        - /stats/index.html            (methodology + sources + full per-trade table)

Keeps the calculator and the public methodology page perfectly in sync. Run:
    python3 scripts/build_leadcost.py
"""
import os, re, json, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "scripts", "_leadcost_data.json"), encoding="utf-8"))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

VER = re.search(r"ha\.css\?v=(\d+)", IDX).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]
PIXEL = IDX[IDX.index('<!-- Meta Pixel -->'):IDX.index('</script>', IDX.index('<!-- Meta Pixel -->')) + len('</script>')]

META = DATA["_meta"]
TRADES = DATA["trades"]


def esc(s):
    return H.escape(str(s if s is not None else ""))


# ---------------------------------------------------------------- LC_BENCH ------
def jd(x):
    return json.dumps(x, ensure_ascii=False)


def js_channel(c):
    v = "null" if c.get("v") is None else str(c["v"])
    return f'[{v}, {jd(c["tier"])}, {jd(c["src"])}]'


def js_book(b):
    def r(x):
        return "null" if x is None else str(x)
    return ("{ lsa: %s, ads: %s, fb: %s, organic: %s, blended: %s }" %
            (r(b.get("lsa")), r(b.get("ads")), r(b.get("fb")), r(b.get("organic")), r(b.get("blended"))))


def build_bench():
    lines = []
    for t in TRADES:
        book = js_book(t["book"]) if t.get("book") else "{ blended: 0.30 }"
        lines.append(
            f'  {t["trade"]}: {{ label: {jd(t["label"])}, '
            f'ads: {js_channel(t["ads"])}, lsa: {js_channel(t["lsa"])}, fb: {js_channel(t["fb"])}, '
            f'book: {book}, kw: {jd(t["seeds"])} }},'
        )
    body = "\n".join(lines).rstrip(",")
    block = "// <LC_BENCH>\nconst LC_BENCH = {\n" + body + "\n};\n// </LC_BENCH>"
    worker_path = os.path.join(ROOT, "_worker.js")
    src = open(worker_path, encoding="utf-8").read()
    a, b = "// <LC_BENCH>", "// </LC_BENCH>"
    if a not in src or b not in src:
        raise SystemExit("LC_BENCH markers not found in _worker.js")
    new = src[:src.index(a)] + block + src[src.index(b) + len(b):]
    open(worker_path, "w", encoding="utf-8").write(new)
    print(f"LC_BENCH: wrote {len(TRADES)} trades into _worker.js")


# ---------------------------------------------------------------- /stats page ---
TIER_LABEL = {"firm": "Firm", "directional": "Directional", "proxy": "Proxy", "na": "N/A"}
TIER_NOTE = {
    "firm": "audited dataset, n&gt;500",
    "directional": "agency-published estimate",
    "proxy": "borrowed from an adjacent trade",
    "na": "channel not available for this trade",
}


def channel_cell(c):
    if c.get("v") is None:
        return f'<td class="na">N/A<span class="tier">{esc(c["src"])}</span></td>'
    return (f'<td>${c["v"]}<span class="tier tier-{c["tier"]}">{TIER_LABEL.get(c["tier"], c["tier"])} '
            f'&middot; {esc(c["src"])}</span></td>')


def book_cell(t):
    b = t.get("book") or {}
    br = b.get("blended")
    if br is None:
        return '<td class="na">&mdash;</td>'
    tier = b.get("tier", "directional")
    return (f'<td>{round(br * 100)}%<span class="tier tier-{tier}">{TIER_LABEL.get(tier, tier)} '
            f'&middot; {esc(b.get("src", ""))}</span></td>')


def trade_rows():
    rows = []
    for t in TRADES:
        season = f'<div class="season">Seasonality: {esc(t["season"])}</div>' if t.get("season") else ""
        rows.append(
            f'<tr><th scope="row">{esc(t["label"])}{season}</th>'
            f'{channel_cell(t["ads"])}{channel_cell(t["lsa"])}{channel_cell(t["fb"])}'
            f'<td class="org">$7</td>{book_cell(t)}</tr>'
        )
    return "\n".join(rows)


def stats_body():
    ch = META["channels"]
    src_items = "".join(
        f'<li><b>{esc(ch[k]["label"])}</b> &mdash; {esc(ch[k]["primary"])} '
        f'(<span>{esc(ch[k]["sample"])}</span>). <a href="{esc(ch[k]["url"])}" target="_blank" rel="noopener">Source &rarr;</a></li>'
        for k in ("ads", "lsa", "fb")
    ) + "".join(
        f'<li><b>Booking rate</b> &mdash; {esc(s["name"])}. <a href="{esc(s["url"])}" target="_blank" rel="noopener">Source &rarr;</a></li>'
        for s in META.get("booking_sources", [])
    )
    tier_defs = "".join(
        f'<div class="tierdef"><span class="tier tier-{k}">{TIER_LABEL[k]}</span><p>{TIER_NOTE[k]}.</p></div>'
        for k in ("firm", "directional", "proxy", "na")
    )
    b = META["bounds"]
    return f'''
<div class="page-hero"><div class="wrap">
  <span class="caps">The numbers behind the calculator</span>
  <h1>What a lead really costs &mdash; and how I know</h1>
  <p>The lead-cost tool on the home page isn&rsquo;t a guess. Here&rsquo;s every source, every formula, and every
  place I&rsquo;d tell you to squint. If a number can&rsquo;t survive a click to its source, it doesn&rsquo;t belong on my site.</p>
</div></div>

<section class="sec"><div class="wrap prose">
  <h2>The short version</h2>
  <p>For your ZIP and trade, I show cost-per-lead on four channels: <b>Google Ads</b>, <b>Google Local Services Ads (LSA)</b>,
  <b>Facebook</b>, and <b>Organic</b>. The three paid numbers start from published industry benchmarks and get nudged to your
  local market. Organic is a flat <b>$7</b> &mdash; what I pay to turn an anonymous visitor on your site into a lead you own,
  through <a href="https://consentresolve.com" target="_blank" rel="noopener">ConsentResolve</a>. Everything is an illustration
  of market rates, not a promise about your results.</p>

  <h2>How each number is built</h2>
  <h3>Google Ads &mdash; live-adjusted to your market</h3>
  <p>I start from LocaliQ&rsquo;s published cost-per-lead for your trade, then adjust it for your market. The adjustment comes
  from real Google Keyword&nbsp;Planner data (via DataForSEO): I pull the average cost-per-click for your trade&rsquo;s search
  terms in <b>your state</b> and nationally, and take the <b>ratio</b>. If your state runs 20% hotter than the national average,
  the benchmark moves up 20%.</p>
  <p><b>Why a ratio and not the raw click cost?</b> Keyword&nbsp;Planner&rsquo;s cost-per-click estimates run 3&ndash;5&times; higher
  than what advertisers actually pay. Used as an absolute, they&rsquo;d spit out $600 leads. Used as a ratio, that inflation sits
  on both the top and bottom of the fraction and cancels out &mdash; leaving a clean read on how pricey <em>your</em> market is.</p>
  <h3>Google LSA &amp; Facebook &mdash; sourced benchmarks, scaled to your market</h3>
  <p>LSA and Facebook don&rsquo;t publish per-ZIP pricing, so these are published industry benchmarks scaled by the same local
  factor. Where a trade isn&rsquo;t eligible for LSA at all (solar, most concrete/paving), the card reads <b>N/A</b> &mdash; never a
  made-up number.</p>
  <h3>Organic &mdash; the $7 you can own</h3>
  <p>Organic leads carry no per-click auction fee. The only cost is resolving anonymous traffic into named leads, which I do
  through ConsentResolve at about <b>$7 a lead</b> &mdash; and unlike every rented channel, you keep them.</p>
  <h3>Cost per booked job &mdash; leads that actually become jobs</h3>
  <p>A lead isn&rsquo;t a job. <b>Cost per booked job = cost per lead &divide; your booking rate</b> (the share of leads that turn
  into a booked job). Booking rate is driven by <b>trade + channel + how fast you answer</b> &mdash; not by ZIP &mdash; so I source it
  per trade and per channel, not per market. LSA and inbound calls book highest (high intent); Facebook lead-ads book lowest.
  The firmest numbers are Google&rsquo;s own LSA book rates (SearchLight&rsquo;s 888-contractor set: HVAC/plumbing/electrical ~43&ndash;44%);
  Google&nbsp;Ads, Facebook, and organic are modeled from channel-intent benchmarks (Invoca, estatehub, NeverMiss).</p>
  <p><b>The one geographic caveat:</b> your cost <em>per lead</em> is localized to your market (live), so your cost <em>per booked
  job</em> moves with it &mdash; but the booking-rate multiplier behind it is a per-trade benchmark, the same in every ZIP.</p>

  <h2>My sources</h2>
  <ul class="srclist">{src_items}</ul>
  <p class="fineprint">Primary studies only, pulled from the original articles (re-citations of the same study routinely
  misreport the numbers). LSA figures reconciled to SearchLight&rsquo;s 2026 audited dataset where a trade is broken out.</p>

  <h2>How solid is each number?</h2>
  <p>Every figure in the table below is tiered so you know how much weight to give it:</p>
  <div class="tiergrid">{tier_defs}</div>

  <h2>The full table (per trade)</h2>
  <p>All cost-per-lead figures, national baseline, reviewed {esc(META["reviewed"])}. Your calculator result takes these and
  applies your market&rsquo;s local factor.</p>
  <div class="lctable-wrap"><table class="lctable">
    <thead><tr><th scope="col">Trade</th><th scope="col">Google Ads</th><th scope="col">Google LSA</th><th scope="col">Facebook</th><th scope="col">Organic</th><th scope="col">Booking rate</th></tr></thead>
    <tbody>
{trade_rows()}
    </tbody>
  </table></div>

  <h2>Where I&rsquo;d tell you to squint</h2>
  <ul class="caveats">
    <li><b>It&rsquo;s state-level.</b> Google Keyword&nbsp;Planner prices by state/metro, not by literal ZIP &mdash; so two ZIPs in the same state show the same market factor.</li>
    <li><b>Benchmarks aren&rsquo;t your account.</b> Your real cost-per-lead depends on your offer, your reviews, your speed to the phone, and your close rate. These are market averages.</li>
    <li><b>Sanity-bounded.</b> Nothing ships outside Google Ads ${b["ads"][0]}&ndash;${b["ads"][1]}, LSA ${b["lsa"][0]}&ndash;${b["lsa"][1]}, Facebook ${b["fb"][0]}&ndash;${b["fb"][1]} without a second source.</li>
    <li><b>Seasonality is real.</b> Storm-driven roofing and summer HVAC swing hard; a spring benchmark can mislead in December.</li>
    <li><b>Proxies are labeled.</b> A few trades (gutters, siding, flooring, fencing) borrow a close cousin&rsquo;s number because no trade-specific study exists. They&rsquo;re marked <span class="tier tier-proxy">Proxy</span> so you can weight them accordingly.</li>
  </ul>

  <h2>The growth-plan model</h2>
  <p>The rate board shows one channel on autopilot. The <a href="/plan/">growth plan</a> shows what happens when you layer
  several channels together &mdash; and it&rsquo;s built on the same live cost-per-lead and booking numbers as this page, plus
  a short list of published lift benchmarks. Here&rsquo;s how I keep that projection honest:</p>
  <ul class="caveats">
    <li><b>The lifts don&rsquo;t stack.</b> Speed-to-lead (~1.8&times; booking), reviews (+25%), a real website (+20%), Google
    Business Profile (+30% leads) and being on several channels (+40% leads) all overlap. I discount the overlap instead of
    multiplying straight through, and <b>no channel books above 60%</b> no matter how much you optimize.</li>
    <li><b>Quality lifts and volume lifts are separate.</b> Speed, reviews and CRO raise your <em>booking rate</em>; GBP and
    multichannel raise your <em>lead count</em>. I never let one masquerade as the other.</li>
    <li><b>Resolved visitors ride on top, not through the lifts.</b> Anonymous site traffic that ConsentResolve turns into a
    named lead (~$7 each) books low (~1 in 20) and doesn&rsquo;t get amplified by anything.</li>
    <li><b>Total eyeballs = impressions served, not people.</b> The same neighbor gets counted across Maps, your site and
    social. It&rsquo;s the &ldquo;how often your name shows up&rdquo; number.</li>
    <li><b>Every dollar is on the table &mdash; including mine.</b> Ad spend goes to Google/Meta; my fees (Website &amp; Growth
    $500, Social $500, 15% ad management) are itemized right in the dashboard.</li>
  </ul>
  <p>It&rsquo;s a projection of market rates, not a promise. Your real numbers move with your trade, market, season, ticket
  size and how well it&rsquo;s run. <a href="/plan/">Run your own plan &rarr;</a></p>

  <div class="center" style="margin-top:34px">
    <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="stats"><svg><use href="#i-phone"/></svg>Call Aaron &mdash; 713-384-8985</a>
  </div>
</div></section>
'''


def build_stats():
    url = "https://aaron.chat/stats/"
    title = "The numbers behind the lead-cost calculator | Hey Aaron!"
    desc = ("Every source, formula, and caveat behind Hey Aaron!'s lead-cost calculator: Google Ads, LSA, "
            "Facebook and organic cost-per-lead by trade, with tiers and citations.")
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
{PIXEL}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{HEADER}
<main id="main">
{stats_body()}
</main>
{TAIL}
</body>
</html>
'''
    out_dir = os.path.join(ROOT, "stats")
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)
    print(f"stats: wrote /stats/index.html (v={VER})")


if __name__ == "__main__":
    build_bench()
    build_stats()
    print("done")
