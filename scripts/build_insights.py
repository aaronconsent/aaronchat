#!/usr/bin/env python3
"""Build /insights/ — internal, unlisted, noindex dashboard of every ZIP report run.
Reuses the site chrome and loads brand/insights.js (which fetches /api/insights).
Run: python3 scripts/build_insights.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
VER = re.search(r"ha\.css\?v=(\d+)", IDX).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]

BODY = f'''
<div class="page-hero"><div class="wrap">
  <span class="caps">Internal &middot; unlisted</span>
  <h1>Lookup insights</h1>
  <p>Every ZIP report run across the site &mdash; live market intel, activity, and auto-pulled content
  &amp; lead-gen angles. Newest first. <button class="ins-refresh" data-ins-refresh type="button">Refresh</button>
  <span class="ins-updated" data-ins-updated></span></p>
</div></div>

<section class="sec sec-low"><div class="wrap">
  <div class="insights" data-insights>
    <div data-ins-body>
      <div class="ins-empty-state"><h2>Loading&hellip;</h2></div>
    </div>
  </div>
</div></section>

<script src="/brand/insights.js?v={VER}" defer></script>
'''

title = "Lookup insights — Hey Aaron! (internal)"
PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<script>document.documentElement.classList.add('js')</script>
<title>{H.escape(title)}</title>
<meta name="theme-color" content="#074588">
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
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

out = os.path.join(ROOT, "insights")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(PAGE)
print(f"insights: wrote /insights/index.html (v={VER})")
