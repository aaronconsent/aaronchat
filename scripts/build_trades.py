#!/usr/bin/env python3
"""Generate one Hey Aaron! landing page per ICP trade (17), on the ha.css navy system.

Each page is a call-first StoryBrand lander with the full conversion layer, trade-specific pain and
search-moment copy (specificity is what converts), DTR-ready hero, quiz + callback, schema, a11y.
Run:  python3 scripts/build_trades.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = "106"
LOGO = open("/tmp/ha_logo.svg").read() if os.path.exists("/tmp/ha_logo.svg") else ""
if not LOGO:  # fall back to extracting from the homepage
    idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    LOGO = re.search(r'(<svg class="ha-logo".*?</svg>)', idx, re.S).group(1)
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
FOOTER = IDX[IDX.index('<footer class="site-foot">'):IDX.index('</footer>') + len('</footer>')]
SPRITE = IDX[IDX.index('<!-- icon sprite -->'):IDX.index('</defs></svg>') + len('</defs></svg>')]

PHONE = '<svg><use href="#i-phone"/></svg>'


def esc(s): return H.escape(str(s or ""))


HEADER = f'''<header class="site-head">
  <div class="wrap">
    <a href="/" aria-label="Hey Aaron! home">{LOGO}</a>
    <nav class="site-nav" aria-label="Main"><a href="/services/">What I do</a><a href="/trades/">Who I help</a><a href="/work/">Real work</a><a href="/pricing/">Pricing</a><a href="/about/">About</a></nav>
    <a class="head-call" href="tel:+17133848985" data-cta-location="header">{PHONE}713-384-8985</a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false"><svg><use href="#i-menu"/></svg></button>
  </div>
</header>'''

TAIL = f'''<div class="callbar">
  <a class="c" href="tel:+17133848985" data-cta-location="sticky-call">{PHONE}Call Aaron</a>
  <a class="t" href="sms:+17133848985" data-cta-location="sticky-text"><svg><use href="#i-msg"/></svg>Text</a>
</div>
<a class="floatcall" href="tel:+17133848985" data-cta-location="float">{PHONE}Call Aaron &mdash; I answer</a>
{FOOTER}
<div class="ha-modal" data-exit hidden role="dialog" aria-modal="true" aria-label="One more thing">
  <div class="ha-modal-card">
    <button class="ha-modal-x" data-exit-close aria-label="Close">&times;</button>
    <h3>Before you go &mdash; one honest question.</h3>
    <p>Is the phone ringing like it used to? If not, that's a ten-minute call to fix. No pitch, no contract.</p>
    <a class="btn btn-white btn-block" href="tel:+17133848985" data-cta-location="exit">{PHONE}Call Aaron: 713-384-8985</a>
  </div>
</div>
<script src="/brand/ha.js?v={VER}" defer></script>'''

PIXEL = '''<!-- Meta Pixel -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
var PIXEL_ID='2449103548914877';
if(PIXEL_ID.indexOf('PASTE')===-1){fbq('init',PIXEL_ID);fbq('track','PageView');}
</script>'''

# ---- the 17 ICP trades: slug, plural label, hero trade word, the search moment (trade-specific pain),
#      a one-line villain, the money job, and one trade-specific FAQ ----
TRADES = [
    dict(slug="hvac-marketing", label="HVAC & AC companies", word="HVAC shops", one="HVAC shop",
         moment="When someone's AC quits at 11pm in a July heat wave, they grab the phone and call the first shop that looks legit on Google.",
         search='"AC repair near me"', job="a $12,000 system install", trade="HVAC",
         faqq="Do you get the difference between a tune-up lead and an install?",
         faqa="Yes. A tune-up caller and a ready-to-replace caller are worth wildly different money, and I build your ads and pages so the high-ticket installs actually find you, not just the $79 checkups."),
    dict(slug="plumber-marketing", label="Plumbers", word="Plumbers", one="plumbing shop",
         moment="A pipe bursts at 2am and there's water coming through the ceiling. That homeowner is calling whoever shows up first and answers.",
         search='"emergency plumber near me"', job="a repipe or water-heater job", trade="plumbing",
         faqq="Can you help me get the bigger jobs, not just clogs?",
         faqa="That's the whole point. I aim your marketing at repipes, water heaters, and remodels, the jobs that actually move your month, instead of a pile of $89 drain calls."),
    dict(slug="electrician-marketing", label="Electricians", word="Electricians", one="electrical shop",
         moment="Half the house loses power or a panel starts buzzing, and a nervous homeowner wants a licensed electrician on the phone right now.",
         search='"electrician near me"', job="a panel upgrade or rewire", trade="electrical",
         faqq="Will this bring in panel upgrades and not just outlet swaps?",
         faqa="Yes. I target the higher-ticket work, panel upgrades, EV chargers, rewires, so the good jobs come to you instead of a queue of ten-dollar handyman requests."),
    dict(slug="roofer-marketing", label="Roofers", word="Roofers", one="roofing company",
         moment="A storm rolls through and half the neighborhood suddenly needs a roofer. The ones who show up first on Google and answer the phone book the whole street.",
         search='"roof repair near me"', job="a full roof replacement", trade="roofing",
         faqq="Can you handle storm-season spikes?",
         faqa="Yes. When a storm hits, demand explodes for a week. I make sure your ads, phone, and site are ready to catch that spike instead of watching it go to the guy with the billboard."),
    dict(slug="remodeler-marketing", label="Remodelers & general contractors", word="Remodelers", one="remodeling company",
         moment="Someone's finally ready to spend $40,000 on a kitchen. They spend a week judging contractors by their website and reviews before they ever call.",
         search='"kitchen remodel contractor"', job="a full kitchen or bath remodel", trade="remodeling",
         faqq="My jobs are big and slow. Does this even work for me?",
         faqa="It's built for it. Big-ticket remodels are a considered purchase, so your site and reviews have to close the trust gap before they call. That's exactly what I build."),
    dict(slug="fence-marketing", label="Fence contractors", word="Fence builders", one="fence company",
         moment="New dog, new baby, or a nosy neighbor, and suddenly someone needs a fence this month. They're comparing two or three local fencers on their phone.",
         search='"fence installation near me"', job="a full-yard fence install", trade="fencing",
         faqq="It's seasonal for me. Can marketing smooth that out?",
         faqa="Yes. I keep you visible year-round and lean the ads harder in your busy season, so the good months are bigger and the slow months aren't dead."),
    dict(slug="concrete-marketing", label="Concrete contractors", word="Concrete crews", one="concrete company",
         moment="A cracked driveway or a dream patio, and the homeowner is scrolling local concrete guys, judging by photos and reviews before they'll call for a quote.",
         search='"concrete contractor near me"', job="a driveway or patio pour", trade="concrete",
         faqq="Photos matter in my trade. Can you help there?",
         faqa="Big time. Concrete sells on before-and-after photos. I make sure your best work is front and center and generate scroll-stopping images when you need them."),
    dict(slug="lawn-care-marketing", label="Lawn care & landscaping", word="Lawn & landscape pros", one="lawn care business",
         moment="Spring hits, the grass explodes, and every homeowner suddenly wants a lawn guy. The ones who show up first lock in recurring customers for the whole season.",
         search='"lawn care near me"', job="a recurring mowing or landscape contract", trade="lawn care",
         faqq="I want recurring accounts, not one-offs. Can you do that?",
         faqa="Yes. Recurring is the goal. I aim marketing at customers who want a season-long relationship, so you build a route, not just a stack of one-time jobs."),
    dict(slug="tree-service-marketing", label="Tree services", word="Tree services", one="tree service",
         moment="A limb's hanging over the roof after a storm, or a dead oak is one gust from the house. That's an urgent, high-dollar call, and it goes to whoever answers.",
         search='"tree removal near me"', job="a large removal or storm cleanup", trade="tree service",
         faqq="Can you bring in the big removals, not just trimming?",
         faqa="Yes. I target the high-ticket removals and storm work, the jobs that pay for the truck, instead of a pile of small trim requests."),
    dict(slug="septic-marketing", label="Septic services", word="Septic pros", one="septic company",
         moment="A septic backs up into the yard and it's a five-alarm emergency. The homeowner is calling the first licensed septic company that answers, price is not the issue.",
         search='"septic pumping near me"', job="a system repair or install", trade="septic",
         faqq="It's an emergency trade. How does marketing help?",
         faqa="Emergencies go to whoever shows up first and answers. I make sure that's you, on Google and on the phone, so you catch the urgent, high-value calls."),
    dict(slug="pressure-washing-marketing", label="Pressure washing pros", word="Pressure washers", one="pressure washing business",
         moment="A homeowner looks at their grimy driveway or dingy siding and decides today's the day. They pick the local washer with the best before-and-after photos.",
         search='"pressure washing near me"', job="a full house-and-driveway wash", trade="pressure washing",
         faqq="My whole pitch is before-and-after. Can you show that off?",
         faqa="That's your superpower and I lean into it hard, real before-and-afters on your site and in your ads, plus generated visuals when you need to fill a gap."),
    dict(slug="pool-service-marketing", label="Pool service companies", word="Pool pros", one="pool service",
         moment="The pool turns green a week before a pool party, and a stressed homeowner needs a pro today, then ideally every week after.",
         search='"pool cleaning service near me"', job="a recurring weekly service route", trade="pool service",
         faqq="I want weekly accounts. Can marketing get those?",
         faqa="Yes. Recurring routes are the money. I aim your marketing at homeowners who want a set-and-forget weekly pro, so you build a dense, profitable route."),
    dict(slug="garage-door-marketing", label="Garage door companies", word="Garage door pros", one="garage door company",
         moment="A spring snaps and the door won't open with the car trapped inside. That's a right-now call, and it goes to the first shop that looks real and answers.",
         search='"garage door repair near me"', job="a door or opener replacement", trade="garage door",
         faqq="Can you bring in replacements, not just repairs?",
         faqa="Yes. A snapped spring is a foot in the door for a full replacement. I set up your marketing to win the urgent repair and turn it into the bigger job."),
    dict(slug="gutter-marketing", label="Gutter companies", word="Gutter pros", one="gutter company",
         moment="Water's pouring over the edge in a storm, or leaves have turned the gutters into planters. The homeowner wants it handled before the next rain.",
         search='"gutter installation near me"', job="a full gutter or guard install", trade="gutter service",
         faqq="It's weather-driven work. Can you time that?",
         faqa="Yes. Demand spikes after every big rain. I keep you visible and ready so those weather-driven calls come to you, not the national franchise."),
    dict(slug="pest-control-marketing", label="Pest control companies", word="Pest control pros", one="pest control company",
         moment="Someone spots a roach on the counter or a wasp nest by the door and wants it gone today, then wants to never think about it again.",
         search='"exterminator near me"', job="a recurring quarterly plan", trade="pest control",
         faqq="I want recurring plans, not one-time sprays. Can you do that?",
         faqa="Yes. The recurring plan is the whole game. I aim your marketing at the urgent first call and set it up to convert into a quarterly plan that pays every month."),
    dict(slug="painter-marketing", label="Painters", word="Painters", one="painting company",
         moment="A homeowner's finally ready to repaint the whole house, a $6,000 job, and they're judging painters by their photos and reviews before they'll book a quote.",
         search='"house painters near me"', job="a full interior or exterior repaint", trade="painting",
         faqq="Painting sells on looks. Can you make me look good online?",
         faqa="That's the job. Crisp photos of your work, real reviews, and a site that looks as clean as your finish. I make sure you look like the pro you are."),
    dict(slug="appliance-repair-marketing", label="Appliance repair companies", word="Appliance repair pros", one="appliance repair business",
         moment="The fridge dies with a week of groceries inside, and the homeowner needs someone today, before everything spoils.",
         search='"appliance repair near me"', job="a same-day repair call", trade="appliance repair",
         faqq="Volume matters in my trade. Can you keep the calls coming?",
         faqa="Yes. Appliance repair is a volume game, so I keep you at the top of the local search when people need a fast fix, and keep your calendar full."),
]


def sec_services():
    cards = [
        ("i-web", "A site that books jobs", "Fast, clean, built to turn a click into a phone call. Like this one. It loads before your competitor's homepage shows up.", "You're on one right now"),
        ("i-search", "Show up on Google", "Local SEO and your Google Business Profile done right, so you're the first name they see when they search near them.", "Ask me where you rank"),
        ("i-target", "Ads that pay for themselves", "Google and Facebook ads aimed at people who need you now, every dollar tracked to a booked job, not a click.", "Tracked, not guessed"),
        ("i-msg", "Speed-to-lead callbacks", "The second a lead comes in, they get a call, while they're still holding the phone. See the widget below.", "Try it below"),
    ]
    out = []
    for ic, h, p, tag in cards:
        out.append(f'<div class="card reveal"><span class="ic"><svg><use href="#{ic}"/></svg></span>'
                   f'<h3>{h}</h3><p>{p}</p><span class="demo-tag">{tag}</span></div>')
    return "".join(out)


def render(t):
    title = f"Marketing for {t['label']} — Hey Aaron! | Livingston, TX"
    desc = f"I'm Aaron. I book jobs for {t['label'].lower()}, not just 'leads.' A site that works, top of Google, and ads that pay for themselves. Call and I answer: 713-384-8985."
    url = f"https://aaron.chat/{t['slug']}/"
    schema = ('{"@context":"https://schema.org","@type":"ProfessionalService",'
              f'"name":"Hey Aaron! Marketing for {esc(t["label"])}","url":"{url}",'
              f'"description":"Marketing for {esc(t["label"]).lower()}: websites, local SEO, Google Business Profile, and ads that book jobs.",'
              '"telephone":"+1-713-384-8985","email":"hello@aaron.chat","priceRange":"$$",'
              '"areaServed":[{"@type":"City","name":"Livingston"},{"@type":"City","name":"Onalaska"},{"@type":"City","name":"Coldspring"},{"@type":"City","name":"Huntsville"},{"@type":"State","name":"Texas"}],'
              '"founder":{"@type":"Person","name":"Aaron Phillips","jobTitle":"Founder — 20+ years in marketing"}}')
    faq_schema = ('{"@context":"https://schema.org","@type":"FAQPage","mainEntity":['
                  '{"@type":"Question","name":"Who owns my website and leads if we part ways?","acceptedAnswer":{"@type":"Answer","text":"You do, from day one. The website, domain, ad accounts, Google profile, and customer list are all in your name. Fire me and you keep every bit of it. I never hold anything hostage."}},'
                  f'{{"@type":"Question","name":"Is my market exclusive?","acceptedAnswer":{{"@type":"Answer","text":"Yes. I take one {esc(t["one"])} per area, so I am never working for you and your competitor at the same time, and I never resell leads."}}}},'
                  f'{{"@type":"Question","name":{esc_json(t["faqq"])},"acceptedAnswer":{{"@type":"Answer","text":{esc_json(t["faqa"])}}}}},'
                  '{"@type":"Question","name":"Is there a contract?","acceptedAnswer":{"@type":"Answer","text":"No lock-in. Month to month, no setup fee and no cancellation fee. If I do not earn it this month, fire me and keep everything I built."}},'
                  '{"@type":"Question","name":"What does it cost?","acceptedAnswer":{"@type":"Answer","text":"Website & Growth is $500/mo, Social Media is $500/mo, and paid ads are 15% of your ad spend with a $2,000/mo minimum ad budget. Month to month, no setup fees, no contracts."}}]}')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="Marketing for {esc(t['label'])} — Hey Aaron!">
<meta property="og:description" content="I book jobs, not 'leads.' Call and Aaron answers.">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
<script type="application/ld+json">{schema}</script>
<script type="application/ld+json">{faq_schema}</script>
{PIXEL}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{HEADER}
<main id="main">

<section class="hero grid-bg">
  <div class="wrap">
    <div>
      <span class="pill"><span class="dot pulse"></span>Marketing for {esc(t['trade'])}</span>
      <h1>More booked jobs for <span class="swap" data-dtr="trade">{esc(t['word'])}</span> in
        <span class="swap" data-dtr="region">East Texas</span>. Not more "leads."</h1>
      <p class="hero-sub">I'm Aaron, and I get {esc(t['word'])} in East Texas booked jobs, real work on the
        calendar, not clicks you paid for. You own everything I build. It's month to month. And I only take one
        {esc(t['one'])} per area, so your competitor can't hire me.</p>
      <div class="hero-cta">
        <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="hero">{PHONE}Call Aaron &mdash; he actually answers</a>
        <!-- [AARON: CONFIRM] 92% answer-rate stat, from your own outreach email. -->
        <span class="hero-note"><svg><use href="#i-check"/></svg>My phone's on and I answer it more than 92% of the time.</span>
      </div>
      <p class="hero-avail" data-avail><span class="live"></span><span data-avail-text>Give me a call.</span></p>
    </div>
    <div class="hero-media reveal">
      <div class="kick" aria-hidden="true"></div>
      <div class="frame">
        <div class="imgslot imgslot--wide" data-slot="{t['slug']}-hero" style="height:100%">
          <span class="tag">AI capability demo · clearly a demo, not a real job</span>
          <span class="lbl">A {esc(t['trade'])} scene, generated on demand</span>
          <span class="cue">Recraft: a clean, dramatic {esc(t['trade'])} work scene at golden hour, magazine-quality, no text, no fake people</span>
        </div>
      </div>
      <div class="float-card">
        <span class="ic"><svg><use href="#i-trend"/></svg></span>
        <div><b>20 yrs</b><span>doing this for a living</span></div>
      </div>
    </div>
  </div>
</section>

<div class="trust">
  <div class="wrap">
    <span class="lbl">Where I learned this</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Ex-CBO, cPanel</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Ex-CMO, Monarx</span>
    <span class="item"><svg><use href="#i-shield"/></svg>Co-founder, Consent Resolve</span>
    <a class="item" href="/work/"><svg><use href="#i-web"/></svg>See sites I've built &rarr;</a>
  </div>
</div>

<section class="sec sec-low">
  <div class="wrap">
    <div class="sec-head center reveal">
      <h2>You do great {esc(t['trade'])} work. So why is the phone quiet?</h2>
      <p class="lede">{esc(t['moment'])} If that's not you, it's the shop across town, and it's a marketing
      problem, not a skill problem. It's fixable.</p>
    </div>
    <div class="proof reveal">
      <div class="p"><b>{esc(t['search'])}</b><span>That's the moment that decides who gets the job. I make sure the answer is you.</span></div>
      <div class="p"><b>"Leads" aren't jobs</b><span>Most agencies sell clicks and call it a day. I care about one number: {esc(t['job'])} on your calendar.</span></div>
      <div class="p"><b>You live on the phone</b><span>Agencies that hide behind a contact form and a 3-day reply don't get how you work. I answer.</span></div>
    </div>
  </div>
</section>

<section class="sec sec-white">
  <div class="wrap">
    <div class="reveal" style="max-width:660px;margin-inline:auto;background:var(--primary-tint);border:1px solid var(--line-soft);border-radius:var(--r-lg);padding:24px 26px">
      <b style="display:block;margin-bottom:6px">Run the math on those junk leads:</b>
      <p style="color:var(--ink-variant)">$80 a lead. Five {esc(t['word'])} all buying the same one. Maybe one in ten
      turns into a real job. That's <strong style="color:var(--ink)">$800 out of your pocket for one booked job</strong>
      &mdash; if you even win the footrace to voicemail. Nobody selling you leads does that math out loud. I just did.</p>
    </div>
    <p class="lede center reveal" style="max-width:640px;margin:26px auto 0">I'm not for every shop, and I'll tell you
    straight if we're not a fit. <a href="/not-a-fit/">Here's who I'm not for.</a> Want the money and the terms up
    front? <a href="/pricing/">What it costs</a> &middot; <a href="/compare/">me vs. the big agencies</a>.</p>
  </div>
</section>

<section class="sec sec-white">
  <div class="wrap">
    <div class="sec-head center reveal"><h2>What I do for {esc(t['label'].lower())}</h2>
      <p class="lede">Everything that gets you found and gets you called. And I run every one of these right here on this page. The site is the demo.</p></div>
    <div class="cards">{sec_services()}</div>
  </div>
</section>

<section class="sec sec-low">
  <div class="wrap duo">
    <div class="reveal">
      <span class="caps">30 seconds, 3 taps</span>
      <h2 style="font-size:var(--d-lg);margin:10px 0 14px">Not ready to call? Start here.</h2>
      <p class="lede" style="margin-bottom:22px">Three quick taps and I'll call you back with something useful, not a pitch.</p>
      <div class="quiz" data-quiz>
        <div class="quiz-prog"><i class="on"></i><i></i><i></i></div>
        <div class="quiz-step on" data-q="trade"><h3>What's your trade?</h3><div class="quiz-grid">
          <button class="quiz-opt" type="button">{esc(t['trade'].title())}</button>
          <button class="quiz-opt" type="button">HVAC</button>
          <button class="quiz-opt" type="button">Plumbing</button>
          <button class="quiz-opt" type="button">Roofing</button>
          <button class="quiz-opt" type="button">Remodel / GC</button>
          <button class="quiz-opt" type="button">Something else</button></div></div>
        <div class="quiz-step" data-q="need"><h3>What do you need most?</h3><div class="quiz-grid">
          <button class="quiz-opt" type="button">More calls</button>
          <button class="quiz-opt" type="button">A better website</button>
          <button class="quiz-opt" type="button">Show up on Google</button>
          <button class="quiz-opt" type="button">All of it, honestly</button></div></div>
        <div class="quiz-step" data-q="phone"><h3>Where do I call you?</h3>
          <div class="quiz-field"><label for="qp">Your mobile</label>
          <input id="qp" data-q-phone type="tel" inputmode="tel" placeholder="(936) 555-0100" autocomplete="tel"></div>
          <button class="btn btn-call btn-block" type="button" data-q-submit style="margin-top:14px">{PHONE}Get my callback</button>
          <p class="quiz-err" role="alert"></p>
          <a class="quiz-skip" href="tel:+17133848985" data-cta-location="quiz-skip">or just call now &rarr;</a></div>
        <div class="quiz-step quiz-done" data-q="done"><span class="big"><svg width="30" height="30"><use href="#i-check"/></svg></span>
          <h3>Got it.</h3><p class="lede">Aaron will call you back shortly. Rather not wait? Call 713-384-8985.</p></div>
      </div>
    </div>
    <div class="reveal" data-callback>
      <div class="cbw">
        <h3>Call me in 28 seconds.</h3>
        <span class="demo-note"><svg width="14" height="14"><use href="#i-bolt"/></svg>This is speed-to-lead. I'll put it on your site too.</span>
        <p style="margin-bottom:18px">Drop your number. My system calls you almost instantly, while you're still
        thinking about it. That's the tool that turns a visitor into a booked job.</p>
        <form class="cbw-form"><input name="phone" type="tel" inputmode="tel" placeholder="Your mobile number" autocomplete="tel" aria-label="Your mobile number" required>
          <button class="btn btn-white" type="submit">{PHONE}Call me now</button></form>
        <p class="status" role="status" aria-live="polite"></p>
        <p class="fine">No spam, no list. Just a call from Aaron about your {esc(t['one'])}.</p>
      </div>
    </div>
  </div>
</section>

<section class="sec sec-white" id="faq">
  <div class="wrap">
    <div class="sec-head center reveal"><h2>Straight answers</h2><p class="lede">No fluff. Just how this works.</p></div>
    <div class="faq reveal">
      <details><summary>Who owns my website and leads if we part ways?<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">You do, from day one. The website, the domain, the ad accounts, your Google profile, your customer
        list, all in your name. Fire me and you walk out with every bit of it. I never hold anything hostage.</div></details>
      <details><summary>Is my market exclusive?<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">Yes. I take one {esc(t['one'])} per area, so I'm never working for you and your competitor at the
        same time. And I don't resell leads to anybody, every call is yours.</div></details>
      <details><summary>{esc(t['faqq'])}<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">{esc(t['faqa'])}</div></details>
      <details><summary>Is there a contract?<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">No lock-in. Month to month, no setup fee, no cancellation fee. If I don't earn it this month,
        fire me and keep everything I built.</div></details>
      <details><summary>Who does the work, you or an offshore team?<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">Me. Aaron. You call, I answer. You get the guy who ran marketing for cPanel and Monarx, not a
        script. I keep a cap on shops so you actually get my attention.</div></details>
      <details><summary>What does it cost?<svg class="chev"><use href="#i-chev"/></svg></summary>
        <div class="a">$500/mo for Website &amp; Growth, $500/mo for Social, ads at 15% of spend. Month to month, no
        setup fees. Call and I'll tell you exactly what your {esc(t['one'])} needs. <a href="/pricing/">See the plans &rarr;</a></div></details>
    </div>
  </div>
</section>

<section class="sec final">
  <div class="wrap reveal">
    <h2>One {esc(t['one'])} per area. Right now, that spot's open.</h2>
    <p class="lede">Once one of your competitors takes it, I can't work with you, that's the deal. One call, ten
    minutes, and I'll tell you straight whether I can fix what's costing you jobs.</p>
    <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="final">{PHONE}Call Aaron: 713-384-8985</a>
    <p class="hero-avail" data-avail style="justify-content:center;margin-top:16px"><span class="live"></span><span data-avail-text></span></p>
  </div>
</section>
</main>
{TAIL}
</body>
</html>
'''


def esc_json(s):
    import json
    return json.dumps(str(s))


def render_index():
    title = "Trades I help — contractor marketing by trade | Hey Aaron!"
    desc = "Marketing built for your specific trade: HVAC, plumbing, electrical, roofing, remodeling and 12 more. Pick your trade and see how I book you jobs. Call 713-384-8985."
    url = "https://aaron.chat/trades/"
    items = "\n".join(
        f'      <a href="/{t["slug"]}/"><svg><use href="#i-check"/></svg>{esc(t["label"])}</a>'
        for t in TRADES)
    ld = ('{"@context":"https://schema.org","@type":"CollectionPage",'
          f'"name":"Trades I help","url":"{url}",'
          '"about":"Contractor and home-service marketing organized by trade."}')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#074588">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="Trades I help — Hey Aaron! Marketing">
<meta property="og:description" content="Marketing built for your specific trade. Pick yours and see how I book you jobs.">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/ha.css?v={VER}">
<script type="application/ld+json">{ld}</script>
{PIXEL}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SPRITE}
{HEADER}
<main id="main">
<div class="page-hero">
  <div class="wrap">
    <span class="caps">Who I help</span>
    <h1>Marketing built for your trade.</h1>
    <p>The way an HVAC shop wins a job isn't how a plumber or a roofer wins theirs. Pick your trade and see
    marketing aimed at exactly how <em>your</em> phone rings &mdash; not generic "small business" advice.</p>
  </div>
</div>
<section class="sec">
  <div class="wrap">
    <div class="tradegrid reveal">
{items}
    </div>
    <p class="lede center" style="margin-top:26px;max-width:56ch;margin-inline:auto">Don't see your exact trade?
    <a href="tel:+17133848985">Call me at 713-384-8985</a> &mdash; if you run service trucks in East Texas, I can help.</p>
    <div class="center" style="margin-top:24px">
      <a class="btn btn-call btn-lg" href="tel:+17133848985" data-cta-location="trades-hub">{PHONE}Call Aaron: 713-384-8985</a>
    </div>
  </div>
</section>
</main>
{FOOTER}
{TAIL}
</body>
</html>
'''


def main():
    n = 0
    for t in TRADES:
        d = os.path.join(ROOT, t["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render(t))
        n += 1
    hub = os.path.join(ROOT, "trades")
    os.makedirs(hub, exist_ok=True)
    open(os.path.join(hub, "index.html"), "w", encoding="utf-8").write(render_index())
    print(f"wrote {n} ICP trade landing pages + /trades/ hub")


if __name__ == "__main__":
    main()
