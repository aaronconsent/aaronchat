#!/usr/bin/env python3
"""Build /dashboard/ — the client dashboard demo (sample 12-month journey).
Reuses the site chrome; brand/dashboard.js holds the sample data + renders everything.
Run: python3 scripts/build_dashboard.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
VER = re.search(r"ha\.css\?v=(\d+)", IDX).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]
PIXEL = IDX[IDX.index('<!-- Meta Pixel -->'):IDX.index('</script>', IDX.index('<!-- Meta Pixel -->')) + len('</script>')]

BODY = f'''
<div class="page-hero"><div class="wrap">
  <span class="caps">Client dashboard &middot; live sample</span>
  <h1>Your first 12 months, in one place</h1>
  <p>This is the dashboard my clients open to see exactly what their money is doing. Below is a <b>modeled
  sample</b> &mdash; not a real client, but built from real benchmarks &mdash; a roofing company growing from a
  blank slate. Money in, money out, every move that made the phone ring, and the ROAS after my fees.</p>
</div></div>

<section class="sec sec-low"><div class="wrap">
  <div class="dash" data-dash>
    <div class="dash-disclose" role="note">
      <svg class="dash-disclose-i" aria-hidden="true"><use href="#i-shield"/></svg>
      <div>
        <b>Illustrative example &mdash; an above-median result. Not typical, and not a promise of your numbers.</b>
        <p>This is a <b>model</b> of how the pieces compound for a roofing company that executes well &mdash; not a real client and not a guarantee. A typical new business, with average execution, lands closer to the <a href="#dash-floor">conservative floor</a> below. Figures assume a <b>funded ad budget of at least $2,000/mo</b>, a <b>~$6,000 blended job</b>, and <b>fast lead response</b>. Revenue shown is <b>booked</b> (contracted), not yet collected.</p>
      </div>
    </div>

    <div class="dash-kpis" data-dash-kpis></div>

    <div class="dash-floor" id="dash-floor" data-dash-floor></div>

    <div class="dash-panel dash-chartwrap">
      <div class="dash-chart-head">
        <div><h2>Month by month</h2><p class="dash-sub">Click through all 12 months &mdash; watch the growth, the milestones, and the running totals climb.</p></div>
        <div class="dash-metrics" data-dash-metrics></div>
      </div>
      <button type="button" class="dash-tour-launch" data-tour-launch><svg><use href="#i-bolt"/></svg>Walk me through the first 12 months</button>
      <div class="dash-months" data-dash-months></div>
      <div class="dash-chart" data-dash-chart></div>
      <div class="dash-monthdetail" data-dash-monthdetail></div>
    </div>

    <div class="dash-cols">
      <div class="dash-panel">
        <h2>What we did &amp; what happened</h2>
        <div class="dash-timeline" data-dash-timeline></div>
      </div>
      <div class="dash-panel dash-plan">
        <h2>The plan we run every month</h2>
        <p class="dash-sub">Targets, actions, and the hours behind them &mdash; so you always know what you&rsquo;re paying for.</p>
        <div class="dash-actions" data-dash-actions></div>
      </div>
    </div>

    <div class="dash-cta reveal">
      <div>
        <h2>Want to see your own numbers?</h2>
        <p>Run your ZIP and trade and I&rsquo;ll build the plan that gets you here.</p>
      </div>
      <a class="btn btn-primary btn-lg" href="/plan/"><svg><use href="#i-trend"/></svg>Build my plan</a>
    </div>
  </div>
</div></section>

<script src="/brand/dashboard.js?v={VER}" defer></script>
'''

url = "https://aaron.chat/dashboard/"
title = "Client dashboard — your first 12 months | Hey Aaron!"
desc = ("The dashboard my clients see: money in, money out, total eyeballs, leads, cost per booked job, and "
        "ROAS after fees — a real-shaped sample of a contractor growing from scratch over 12 months.")
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

out = os.path.join(ROOT, "dashboard")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(PAGE)
print(f"dashboard: wrote /dashboard/index.html (v={VER})")
