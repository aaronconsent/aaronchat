#!/usr/bin/env python3
"""Generate the /services/ hub + one clean navy page per service, on ha.css.
De-themed off the retired report-card system. Run: python3 scripts/build_services.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = "102"
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
LOGO = re.search(r'(<svg class="ha-logo".*?</svg>)', IDX, re.S).group(1)
FOOTER = IDX[IDX.index('<footer class="site-foot">'):IDX.index('</footer>') + len('</footer>')]
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]
PHONE = '<svg><use href="#i-phone"/></svg>'
BIZ = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"ProfessionalService","name":"Hey Aaron! Marketing","url":"https://aaron.chat/","telephone":"+1-713-384-8985","email":"hello@aaron.chat","priceRange":"$$","areaServed":{"@type":"State","name":"Texas"},"address":{"@type":"PostalAddress","addressLocality":"Livingston","addressRegion":"TX","addressCountry":"US"},"founder":{"@type":"Person","name":"Aaron Phillips"}}</script>'

HEADER = f'''<header class="site-head"><div class="wrap">
<a href="/" aria-label="Hey Aaron! home">{LOGO}</a>
<nav class="site-nav" aria-label="Main"><a href="/work/">Real work</a><a href="/pricing/">Pricing</a><a href="/about/">About</a><a href="/quote/">Get a quote</a></nav>
<a class="head-call" href="tel:+17133848985" data-cta-location="header">{PHONE}713-384-8985</a>
<button class="nav-toggle" aria-label="Menu" aria-expanded="false"><svg><use href="#i-menu"/></svg></button>
</div></header>'''

TAIL = f'''<a class="floatcall" href="tel:+17133848985" data-cta-location="float">{PHONE}Call Aaron &mdash; I answer</a>
{FOOTER}
<script src="/brand/ha.js?v={VER}" defer></script>
<script src="/brand/chat.js?v={VER}" defer></script>'''

CATS = [
    ("Get found", "They can't hire you if they can't find you."),
    ("Get chosen", "Found is step one. Trusted is what gets the call."),
    ("Keep them coming back", "The cheapest job to win is from a customer you already have."),
    ("Paid growth", "When you're ready to buy reach, not just earn it."),
]

# slug, cat-index, icon, name, one-liner, problem, deliverables
S = [
 ("website", 0, "i-web", "A website that books jobs",
  "Fast, modern, built to turn a click into a phone call.",
  "A Facebook page isn't a website. Homeowners searching from a phone bounce off logins and dead links, and the shop next to you with a real site gets the call.",
  ["A custom site, built and hosted, nothing for you to manage", "Loads in under a second on a phone", "Built to turn visits into calls", "Town and service pages that rank locally", "Unlimited updates, never a change fee"]),
 ("local-seo", 0, "i-search", "Local SEO",
  "Show up when someone searches for your trade near them.",
  "If you're not in the top few Google results for your service in your town, you're invisible at the exact moment someone needs you.",
  ["Your Google Business Profile fixed and optimized", "Local pages built to rank in your towns", "Consistent name, address, and phone everywhere", "The technical stuff that makes Google trust you"]),
 ("google-business-profile", 0, "i-target", "Google Business Profile",
  "The little map box that decides who gets the emergency call.",
  "Most contractors leave their Google profile half-empty. Missing photos, wrong hours, no posts. That's points you're handing to the competition.",
  ["Profile claimed, verified, and filled out right", "Photos, services, and hours all correct", "Regular posts so it looks alive", "Review requests wired in"]),
 ("ai-optimization", 0, "i-bolt", "AI answer optimization",
  "Get recommended by ChatGPT and Google's AI answers.",
  "More people ask an AI 'who's a good plumber near me' every month. If your business isn't structured for it, you don't exist in that answer.",
  ["Content and schema built so AI engines can quote you", "Q&A formatting the models actually read", "Structured data done right", "The same AEO work I do for my own sites"]),
 ("reviews", 1, "i-trend", "Reviews on autopilot",
  "The stars next to your name are the first thing a homeowner judges.",
  "You do great work but forget to ask for the review. Meanwhile the other guy has 200 and you have 12.",
  ["Automatic review asks after every job", "One-tap links so customers actually leave them", "Every review answered, good or bad", "Your rating working for you 24/7"]),
 ("social-media", 1, "i-image", "Social media, handled",
  "Posted for you, so your name stays in front of the neighborhood.",
  "Nobody has time to post between jobs. So the account goes stale, and stale looks like out-of-business.",
  ["Several channels posted for you", "Real photos of your work, made to look good", "AI images and short video when you need them", "Consistent, on-brand, hands-off"]),
 ("auto-blog", 1, "i-web", "Fresh content that ranks",
  "Helpful pages that pull in searches while you sleep.",
  "Google rewards sites that stay fresh. A site that never changes slowly slides down the results.",
  ["Regular, genuinely useful articles", "Written to rank for what your customers search", "Zero effort from you", "Turns your expertise into found-you traffic"]),
 ("customer-newsletter", 2, "i-msg", "The email past customers actually read",
  "Stay in their inbox so the repeat and referral work comes to you.",
  "Your best next customer is one you already have. Most contractors never talk to them again.",
  ["A monthly email people don't hate", "Seasonal reminders that book work", "Referral asks that feel natural", "Built and sent for you"]),
 ("email-outreach", 2, "i-target", "Automated follow-up",
  "So a lead never goes cold because you were on a roof.",
  "A lead that doesn't hear back in an hour is usually gone. You can't drop a job to email someone.",
  ["Instant, automatic follow-up to every lead", "Text and email, timed to convert", "Nurture for the not-ready-yet", "Nothing slips through"]),
 ("paid-advertising", 3, "i-target", "Ads that pay for themselves",
  "Google and Facebook ads aimed at people who need you now.",
  "Boosting a post and hoping isn't advertising. Untracked ad spend is just donating to Google.",
  ["Google and Facebook ads managed end to end", "Aimed at high-intent, ready-to-buy searches", "Every dollar tracked to a booked job", "Ad spend separate and always yours"]),
 ("reel-video", 3, "i-image", "Short video that stops the scroll",
  "Before/afters and quick clips built from your job photos.",
  "Video gets seen far more than a photo, but you're not going to edit reels at 9pm.",
  ["Short vertical videos from your job photos", "Before-and-after and meet-the-crew clips", "Made for you, monthly", "The format the algorithm actually pushes"]),
 ("group-sharing", 3, "i-msg", "Nextdoor + local group reach",
  "Get your name into the neighborhood conversations that drive referrals.",
  "The 'who do you recommend for...' posts in local groups send real work. If you're not there, you miss it.",
  ["Presence in the local groups that matter", "Nextdoor set up and worked", "Genuine, non-spammy participation", "Turns neighbors into a referral engine"]),
]


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


def chk(t):
    return f'<li><svg width="18" height="18"><use href="#i-check"/></svg><span>{esc(t)}</span></li>'


def render_service(x, i):
    slug, ci, icon, name, one, prob, deliver = x
    prev = S[i - 1] if i > 0 else None
    nxt = S[i + 1] if i < len(S) - 1 else None
    nav = '<div class="svc-nav">'
    nav += f'<a href="/services/{prev[0]}/">&larr; {esc(prev[3])}</a>' if prev else '<span></span>'
    nav += f'<a href="/services/{nxt[0]}/">{esc(nxt[3])} &rarr;</a>' if nxt else '<span></span>'
    nav += '</div>'
    return f'''{head(esc(name) + " — Hey Aaron! Marketing", one + " " + prob[:110], f"/services/{slug}/")}
<div class="page-hero"><div class="wrap"><span class="caps">{esc(CATS[ci][0])}</span><h1>{esc(name)}</h1><p>{esc(one)}</p></div></div>
<section class="sec"><div class="wrap split">
  <div class="reveal">
    <h2 style="font-size:var(--d-lg);margin-bottom:12px">Why it matters</h2>
    <p class="lede" style="margin-bottom:20px">{esc(prob)}</p>
    <div class="hero-cta"><a class="btn btn-call" href="tel:+17133848985" data-cta-location="service">{PHONE}Call and ask about this</a>
    <a class="btn btn-ghost" href="/quote/">Get a quote</a></div>
  </div>
  <div class="reveal">
    <div class="card" style="box-shadow:var(--sh-md)"><span class="ic"><svg><use href="#{icon}"/></svg></span>
    <h3 style="margin-bottom:14px">What you get</h3>
    <ul class="svc-get">{''.join(chk(d) for d in deliver)}</ul></div>
  </div>
</div>
<div class="wrap">{nav}</div>
</section>
<section class="sec final"><div class="wrap reveal"><h2>Want this handled?</h2>
<p class="lede">One call, ten minutes. I'll tell you straight if it's worth doing for your shop.</p>
<a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="service-final">{PHONE}Call Aaron: 713-384-8985</a></div></section>
</main>{TAIL}</body></html>'''


def render_hub():
    cards = ""
    for ci, (cname, cdesc) in enumerate(CATS):
        items = [x for x in S if x[1] == ci]
        lis = "".join(f'<li><a href="/services/{x[0]}/"><b>{esc(x[3])}</b><span>{esc(x[4])}</span></a></li>' for x in items)
        cards += f'<div class="svc-cat reveal"><h3>{esc(cname)}</h3><p class="cat-desc">{esc(cdesc)}</p><ul class="svc-list">{lis}</ul></div>'
    return f'''{head("What I do — Hey Aaron! Marketing", "Everything that gets contractors found and gets them called: websites, local SEO, Google, reviews, ads, video, and follow-up. Done by Aaron.", "/services/")}
<div class="page-hero"><div class="wrap"><span class="caps">The whole toolbox</span>
<h1>Everything that gets you found and gets you called.</h1>
<p>I do all of it, so you don't have to hire five vendors or learn marketing. And I run every one of these
right here on my own site. The site is the demo.</p></div></div>
<section class="sec"><div class="wrap"><div class="svc-cats">{cards}</div>
<div class="center" style="margin-top:40px"><a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="services-cta">{PHONE}Not sure what you need? Call me.</a></div></div></section>
</main>{TAIL}</body></html>'''


def main():
    for i, x in enumerate(S):
        d = os.path.join(ROOT, "services", x[0])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_service(x, i))
    open(os.path.join(ROOT, "services", "index.html"), "w", encoding="utf-8").write(render_hub())
    print(f"wrote services hub + {len(S)} service pages")


if __name__ == "__main__":
    main()
