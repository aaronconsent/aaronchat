#!/usr/bin/env python3
"""Build /plan/ — the interactive Growth-Plan dashboard ("see how I make this better").

Reuses the site chrome (header/footer/sprite/tail from index.html), embeds the sourced
reference model (scripts/_plan_data.json) as JSON for brand/plan.js, and renders the
dashboard shell. Run: python3 scripts/build_plan.py
"""
import os, re, json, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
REF = json.load(open(os.path.join(ROOT, "scripts", "_plan_data.json"), encoding="utf-8"))
VER = re.search(r"ha\.css\?v=(\d+)", IDX).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]
PIXEL = IDX[IDX.index('<!-- Meta Pixel -->'):IDX.index('</script>', IDX.index('<!-- Meta Pixel -->')) + len('</script>')]
PHONE = '<svg><use href="#i-phone"/></svg>'
REF_JSON = json.dumps(REF, ensure_ascii=False, separators=(",", ":"))
# reuse the homepage rate-board trade list so the gate form stays in sync
_sel = IDX.index('<select id="lc-trade"')
TRADE_OPTS = IDX[IDX.index('>', _sel) + 1:IDX.index('</select>', _sel)].strip()

# sources for the disclosure (dedup by url)
_src = {}
for s in REF.get("sources", []):
    _src[s["url"]] = s["name"]
SRC_LI = "".join(f'<a href="{H.escape(u)}" target="_blank" rel="noopener">{H.escape(n)}</a>' for u, n in _src.items())

BODY = f'''
<div class="page-hero"><div class="wrap">
  <span class="caps">Your growth plan</span>
  <h1>See how I make this better</h1>
  <p>The rate board showed the market on autopilot &mdash; one channel, top-dollar clicks, the phone answered
  <em>most</em> of the time. Flip on the pieces below and watch the whole machine work together: more channels,
  better-booked leads, lower cost per job. <b data-plan-sub>your trade</b>.</p>
</div></div>

<section class="sec sec-low"><div class="wrap">
  <div class="plan" data-plan>
    <!-- LEFT: controls -->
    <div class="plan-controls">
      <div class="plan-market" data-plan-market>
        <div class="plan-market-head"><h4>Your market</h4><span class="plan-market-sub" data-plan-marketsub>&mdash;</span></div>
        <form class="plan-market-form" novalidate>
          <div class="lc-field">
            <label for="pg-zip">ZIP</label>
            <input id="pg-zip" name="zip" type="text" inputmode="numeric" maxlength="5" autocomplete="postal-code" placeholder="77331">
          </div>
          <div class="lc-field">
            <label for="pg-trade">Trade</label>
            <select id="pg-trade" name="trade">{TRADE_OPTS}</select>
          </div>
          <button class="btn btn-primary btn-block" type="submit" data-plan-marketgo>Run it</button>
          <div class="plan-bar" data-plan-bar role="progressbar" aria-label="Pulling your market" hidden><i></i><span>Pulling your market&hellip;</span></div>
          <p class="lc-status" data-gate-status hidden></p>
        </form>
      </div>
      <div class="plan-toggles" data-plan-toggles><!-- toggles injected --></div>
      <div class="plan-budget">
        <div class="plan-budget-head"><label for="pl-budget">Monthly ad budget</label><b data-plan-budgetval>$0</b></div>
        <input id="pl-budget" type="range" min="0" max="10000" step="250" value="0" data-plan-budget>
        <div class="plan-budget-scale"><span>$0</span><span>$10k</span></div>
      </div>
    </div>
    <!-- RIGHT: outputs -->
    <div class="plan-out">
      <div class="plan-await" data-plan-await hidden>Punch in your ZIP &amp; trade on the left and I&rsquo;ll run your real numbers &mdash; no made-up averages.</div>
      <div class="plan-tiles">
        <div class="plan-tile hero">
          <div class="pl-hero-main"><span class="pl-tl">Cost per booked job</span><b class="pl-tv" data-o-cpbj>$0</b><span class="pl-ts">all-in, incl. what you pay me</span></div>
          <div class="pl-hero-anchor" data-o-anchor hidden><span class="pl-anchor-lbl">The market, on autopilot</span><b class="pl-anchor-v" data-o-anchorv>$0</b><span class="pl-anchor-sub">per booked job on Google&nbsp;Ads alone</span></div>
        </div>
        <div class="plan-tile"><span class="pl-tl">Booked jobs / mo</span><b class="pl-tv" data-o-jobs>0</b></div>
        <div class="plan-tile"><span class="pl-tl">Leads / mo</span><b class="pl-tv" data-o-leads>0</b></div>
        <div class="plan-tile eye"><span class="pl-tl">Total eyeballs / mo</span><b class="pl-tv" data-o-eyeballs>0</b><span class="pl-ts">brand impressions, all channels</span></div>
      </div>
      <div class="plan-panel">
        <h3>What you actually pay <span data-o-spend>$0</span>/mo</h3>
        <div class="plan-fee" data-o-fee></div>
      </div>
      <div class="plan-panel">
        <h3>Where the eyeballs &amp; leads come from</h3>
        <div class="plan-channels" data-o-channels></div>
      </div>
    </div>
  </div>

  <details class="plan-method">
    <summary>How this is modeled (and where I keep myself honest)</summary>
    <div class="plan-method-body">
      <p>Every number here is a <b>projection</b>, not a promise &mdash; an illustration of what these channels tend to do,
      built on published benchmarks. Your real results depend on your market, your trade, the season, your ticket size, and
      how well it's run.</p>
      <ul>
        <li><b>Cost per lead</b> is your live, market-localized figure (same engine as the rate board). <b>Booked jobs</b> use
        real per-trade, per-channel booking rates.</li>
        <li><b>The lifts don't stack.</b> Reviews (+25% booking), a real website (+20% booking), and being on several
        channels (+40% leads) all help &mdash; but they overlap, so I <b>discount the overlap</b> (never multiply straight
        through) and <b>no channel books above 60%</b>, no matter how much you optimize.</li>
        <li><b>Google Business Profile leads are predicted from your live local pack.</b> I pull the actual Map competitors
        for your trade in your city (via DataForSEO) and read how crowded it is and how big the review bar is &mdash; then
        estimate the leads a fully-managed, well-reviewed profile can realistically pull. Fewer/weaker competitors &rarr; more.
        Turn reviews off and it drops, because you can't hold Maps rank without review velocity.</li>
        <li><b>Total eyeballs = impressions served, not unique people.</b> The same neighbor gets counted across Maps, your
        site, and social. It's the "how often your name shows up" number, not reach.</li>
        <li><b>Organic leads</b> are anonymous site visitors ConsentResolve turns into a named lead at ~$7 &mdash; they book
        low (~1 in 20), but they're cheap and they're yours. They ride on top and don't get amplified by anything.</li>
        <li><b>Social media</b> (7 networks, daily posts + reels) adds ~10&ndash;12 inbound leads a month, weighted by how well
        your trade does on social &mdash; visual, before-&-after work (remodels, landscaping, pools) earns more than urgent
        commodity calls. They book at your trade's inbound rate.</li>
        <li><b>Everything you pay me is on the table</b> above: Website &amp; Growth $500/mo, Social $500/mo, ad management 15%
        of spend. Ad spend goes to Google/Meta, never to me.</li>
      </ul>
      <div class="plan-src">{SRC_LI}</div>
    </div>
  </details>

  <div class="lc-kick reveal">
    <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="plan"><svg><use href="#i-phone"/></svg>Call Aaron &mdash; let's build this</a>
  </div>
</div></section>

<script id="plan-ref" type="application/json">{REF_JSON}</script>
<script src="/brand/plan.js?v={VER}" defer></script>
'''

url = "https://aaron.chat/plan/"
title = "See how I make this better — your growth plan | Hey Aaron!"
desc = ("Interactive plan: layer in website, SEO, Google Business Profile, ads, reviews and visitor resolution and watch "
        "cost per booked job drop. Real benchmarks, full budget transparency.")
PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{H.escape(title)}</title>
<meta name="description" content="{H.escape(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{H.escape(title)}">
<meta property="og:description" content="{H.escape(desc)}">
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
{BODY}
</main>
{TAIL}
</body>
</html>
'''

out = os.path.join(ROOT, "plan")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(PAGE)
print(f"plan: wrote /plan/index.html (v={VER})")
