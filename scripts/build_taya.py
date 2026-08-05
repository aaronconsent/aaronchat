#!/usr/bin/env python3
"""Build the They-Ask-You-Answer transparency pages (direct-response content rework).

Writes:
  /not-a-fit/   "When NOT to Hire Me" (disqualifier)
  /compare/     "Hey Aaron! vs Scorpion vs RYNO vs DIY" (honest comparison)
  /questions/   "Questions Contractors Ask Before Hiring Any Agency" (FAQ + FAQPage JSON-LD)
  /results/     verifiable results + reviews (honest, gated on [AARON: CONFIRM])

Shares the exact header/footer/sprite/tail as the rest of the site (extracted from index.html),
so nav, the 4-col footer, sticky call bar, and tracking stay in sync.

Run: python3 scripts/build_taya.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = "112"

IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
HEADER = IDX[IDX.index('<header class="site-head">'):IDX.index('</header>') + len('</header>')]
# tail = sticky callbar + floatcall + footer + exit modal + scripts (everything after </main>)
TAIL = IDX[IDX.index('<!-- sticky mobile call bar'):IDX.index('</body>')]
PIXEL = IDX[IDX.index('<!-- Meta Pixel -->'):IDX.index('</script>', IDX.index('<!-- Meta Pixel -->')) + len('</script>')]

PHONE = '<svg><use href="#i-phone"/></svg>'


def esc(s):
    return H.escape(str(s or ""))


def page(slug, title, desc, main, extra_head=""):
    url = f"https://aaron.chat/{slug}/"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
{extra_head}{PIXEL}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{HEADER}
<main id="main">
{main}
</main>
{TAIL}
</body>
</html>
'''


def cta(loc, label="Call Aaron: 713-384-8985"):
    return (f'<div class="center" style="margin-top:32px">'
            f'<a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="{loc}">{PHONE}{label}</a></div>')


def phero(caps, h1, sub):
    return (f'<div class="page-hero"><div class="wrap"><span class="caps">{caps}</span>'
            f'<h1>{h1}</h1><p>{sub}</p></div></div>')


# --------------------------------------------------------------- NOT A FIT ------
def p_not_a_fit():
    blocks = [
        ("You need 50 leads by Friday.",
         "I'm not a lead firehose. If you need volume yesterday, go buy shared leads and take what you get. I build "
         "something that compounds, and it needs a little time to pay off. If you can't give it a beat, we're not a fit."),
        ("You want a $99 website.",
         "There are $99 site builders, and if that's the budget, use one. A site that actually books jobs, loads fast, "
         "and ranks takes real work. I'm not the cheapest, and I won't pretend to be."),
        ("You won't answer your phone.",
         "All the marketing in the world dies at a voicemail. I can make the phone ring all day and it won't matter "
         "worth a damn if nobody picks up. If you can't answer or call back fast, that's the first leak to plug, "
         "before you spend a dime with me."),
        ("You want me to guarantee jobs I can't control.",
         "I control the marketing. I don't control whether you pick up, show up, or close the sale. So I won't promise "
         "“30 jobs a month, guaranteed.” Anybody who does is lying to you, and you already know it."),
        ("Price is the only thing that matters to you.",
         "Cheapest and best-for-your-business are rarely the same thing. If the whole decision comes down to the lowest "
         "number, I'm probably not your guy, and that's okay."),
    ]
    items = "".join(
        f'<div class="card"><h3>{esc(t)}</h3><p>{b}</p></div>' for t, b in blocks)
    main = f'''
{phero("Real talk", "When you should <em>not</em> hire me.",
       "I'd rather tell you no than take your money and waste it. If any of these sound like you, save us both the call.")}
<section class="sec"><div class="wrap">
  <div class="cards reveal">{items}</div>
  <div class="sec-head center reveal" style="margin-top:44px;max-width:640px;margin-inline:auto">
    <h2>Still here?</h2>
    <p class="lede">Good. That probably means we'll get along. If you run service trucks in East Texas, want to own
    what you pay for, and you answer your phone, call me.</p>
  </div>
  {cta("not-a-fit")}
</div></section>'''
    return page("not-a-fit", "When NOT to Hire Me — Hey Aaron! Marketing",
                "I turn away work that isn't a fit. If you need 50 leads by Friday, want a $99 website, or won't "
                "answer your phone, I'm honestly not your guy. Here's who I am for.", main)


# ---------------------------------------------------------------- COMPARE -------
def p_compare():
    rows = [
        ("Who does your work", '<span class="yes">Aaron, every time</span>',
         "A team you rotate through", "You, after hours"),
        ("Contract length", '<span class="yes">Month to month</span>',
         "Often 6&ndash;12+ months (read it closely)", "None"),
        ("Who owns the website, ads &amp; leads", '<span class="yes">You, from day one</span>',
         "Sometimes them &mdash; ask before you sign", "You"),
        ("One shop per market", '<span class="yes">Yes, guaranteed</span>',
         "Usually no &mdash; they take your competitor too", "N/A"),
        ("Prices on the website", '<span class="yes">Yes, right here</span>',
         '<span class="no">Almost never</span>', "Free-ish, plus your time"),
        ("Reach a decision-maker", '<span class="yes">Call and get me</span>',
         "Account manager, then a queue", "You are the decision-maker"),
        ("24/7 support team", '<span class="no">No &mdash; it’s one guy</span>',
         '<span class="yes">Yes</span>', "No"),
        ("National / multi-state scale", '<span class="no">Built for local</span>',
         '<span class="yes">Yes, big budgets</span>', "No"),
    ]
    tr = "".join(
        f'<tr><th>{r[0]}</th><td class="me">{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>' for r in rows)
    main = f'''
{phero("An honest comparison", "Me vs. the big agencies vs. doing it yourself.",
       "I'm a solo specialist. Scorpion and RYNO are big national shops with hundreds of people. That's a real "
       "difference, and sometimes they're the better call. Here's the straight version, no spin.")}
<section class="sec"><div class="wrap">
  <div class="table-scroll reveal"><table class="compare">
    <thead><tr><th>&nbsp;</th><th class="me">Hey Aaron!</th><th>Scorpion / RYNO</th><th>Doing it yourself</th></tr></thead>
    <tbody>{tr}</tbody>
  </table></div>
  <!-- [AARON: CONFIRM] competitor cells describe common big-agency patterns, not any specific signed agreement. Keep language general/verifiable. -->
  <p class="lede" style="margin-top:14px;font-size:.9rem;color:var(--ink-variant)">Big-agency terms vary, always read
  the agreement. This is the pattern I see, not a claim about any one company's contract.</p>

  <div class="split reveal" style="margin-top:44px">
    <div>
      <span class="caps">Be honest</span>
      <h2 style="font-size:var(--d-lg);margin:8px 0 12px">Where the big guys genuinely win</h2>
      <ul class="svc-get">
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>A support team on call around the clock</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>Huge budgets and enterprise tooling</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>Rolling out across many locations and states at once</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>Someone always there if you're a 40-truck operation</span></li>
      </ul>
      <p class="lede" style="margin-top:14px;font-size:1rem">If that's you, go hire them. No hard feelings.</p>
    </div>
    <div>
      <span class="caps">The trade-off</span>
      <h2 style="font-size:var(--d-lg);margin:8px 0 12px">Where a solo specialist wins</h2>
      <ul class="svc-get">
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>You get me on the phone, not a rotating rep</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>You own the website, ads, and data, forever</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>One shop per market, your competitor can't hire me</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>No contracts, no markup games, real prices on the site</span></li>
      </ul>
      <p class="lede" style="margin-top:14px;font-size:1rem">If you're a 1&ndash;15 truck shop in East Texas, that's usually the better deal.</p>
    </div>
  </div>
  {cta("compare")}
</div></section>'''
    return page("compare", "Hey Aaron! vs Scorpion vs RYNO vs DIY — an honest comparison",
                "An honest comparison of a solo local specialist versus big national agencies like Scorpion and RYNO, "
                "and versus doing it yourself, including where the big agencies genuinely win.", main)


# -------------------------------------------------------------- QUESTIONS -------
QA = [
    ("Who owns my website, ads, and leads if we part ways?",
     "You do, and you did from day one. The website, the domain, the ad accounts, your Google Business Profile, and "
     "your customer list are all in your name. Fire me and you walk out with every bit of it. I never hold anything "
     "hostage, that's the whole point of how I set this up."),
    ("Are my leads and my market exclusive?",
     "Yes. I take one shop per trade in a service area, so I'm never working for you and your direct competitor at the "
     "same time. And I don't resell leads to anybody, every call your marketing generates is yours alone."),
    ("Is there a contract? What am I locked into?",
     "Nothing. It's month to month, with no setup fee and no cancellation fee. If I don't earn it this month, fire me "
     "and keep everything I built. I'd rather keep earning your business than trap you into a year."),
    ("Who actually does the work, you or an offshore team?",
     "Me. Aaron. Not a rep, not an offshore team reading a script. You get the person who spent 20 years running "
     "marketing for real companies. Because I cap how many shops I take on, you get my actual attention, not a queue."),
    ("How fast do you answer?",
     "You get me, not a ticket. I answer the phone, or I call you back the same day. That's written into the "
     "guarantee, not a nice-to-have I forget about when I'm busy."),
    ("Do you guarantee a number of leads or jobs?",
     "No, and be careful with anyone who does. I control the marketing, not whether you answer, show up, or close. So "
     "I guarantee the work: everything on your task list that month gets done and shown to you, or that month is free. "
     "That's a promise I can actually keep."),
    ("Can I see real reporting, or just “impressions”?",
     "Real reporting. Every month you get a plain-English list of exactly what I did and what it got you, plus call "
     "tracking so you can see which calls came from where. No vanity charts."),
    ("What changes the price?",
     "Mostly which pieces you run (website and growth, social, ads) and how much you put behind ads. The plan fees are "
     "flat and posted on the pricing page. Ad budget goes straight to Google or Facebook, never to me."),
]


def p_questions():
    details = "".join(
        f'<details><summary>{q}<svg class="chev"><use href="#i-chev"/></svg></summary><div class="a">{a}</div></details>'
        for q, a in QA)
    ld_items = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (_json(q), _json(_plain(a))) for q, a in QA)
    ld = ('<script type="application/ld+json">'
          '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + ld_items + ']}</script>\n')
    main = f'''
{phero("Before you hire anybody", "The questions every contractor should ask, answered.",
       "Ask any agency these before you sign. If they dodge, you have your answer. Here are mine, in plain text.")}
<section class="sec"><div class="wrap" style="max-width:820px;margin-inline:auto">
  <div class="faq reveal">{details}</div>
  <div class="sec-head center reveal" style="margin-top:40px">
    <h2>Got one I didn't cover?</h2>
    <p class="lede">Call and ask me anything. If I don't know, I'll tell you that too.</p>
  </div>
  {cta("questions")}
</div></section>'''
    return page("questions", "Questions Contractors Ask Before Hiring Any Agency — Hey Aaron!",
                "The real questions to ask any marketing agency before you sign: who owns your website and leads, "
                "are they exclusive, what's the contract, who does the work, and how fast they answer.",
                main, extra_head=ld)


def _plain(s):
    return re.sub(r"<[^>]+>", "", s).replace("&mdash;", "—").replace("&amp;", "&")


def _json(s):
    import json
    return json.dumps(str(s))


# ---------------------------------------------------------------- RESULTS -------
def p_results():
    main = f'''
{phero("Proof you can check", "Real results, and how to verify them yourself.",
       "I won't paste a wall of stock-photo five stars. Here's the real, checkable version, warts and all.")}
<section class="sec"><div class="wrap">
  <div class="split reveal">
    <div>
      <span class="caps">Real, live work</span>
      <h2 style="font-size:var(--d-lg);margin:8px 0 12px">Sites I built for real businesses</h2>
      <p class="lede" style="margin-bottom:16px">Every one of these is live right now. Click through and poke around,
      that's the proof, not a screenshot I could fake.</p>
      <ul class="svc-get">
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>G4 Electric &mdash; electrician</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>B&amp;R Productions &mdash; CNC machine shop</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>Polk County Golf Carts &mdash; local retail, Livingston TX</span></li>
        <li><svg width="18" height="18"><use href="#i-check"/></svg><span>JAC Builders &mdash; roofing</span></li>
      </ul>
      <div style="margin-top:18px"><a class="btn btn-ghost" href="/work/">See all my work &rarr;</a></div>
    </div>
    <div>
      <div class="card">
        <span class="caps" style="color:var(--tertiary)">Straight talk</span>
        <h3 style="font-size:var(--h-md);margin:8px 0 10px">Why there's no giant review wall here yet</h3>
        <p style="color:var(--ink-variant)">I'm newer to marketing <em>for the trades</em> than I am to marketing
        itself, and I'd rather show you real proof than invent it. As real contractor results come in, they go here,
        with names and numbers you can verify. That honesty is the same reason your customers will trust you.</p>
      </div>
    </div>
  </div>

  <!-- [AARON: CONFIRM] Reviews block — paste your Google Business Profile review link + any real, permissioned client results (client, trade, town, before/after numbers) here. Do not publish numbers that aren't real. -->
  <div class="sec-head center reveal" style="margin-top:48px;max-width:640px;margin-inline:auto">
    <span class="caps">Reviews</span>
    <h2>Read the reviews on Google, not on my own website</h2>
    <p class="lede">Anybody can type five stars onto their own page. Real reviews live on your Google profile where I
    can't edit them. <a href="#0" data-cta-location="results-google">[AARON: CONFIRM &mdash; link your Google profile]</a></p>
  </div>
  {cta("results")}
</div></section>'''
    return page("results", "Real Results You Can Verify — Hey Aaron! Marketing",
                "Real, live sites I built for contractors and local businesses, plus reviews you can check on Google. "
                "Proof you can verify yourself, no invented numbers.", main)


def main():
    out = {
        "not-a-fit": p_not_a_fit(),
        "compare": p_compare(),
        "questions": p_questions(),
        "results": p_results(),
    }
    for slug, html in out.items():
        d = os.path.join(ROOT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    print("wrote TAYA pages: " + ", ".join("/" + s + "/" for s in out))


if __name__ == "__main__":
    main()
