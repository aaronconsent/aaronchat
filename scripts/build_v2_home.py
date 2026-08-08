#!/usr/bin/env python3
"""Build /v2/ — the "Ink & Iron" homepage proof (Design Direction v2).

ISOLATED BY DESIGN. Reads index.html READ-ONLY (logo + icon sprite only) and
writes ONLY to /v2/index.html. Production stays on ha.css v1; this page is the
side-by-side proof so the direction can be judged against something real.

Copy is held CONSTANT — reused verbatim from the live homepage — so what's being
compared is the visual system, not the writing. The voice guide is untouched.

Spec: .docs/design-direction-v2.md    Run: python3 scripts/build_v2_home.py
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
LOGO = re.search(r'(<svg class="ha-logo".*?</svg>)', IDX, re.S).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
VER = "1"  # own cache-buster; deliberately NOT the production ha.css version

PHONE_SVG = '<svg><use href="#i-phone"/></svg>'
TEL = 'tel:+17133848985'

# ---------------------------------------------------------------- content (verbatim from the live homepage)
CLAUSES = [
    ("You own everything",
     "Website, domain, ad accounts, Google Business Profile, your customer list, all of it in your name from day one. Walk away whenever you want and you keep every bit of it. No hostage situation, ever."),
    ("Month to month",
     "No 12-month contract. No cancellation fee. If I don&rsquo;t earn my keep this month, fire me and walk, and you still keep everything I built."),
    ("Better every month",
     "I don&rsquo;t set it and forget it. Every month your site gets sharper, your Google rankings climb, and your reach grows. You&rsquo;re paying to move forward, never to stand still."),
    ("Projects on demand",
     "Think of me as your Chief Marketing Officer in a box. Need a one-off, a landing page, a campaign, a video, a fix? Grab me for any project, big or small, at <strong>$125 an hour</strong>. No retainer required."),
    ("10&times; your reach",
     "Your name everywhere it counts. I post you across all the major networks, 500&ndash;700 posts a month, so you build real coverage, real authority, and a steady stream of new customers finding you."),
    ("Real numbers, not fog",
     "Cost per lead. Cost per booked job. Money in, money out &mdash; the only two numbers that actually matter. No &ldquo;impressions,&rdquo; no &ldquo;engagement,&rdquo; no smoke."),
]

SERVICES = [
    ("A site that books jobs",
     "Fast, clean, built to turn a click into a phone call. Like this one. It loads before your competitor&rsquo;s homepage even shows up.",
     "You&rsquo;re looking at one right now"),
    ("Show up on Google",
     "Local SEO and your Google Business Profile done right, so when someone types &ldquo;AC repair near me&rdquo; at 11pm in July, they find you, not the other guy.",
     "Ask me where you rank today"),
    ("Ads that pay for themselves",
     "Google and Facebook ads aimed at people who need you now, not tire-kickers. Every dollar tracked back to a booked job, not a vanity click.",
     "Tracked, not guessed"),
    ("Speed-to-lead that calls back in seconds",
     "The second a lead comes in, we call them, while they&rsquo;re still holding the phone. I&rsquo;ll put it on your site too.",
     "Try it on the live site"),
    ("AI images &amp; video",
     "Scroll-stopping photos and short videos generated on demand, no photo shoot, no stock. The staged shots on this page? Made with the same tools I&rsquo;ll use for you.",
     "Look around this page"),
    ("Reviews &amp; reputation",
     "The stars next to your name are the first thing a homeowner judges. I make asking for reviews automatic, and answer every one.",
     "The trust machine"),
]

STEPS = [
    ("Call Aaron",
     "Ten minutes. Tell me your trade and where the phone&rsquo;s gone quiet. I&rsquo;ll tell you straight whether I can help, no pitch."),
    ("Get a straight plan with real prices",
     "No mystery quote. A plain plan, the exact monthly number, and what you get for it, so you decide with everything in front of you."),
    ("Your phone rings, and you see the receipts",
     "The work goes live in days. Every month you get a plain-English list of exactly what I did, and you watch the booked jobs land on your calendar."),
]

TRADES = [
    ("hvac-marketing", "HVAC &amp; AC"), ("plumber-marketing", "Plumbers"),
    ("electrician-marketing", "Electricians"), ("roofer-marketing", "Roofers"),
    ("remodeler-marketing", "Remodelers &amp; GCs"), ("fence-marketing", "Fence contractors"),
    ("concrete-marketing", "Concrete"), ("lawn-care-marketing", "Lawn &amp; landscape"),
    ("tree-service-marketing", "Tree services"), ("septic-marketing", "Septic services"),
    ("pressure-washing-marketing", "Pressure washing"), ("pool-service-marketing", "Pool service"),
    ("garage-door-marketing", "Garage door"), ("gutter-marketing", "Gutters"),
    ("pest-control-marketing", "Pest control"), ("painter-marketing", "Painters"),
    ("appliance-repair-marketing", "Appliance repair"),
]

PRICES = [
    ("Website &amp; Growth", "$500", "/mo", "Site, SEO, AEO, blog, outreach, newsletter"),
    ("Social Media", "$500", "/mo", "7 networks &middot; 500&ndash;700 posts &middot; 3 reels a day"),
    ("Paid Ads", "15%", "of spend", "Google + Facebook, tracked to booked jobs"),
]

FAQS = [
    ("Who owns my website and leads if we part ways?",
     "You do, and you did from day one. The website, the domain, the ad accounts, your Google profile, your customer list, all in your name. Fire me and you walk out with every bit of it. I don&rsquo;t hold anything hostage, ever."),
    ("Are my leads and my market exclusive?",
     "Yes. I take one shop per trade in a service area, so I&rsquo;m never working for you and your competitor at the same time. And I don&rsquo;t resell leads to anybody, every call is yours."),
    ("Is there a contract?",
     "No lock-in. It&rsquo;s month to month, no setup fee, no cancellation fee. If I don&rsquo;t earn it this month, fire me and keep everything I built. I&rsquo;d rather keep earning it than trap you into twelve months."),
    ("Who actually does the work &mdash; you or an offshore team?",
     "Me. Aaron. Not a rep, not an offshore team reading a script. You get the person who ran marketing for cPanel and Monarx. And because I cap how many shops I take, you actually get my attention."),
    ("How fast do you answer?",
     "You get me, not a ticket in a queue. I answer the phone, or I call you back the same day. That&rsquo;s part of the written guarantee, not a nice-to-have."),
    ("What does it cost?",
     "No games: Website &amp; Growth is $500/mo, Social Media is $500/mo, and paid ads are 15% of your ad spend (with a $2,000/mo minimum ad budget). Run one, run all three. No setup fees, no contracts. Your ad money goes straight to Google or Facebook, never to me, and I show you every dollar."),
]

# ---------------------------------------------------------------- render
clauses = "".join(
    f'<div class="clause"><span class="clause-n">{i:02d}</span><div><h3>{t}</h3><p>{b}</p></div></div>'
    for i, (t, b) in enumerate(CLAUSES, 1))

services = "".join(
    f'<div class="srv-row"><div><h3>{t}</h3><p>{b}</p></div><span class="srv-note">{n}</span></div>'
    for t, b, n in SERVICES)

steps = "".join(
    f'<div class="step"><span class="step-n">{i}</span><div><h3>{t}</h3><p>{b}</p></div></div>'
    for i, (t, b) in enumerate(STEPS, 1))

trades = "".join(f'<a href="/{s}/">{l}</a>' for s, l in TRADES)

prices = "".join(
    f'<div class="price-cell"><span class="price-name">{n}</span>'
    f'<span class="price">{p}<small>{u}</small></span><span class="price-sub">{s}</span></div>'
    for n, p, u, s in PRICES)

faqs = "".join(
    f'<details><summary>{q}</summary><div class="a">{a}</div></details>' for q, a in FAQS)

PAGE = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<script>document.documentElement.classList.add('js')</script>
<title>Hey Aaron! — design direction v2 proof (Ink &amp; Iron)</title>
<meta name="description" content="Internal design proof — the aaron.chat homepage recomposed in the Ink &amp; Iron system. Copy held constant.">
<meta name="theme-color" content="#1E2A24">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600&family=Public+Sans:wght@400..800&family=JetBrains+Mono:wght@400..700&display=swap">
<link rel="stylesheet" href="/brand/ha2.css?v={VER}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}

<header class="head">
  <div class="wrap">
    <a href="/v2/" aria-label="Hey Aaron! home">{LOGO}</a>
    <nav aria-label="Main">
      <a href="/services/">What I do</a><a href="/trades/">Who I help</a>
      <a href="/work/">Real work</a><a href="/pricing/">Pricing</a><a href="/about/">About</a>
    </nav>
    <a class="head-call" href="{TEL}">{PHONE_SVG}713-384-8985</a>
  </div>
</header>

<main id="main">

<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">East Texas &middot; one contractor per market</span>
      <h1>Tired of paying for leads that <span class="hl">ghost you</span>?</h1>
      <p class="hero-sub">I&rsquo;m Aaron. I get contractors in East Texas booked jobs &mdash; real work on your
      calendar, not clicks you paid for. You own every asset I build. Month to month. And I only take one shop
      per trade in a market, so your competitor can&rsquo;t hire me.</p>
      <div class="hero-cta">
        <a class="btn btn-call btn-lg" href="{TEL}">{PHONE_SVG}Call Aaron &mdash; he actually answers</a>
      </div>
      <p class="hero-note"><b>713-384-8985</b> &nbsp;&middot;&nbsp; you call, I answer. No sales rep, no queue.</p>
    </div>
    <div class="hero-media">
      <div class="frame">
        <img src="/brand/media/ha/hero.jpg" width="1400" height="933" fetchpriority="high" decoding="async"
          alt="Aaron Phillips laughing on the phone at his desk, notepad and coffee in front of him">
      </div>
      <div class="hero-stat"><b>20</b><span>years doing this for a living</span></div>
    </div>
  </div>
</section>

<div class="creds">
  <div class="wrap">
    <span class="lbl">Where I learned this</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Ex-CBO, cPanel</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Ex-CMO, Monarx</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Co-founder, Consent Resolve</span>
    <a class="item" href="/work/"><svg><use href="#i-web"/></svg>See sites I&rsquo;ve built &rarr;</a>
  </div>
</div>

<section class="sec">
  <div class="wrap split">
    <div class="split-media">
      <div class="frame">
        <img src="/brand/media/ha/hero.jpg" width="1400" height="933" loading="lazy" decoding="async"
          alt="Aaron Phillips at his desk, mid-call">
      </div>
    </div>
    <div>
      <h2 style="font-size:var(--d-sec);margin:14px 0 18px">Hey, I&rsquo;m Aaron.</h2>
      <p class="lede">I&rsquo;ve been on your side of this. I&rsquo;ve written checks to vendors who overpromised and
      disappeared, and sat there holding a slick report that didn&rsquo;t mean one dollar of real work. That&rsquo;s
      half the reason I do this the way I do.</p>
      <p class="lede">The other half: I spent 20 years running marketing at the top of the tech world, Chief Business
      Officer at cPanel, CMO at Monarx, co-founder of my own company. Then I moved to Livingston and got tired of
      watching good contractors, roofers, HVAC guys, plumbers, electricians, garage-door shops, lose to worse ones
      online.</p>
      <p class="lede">So I point that same firepower at your shop and I do the whole thing myself. No account
      manager. No offshore team. No ticket in a queue. You call, I answer.</p>
      <div class="hero-cta">
        <a class="btn btn-call" href="{TEL}">{PHONE_SVG}Call and ask me anything</a>
        <a class="btn btn-ghost" href="/about/">More about me</a>
      </div>
    </div>
  </div>
</section>

<section class="sec" style="background:var(--paper-raised);border-block:1px solid var(--rule)">
  <div class="wrap">
    <div class="sec-head">
      <h2>The Straight Deal</h2>
      <p class="lede">One package, six promises I put in writing. No fine print, no fifty-page contract, no games.</p>
    </div>
    <div class="clauses">{clauses}</div>
    <div class="pledge">
      <span class="eyebrow">And two that protect you, in writing</span>
      <div class="pledge-grid">
        <div><h3>One shop per market</h3><p>I take one shop per trade in your service area. Once you&rsquo;re in, your
        competitor down the road literally can&rsquo;t hire me. I work for you, not the whole town.</p></div>
        <div><h3>The guarantee</h3><p>Everything on your task list that month, done and shown to you, or that month
        is free. And I answer the phone, or I call you back the same day.</p></div>
      </div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <h2>What I actually do</h2>
      <p class="lede">Everything that gets you found and gets you called. And yeah, I run every one of these tactics
      right here on this page. The site is the demo.</p>
    </div>
    <div class="srv">{services}</div>
  </div>
</section>

<section class="sec" style="background:var(--paper-raised);border-block:1px solid var(--rule)">
  <div class="wrap">
    <div class="sec-head">
      <h2>Built for your trade, not &ldquo;small business&rdquo; in general</h2>
      <p class="lede">The way you win a job isn&rsquo;t the way a roofer or a plumber wins theirs. Pick your trade and
      see marketing aimed at exactly how <em>your</em> phone rings.</p>
    </div>
    <div class="trades">{trades}</div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <h2>Here&rsquo;s exactly how this goes</h2>
      <p class="lede">Three steps. No 40-page proposal, no discovery-call runaround.</p>
    </div>
    <div class="steps">{steps}</div>
  </div>
</section>

<section class="sec" style="background:var(--paper-raised);border-block:1px solid var(--rule)">
  <div class="wrap">
    <div class="sec-head">
      <h2>Real prices, right here. Month to month.</h2>
      <p class="lede">No contracts, no setup fees, no &ldquo;call for pricing&rdquo; runaround. Two flat plans plus
      ads &mdash; run one, run all three.</p>
    </div>
    <div class="prices">{prices}</div>
    <p class="price-kicker">If an agency won&rsquo;t put prices on their website, ask yourself why.</p>
    <div class="guarantee"><svg><use href="#i-shield"/></svg>Everything on your list that month, or that
    month&rsquo;s free. Fire me anytime.</div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <h2>Straight answers</h2>
      <p class="lede">No marketing fluff. Just how this actually works.</p>
    </div>
    <div class="faq">{faqs}</div>
  </div>
</section>

<section class="final">
  <div class="wrap">
    <h2>Every quiet month, your market&rsquo;s up for grabs.</h2>
    <p class="lede">Stay stuck and it&rsquo;s the same feast-or-famine, while the shop across town grabs the spot you
    could&rsquo;ve owned, and once one of your competitors hires me, it&rsquo;s gone. Or: a booked calendar, a phone
    that rings, and a pile of assets that are yours to keep. One call decides which. Ten minutes, no pitch.</p>
    <a class="btn btn-call btn-lg" href="{TEL}">{PHONE_SVG}Call Aaron: 713-384-8985</a>
    <span class="metaline">713-384-8985 &middot; Coldspring, TX</span>
  </div>
</section>

</main>

<footer class="foot">
  <div class="wrap">
    <div class="cols">
      <div>
        {LOGO}
        <p style="margin:12px 0 10px;color:var(--ink-soft);max-width:34ch">Marketing that books jobs for contractors.
        Owner-operated in Coldspring, TX.</p>
        <a class="phone" href="{TEL}">713-384-8985</a>
        <a href="mailto:hello@aaron.chat">hello@aaron.chat</a>
      </div>
      <div>
        <h4>What I do</h4>
        <a href="/services/">All services</a><a href="/pricing/">Pricing</a><a href="/work/">Real work</a>
      </div>
      <div>
        <h4>Who I help</h4>
        <a href="/trades/">All 17 trades</a><a href="/about/">About Aaron</a><a href="/questions/">Questions</a>
      </div>
    </div>
    <div class="fine">Hey Aaron! Marketing &middot; Livingston &amp; the Lake Livingston area &middot;
    <b>Internal design proof (v2 &ldquo;Ink &amp; Iron&rdquo;) &mdash; not the live homepage.</b></div>
  </div>
</footer>

<div class="callbar"><a class="btn btn-call" href="{TEL}">{PHONE_SVG}Call Aaron &mdash; 713-384-8985</a></div>
</body>
</html>
'''

out = os.path.join(ROOT, "v2")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(PAGE)
print(f"v2 proof: wrote /v2/index.html  ({len(CLAUSES)} clauses, {len(SERVICES)} services, {len(TRADES)} trades)")
