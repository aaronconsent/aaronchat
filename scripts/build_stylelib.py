#!/usr/bin/env python3
"""Build the Hey Aaron! Style Guide + Component Library on the current ha.css system.

Writes (all noindex, internal):
  /style-guide/            hub: brand snapshot, logo variants + source, color, type, buttons
  /style-guide/library/    the component library (37 on-brand sections)
  /style-guide/icp/        ideal-customer profile: buyer persona + 17 trades + message match

Run: python3 scripts/build_stylelib.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = "106"

IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
LOGO = re.search(r'(<svg class="ha-logo".*?</svg>)', IDX, re.S).group(1)
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]


def esc(s):
    return H.escape(str(s or ""))


def use(icon):
    return f'<svg><use href="#{icon}"/></svg>'


NAVITEMS = [("/style-guide/", "Overview"),
            ("/style-guide/library/", "Components"),
            ("/style-guide/voice/", "Voice"),
            ("/style-guide/icp/", "ICP")]


def shell(active, title, desc, body):
    parts = []
    for href, label in NAVITEMS:
        cls = ' class="on"' if href == active else ''
        parts.append(f'<a href="{href}"{cls}>{esc(label)}</a>')
    nav = "".join(parts)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#23252b">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
<link rel="stylesheet" href="/brand/sg.css?v={VER}">
</head>
<body>
{SPRITE}
<header class="sg-top">
  <span class="brand">{LOGO}<span class="tag">Style guide</span></span>
  <nav>{nav}<a href="/">Back to site &rarr;</a></nav>
</header>
{body}
<footer class="sg-sec" style="text-align:center">
  <div class="sg-wrap"><p class="sg-cap">Hey Aaron! Marketing &middot; internal style guide &middot; built on ha.css v{VER}
  &middot; components use production classes from <code>ha.css</code> + <code>sg.css</code>.</p></div>
</footer>
<script src="/brand/ha.js?v={VER}" defer></script>
</body>
</html>
'''


# ---------------------------------------------------------------- HUB ----------
WORDMARK_NOTE = '''<span class="c">// letterforms in the logo's exact language: stroke 22, body 74, counter 30,</span>
<span class="c">// 2:1 angled terminals, vector shield-curve AA pair. Full generative source:</span>
buildWordmark([<span class="s">"H","E","Y"," ","AA","R","O","N","!"</span>]);'''


def swatch(name, var, hexv):
    return (f'<div class="sg-swatch"><div class="chip" style="background:{hexv}"></div>'
            f'<div class="meta"><b>{esc(name)}</b><span>{esc(hexv)}</span><span>{esc(var)}</span></div></div>')


def p_hub():
    colors = [
        ("Primary", "--primary", "#002f62"),
        ("Primary container", "--primary-container", "#074588"),
        ("Tertiary (accent)", "--tertiary", "#7a4a12"),
        ("Accent bright", "--tertiary-bright", "#b4610c"),
        ("Ink", "--ink", "#16181c"),
        ("Ink variant", "--ink-variant", "#3b414b"),
        ("Surface", "--surface", "#f9f9fe"),
        ("Surface low", "--surface-low", "#f3f3f9"),
        ("Dark (footer)", "--dark", "#23252b"),
        ("Good", "--good", "#1f6b23"),
        ("Info", "--info", "#12508f"),
        ("Danger", "--danger", "#ba1a1a"),
    ]
    sw = "".join(swatch(n, v, h) for n, v, h in colors)

    logos = f'''<div class="sg-logo-row">
      <div><div class="sg-logo-cell on-light">{LOGO}</div><div class="sg-cap">Navy on light &mdash; default</div></div>
      <div><div class="sg-logo-cell on-navy">{LOGO}</div><div class="sg-cap">Reversed on primary-container</div></div>
      <div><div class="sg-logo-cell on-dark">{LOGO}</div><div class="sg-cap">Reversed on dark (footer)</div></div>
      <div><div class="sg-logo-cell on-accent">{LOGO}</div><div class="sg-cap">On accent wash</div></div>
    </div>'''

    types = '''
      <div class="sg-type-row"><span class="lbl">Display XL &middot; hero</span><span style="font-size:var(--d-xl);font-weight:700;letter-spacing:-.02em;line-height:1.05">More booked jobs.</span></div>
      <div class="sg-type-row"><span class="lbl">Display LG &middot; section h2</span><span style="font-size:var(--d-lg);font-weight:700;letter-spacing:-.02em">What I actually do</span></div>
      <div class="sg-type-row"><span class="lbl">Headline MD &middot; h3</span><span style="font-size:var(--h-md);font-weight:600">A site that books jobs</span></div>
      <div class="sg-type-row"><span class="lbl">Body LG &middot; lede</span><span style="font-size:var(--body-lg);color:var(--ink-variant)">Marketing that gets your phone ringing, in plain English.</span></div>
      <div class="sg-type-row"><span class="lbl">Caps label</span><span class="caps" style="color:var(--tertiary)">Marketing for the trades</span></div>'''

    body = f'''
<main>
<section class="sg-hero"><div class="sg-wrap">
  <span class="kick">Hey Aaron! Marketing</span>
  <h1>The style guide.</h1>
  <p>One source of truth for how the site looks, sounds, and gets built: the brand, a live component
  library, and who we build it all for. Everything here runs on the same <code>ha.css</code> the live site uses.</p>
  <div class="hero-cta" style="margin-top:20px">
    <a class="btn btn-call" href="/style-guide/library/">Open the component library</a>
    <a class="btn btn-ghost" href="/style-guide/icp/">See the ICP</a>
  </div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Logo</h2>
  <p class="lead">The wordmark is a custom geometric build in the brand's own letterform language. Keep clear space
  equal to the bar height; never recolor mid-letter, stretch, or add effects. Use the reversed (white) version on
  navy or dark.</p>
  {logos}
  <p class="sg-cap" style="text-align:left;margin-top:18px">Production logo = the inline <code>&lt;svg class="ha-logo"&gt;</code> (fill: currentColor, so it
  inherits text color). Generative source stored at <a href="/brand/logo/hey-aaron-wordmark">/brand/logo/hey-aaron-wordmark</a>.</p>
  <div class="sg-code">{WORDMARK_NOTE}</div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Color</h2>
  <p class="lead">The Stitch palette, exact. Deep navy carries the brand; burnt orange is the accent, used sparingly
  for links, stars, and rules. All text pairings are checked to WCAG AA.</p>
  <div class="sg-swatches">{sw}</div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Typography</h2>
  <p class="lead">Inter, everywhere. Tight tracking and heavy weights for authority; generous line-height for body.</p>
  {types}
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Buttons &amp; links</h2>
  <p class="lead">Primary action is always a call. Ghost for secondary, white for dark backgrounds.</p>
  <div class="sg-demo"><div class="pad" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
    <a class="btn btn-call" href="#0">{use('i-phone')}Call me: 713-384-8985</a>
    <a class="btn btn-ghost" href="#0">More about me</a>
    <span style="background:var(--dark);padding:14px;border-radius:8px"><a class="btn btn-white" href="#0">{use('i-phone')}Call Aaron</a></span>
    <a href="#0" style="color:var(--tertiary);font-weight:600">A text link</a>
  </div></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>What&rsquo;s next in here</h2>
  <p class="lead">Sections growing over time.</p>
  <div class="sg-swatches">
    <div class="sg-swatch"><div class="chip" style="background:var(--primary-container);display:grid;place-items:center;color:#fff;font-weight:700">Done</div><div class="meta"><b><a href="/style-guide/library/">Component library</a></b><span>37 on-brand blocks</span></div></div>
    <div class="sg-swatch"><div class="chip" style="background:var(--primary-container);display:grid;place-items:center;color:#fff;font-weight:700">Done</div><div class="meta"><b><a href="/style-guide/icp/">ICP details</a></b><span>persona + 17 trades</span></div></div>
    <div class="sg-swatch"><div class="chip" style="background:var(--surface-high);display:grid;place-items:center;color:var(--ink-variant);font-weight:700">Soon</div><div class="meta"><b>Voice &amp; tone</b><span>your call, when ready</span></div></div>
    <div class="sg-swatch"><div class="chip" style="background:var(--surface-high);display:grid;place-items:center;color:var(--ink-variant);font-weight:700">Soon</div><div class="meta"><b>Motion</b><span>timings + easing</span></div></div>
  </div>
</div></section>
</main>'''
    return shell("/style-guide/", "Style guide — Hey Aaron! Marketing",
                 "Brand, components, and ICP for the Hey Aaron! Marketing site.", body)


# ------------------------------------------------------------- LIBRARY ----------
def item(cid, name, ref, when, demo, tight=False):
    return f'''<div class="sg-item" id="{cid}">
  <div class="sg-h"><h3>{esc(name)}</h3><span class="sg-ref">{esc(ref)}</span></div>
  <p class="sg-when">{when}</p>
  <div class="sg-demo{' tight' if tight else ''}"><div class="pad">{demo}</div></div>
</div>'''


def group(title, items):
    return f'<section class="sg-sec"><div class="sg-wrap"><h2>{esc(title)}</h2>{"".join(items)}</div></section>'


def check_li(txt):
    return f'<li>{use("i-check")}<span>{txt}</span></li>'


def p_library():
    I = []  # (group, item-html), collected then grouped

    # ---- Bars & overlays ----
    bars = [
        item("notification-bar", "Notification bar", "Notification Bar",
             "Thin, quiet, informational. <b>Use for</b> hours, weather/seasonal notices, or a soft status line. Never for hard offers.",
             f'<div class="notifbar">{use("i-bolt")}Storm season is here &mdash; I answer calls 7 days a week. <a href="tel:+17133848985">713-384-8985</a></div>', tight=True),
        item("promotion-bar", "Promotion bar", "Promotion Bar",
             "Louder and dismissible. <b>Use for</b> a real, time-boxed offer only &mdash; honest urgency, never a fake countdown.",
             '<div class="promobar">Booked solid? I keep a cap on clients. A couple of spots open this month. <a class="btn" href="tel:+17133848985">Grab one</a><button class="x" aria-label="Dismiss">&times;</button></div>', tight=True),
        item("cookie", "Cookie consent", "Cookie",
             "Privacy-first. <b>Use for</b> consent when analytics/pixels load. Default to the least-intrusive choice.",
             '<div class="cookiebar"><p>This site uses a couple of cookies to see what&rsquo;s working. Your call. <a href="/privacy-policy/">Privacy</a>.</p><div class="row"><a class="btn btn-call" href="#0">Accept</a><a class="btn btn-ghost" href="#0">Only essentials</a></div></div>'),
        item("popup", "Popup / modal", "Popup",
             "One honest question on exit, once per session. <b>Use for</b> a last-chance nudge &mdash; the production version is the exit-intent modal.",
             '<div style="position:relative;max-width:440px;margin-inline:auto"><div class="ha-modal-card" style="position:static"><button class="ha-modal-x" aria-label="Close" style="position:absolute">&times;</button><h3>Before you go &mdash; one honest question.</h3><p>Is the phone ringing like it used to? If not, that&rsquo;s a ten-minute call to fix. No pitch, no contract.</p><a class="btn btn-call btn-block" href="tel:+17133848985">' + use("i-phone") + 'Call Aaron: 713-384-8985</a></div></div>'),
    ]

    # ---- Navigation ----
    header_demo = f'''<div style="border-radius:10px;overflow:clip"><header class="site-head" style="position:static">
  <div class="wrap"><a href="#0" aria-label="Hey Aaron! home">{LOGO}</a>
  <nav class="site-nav" aria-label="Main"><a href="#0">What I do</a><a href="#0">Who I help</a><a href="#0">Real work</a><a href="#0">Pricing</a><a href="#0">About</a></nav>
  <a class="head-call" href="#0">{use('i-phone')}713-384-8985</a>
  <button class="nav-toggle" aria-label="Menu">{use('i-menu')}</button></div></header></div>'''
    footer_demo = f'''<footer class="site-foot" style="border-radius:10px;overflow:clip"><div class="wrap" style="padding-block:28px">
  <div class="brandcol">{LOGO}<p style="margin-top:6px">Marketing that books jobs for contractors. Owner-operated in Coldspring, TX.</p>
  <p style="margin-top:10px"><a href="#0" style="display:inline">713-384-8985</a> &middot; <a href="#0" style="display:inline">hello@aaron.chat</a></p></div>
  <div><h4>What I do</h4><a href="#0">Websites</a><a href="#0">Local SEO</a><a href="#0">Paid ads</a><a class="seeall" href="#0">All services &rarr;</a></div>
  <div><h4>Who I help</h4><a href="#0">HVAC</a><a href="#0">Plumbers</a><a href="#0">Roofers</a><a class="seeall" href="#0">All trades &rarr;</a></div>
  <div><h4>Company</h4><a href="#0">Real work</a><a href="#0">Pricing</a><a href="#0">About</a></div>
</div></footer>'''
    nav = [
        item("header", "Header / nav", "Header",
             "Sticky top bar, phone always visible, mobile hamburger. <b>Use on</b> every page.", header_demo, tight=True),
        item("footer", "Footer", "Footer",
             "4-column directory: services, trades, company + fine print. <b>Use on</b> every page &mdash; big for discoverability and SEO.", footer_demo, tight=True),
    ]

    # ---- Hero & top-of-page ----
    hero_demo = f'''<section class="hero grid-bg" style="border-radius:10px"><div class="wrap" style="padding:20px">
  <div><span class="pill"><span class="dot pulse"></span>Marketing for the trades</span>
  <h1 style="font-size:clamp(1.8rem,1.2rem+2vw,2.6rem)">More booked jobs for <span style="color:var(--primary-container)">contractors</span>. Not more "leads."</h1>
  <p class="hero-sub">I&rsquo;m Aaron. 20 years of real marketing, now pointed at your shop.</p>
  <div class="hero-cta"><a class="btn btn-call btn-lg" href="#0">{use('i-phone')}Call me: 713-384-8985</a>
  <span class="hero-note">{use('i-check')}You get Aaron, not a sales rep</span></div></div>
  <div class="hero-media"><div class="frame"><div class="imgslot imgslot--wide" style="height:180px"><span class="lbl">Founder photo drops in here</span></div></div></div>
</div></section>'''
    top = [
        item("hero", "Hero", "Hero",
             "The thesis. Headline promise + the one action (call) + a founder-real visual. <b>Use as</b> the opening of any landing page.", hero_demo, tight=True),
        item("problem", "Problem", "Problem",
             "Name the pain in the customer&rsquo;s words before the pitch. <b>Use right after</b> the hero to earn the read.",
             '<div class="sec-head center"><h2 style="font-size:1.6rem">You do great work. So why is the phone quiet?</h2><p class="lede">When someone&rsquo;s AC quits at 11pm, they call the first shop that looks legit on Google. If that&rsquo;s not you, it&rsquo;s the shop across town &mdash; and it&rsquo;s a marketing problem, not a skill problem.</p></div>'),
        item("solution", "Solution", "Solution",
             "Show the fix as a simple, believable path. <b>Use to</b> answer the problem you just named.",
             f'<div class="split2"><div><span class="caps" style="color:var(--tertiary)">The fix</span><h3 style="font-size:1.5rem;margin:6px 0">Be the obvious choice when they search.</h3><ul>{check_li("A site that loads fast and turns clicks into calls")}{check_li("Top of the local map when they search near you")}{check_li("Every dollar tracked to a booked job")}</ul></div><div class="art"></div></div>'),
        item("how-it-works", "How it works", "How It Works",
             "Three plain steps, no jargon. <b>Use to</b> de-risk starting.",
             '<div class="steps"><div class="step"><span class="n">1</span><div><h3>Call me</h3><p>Tell me your trade and where the phone&rsquo;s quiet. Ten minutes.</p></div></div><div class="step"><span class="n">2</span><div><h3>I build it</h3><p>Site, Google, ads, tracking &mdash; usually live in days.</p></div></div><div class="step"><span class="n">3</span><div><h3>Your phone rings</h3><p>We watch booked jobs, not clicks. Month to month.</p></div></div></div>'),
        item("feature", "Feature grid", "Feature",
             "Scannable capability cards with an icon + demo tag. <b>Use to</b> lay out what you do.",
             f'''<div class="cards"><div class="card"><span class="ic">{use('i-web')}</span><h3>A site that books jobs</h3><p>Fast, clean, built to turn a click into a call.</p><span class="demo-tag">You&rsquo;re on one now</span></div>
             <div class="card"><span class="ic">{use('i-search')}</span><h3>Show up on Google</h3><p>Local SEO + your Google profile done right.</p><span class="demo-tag">Ask where you rank</span></div>
             <div class="card"><span class="ic">{use('i-target')}</span><h3>Ads that pay for themselves</h3><p>Aimed at people who need you now.</p><span class="demo-tag">Tracked, not guessed</span></div></div>'''),
        item("content", "Content / rich text", "Content",
             "Long-form prose for case studies, guides, legal. <b>Use for</b> anything read top to bottom.",
             '<div class="contentblock"><h3>Why I do this</h3><p>I spent 20 years running marketing at the top of the tech world. Then I moved to Livingston and got tired of watching good contractors lose to worse ones online.</p><h4>What that means for you</h4><p>Same firepower I used for companies you&rsquo;ve heard of, pointed at your trucks &mdash; in plain English, month to month.</p></div>'),
    ]

    # ---- Proof & trust ----
    proof = [
        item("logo-cloud", "Logo cloud", "Logo Cloud",
             "Borrowed credibility as a quiet row. <b>Use</b> real logos only &mdash; here, where Aaron&rsquo;s experience comes from.",
             '<div class="logocloud"><div class="lbl">Where I learned this</div><div class="row"><b>cPanel</b><b>Monarx</b><b>Consent Resolve</b><b>Rocket</b><b>Help.com</b></div></div>'),
        item("stats", "Stats", "Stats",
             "Big honest numbers. <b>Use</b> only true figures &mdash; never invent a growth stat.",
             '<div class="statstrip"><div class="stat"><div class="n">20 yrs</div><div class="l">doing marketing for a living</div></div><div class="stat"><div class="n">7+</div><div class="l">real sites shipped</div></div><div class="stat"><div class="n">1</div><div class="l">person you call &mdash; me</div></div><div class="stat"><div class="n">$0</div><div class="l">setup fees, ever</div></div></div>'),
        item("testimonial", "Testimonial", "Testimonial",
             "Social proof in the customer&rsquo;s voice. <b>Integrity rule:</b> no testimonial ships until it&rsquo;s a real client&rsquo;s real words &mdash; the block below is a labeled placeholder.",
             '<div class="quotecard"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;[Real client quote goes here once we have one &mdash; their words, their name, their trade.]&rdquo;</blockquote><div class="who"><span class="av"></span><div><b>Client name</b><br><span style="color:var(--ink-variant);font-size:.85rem">Trade &middot; Town, TX</span></div></div><div class="ph-note">Placeholder &mdash; never ship a fabricated testimonial.</div></div>'),
        item("case-studies", "Case studies", "Case studies",
             "Real, clickable work. <b>Use to</b> prove it&rsquo;s live, not fan fiction.",
             '''<div class="worklist"><a class="workcard" href="#0"><div class="shot"><div class="imgslot" style="height:150px"></div></div><div class="meta"><div class="t">G4 Electric</div><div class="s">Electrician &middot; a trade like yours</div></div></a>
             <a class="workcard" href="#0"><div class="shot"><div class="imgslot" style="height:150px"></div></div><div class="meta"><div class="t">Polk County Golf Carts</div><div class="s">Local retail &middot; Livingston, TX</div></div></a></div>'''),
        item("competitors", "Competitors / comparison", "Competitors",
             "Honest side-by-side. <b>Use to</b> frame the choice without trashing anyone.",
             '''<div style="overflow-x:auto"><table class="compare"><thead><tr><th>&nbsp;</th><th class="me">Hey Aaron!</th><th>Typical agency</th><th>DIY</th></tr></thead><tbody>
             <tr><td>You reach a person</td><td class="me"><span class="yes">Always Aaron</span></td><td><span class="no">Account manager</span></td><td><span class="no">You are it</span></td></tr>
             <tr><td>Contract</td><td class="me"><span class="yes">Month to month</span></td><td><span class="no">6&ndash;12 months</span></td><td>&mdash;</td></tr>
             <tr><td>Tracks booked jobs</td><td class="me"><span class="yes">Yes</span></td><td><span class="no">Clicks</span></td><td><span class="no">No</span></td></tr>
             </tbody></table></div>'''),
        item("before-after", "Before / after", "Before After",
             "The trade&rsquo;s superpower &mdash; visual proof. <b>Use for</b> concrete, painting, pressure washing, remodels.",
             '<div class="bagrid"><div class="bacard"><div class="img"><span class="badge">Before</span></div></div><div class="bacard after"><div class="img"><span class="badge">After</span></div></div></div>'),
        item("awards", "Awards / recognition", "Awards",
             "Badges of trust. <b>Use</b> real credentials only &mdash; placeholders shown until earned.",
             f'<div class="awards"><div class="awardcard"><span class="ic">{use("i-shield")}</span><b>Licensed &amp; local</b><span>Livingston, TX</span></div><div class="awardcard"><span class="ic">{use("i-trend")}</span><b>[Award]</b><span>when earned</span></div><div class="awardcard"><span class="ic">{use("i-check")}</span><b>[Badge]</b><span>real only</span></div></div>'),
        item("partners", "Partners", "Partners",
             "Who you build on. <b>Use for</b> platform partners (Google, Meta) once formalized.",
             '<div class="logocloud"><div class="lbl">Built on platforms you already trust</div><div class="row"><b>Google</b><b>Meta</b><b>Cloudflare</b><b>Resend</b></div></div>'),
    ]

    # ---- Info & context ----
    info = [
        item("audience", "Audience / who it&rsquo;s for", "Audience",
             "Qualify fast &mdash; who this is and isn&rsquo;t for. <b>Use to</b> attract the right shop and repel the wrong fit.",
             f'''<div class="audiencegrid"><div class="audcard is"><h4>{use('i-check')}Built for you if&hellip;</h4><ul>{check_li("You run 1&ndash;15 service trucks")}{check_li("You&rsquo;re the owner, and the phone matters")}{check_li("You&rsquo;d rather book jobs than chase clicks")}</ul></div>
             <div class="audcard not"><h4>{use('i-check')}Probably not if&hellip;</h4><ul>{check_li("You want the cheapest possible logo")}{check_li("You need a national brand campaign")}{check_li("You want a 12-month lock-in")}</ul></div></div>'''),
        item("timeline", "Timeline", "Timeline",
             "A sequence that carries real order &mdash; history or onboarding. <b>Use for</b> the founder story or the first 30 days.",
             '<div class="timeline"><div class="ev"><div class="yr">Day 1</div><h4>We talk</h4><p>Ten-minute call. Your trade, your gaps.</p></div><div class="ev"><div class="yr">Day 2&ndash;5</div><h4>I build</h4><p>Site + Google profile go live.</p></div><div class="ev"><div class="yr">Week 2</div><h4>The phone rings</h4><p>Ads and tracking switched on.</p></div></div>'),
        item("team", "Team", "Team",
             "Who&rsquo;s behind it. <b>Honest here:</b> it&rsquo;s one guy &mdash; that&rsquo;s the pitch.",
             '<div class="teamgrid" style="max-width:280px"><div class="teamcard"><div class="ph"></div><h4>Aaron Phillips</h4><div class="role">Founder &amp; the whole team</div><p>Ex-CBO cPanel, ex-CMO Monarx. You call, I answer.</p></div></div>'),
        item("integrations", "Integrations", "Integrations",
             "The tools you wire together for the client. <b>Use to</b> show the stack without jargon.",
             '<div class="intgrid"><div class="intcard"><span class="dot">G</span>Google Business</div><div class="intcard"><span class="dot">Ads</span>Google Ads</div><div class="intcard"><span class="dot">f</span>Facebook</div><div class="intcard"><span class="dot">@</span>Email / Resend</div><div class="intcard"><span class="dot">SMS</span>Text follow-up</div><div class="intcard"><span class="dot">&#9733;</span>Reviews</div></div>'),
        item("maps", "Maps / service area", "Maps",
             "Ground the business in place. <b>Use to</b> show the service radius for local SEO.",
             '<div class="maptile"><div class="canvas"><span class="pin"></span></div><div class="side"><h4>Serving East Texas</h4><p style="color:var(--ink-variant);font-size:.9rem">Livingston and the Lake Livingston area.</p><div class="areas"><span>Livingston</span><span>Onalaska</span><span>Coldspring</span><span>Huntsville</span><span>Trinity</span></div></div></div>'),
        item("blog", "Blog", "Blog",
             "Content that ranks and answers. <b>Use for</b> the auto-blog and guides.",
             '''<div class="bloggrid"><article class="blogcard"><div class="thumb"></div><div class="b"><span class="cat">HVAC</span><h4>Why your AC leads dry up in October</h4><p>And the three things that keep the calls coming in the shoulder season.</p><div class="meta">5 min read</div></div></article>
             <article class="blogcard"><div class="thumb"></div><div class="b"><span class="cat">Local SEO</span><h4>The Google Business trick most contractors miss</h4><p>A fifteen-minute fix that moves you up the map.</p><div class="meta">4 min read</div></div></article></div>'''),
        item("api", "API / technical block", "API",
             "For a technical audience. <b>Use sparingly</b> &mdash; most contractors don&rsquo;t need this; keep it for tooling or partner pages.",
             '''<div class="apiblock"><div class="copy"><h4>Leads, wired straight to you</h4><p>Every form and callback posts to a single endpoint and emails you instantly &mdash; no dashboard to babysit.</p></div><div class="sg-code" style="margin:0"><span class="k">POST</span> /api/lead
<span class="s">{ "phone": "&hellip;", "trade": "&hellip;" }</span>
<span class="c">// &rarr; emails Aaron in seconds</span></div></div>'''),
    ]

    # ---- Conversion ----
    conv = [
        item("cta", "Call to action", "Call To Action",
             "The recurring ask. Always a call, with the risk-reversal line. <b>Use to</b> close every section.",
             f'<div class="sec-head center"><h2 style="font-size:1.5rem">Ready when you are.</h2><p class="lede">Ten minutes, no pitch, no contract.</p><div style="margin-top:16px"><a class="btn btn-call btn-lg" href="#0">{use("i-phone")}Call Aaron: 713-384-8985</a></div><div class="guarantee" style="margin-top:14px">{use("i-shield")}If I&rsquo;m not booking you jobs, fire me.</div></div>'),
        item("pricing", "Pricing", "Pricing",
             "Straight prices, modular. <b>Use to</b> kill the &ldquo;call for pricing&rdquo; friction.",
             f'''<div class="tiers"><div class="tier pop"><span class="badge">Start here</span><span class="name">Website &amp; Growth</span><div class="price">$500<span>/mo</span></div><p class="sub">The foundation.</p><ul>{check_li("Fast managed website")}{check_li("Local SEO + AEO")}{check_li("Blog, outreach, newsletter")}</ul><a class="btn btn-call btn-block" href="#0">Call to start</a></div>
             <div class="tier"><span class="name">Social Media</span><div class="price">$500<span>/mo</span></div><p class="sub">7 networks, handled.</p><ul>{check_li("500&ndash;700 posts/mo")}{check_li("3 reels a day")}{check_li("100% automated")}</ul><a class="btn btn-call btn-block" href="#0">Call to start</a></div>
             <div class="tier"><span class="name">Paid Ads</span><div class="price">15%<span>of spend</span></div><p class="sub">Scale when ready.</p><ul>{check_li("Google + Facebook")}{check_li("$2,000/mo min budget")}{check_li("Tracked to jobs")}</ul><a class="btn btn-call btn-block" href="#0">Call to start</a></div></div>'''),
        item("products", "Products / packages", "Products",
             "For a service business, &ldquo;products&rdquo; = productized services. <b>Use to</b> present add-ons.",
             f'''<div class="cards"><div class="card"><span class="ic">{use('i-image')}</span><h3>Reel package</h3><p>Short vertical video that stops the scroll, made monthly.</p></div>
             <div class="card"><span class="ic">{use('i-trend')}</span><h3>Review engine</h3><p>Automatic review requests after every job.</p></div>
             <div class="card"><span class="ic">{use('i-search')}</span><h3>AEO tune-up</h3><p>Get quoted by AI answer engines, not just Google.</p></div></div>'''),
        item("demo", "Demo", "Demo",
             "&ldquo;The site is the demo.&rdquo; A framed product shot. <b>Use to</b> show, not tell.",
             '<div class="frame" style="max-width:520px;margin-inline:auto"><div class="imgslot imgslot--wide" style="height:240px"><span class="tag">Live product screenshot</span><span class="lbl">A site I built, shown right here</span></div></div>'),
        item("faq", "FAQ", "FAQ",
             "Objections, answered plainly, with FAQ schema. <b>Use near</b> the bottom of every page.",
             '<div class="faq"><details open><summary>What does it cost?<svg class="chev"><use href="#i-chev"/></svg></summary><div class="a">$500/mo for Website &amp; Growth, $500/mo for Social, ads at 15% of spend. Month to month.</div></details><details><summary>Who does the work?<svg class="chev"><use href="#i-chev"/></svg></summary><div class="a">Me. Aaron. You call, I answer.</div></details></div>'),
        item("newsletter", "Newsletter", "Newsletter",
             "Owned audience. <b>Use to</b> capture emails for the monthly send.",
             '<div class="newsletter"><h3>The monthly your customers actually read</h3><p>One useful email a month for East Texas contractors. No spam, unsubscribe anytime.</p><form class="inlineform" onsubmit="return false"><input type="email" placeholder="you@yourshop.com" aria-label="Email"><button class="btn btn-white" type="submit">Sign me up</button><span class="note">We never share your email.</span></form></div>'),
        item("lead-magnet", "Lead magnet", "Leadmagnet",
             "A useful free thing in exchange for an email. <b>Use to</b> warm up people not ready to call.",
             '<div class="leadmag"><div class="cover"><b>The 7-Point Contractor Website Checklist</b></div><div><span class="caps" style="color:var(--tertiary)">Free download</span><h3 style="font-size:1.4rem;margin:6px 0 8px">Is your site costing you jobs?</h3><p style="color:var(--ink-variant);margin-bottom:14px">Seven things I check on every contractor site. Grab the checklist, no call required.</p><form class="inlineform" style="margin:0" onsubmit="return false"><input type="email" placeholder="you@yourshop.com" aria-label="Email"><button class="btn btn-call" type="submit">Send it</button></form></div></div>'),
        item("signup", "Signup", "Signup",
             "Account creation. <b>Note:</b> Aaron is call-first, so this is for a future client portal, not the main funnel.",
             '<div class="authcard"><h3>Create your client login</h3><p class="sub">See your site, leads, and reports in one place.</p><div class="field"><label>Name</label><input placeholder="Your name"></div><div class="field"><label>Email</label><input type="email" placeholder="you@yourshop.com"></div><div class="field"><label>Password</label><input type="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"></div><button class="btn btn-call btn-block">Create account</button><p class="alt">Already have one? <a href="#0" style="color:var(--tertiary);font-weight:600">Log in</a></p></div>'),
        item("login", "Login", "Login",
             "Return access for the client portal. <b>Use for</b> the same future portal as signup.",
             '<div class="authcard"><h3>Welcome back</h3><p class="sub">Log in to your dashboard.</p><div class="field"><label>Email</label><input type="email" placeholder="you@yourshop.com"></div><div class="field"><label>Password</label><input type="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"></div><button class="btn btn-call btn-block">Log in</button><p class="alt"><a href="#0" style="color:var(--tertiary);font-weight:600">Forgot password?</a></p></div>'),
        item("contact", "Contact", "Contact",
             "Every way to reach a human. <b>Use to</b> put the phone first, form second.",
             f'''<div class="contactgrid"><div><div class="chan"><span class="ic">{use('i-phone')}</span><div><b>Call or text</b><span>713-384-8985 &mdash; you get Aaron</span></div></div>
             <div class="chan"><span class="ic">{use('i-msg')}</span><div><b>Email</b><span>hello@aaron.chat</span></div></div>
             <div class="chan"><span class="ic">{use('i-web')}</span><div><b>Where</b><span>Livingston, TX &middot; serving East Texas</span></div></div></div>
             <div><div class="field"><label>Name</label><input placeholder="Your name"></div><div class="field"><label>Phone</label><input placeholder="(000) 000-0000"></div><div class="field"><label>What&rsquo;s up?</label><input placeholder="Phone&rsquo;s been quiet&hellip;"></div><button class="btn btn-call btn-block">Send it to Aaron</button></div></div>'''),
    ]

    toc_groups = [
        ("Bars &amp; overlays", bars, ["notification-bar", "promotion-bar", "cookie", "popup"],
         ["Notification bar", "Promotion bar", "Cookie", "Popup"]),
        ("Navigation", nav, ["header", "footer"], ["Header", "Footer"]),
        ("Hero &amp; top of page", top, ["hero", "problem", "solution", "how-it-works", "feature", "content"],
         ["Hero", "Problem", "Solution", "How it works", "Feature grid", "Content"]),
        ("Proof &amp; trust", proof, ["logo-cloud", "stats", "testimonial", "case-studies", "competitors", "before-after", "awards", "partners"],
         ["Logo cloud", "Stats", "Testimonial", "Case studies", "Competitors", "Before / after", "Awards", "Partners"]),
        ("Info &amp; context", info, ["audience", "timeline", "team", "integrations", "maps", "blog", "api"],
         ["Audience", "Timeline", "Team", "Integrations", "Maps", "Blog", "API"]),
        ("Conversion", conv, ["cta", "pricing", "products", "demo", "faq", "newsletter", "lead-magnet", "signup", "login", "contact"],
         ["CTA", "Pricing", "Products", "Demo", "FAQ", "Newsletter", "Lead magnet", "Signup", "Login", "Contact"]),
    ]

    total = sum(len(g[1]) for g in toc_groups)
    toc = ""
    for gtitle, _, ids, names in toc_groups:
        links = "".join(f'<a href="#{i}">{esc(n)}</a>' for i, n in zip(ids, names))
        toc += f'<div style="break-inside:avoid;margin-bottom:14px"><b style="display:block;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-variant);margin-bottom:4px">{gtitle}</b>{links}</div>'

    sections = "".join(group(re.sub("&amp;", "&", g[0]), g[1]) for g in toc_groups)

    body = f'''
<main>
<section class="sg-hero"><div class="sg-wrap">
  <span class="kick">Component library</span>
  <h1>{total} building blocks, on brand.</h1>
  <p>Every section below is a live, on-brand component built from the production <code>ha.css</code> + <code>sg.css</code>.
  Copy the pattern to assemble a new page fast. Anything with a placeholder or integrity note stays honest &mdash;
  no fake reviews, stats, or awards ship to a live page.</p>
  <div class="sg-toc" style="columns:2;margin-top:24px">{toc}</div>
</div></section>
{sections}
</main>'''
    return shell("/style-guide/library/", "Component library — Hey Aaron! Marketing",
                 "37 on-brand, reusable components for building Hey Aaron! pages.", body)


# ----------------------------------------------------------------- ICP ----------
def p_icp():
    trades = [
        ("HVAC & AC", "hvac-marketing"), ("Plumbers", "plumber-marketing"),
        ("Electricians", "electrician-marketing"), ("Roofers", "roofer-marketing"),
        ("Remodelers & GCs", "remodeler-marketing"), ("Fence contractors", "fence-marketing"),
        ("Concrete", "concrete-marketing"), ("Lawn & landscape", "lawn-care-marketing"),
        ("Tree services", "tree-service-marketing"), ("Septic", "septic-marketing"),
        ("Pressure washing", "pressure-washing-marketing"), ("Pool service", "pool-service-marketing"),
        ("Garage door", "garage-door-marketing"), ("Gutters", "gutter-marketing"),
        ("Pest control", "pest-control-marketing"), ("Painters", "painter-marketing"),
        ("Appliance repair", "appliance-repair-marketing"),
    ]
    tg = "".join(f'<a href="/{s}/">{use("i-check")}{esc(n)}</a>' for n, s in trades)

    body = f'''
<main>
<section class="sg-hero"><div class="sg-wrap">
  <span class="kick">Ideal customer profile</span>
  <h1>Who we build all this for.</h1>
  <p>Message-match beats clever every time. This is the one buyer we write and design for &mdash; and the 17 trades
  we tailor it to. When in doubt, write to this person.</p>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>The buyer</h2>
  <p class="lead">One primary persona. Everything on the site should sound like it was written for him.</p>
  <div class="split2"><div>
    <h3 style="font-size:1.4rem">&ldquo;Mike&rdquo; &mdash; the owner-operator</h3>
    <ul>
      {check_li("Owns a 1&ndash;15 truck home-service shop in East Texas")}
      {check_li("Great at the trade, not at marketing &mdash; and knows it")}
      {check_li("Wears every hat; checks his phone between jobs, mostly on mobile")}
      {check_li("Been burned by an agency that took a retainer and vanished")}
      {check_li("Judges vendors the way his customers judge him: show up, answer, do what you said")}
    </ul>
  </div><div>
    <h4 style="margin-bottom:8px">What he actually wants</h4>
    <ul style="list-style:none;display:grid;gap:8px">
      {check_li("The phone to ring with real jobs, not &ldquo;leads&rdquo;")}
      {check_li("A straight price and no 12-month trap")}
      {check_li("To reach a human when something breaks")}
    </ul>
    <h4 style="margin:16px 0 8px">What scares him off</h4>
    <ul style="list-style:none;display:grid;gap:8px">
      <li style="display:grid;grid-template-columns:20px 1fr;gap:9px"><span style="color:var(--danger)">&times;</span><span>Jargon, dashboards, and &ldquo;strategy decks&rdquo;</span></li>
      <li style="display:grid;grid-template-columns:20px 1fr;gap:9px"><span style="color:var(--danger)">&times;</span><span>Fake urgency and too-good-to-be-true numbers</span></li>
      <li style="display:grid;grid-template-columns:20px 1fr;gap:9px"><span style="color:var(--danger)">&times;</span><span>Being handed to an account manager</span></li>
    </ul>
  </div></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Message match &mdash; how to talk to him</h2>
  <p class="lead">The rules that keep every page sounding like us.</p>
  <div style="overflow-x:auto"><table class="compare"><thead><tr><th>Instead of&hellip;</th><th class="me">Say&hellip;</th></tr></thead><tbody>
    <tr><td>&ldquo;Lead generation solutions&rdquo;</td><td class="me">&ldquo;Your phone rings with real jobs&rdquo;</td></tr>
    <tr><td>&ldquo;Omnichannel strategy&rdquo;</td><td class="me">&ldquo;A site, Google, and ads &mdash; done for you&rdquo;</td></tr>
    <tr><td>&ldquo;Schedule a discovery consultation&rdquo;</td><td class="me">&ldquo;Call me. Ten minutes. I answer.&rdquo;</td></tr>
    <tr><td>&ldquo;Trusted by hundreds&rdquo; (unproven)</td><td class="me">&ldquo;Month to month &mdash; fire me if the phone stays quiet&rdquo;</td></tr>
  </tbody></table></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>The 17 trades</h2>
  <p class="lead">Same buyer, tailored per trade &mdash; because the moment a homeowner calls a roofer isn&rsquo;t the moment they call a plumber. Each links to its live landing page.</p>
  <div class="tradegrid">{tg}</div>
</div></section>
</main>'''
    return shell("/style-guide/icp/", "ICP — Hey Aaron! Marketing",
                 "The Hey Aaron! ideal customer profile: buyer persona, message match, and the 17 trades.", body)


def p_voice():
    lex = [
        ("conversions, lead flow, pipeline", "booked jobs, the phone ringing, work on the calendar"),
        ("holistic, omnichannel, synergy, leverage", "(banned &mdash; rewrite the sentence)"),
        ("digital solutions, deliverables", "the work, what I actually did, your website / your ads"),
        ("utilize", "use"),
        ("best-in-class, cutting-edge, innovative", "(show the result, don't claim the adjective)"),
        ("reach out", "call me, text me"),
        ("our team", "I / me (it's Aaron; name a contractor if one helps)"),
        ("SEO, PPC, LSA (unexplained)", "showing up on Google, the ads &mdash; plain words first, acronym after"),
        ("clients", "contractors, or the trade by name (roofers, HVAC guys)"),
    ]
    lex_rows = "".join(
        f'<tr><td>{a}</td><td class="me">{b}</td></tr>' for a, b in lex)

    moves = [
        ("The oddly-specific stat", "Precise where round is expected: &ldquo;answered in 12 seconds,&rdquo; &ldquo;three towns, not the whole county.&rdquo; A real, specific number beats &ldquo;usually.&rdquo; Only ever use one you'll stand behind."),
        ("Napkin math out loud", "Walk the money right in the prose: &ldquo;$80 a lead, 5 contractors, 1 in 10 books = $800 a job.&rdquo; Show the arithmetic, let them gasp. His single best move."),
        ("Admit what you can't do", "Volunteer your limits, even when it kills the deal. Deepest trust move in the voice. The site should do it too."),
        ("The receipts", "Follow every claim with the verifiable thing. &ldquo;Don't take my word for it &mdash; here's the real task list.&rdquo;"),
        ("Name the uncomfortable thing first", "Open with the objection they're already thinking. &ldquo;You've been burned before. Probably twice.&rdquo;"),
        ("The anti-pitch", "Tell them when NOT to hire you, what the big guys do better, what it costs. Transparency IS the sales strategy."),
        ("Poker is a place, not a metaphor", "Aaron networks at the poker table; he doesn't talk in card metaphors. Reference the table as community, drop the wordplay."),
        ("Job-site respect", "Talk about their work like the skilled work it is. The villain is always the marketing industry, never the contractor."),
    ]
    move_cards = "".join(
        f'<div class="card"><h3>{t}</h3><p>{b}</p></div>' for t, b in moves)

    ba = [
        ("&ldquo;We deliver comprehensive digital marketing solutions tailored to your needs.&rdquo;",
         "&ldquo;I get roofers and HVAC companies booked jobs. That's it. That's the whole company.&rdquo;"),
        ("&ldquo;Our proven process ensures maximum ROI through data-driven optimization.&rdquo;",
         "&ldquo;Every month you get a list of exactly what I did and what it made you. If the math doesn't work, fire me.&rdquo;"),
        ("&ldquo;Contact us today to schedule a free consultation!&rdquo;",
         "&ldquo;Call me. I answer my own phone &mdash; which, if you've dealt with a big agency, might be the strangest thing on this website.&rdquo;"),
    ]
    ba_rows = "".join(
        f'<tr><td>{t}</td><td class="me">{a}</td></tr>' for t, a in ba)

    body = f'''
<main>
<section class="sg-hero"><div class="sg-wrap">
  <span class="kick">Voice &amp; tone &mdash; locked</span>
  <h1>How Hey Aaron! talks.</h1>
  <p>Aaron. One guy, 20+ years in marketing, talking to another owner-operator with a truck, a crew, and a phone
  that isn't ringing enough. Not an agency &ldquo;we.&rdquo; The straight talk you'd give a buddy at the poker table
  who asked &ldquo;should I hire this marketing company?&rdquo; &mdash; the answer with no commission riding on it.</p>
  <div class="sg-demo" style="margin-top:22px"><div class="pad" style="border-left:3px solid var(--primary-container)">
    <b>This guide is the source of truth.</b> If new copy drifts from it, the move is: fix the copy, or update this
    page on purpose &mdash; never quietly let the voice slide. Full guide lives in the repo at
    <code>brand/voice-guide.md</code>.</div></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Say this, not that</h2>
  <p class="lead">The lexicon. Left column is banned; rewrite to the right.</p>
  <div class="table-scroll"><table class="compare"><thead><tr><th>Never say</th><th class="me">Say instead</th></tr></thead>
  <tbody>{lex_rows}</tbody></table></div>
  <p class="lead" style="margin-top:14px"><b>Numbers:</b> round when talking (&ldquo;fifteen hundred bucks&rdquo;),
  exact when promising (&ldquo;$1,500/mo&rdquo;). <b>Contractions:</b> always. A sentence without them reads like a lawyer wrote it.</p>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Profanity &mdash; a highlighter, not a filler</h2>
  <p class="lead">Aaron's natural baseline is <b>zero</b>. Used right, one &ldquo;damn&rdquo; does more than three
  exclamation points, on the villain, the stakes, or the hard truth. Never as seasoning in a neutral sentence.
  Register is PG-13 (<em>damn, hell, ass, crap, BS, sucks</em>); one notch stronger is rationed to load-bearing only.</p>
  <div class="split2" style="margin-top:10px"><div>
    <div class="card" style="border-top:3px solid var(--good)"><h3 style="font-size:1rem">Where it's allowed</h3>
    <p>Body copy on pages that aren't primarily paid-ad landers. Max 2&ndash;3 per page; zero is common and fine.
    On the point that carries the argument, never the setup.</p></div>
  </div><div>
    <div class="card" style="border-top:3px solid var(--danger)"><h3 style="font-size:1rem">Hard no-fly zones (never)</h3>
    <p>Meta titles &amp; descriptions, anything Google/Meta crawls for ad approval, the guarantee, pricing &amp;
    legal terms, schema/JSON-LD, email subject lines, and anything a client's own customer sees. <b>The website is
    ad-crawled &mdash; keep it near-zero.</b></p></div>
  </div></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Cadence &amp; mechanics</h2>
  <ul class="svc-get" style="max-width:760px">
    <li>{use('i-check')}<span>Short sentences. Then a shorter one. Then one long one that stacks up three things they already agree with before the point lands.</span></li>
    <li>{use('i-check')}<span>Questions open sections. Statements close them. One-sentence paragraphs for the knockout line.</span></li>
    <li>{use('i-check')}<span>Dashes over semicolons &mdash; semicolons are banned. Sentence fragments allowed for punch.</span></li>
    <li>{use('i-check')}<span>6th-grade reading level. If a roofer would squint at a word, swap it. Second person dominant; &ldquo;I&rdquo; for Aaron; &ldquo;we&rdquo; only when it means Aaron + the reader.</span></li>
    <li>{use('i-check')}<span>Ellipses (&ldquo;....&rdquo;) and the &ldquo;=&rdquo; punchline live in email &amp; social, not website headers. &ldquo;Howdy&rdquo; and rotating warm sign-offs are real.</span></li>
  </ul>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Signature moves</h2>
  <p class="lead">The moves that make it sound like Aaron and nobody else.</p>
  <div class="cards">{move_cards}</div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Before / after</h2>
  <div class="table-scroll"><table class="compare"><thead><tr><th>Templated</th><th class="me">Aaron</th></tr></thead>
  <tbody>{ba_rows}</tbody></table></div>
</div></section>

<section class="sg-sec"><div class="sg-wrap">
  <h2>Sample passages</h2>
  <p class="lead">The voice, in place. Hold new copy against these.</p>
  <div class="contentblock" style="max-width:760px">
    <h4>Hero</h4>
    <p style="border-left:3px solid var(--line);padding-left:14px;color:var(--ink)">Tired of paying for junk leads
    that don't answer the phone? I'm Aaron. I get East Texas contractors booked jobs &mdash; real ones, on your
    calendar &mdash; and everything I build belongs to you. Month-to-month. One contractor per market.</p>
    <h4>Villain (napkin math)</h4>
    <p style="border-left:3px solid var(--line);padding-left:14px;color:var(--ink)">That $80 &ldquo;exclusive&rdquo;
    lead got sold to four other roofers before your phone buzzed. $80 a lead, 5 contractors, 1 in 10 books =
    you're paying $800 a booked job for a footrace to voicemail. That's not marketing. That's a coin toss you paid for.</p>
    <h4>When NOT to hire me</h4>
    <p style="border-left:3px solid var(--line);padding-left:14px;color:var(--ink)">Don't hire me if you need 50
    leads by Friday, anyone promising that is lying. Don't hire me if nobody answers the phone, because I can make
    it ring all day and it won't matter worth a damn if it goes to voicemail. Still here? Good.</p>
  </div>
</div></section>
</main>'''
    return shell("/style-guide/voice/", "Voice & Tone — Hey Aaron! Marketing",
                 "The locked Hey Aaron! voice: lexicon, profanity rules, cadence, signature moves, and sample passages.", body)


def main():
    out = {
        "style-guide": p_hub(),
        "style-guide/library": p_library(),
        "style-guide/voice": p_voice(),
        "style-guide/icp": p_icp(),
    }
    for path, html in out.items():
        d = os.path.join(ROOT, path)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    print(f"wrote style guide: {', '.join('/' + p + '/' for p in out)}")


if __name__ == "__main__":
    main()
