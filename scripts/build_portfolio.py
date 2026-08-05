#!/usr/bin/env python3
"""Generate /work/ (portfolio grid) + a case-study page per project, on ha.css navy.
Real projects and real metrics kept verbatim from scripts/_projects_data.py.
Run: python3 scripts/build_portfolio.py
"""
import os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from _projects_data import PROJECTS  # noqa: E402

# Persona review (Big Tom): lead the portfolio with client/trade work, not Aaron's own
# companies. Trade-relevant + local client work first; own/former companies last.
LEAD_ORDER = ["g4-electric","br-productions","midwest-cnc","polk-county-golf-carts",
              "lakeside-ink-threadz","deuces-wild-poker","first-byte","booked-job",
              "dosey-doe","jurassic-quest","consent-resolve","monarx"]
PROJECTS = sorted(PROJECTS, key=lambda p: LEAD_ORDER.index(p["slug"]) if p["slug"] in LEAD_ORDER else 99)

VER = "114"
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
LOGO = re.search(r'(<svg class="ha-logo".*?</svg>)', IDX, re.S).group(1)
FOOTER = IDX[IDX.index('<footer class="site-foot">'):IDX.index('</footer>') + len('</footer>')]
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
PHONE = '<svg><use href="#i-phone"/></svg>'
BIZ = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"ProfessionalService","name":"Hey Aaron! Marketing","url":"https://aaron.chat/","telephone":"+1-713-384-8985","email":"hello@aaron.chat","priceRange":"$$","areaServed":{"@type":"State","name":"Texas"},"address":{"@type":"PostalAddress","streetAddress":"50 Harbour Lane","addressLocality":"Coldspring","addressRegion":"TX","postalCode":"77331","addressCountry":"US"},"founder":{"@type":"Person","name":"Aaron Phillips"}}</script>'

HEADER = f'''<header class="site-head"><div class="wrap">
<a href="/" aria-label="Hey Aaron! home">{LOGO}</a>
<nav class="site-nav" aria-label="Main"><a href="/services/">What I do</a><a href="/trades/">Who I help</a><a href="/work/">Real work</a><a href="/pricing/">Pricing</a><a href="/about/">About</a></nav>
<a class="head-call" href="tel:+17133848985" data-cta-location="header">{PHONE}713-384-8985</a>
<button class="nav-toggle" aria-label="Menu" aria-expanded="false"><svg><use href="#i-menu"/></svg></button>
</div></header>'''

TAIL = f'''<a class="floatcall" href="tel:+17133848985" data-cta-location="float">{PHONE}Call Aaron &mdash; I answer</a>
{FOOTER}
<script src="/brand/ha.js?v={VER}" defer></script>'''


def esc(s): return H.escape(str(s or ""))


def head(title, desc, path):
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#074588"><link rel="canonical" href="https://aaron.chat{path}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">{BIZ}</head><body>
<a class="skip" href="#main">Skip to content</a>{SPRITE}{HEADER}<main id="main">'''


def card(p):
    metric = f'<span class="work-metric">{p["metric_n"]} {esc_txt(p["metric_l"])}</span>' if p.get("metric_n") else ""
    return (f'<a class="workcard" href="/work/{p["slug"]}/">'
            f'<div class="shot"><img src="/brand/media/portfolio/{p["shot"]}" alt="{p["name"]} website" '
            f'width="1280" height="800" loading="lazy" decoding="async"></div>'
            f'<div class="meta"><div class="t">{p["name"]}</div><div class="s">{p["tag"]}</div>{metric}</div></a>')


def esc_txt(s):
    # data already has entities; strip tags only
    return re.sub(r"<[^>]+>", "", str(s))


def render_index():
    grid = "".join(card(p) for p in PROJECTS)
    return f'''{head("Real work — sites & systems I've built | Hey Aaron! Marketing", "A dozen live businesses I built the marketing and websites for — SaaS, local service pros, events, and machine shops. Real work, click through and poke around.", "/work/")}
<div class="page-hero"><div class="wrap"><span class="caps">Not case-study fan fiction</span>
<h1>Real sites for real businesses.</h1>
<p>Every one of these is live. Some are my own companies, some are local shops down the road. Click through
and poke around, that's the best proof I can give you.</p></div></div>
<section class="sec"><div class="wrap"><div class="worklist">{grid}</div>
<div class="center" style="margin-top:40px"><a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="work-cta">{PHONE}Want one like these? Call me.</a></div></div></section>
</main>{TAIL}</body></html>'''


def render_case(p):
    work = "".join(f'<li><svg width="18" height="18"><use href="#i-check"/></svg><span>{w}</span></li>' for w in p["work"])
    stack = "".join(f'<span class="stacktag">{esc(s)}</span>' for s in p["stack"])
    metric = ""
    if p.get("metric_n"):
        metric = f'<div class="case-metric"><b>{p["metric_n"]}</b><span>{esc_txt(p["metric_l"])}</span></div>'
    return f'''{head(H.unescape(p["name"]) + " — work by Hey Aaron! Marketing", H.unescape(esc_txt(p["blurb"]))[:150], f"/work/{p['slug']}/")}
<div class="page-hero"><div class="wrap"><a class="caps" href="/work/" style="text-decoration:none">&larr; All work</a>
<h1>{p["name"]}</h1><p>{p["blurb"]}</p></div></div>
<section class="sec"><div class="wrap split">
  <div class="split-media reveal"><div class="frame" style="aspect-ratio:16/10;max-height:none">
    <img src="/brand/media/portfolio/{p["shot"]}" alt="{p["name"]} website" width="1280" height="800" style="width:100%;height:100%;object-fit:cover;object-position:top" loading="lazy"></div></div>
  <div class="reveal">
    <span class="caps">{p["tag"]}</span>
    <h2 style="font-size:var(--d-lg);margin:8px 0 14px">The brief</h2>
    <p class="lede" style="margin-bottom:18px">{p["brief"]}</p>
    {metric}
    <h3 style="margin:20px 0 10px">What I built</h3>
    <ul class="svc-get">{work}</ul>
    <div class="stack">{stack}</div>
    <div class="hero-cta" style="margin-top:22px"><a class="btn btn-call" href="tel:+17133848985" data-cta-location="case">{PHONE}Want something like this?</a>
    <a class="btn btn-ghost" href="{p['url']}" target="_blank" rel="noopener">Visit the live site &rarr;</a></div>
  </div>
</div></section>
<section class="sec final"><div class="wrap reveal"><h2>Let's build yours.</h2>
<p class="lede">One call, ten minutes. I'll tell you exactly what I'd do for your shop. And like these, it's built in
your name, yours to keep, month to month.</p>
<a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="case-final">{PHONE}Call Aaron: 713-384-8985</a></div></section>
</main>{TAIL}</body></html>'''


def main():
    open(os.path.join(ROOT, "work", "index.html"), "w", encoding="utf-8").write(render_index())
    for p in PROJECTS:
        d = os.path.join(ROOT, "work", p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_case(p))
    print(f"wrote work index + {len(PROJECTS)} case studies")


if __name__ == "__main__":
    main()
