#!/usr/bin/env python3
"""Generate the work portfolio: /work/ index + one case study per project.

Static-site model: emits committed HTML into the repo (no runtime build).
Edit PROJECTS, re-run, commit. Shares brand/style.css + nav.js + lead.js.
Copy is work-focused and factual — no invented metrics.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIXEL = """<!-- Meta Pixel -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
var PIXEL_ID='2449103548914877';
if(PIXEL_ID.indexOf('PASTE')===-1){fbq('init',PIXEL_ID);fbq('track','PageView');}
</script>"""

HEADER = """<header class="site-head">
  <div class="wrap">
    <a class="logo" href="/"><span class="mark">A+</span> Top of Class Marketing</a>
    <nav class="site-nav">
      <a href="/services/">Services</a>
      <a href="/work/">Work</a>
      <a href="/hvac-marketing/">HVAC</a>
      <a href="/plumber-marketing/">Plumbing</a>
      <a href="/pricing/">Pricing</a>
      <a href="/about/">About</a>
      <a class="cta" href="/report-card/">Get your report card</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="site-foot">
  <div class="wrap cols">
    <div>
      <span class="hand">Top of Class Marketing</span>
      <p>Aaron Phillips · Livingston, Texas</p>
      <p><a href="tel:+17133848985">713-384-8985</a> · <a href="mailto:hello@aaron.chat">hello@aaron.chat</a></p>
    </div>
    <div>
      <p><a href="/work/">Our work</a> · <a href="/services/">Services</a> · <a href="/pricing/">Pricing</a> · <a href="/about/">About</a></p>
      <p><a href="https://stats.lakelivingston.aaron.chat/">The Lake Livingston Service Pro Report</a></p>
      <p><a href="/privacy-policy/">Privacy</a> · <a href="/terms-of-service/">Terms</a></p>
    </div>
  </div>
</footer>
<script src="/brand/nav.js?v=5" defer></script>
<script src="/brand/lead.js?v=5" defer></script>"""


def page_head(title, desc, path):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://aaron.chat{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://aaron.chat{path}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/style.css?v=5">
{PIXEL}
</head>
<body>
{HEADER}"""


# ---- project data (factual, work-focused) -----------------------------------
PROJECTS = [
    dict(
        slug="jurassic-quest", name="Jurassic Quest", url="https://jurassicquest.com",
        cat="Growth &amp; Platform", tag="Growth &amp; Platform", shot="jurassicquest.jpg",
        metric_n="3,500", metric_l="ticket sales recovered",
        blurb="North America&rsquo;s largest touring dinosaur experience &mdash; where I built an abandoned-cart recovery platform on their Universe.com ticketing that won back 3,500 sales.",
        brief="Jurassic Quest sells event tickets through Universe.com. Like every ticketing store, a large share of buyers add tickets and leave before paying &mdash; and there was no built-in way to bring them back.",
        work=[
            "Built a shopping-cart recovery platform on top of their Universe.com ticketing store to catch abandoned checkouts.",
            "Automated recovery outreach that reconnected drop-off buyers with the exact event they were about to book.",
            "Recovered <b>3,500 ticket sales</b> that would otherwise have been lost.",
        ],
        stack=["Universe.com", "Cart-recovery automation", "Email"],
    ),
    dict(
        slug="dosey-doe", name="Dosey Doe", url="https://doseydoe.com",
        cat="Social &amp; Events", tag="Social &amp; Events", shot="doseydoe.jpg",
        metric_n="600+", metric_l="events promoted",
        blurb="A legendary live-music hall and restaurant in The Woodlands, TX &mdash; where I ran Facebook Events and social media across 600+ shows.",
        brief="Dosey Doe runs a packed calendar of live music, and every show has to fill the room. That work starts on social &mdash; event pages, promotion, and audience engagement, week after week.",
        work=[
            "Managed Facebook Events and social-media promotion for <b>600+</b> live-music events.",
            "Built and ran the event pages that drove ticket awareness and turnout, show after show.",
            "Kept the social calendar full across a relentless live-event schedule.",
        ],
        stack=["Facebook Events", "Meta Business", "Social Media"],
    ),
    dict(
        slug="consent-resolve", name="Consent Resolve", url="https://consentresolve.com",
        cat="SaaS · Brand &amp; Web", tag="SaaS &amp; Web", shot="consentresolve.jpg",
        blurb="A compliance-first way for contractors to identify the real people visiting their site — and win the job — without ever cold-calling anyone.",
        brief="Consent Resolve needed a marketing site that sold a genuinely new idea — warm-inbound visitor identification — while staying on the right side of U.S. privacy law. The whole thing had to feel trustworthy, not creepy.",
        work=[
            "Designed and built the full marketing site (Astro &rarr; Cloudflare) around a locked &ldquo;warm-inbound&rdquo; story: identify a consented email, feed the client&rsquo;s own retargeting, let the homeowner come back and call.",
            "Reframed the compliance narrative around real U.S. contractor risk &mdash; TCPA, CIPA, and the Texas TDPSA &mdash; instead of generic GDPR boilerplate.",
            "Built an interactive product demo (register &rarr; visit &rarr; consent) that emails the prospect their own &ldquo;recovered lead&rdquo; so they feel the product work.",
            "Wired a consent-management autoblocker and mirrored every demo into an in-house CRM.",
        ],
        stack=["Astro", "Cloudflare Pages/Workers", "Resend", "D1 &amp; KV"],
    ),
    dict(
        slug="deuces-wild-poker", name="Deuces Wild Poker Club", url="https://deuceswildpokertx.com",
        cat="Website &amp; Local SEO", tag="Website &amp; SEO", shot="deuceswildpoker.jpg",
        blurb="A private poker club in Huntsville, TX — rebuilt from a page builder into a fast, self-owned site engineered to be found and to fill seats.",
        brief="Deuces Wild was locked inside a page builder with organic search as its only real channel. It needed a site it owned, built to rank in a market full of bigger-city competitors.",
        work=[
            "Replaced a Durable page-builder site with a hand-built, conversion-first static site on Cloudflare Workers &mdash; no builder, fully owned.",
            "Shipped 40+ pages including 20 local &ldquo;poker near {town}&rdquo; pages with real geographic hooks and schema.",
            "Built the SEO/AEO layer &mdash; llms.txt, structured data, a 301 map, and explicit AI-crawler access so answer engines can cite it.",
            "Stood up an autonomous B2B events-outreach engine (Resend, 3-touch sequences) and an SMS opt-in that writes straight to the owner&rsquo;s spreadsheet.",
        ],
        stack=["Cloudflare Workers", "D1", "KV", "Resend", "GA4"],
    ),
    dict(
        slug="booked-job", name="Booked Job", url="https://booked-job.com",
        cat="Brand &amp; AI Automation", tag="AI &amp; Automation", shot="bookedjob.jpg",
        blurb="An autonomous content brand for service pros — a marketing machine that writes, renders, voices, and posts itself across every channel.",
        brief="Booked Job is a proving ground: can an entire content brand run itself? The goal was a marketing engine that produces and publishes real, fact-checked content with no one at the keyboard.",
        work=[
            "Built a fully autonomous multi-channel publishing engine (GitHub Actions + a Cloudflare cron Worker) posting to Facebook, Instagram, YouTube, Mastodon, Pinterest and LinkedIn &mdash; no laptop in the loop.",
            "Engineered a Remotion video engine that renders brand-locked vertical reels and long-form video, voiced with ElevenLabs over generated art.",
            "Ran an audio podcast pipeline that publishes an RSS feed live on Spotify.",
            "Grounded every statistic in a sourced, adversarially fact-checked dataset &mdash; no invented numbers.",
        ],
        stack=["Cloudflare Workers", "GitHub Actions", "Remotion", "ElevenLabs", "Buffer", "Resend"],
    ),
    dict(
        slug="br-productions", name="B&amp;R Productions", url="https://bandrproduction.com",
        cat="Website Migration", tag="Website &amp; Migration", shot="bandrproduction.jpg",
        blurb="A Texas CNC machine shop, in business since 1994 — moved off a page builder onto a fast, self-owned site.",
        brief="B&amp;R had decades of reputation but a site trapped in a page builder, with broken images and a dead contact form. They needed to own their site and have it actually work.",
        work=[
            "Migrated the shop off Durable to a static, self-owned site on Cloudflare Workers.",
            "Mirrored 32 pages &mdash; capabilities, industries, and 20 service-area pages &mdash; from a sitemap-restricted crawler.",
            "Solved the framework&rsquo;s image-optimizer hydration bug by self-hosting all 212 images behind a runtime shim.",
            "Rebuilt a working quote form on a Cloudflare Worker with Resend, removed the third-party chat widget, and preserved analytics.",
        ],
        stack=["Cloudflare Workers", "Resend", "Python pipeline", "GTM"],
    ),
    dict(
        slug="lakeside-ink-threadz", name="Lakeside Ink &amp; Threadz", url="https://lakesidethreadz.com",
        cat="Website Migration", tag="Website &amp; Migration", shot="lakesidethreadz.jpg",
        blurb="A custom-embroidery and DTF shop in Onalaska, TX — moved off an AI site builder onto a site they actually own.",
        brief="Lakeside&rsquo;s site lived inside an AI builder that shipped a single-page app &mdash; impossible to own, hard to change, and invisible to search. They needed the real thing.",
        work=[
            "Migrated the shop off Mocha (an AI builder that shipped a client-rendered SPA) to a static, self-owned site on Cloudflare Workers.",
            "Built a Playwright headless-Chromium snapshot pipeline to capture real, per-page HTML from the single-page app across 31 routes.",
            "Rebuilt working contact and quote forms on a Cloudflare Worker with Resend email and spam protection.",
            "Self-hosted every image and asset and shipped a branded 404, sitemap, and robots.",
        ],
        stack=["Cloudflare Workers", "Playwright", "Resend"],
    ),
    dict(
        slug="polk-county-golf-carts", name="Polk County Golf Carts", url="https://polkcountygolfcarts.com",
        cat="Website &amp; Booking Tool", tag="Website &amp; Tool", shot="polkcountygolfcarts.jpg",
        blurb="Golf-cart sales, service and custom builds in Livingston, TX — with a private rental-booking system running behind the site.",
        brief="PCGC wanted more than a brochure: a fast marketing site plus a real tool to take and manage cart rentals without paying for another SaaS.",
        work=[
            "Built a fast, self-owned static site on Cloudflare Workers, generated from shared templates.",
            "Added a customer rental-booking flow backed by Cloudflare KV, with an admin review dashboard behind auth.",
            "Wired a booking API plus Resend transactional email &mdash; a notice to the shop on every request, a thank-you to the customer on return.",
            "Generated social-share images and shipped the full SEO scaffold.",
        ],
        stack=["Cloudflare Workers", "KV", "Resend", "Python"],
    ),
    dict(
        slug="midwest-cnc", name="Midwest CNC Services", url="https://midwestcncservices.com",
        cat="Website", tag="Website", shot="midwestcnc.jpg",
        blurb="A CNC machine-repair specialist — CNC repair, spindle rebuilds, and way covers — with a clean, fast site to match the precision of the work.",
        brief="A precision CNC repair shop needed a site that read as trustworthy and technical, and loaded instantly on a phone in a machine shop.",
        work=[
            "Designed and built a fast, mobile-first marketing site for a CNC machine-repair specialist.",
            "Structured the pages around the shop&rsquo;s core work &mdash; CNC repair, spindle rebuilds, and way covers.",
            "Built and hosted on the same self-owned Cloudflare stack used across the portfolio.",
        ],
        stack=["Cloudflare", "Static HTML"],
    ),
]

PROJ_BY_SLUG = {p["slug"]: p for p in PROJECTS}
ORDER = [p["slug"] for p in PROJECTS]


def card(p):
    metric = (f'\n          <span class="work-metric">&#9733; {p["metric_n"]} {p["metric_l"]}</span>'
              if p.get("metric_n") else "")
    return f"""      <a class="work-card reveal" href="/work/{p['slug']}/">
        <div class="work-shot"><img src="/brand/media/portfolio/{p['shot']}" alt="{p['name']} website" width="1280" height="800" loading="lazy" decoding="async"></div>
        <div class="work-body">
          <span class="work-cat">{p['cat']}</span>
          <h3>{p['name']}</h3>
          <p>{p['blurb']}</p>{metric}
          <span class="work-more">View case study &rarr;</span>
        </div>
      </a>"""


def render_index():
    title = "Our Work — Websites, Brands &amp; AI Builds | Top of Class Marketing"
    desc = ("Real, live sites and brands we designed and built — Consent Resolve, Deuces Wild Poker, "
            "Booked Job, B&R Productions, Lakeside Ink & Threadz, Polk County Golf Carts, Midwest CNC and more.")
    cards = "\n".join(card(PROJ_BY_SLUG[s]) for s in ORDER)
    return f"""{page_head(title, desc, '/work/')}

<div class="hero hero--split hero--work">
  <div class="wrap">
    <div class="hero-copy">
      <p class="kicker">Selected work</p>
      <h1>Real sites. Real brands. Real results.</h1>
      <p class="sub">A national dinosaur tour, a poker club, a live-music hall, a CNC machine shop, a
      compliance SaaS, and a stack of local shops &mdash; sites we&rsquo;ve built, platforms we&rsquo;ve
      shipped, and campaigns we run. <b>This website is one of them.</b></p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="/report-card/">Get my free report card</a>
        <a class="btn btn-ghost" href="/services/">See what we do</a>
      </div>
    </div>
    <div class="hero-figure">
      <div class="hero-imgwrap">
        <img src="/brand/media/portfolio/deuceswildpoker.jpg" alt="A site we built" width="1280" height="800" fetchpriority="high" decoding="async" style="border-radius:var(--r-lg);border:3px solid rgba(255,255,255,.14);box-shadow:0 20px 50px rgba(0,0,0,.38)">
      </div>
    </div>
  </div>
</div>

<section>
  <div class="wrap">
    <div class="work-grid">
{cards}
    </div>
  </div>
</section>

<section class="band-green">
  <div class="wrap reveal" style="text-align:center">
    <p class="eyebrow">Your shop, next</p>
    <div class="section-head" style="margin:0 auto var(--sp-m)"><h2>Want one like these?</h2></div>
    <p class="lede" style="margin:0 auto var(--sp-m);color:var(--chalk)">Start with your free report card. We&rsquo;ll show you exactly where you stand today &mdash; then build you something you own.</p>
    <a class="btn btn-primary btn-lg" href="/report-card/">Get my free report card</a>
  </div>
</section>
{FOOTER}
</body>
</html>
"""


def render_case(p):
    i = ORDER.index(p["slug"])
    prev_link = next_link = ""
    if i > 0:
        pv = PROJ_BY_SLUG[ORDER[i - 1]]
        prev_link = f'<a href="/work/{pv["slug"]}/">&larr; {pv["name"]}</a>'
    if i < len(ORDER) - 1:
        nx = PROJ_BY_SLUG[ORDER[i + 1]]
        next_link = f'<a href="/work/{nx["slug"]}/">{nx["name"]} &rarr;</a>'
    name_plain = p["name"].replace("&amp;", "&")
    title = f'{name_plain} — Case Study | Top of Class Marketing'
    desc = p["blurb"].replace("&mdash;", "—").replace("&rsquo;", "'")[:155]
    work = "\n".join(f"        <li>{w}</li>" for w in p["work"])
    tags = "\n".join(f'        <span class="tag">{t}</span>' for t in p["stack"])
    stat = (f'\n    <div class="case-stat"><span class="n">{p["metric_n"]}</span>'
            f'<span class="l">{p["metric_l"]}</span></div>' if p.get("metric_n") else "")
    return f"""{page_head(title, desc, f'/work/{p["slug"]}/')}

<div class="hero hero--split hero--work">
  <div class="wrap">
    <div class="hero-copy">
      <p class="kicker">{p['cat']}</p>
      <h1>{p['name']}</h1>
      <p class="sub">{p['blurb']}</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{p['url']}" target="_blank" rel="noopener">Visit the live site &#8599;</a>
        <a class="btn btn-ghost" href="/work/">&larr; All work</a>
      </div>
    </div>
    <div class="hero-figure">
      <div class="hero-imgwrap">
        <img src="/brand/media/portfolio/{p['shot']}" alt="{p['name']} website" width="1280" height="800" fetchpriority="high" decoding="async" style="border-radius:var(--r-lg);border:3px solid rgba(255,255,255,.14);box-shadow:0 20px 50px rgba(0,0,0,.38)">
      </div>
    </div>
  </div>
</div>

<section>
  <div class="wrap reveal" style="max-width:820px">
    <p class="eyebrow">The brief</p>
    <p class="lede">{p['brief']}</p>{stat}
    <p class="eyebrow" style="margin-top:var(--sp-l)">What we built</p>
    <ul class="deliverables">
{work}
    </ul>
    <p class="eyebrow" style="margin-top:var(--sp-l)">Built with</p>
    <div class="tags">
{tags}
    </div>
    <div class="svc-nextprev">{prev_link}{next_link}</div>
  </div>
</section>

<section class="band-green">
  <div class="wrap reveal" style="text-align:center">
    <div class="section-head" style="margin:0 auto var(--sp-m)"><h2>Want one like this?</h2></div>
    <a class="btn btn-primary btn-lg" href="/report-card/">Get my free report card</a>
  </div>
</section>
{FOOTER}
</body>
</html>
"""


def main():
    work_dir = os.path.join(ROOT, "work")
    os.makedirs(work_dir, exist_ok=True)
    with open(os.path.join(work_dir, "index.html"), "w") as f:
        f.write(render_index())
    for p in PROJECTS:
        d = os.path.join(work_dir, p["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write(render_case(p))
    print(f"wrote /work/ + {len(PROJECTS)} case studies")


if __name__ == "__main__":
    main()
