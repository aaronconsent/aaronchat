#!/usr/bin/env python3
"""Generate the services hub (/services/) + one page per service (/services/<slug>/).

Static-site model: this emits committed HTML into the repo (no runtime build).
Edit the SERVICES list, re-run, commit the output. Shares brand/style.css.
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
      <p><a href="/services/">All services</a> · <a href="/pricing/">Pricing</a> · <a href="/about/">About</a></p>
      <p><a href="https://stats.lakelivingston.aaron.chat/">The Lake Livingston Service Pro Report</a></p>
      <p><a href="/privacy-policy/">Privacy</a> · <a href="/terms-of-service/">Terms</a></p>
    </div>
  </div>
</footer>
<script src="/brand/nav.js?v=9" defer></script>
<script src="/brand/lead.js?v=9" defer></script>"""


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
<link rel="stylesheet" href="/brand/style.css?v=9">
{PIXEL}
</head>
<body>
{HEADER}"""


# Categories in funnel order
CATEGORIES = [
    ("get-found", "Get Found", "The homeowner can't hire you if they can't find you."),
    ("get-chosen", "Get Chosen", "Found is step one. Trusted is what gets the call."),
    ("keep-them", "Keep Them Coming Back", "The cheapest job to win is from a customer you already have."),
    ("paid-growth", "Paid Growth", "When you're ready to buy reach, not just earn it."),
]

# plan label → pricing anchor
PLAN_LINKS = {
    "every": ("Included in every plan", "/pricing/#enrolled"),
    "honor": ("Honor Roll and up", "/pricing/#honor-roll"),
    "top": ("Top of Class and up", "/pricing/#top-of-class"),
    "top-val": ("Top of Class (Facebook) · Valedictorian (full stack)", "/pricing/#top-of-class"),
    "addon": ("Add-on — $200/mo, any plan (2 included in Valedictorian)", "/pricing/"),
}

SERVICES = [
    # ---- Get Found ----
    dict(slug="website", cat="get-found", icon="🌐",
        name="Website Build &amp; Management",
        tag="A fast, modern website — built, hosted, secured, and updated forever.",
        problem=("Nearly half the plumbing shops around the lake have no working website. "
                 "A Facebook page isn't a website — homeowners searching from a phone bounce off "
                 "logins and dead links. The shop next to you with a real site gets the call."),
        deliver=["Custom website built on a modern, AI-assisted stack",
                 "Hosting, SSL, and security — all handled, nothing to manage",
                 "Mobile-first and fast — loads in under a second",
                 "Town and service pages built to rank across the lake communities",
                 "Unlimited updates — email a change, it's done",
                 "You own the site, always"],
        plan="every"),
    dict(slug="local-seo", cat="get-found", icon="📍",
        name="Local SEO",
        tag="Show up first when someone nearby needs exactly what you do.",
        problem=("When an AC dies in July, the homeowner picks from the top of Google in about "
                 "ninety seconds. If you're not in the top three of the map pack, you're not in "
                 "the running — no matter how good your work is."),
        deliver=["Google Maps and local-pack optimization",
                 "Town + service landing pages targeting your trade",
                 "On-page SEO: titles, structure, schema markup",
                 "Keyword targeting for the searches that turn into jobs",
                 "Rank tracking on your monthly report card"],
        plan="every"),
    dict(slug="ai-optimization", cat="get-found", icon="🤖",
        name="AI Engine Optimization",
        tag="Get recommended by ChatGPT, Google AI Overviews, and Perplexity.",
        problem=("Your next customer might not Google at all. They'll ask ChatGPT "
                 "&ldquo;who's a good plumber near Livingston?&rdquo; The answer is built from "
                 "structured data almost no local shop bothers to set up. First one who does "
                 "becomes the name the AI repeats."),
        deliver=["Structured data and schema so the engines can read you",
                 "Q&amp;A content written to be quoted by AI answers",
                 "llms.txt and entity optimization",
                 "Consistent business identity across the web",
                 "Positioned to be the named answer in your trade + town"],
        plan="every"),
    dict(slug="google-business-profile", cat="get-found", icon="🅶",
        name="Google Business Profile Management",
        tag="Your most valuable listing — claimed, tuned, and worked every week.",
        problem=("A pile of local shops haven't even claimed their Google Business Profile. "
                 "Unclaimed means you can't answer reviews, fix wrong hours, or post updates — "
                 "and Google quietly ranks you lower for it."),
        deliver=["Claimed, verified, and fully optimized",
                 "Weekly Google posts that keep the listing active",
                 "Reviews responded to — every one",
                 "Photos, services, and hours kept current",
                 "Questions and answers managed"],
        plan="every"),
    dict(slug="citations", cat="get-found", icon="📒",
        name="Perfect Attendance — Local Citations",
        tag="Listed correctly everywhere that matters — and kept in sync.",
        problem=("Google trusts businesses whose name, address, and phone match across the web. "
                 "One wrong number on Yelp or an old directory and your ranking slips. Most shops "
                 "have dozens of mismatches they've never seen."),
        deliver=["Listed in 50+ local and trade directories",
                 "Name / address / phone audited and made consistent everywhere",
                 "Duplicate and wrong listings cleaned up",
                 "Kept in sync as your details change"],
        plan="honor"),
    # ---- Get Chosen ----
    dict(slug="reviews", cat="get-chosen", icon="⭐",
        name="Gold Stars — Review Engine",
        tag="Turn every finished job into a five-star review — automatically.",
        problem=("The median local plumber has 11 Google reviews. The top three have 365. "
                 "That gap is the whole game — and it's the single most catchable thing on your "
                 "report card. Shops that ask get reviews. Shops that don't, don't."),
        deliver=["Automatic review request after every job",
                 "One-tap review links — no typing for the customer",
                 "Every review answered, good or bad, in your voice",
                 "Unhappy customers intercepted before they post publicly",
                 "Review count tracked weekly against your rivals"],
        plan="honor"),
    dict(slug="auto-blog", cat="get-chosen", icon="✍️",
        name="Auto Blog",
        tag="Fresh, ranking content every week — without you writing a word.",
        problem=("Google rewards sites that stay active. Most contractors post once and never "
                 "again. A steady drip of useful local content is a ranking lever almost nobody "
                 "in your market is pulling."),
        deliver=["Regular posts written for your trade and towns",
                 "Answers the questions homeowners actually search",
                 "Internal links that lift your whole site's rankings",
                 "Written, published, and optimized automatically"],
        plan="every"),
    dict(slug="social-media", cat="get-chosen", icon="📱",
        name="Social Media Management",
        tag="Your channels posted for you — from real jobs, not stock photos.",
        problem=("Homeowners check Facebook before they call. An empty or abandoned page reads "
                 "as &ldquo;out of business.&rdquo; But no working contractor has time to post "
                 "three times a week."),
        deliver=["3 to 6 channels posted for you, depending on plan",
                 "Content built from your job photos and reviews",
                 "A consistent schedule, completely hands-off",
                 "Facebook, Instagram, and the channels that fit your trade"],
        plan="every"),
    dict(slug="report-card", cat="get-chosen", icon="📝",
        name="The Monthly Report Card",
        tag="The same public scoreboard we grade the whole county on — pointed at you.",
        problem=("You can't improve what you can't see. Most shops have no idea where they rank "
                 "until a slow month tells them. We measure it every week and hand you the card."),
        deliver=["Your grade across every ranking factor",
                 "Class rank against every competitor in the county",
                 "Review-velocity vs your top three rivals",
                 "What moved, what didn't, and what's next",
                 "Monthly — or weekly on Top of Class and up"],
        plan="every"),
    # ---- Keep Them ----
    dict(slug="customer-newsletter", cat="keep-them", icon="📬",
        name="Class Notes — Customer Newsletter",
        tag="The monthly email that turns past customers into repeat jobs.",
        problem=("The cheapest job to win is one from a customer you already have. Most "
                 "contractors never contact past customers again — and lose them to whoever "
                 "shows up in the mailbox first."),
        deliver=["Monthly email to your customer list",
                 "Seasonal reminders — tune-ups, inspections, freeze prep",
                 "Written in your voice, sent for you",
                 "Drives repeat work and referrals"],
        plan="top"),
    dict(slug="email-outreach", cat="keep-them", icon="✉️",
        name="Automated Email Outreach",
        tag="Consistent outreach that fills the pipeline — 1,000+ sends a month.",
        problem=("Word of mouth is great until it's a slow month. A steady outbound channel "
                 "means you're never sitting around waiting on the phone to ring."),
        deliver=["1,000 to 10,000 sends per month, scaling by plan",
                 "Targeted local lists for your service area",
                 "Written and scheduled for you",
                 "Replies routed straight to your inbox"],
        plan="every"),
    # ---- Paid Growth ----
    dict(slug="paid-advertising", cat="paid-growth", icon="🎯",
        name="Paid Advertising Management",
        tag="Facebook, Google, and Local Services Ads — run by someone who reads the report card.",
        problem=("Ads only work when they point at a shop that's already set up to convert. Most "
                 "contractors boost a post, get nothing, and quit. We run the whole funnel — "
                 "from the ad to the landing page to the phone call."),
        deliver=["Facebook Ads managed (Top of Class)",
                 "Google Ads + Local Services Ads managed (Valedictorian)",
                 "Landing pages built specifically to convert",
                 "Call tracking — know which jobs came from which ad",
                 "Ad spend billed separately, plus 10% management"],
        plan="top-val"),
    dict(slug="reel-video", cat="paid-growth", icon="🎬",
        name="Reel Video Marketing",
        tag="Short, scroll-stopping videos from your job photos — four a month.",
        problem=("Video gets more reach than anything else on social, and homeowners trust a "
                 "face. But a local videographer costs more per shoot than this costs per month."),
        deliver=["4 short reels every month",
                 "Before / after job reels",
                 "Gold Star of the Week — review shout-outs",
                 "Seasonal alerts and meet-the-crew clips",
                 "Built from footage and photos you already have"],
        plan="addon"),
    dict(slug="group-sharing", cat="paid-growth", icon="🏘️",
        name="Local Group Sharing + Nextdoor",
        tag="Show up where lake-community jobs actually start — the neighborly channels.",
        problem=("Around the lake, half the jobs start with &ldquo;anyone know a good…?&rdquo; "
                 "in a Facebook group or on Nextdoor. If you're not there when the question gets "
                 "asked, someone else is."),
        deliver=["Presence in the local Facebook groups that matter",
                 "Nextdoor business posting",
                 "Neighborhood-level targeting around the lake",
                 "Real, helpful participation — not spam"],
        plan="top"),
]

SVC_BY_SLUG = {s["slug"]: s for s in SERVICES}
ORDER = [s["slug"] for s in SERVICES]

# Purpose-built landscape hero per service — each a different educator persona.
# (img, alt). Any slug not listed falls back to the rotating pool below.
SVC_IMAGES = {
    "website":                 ("/brand/media/svc-website.jpg",  "Aaron as a Renaissance inventor sketching website blueprints"),
    "google-business-profile": ("/brand/media/svc-gbp.jpg",      "Aaron holding a giant map pin beside a chalkboard town map"),
    "reviews":                 ("/brand/media/svc-reviews.jpg",  "Aaron in graduation regalia holding a straight-A report card"),
    "auto-blog":               ("/brand/media/svc-autoblog.jpg", "Aaron as a Victorian schoolmaster at a printing press churning out pages"),
    "social-media":            ("/brand/media/svc-social.jpg",   "Aaron as an orchestra conductor conducting glowing social icons"),
    "email-outreach":          ("/brand/media/svc-email.jpg",    "Aaron as a caveman teacher sending a message from a stone tablet"),
    "reel-video":              ("/brand/media/svc-reels.jpg",    "Aaron cranking an antique Edison-era movie camera"),
    "ai-optimization":         ("/brand/media/svc-ai.jpg",       "Aaron as a mad scientist with a tin robot and a neural-network board"),
    "paid-advertising":        ("/brand/media/svc-ads.jpg",      "Aaron as a Wild West schoolmaster pointing at a WANTED bullseye board"),
}

# Fallback professor imagery rotated across any remaining service heroes (img, object-position%)
HERO_IMAGES = [
    ("/brand/media/hero-professor.jpg", 68),
    ("/brand/media/professor-left.jpg", 32),
    ("/brand/media/era-future.jpg", 72),
    ("/brand/media/era-greece.jpg", 50),
    ("/brand/media/era-renaissance.jpg", 62),
]


def render_service(s):
    plan_label, plan_url = PLAN_LINKS[s["plan"]]
    deliver = "\n".join(f"        <li>{d}</li>" for d in s["deliver"])
    cat_name = next(c[1] for c in CATEGORIES if c[0] == s["cat"])

    # prev / next within the full list
    i = ORDER.index(s["slug"])
    prev_link = next_link = ""
    if i > 0:
        p = SVC_BY_SLUG[ORDER[i - 1]]
        prev_link = f'<a href="/services/{p["slug"]}/">← {p["name"]}</a>'
    if i < len(ORDER) - 1:
        n = SVC_BY_SLUG[ORDER[i + 1]]
        next_link = f'<a href="/services/{n["slug"]}/">{n["name"]} →</a>'

    title = f'{s["name"].replace("&amp;", "&")} — Top of Class Marketing'
    desc = s["tag"].replace('&ldquo;', '"').replace('&rdquo;', '"')
    # dedicated persona shot if we have one, else rotate the fallback pool
    if s["slug"] in SVC_IMAGES:
        src, alt = SVC_IMAGES[s["slug"]]
        img_tag = (f'<img src="{src}" alt="{alt}" width="1500" height="843" '
                   f'style="object-position:center" loading="eager">')
    else:
        img, pos = HERO_IMAGES[i % len(HERO_IMAGES)]
        img_tag = (f'<img src="{img}" alt="Aaron, Top of Class Marketing" width="1000" height="1250" '
                   f'style="object-position:{pos}% center" loading="eager">')
    return f"""{page_head(title, desc, f'/services/{s["slug"]}/')}

<div class="hero hero--split">
  <div class="wrap">
    <div class="hero-copy">
    <p class="kicker">{cat_name}</p>
    <h1>{s['name']}</h1>
    <p class="sub">{s['tag']}</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/report-card/">Get my free report card</a>
      <a class="btn btn-ghost" href="/pricing/">See the plans</a>
    </div>
    </div>
    <div class="hero-figure">{img_tag}</div>
  </div>
</div>

<section>
  <div class="wrap">
    <p class="eyebrow">Why it matters</p>
    <h2>The problem it solves.</h2>
    <p class="lede">{s['problem']}</p>
  </div>
</section>

<section class="alt">
  <div class="wrap">
    <p class="eyebrow">What you get</p>
    <h2>Exactly what's included.</h2>
    <ul class="deliverables">
{deliver}
    </ul>
    <div class="plan-badge" style="margin-top:26px">
      <span><b>Availability:</b> {plan_label}</span>
      <a href="{plan_url}">See plans →</a>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Start here</p>
    <h2>See where you stand first — it's free.</h2>
    <p class="lede">Every contractor around Lake Livingston is already graded. Look yourself up,
    or have Aaron walk you through your card and show you exactly where this service would move
    the needle for your shop.</p>
    <p><a class="btn btn-primary" href="/report-card/">Get my free report card</a></p>
    <div class="svc-nextprev">
      <span>{prev_link}</span>
      <span>{next_link}</span>
    </div>
  </div>
</section>

{FOOTER}
</body>
</html>
"""


# plan comparison matrix (columns) + features (rows). Values: True=✓, False=—, or text.
PLANS = [("🎒 Enrolled", "$300/mo"), ("⭐ Honor Roll", "$600/mo"),
         ("🏆 Top of Class", "$1,200/mo"), ("🎓 Valedictorian", "$2,400/mo")]
FEAT_COL = 1  # index of the highlighted (featured) plan column

MATRIX = [
    ("Get found", [
        ("Website built &amp; managed", [True, True, True, True]),
        ("Local SEO", [True, True, True, True]),
        ("AI Engine Optimization", [True, True, True, True]),
        ("Google Business Profile", [True, True, True, True]),
        ("Local citations (50+ directories)", [False, True, True, True]),
    ]),
    ("Get chosen", [
        ("Auto blog &mdash; ranking content", [True, True, True, True]),
        ("Reviews engine (Gold Stars)", [False, True, True, True]),
        ("Social channels, posted for you", ["3", "6", "6", "All"]),
        ("Report card", ["Monthly", "Monthly", "Weekly", "Weekly"]),
    ]),
    ("Keep them coming back", [
        ("Automated email outreach", ["1,000/mo", "2,500/mo", "2,500/mo", "10,000/mo"]),
        ("Customer newsletter (Class Notes)", [False, False, True, True]),
    ]),
    ("Paid growth", [
        ("Facebook Ads managed", [False, False, True, True]),
        ("Google Ads + Local Services Ads", [False, False, False, True]),
        ("Local Group Sharing + Nextdoor", [False, False, True, True]),
        ("Call tracking", [False, False, True, True]),
        ("Reel videos", ["Add-on", "Add-on", "Add-on", "2/mo"]),
        ("Seasonal campaign calendar", [False, False, False, True]),
        ("In-person strategy visits + priority support", [False, False, False, True]),
    ]),
]


def _cell(v, feat):
    fc = " feat" if feat else ""
    if v is True:
        return f'<td class="yes{fc}" aria-label="included">&#10003;</td>'
    if v is False:
        return f'<td class="no{fc}" aria-label="not included">&mdash;</td>'
    return f'<td class="val{fc}">{v}</td>'


def render_matrix():
    heads = "".join(
        f'<th class="{"feat" if i == FEAT_COL else ""}">{name}<span>{price}</span></th>'
        for i, (name, price) in enumerate(PLANS))
    body = ""
    for group, rows in MATRIX:
        body += f'\n        <tr class="grp"><td colspan="5">{group}</td></tr>'
        for label, vals in rows:
            cells = "".join(_cell(v, i == FEAT_COL) for i, v in enumerate(vals))
            body += f'\n        <tr><th scope="row">{label}</th>{cells}</tr>'
    starts = "".join(
        f'<td class="{"feat" if i == FEAT_COL else ""}"><a class="btn btn-primary" href="/report-card/">Start</a></td>'
        for i in range(len(PLANS)))
    body += f'\n        <tr class="cta-row"><th scope="row"></th>{starts}</tr>'
    return f"""<div class="matrix-wrap">
    <table class="matrix">
      <thead><tr><th class="corner">What's included</th>{heads}</tr></thead>
      <tbody>{body}
      </tbody>
    </table>
  </div>"""


def render_hub():
    cats_html = ""
    for cat_slug, cat_name, cat_sub in CATEGORIES:
        cards = ""
        for s in SERVICES:
            if s["cat"] != cat_slug:
                continue
            plan_label, _ = PLAN_LINKS[s["plan"]]
            short_plan = ("Every plan" if s["plan"] == "every"
                          else "Honor Roll +" if s["plan"] == "honor"
                          else "Top of Class +" if s["plan"] in ("top", "top-val")
                          else "Add-on")
            cards += f"""
        <a class="svc-card" href="/services/{s['slug']}/">
          <span class="svc-icon">{s['icon']}</span>
          <h3>{s['name']}</h3>
          <p>{s['tag']}</p>
          <span class="svc-plan">{short_plan}</span>
          <span class="svc-more">Learn more →</span>
        </a>"""
        cats_html += f"""
    <div class="svc-cat">
      <p class="eyebrow">{cat_name}</p>
      <h2>{cat_sub}</h2>
      <div class="svc-cards">{cards}
      </div>
    </div>"""

    title = "Services — Top of Class Marketing"
    desc = ("Everything a Lake Livingston contractor needs to win — website, local SEO, reviews, "
            "Google profile, social, ads, and reels. One team, one bill, one report card.")
    return f"""{page_head(title, desc, '/services/')}

<div class="hero hero--split">
  <div class="wrap">
    <div class="hero-copy">
    <p class="kicker">One team · one bill · one report card</p>
    <h1>Everything a shop needs to win. Under one roof.</h1>
    <p class="sub">Most contractors juggle a web guy, a review app, a social tool, and an ads
    freelancer — and none of them talk to each other. We run all of it, measured against the
    same public scoreboard, starting at <b>$300 a month</b>.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/report-card/">Get my free report card</a>
      <a class="btn btn-ghost" href="/pricing/">See the plans</a>
    </div>
    </div>
    <div class="hero-figure"><img src="/brand/media/professor-left.jpg" alt="Aaron teaching at the chalkboard" width="1600" height="900" loading="eager" decoding="async"></div>
  </div>
</div>

<section>
  <div class="wrap">
{cats_html}
  </div>
</section>

<section class="alt">
  <div class="wrap">
    <p class="eyebrow">Compare plans</p>
    <div class="section-head"><h2>What's included in each plan.</h2>
      <p class="lede">Every plan is one team, one bill, one report card. Here's exactly what you get
      as you move up &mdash; or see the <a href="/pricing/">full pricing page</a>.</p></div>
    {render_matrix()}
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">The honest version</p>
    <h2>How all of this fits in a $300 plan.</h2>
    <p class="lede">Simple: it's run by an AI-powered stack instead of a room full of account
    managers — the same stack that built <a href="https://stats.lakelivingston.aaron.chat/">the
    county scoreboard</a> that grades all 1,900 contractors around the lake every week. That's
    the whole edge, and it's why we can hand a local shop a full marketing department for the
    price of a single freelancer's afternoon.</p>
    <p><a class="btn btn-primary" href="/pricing/">See what's in each plan →</a></p>
  </div>
</section>

{FOOTER}
</body>
</html>
"""


def main():
    hub_dir = os.path.join(ROOT, "services")
    os.makedirs(hub_dir, exist_ok=True)
    with open(os.path.join(hub_dir, "index.html"), "w") as f:
        f.write(render_hub())
    n = 1
    for s in SERVICES:
        d = os.path.join(hub_dir, s["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write(render_service(s))
        n += 1
    print(f"[services] wrote hub + {len(SERVICES)} service pages -> {hub_dir}")


if __name__ == "__main__":
    main()
