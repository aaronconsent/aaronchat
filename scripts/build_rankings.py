#!/usr/bin/env python3
"""Generate /report-card/<trade>/ leaderboard pages on aaron.chat.

A sexy, FOMO-driven ranked list of EVERY shop in a trade, parsed straight from
the grading engine's biz pages (the complete set — the search-index is only a
subset). Linked from the diagnose dashboard's rank line, with ?you=<slug> to
spotlight the visitor's own row. Run after build_lookup.py.
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIZ = os.path.join(ROOT, "stats-lakelivingston/docs/biz")
OUT = os.path.join(ROOT, "report-card")
RANKS = os.path.join(ROOT, "data/ranks.json")
VER = "30"


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def num(s):
    try:
        return float(re.sub(r"[^0-9.]", "", str(s)))
    except Exception:
        return 0.0


def esc(s):
    return H.escape(str(s or ""))


def gclass(g):
    c = (g or "")[:1].upper()
    return "g-a" if c == "A" else "g-b" if c == "B" else "g-c" if c == "C" else "g-f"


def parse_biz(slug):
    fn = os.path.join(BIZ, slug, "index.html")
    if not os.path.isfile(fn):
        return None
    h = open(fn, encoding="utf-8").read()

    def row(label):
        m = re.search(r'rc-label">' + re.escape(label) + r'</span><span class="rc-fill">(.*?)</span>', h, re.S)
        return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

    rankfill = row("Class rank")
    rm = re.search(r"#(\d+)\s*of\s*(\d+)\s*(?:local\s*)?(.+)", rankfill)
    if not rm:
        return None  # unranked / out of service area
    rk = [int(rm.group(1)), int(rm.group(2)), rm.group(3).strip()]
    gm = re.search(r'class="rc-grade[^"]*"[^>]*>([A-F][+-]?)</span>', h)
    sm = re.search(r'class="rc-score">(\d+)\s*/\s*100', h)
    standing = row("Google standing")
    st = re.search(r"([\d.]+)\s*[·|]\s*([\d,]+)\s*reviews", standing)
    return {
        "slug": slug,
        "n": H.unescape(row("Business")) or slug.replace("-", " ").title(),
        "c": H.unescape(row("Town")),
        "g": gm.group(1) if gm else "?",
        "p": int(sm.group(1)) if sm else 0,
        "rk": rk,
        "r": st.group(1) if st else "",
        "rv": st.group(2).replace(",", "") if st else "",
    }


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

FOOTER = f"""<footer class="site-foot">
  <div class="wrap cols">
    <div>
      <span class="hand">Top of Class Marketing</span>
      <p>Aaron Phillips · Livingston, Texas</p>
      <p><a href="tel:+17133848985">713-384-8985</a> · <a href="mailto:hello@aaron.chat">hello@aaron.chat</a></p>
    </div>
    <div>
      <p><a href="/report-card/">Get your report card</a> · <a href="/pricing/">Pricing</a> · <a href="/about/">About</a></p>
      <p><a href="/privacy-policy/">Privacy</a> · <a href="/terms-of-service/">Terms</a></p>
    </div>
  </div>
</footer>
<script src="/brand/nav.js?v={VER}" defer></script>
<script src="/brand/chat.js?v={VER}" defer></script>"""

HILITE = """<script>
(function(){
  var you = new URLSearchParams(location.search).get('you');
  var row = you && document.querySelector('.rr[data-slug="' + you.replace(/[^a-z0-9-]/gi,'') + '"]');
  var banner = document.getElementById('rank-you');
  if (row) {
    row.classList.add('is-you');
    var n = row.getAttribute('data-rank'), m = row.getAttribute('data-total');
    if (banner) { banner.innerHTML = 'That\\u2019s you at <b>#' + n + ' of ' + m + '</b>. Every shop above you is getting calls you\\u2019re not \\u2014 <a href="/report-card/">here\\u2019s how to pass them \\u2192</a>'; banner.hidden = false; }
    setTimeout(function(){ row.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 300);
  }
})();
</script>"""


def render_row(s, total):
    rank = s["rank"]
    stars = ("★ " + esc(s["r"]) if s.get("r") else "")
    revs = (esc(s["rv"]) + " reviews" if s.get("rv") else "no reviews")
    meta = " · ".join([x for x in [stars, revs, esc(s.get("c"))] if x])
    return (
        f'<li class="rr{" top" if rank <= 3 else ""}" data-slug="{esc(s["slug"])}" data-rank="{rank}" data-total="{total}" style="--sc:{int(s.get("p") or 0)}%">'
        f'<span class="rr-n">{rank}</span>'
        f'<span class="rr-grade {gclass(s["g"])}">{esc(s["g"])}</span>'
        f'<span class="rr-main"><span class="rr-name">{esc(s["n"])}</span>'
        f'<span class="rr-meta">{meta}</span></span>'
        f'<span class="rr-score">{int(s.get("p") or 0)}</span></li>'
    )


def render_page(slug, label, shops):
    total = len(shops)
    tl = label[:1].upper() + label[1:]
    rows = "\n      ".join(render_row(s, total) for s in shops)
    title = f"{tl} around Lake Livingston, graded — Top of Class Marketing"
    desc = f"All {total} {label} around Lake Livingston, ranked this week by the six things that decide who gets the call."
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://aaron.chat/report-card/{slug}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{tl} around Lake Livingston, graded.">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://aaron.chat/report-card/{slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/brand/style.css?v={VER}">
</head>
<body class="rank-page">
{HEADER}

<div class="hero rank-hero">
  <div class="wrap">
    <p class="kicker">Updated weekly · public Google data</p>
    <h1>{tl} around Lake Livingston, graded.</h1>
    <p class="sub"><b>{total} shops.</b> A handful are pulling away and getting the calls — everyone below is
    fighting for what's left. Here's this week's board.</p>
    <p id="rank-you" class="rank-you" hidden></p>
  </div>
</div>

<section class="rank-sec">
  <div class="wrap">
    <ol class="rank-list">
      {rows}
    </ol>
    <div class="rank-cta">
      <h2>Not where you want to be?</h2>
      <p>Where you land on this board decides who gets the call. See your own report card — every factor
      scored — and the exact plan to climb, free.</p>
      <a class="btn btn-primary" href="/report-card/">Get my free report card →</a>
    </div>
  </div>
</section>

{FOOTER}
{HILITE}
</body>
</html>
"""


def main():
    import json
    groups = {}
    for d in sorted(os.listdir(BIZ)):
        if not os.path.isdir(os.path.join(BIZ, d)):
            continue
        s = parse_biz(d)
        if not s:
            continue
        slug = slugify(s["rk"][2])
        groups.setdefault(slug, {"label": s["rk"][2], "shops": []})
        groups[slug]["shops"].append(s)

    n, ranks = 0, {}
    for slug, g in groups.items():
        # one consistent ranking: by grading score, then reviews
        shops = sorted(g["shops"], key=lambda s: (s.get("p") or 0, num(s.get("rv"))), reverse=True)
        total = len(shops)
        for i, s in enumerate(shops):
            s["rank"] = i + 1
            ranks[s["slug"]] = [i + 1, total, g["label"]]
        outd = os.path.join(OUT, slug)
        os.makedirs(outd, exist_ok=True)
        open(os.path.join(outd, "index.html"), "w").write(render_page(slug, g["label"], shops))
        n += 1

    os.makedirs(os.path.dirname(RANKS), exist_ok=True)
    json.dump(ranks, open(RANKS, "w"), separators=(",", ":"))
    print(f"wrote {n} trade leaderboard pages + {len(ranks)} ranks to data/ranks.json")


if __name__ == "__main__":
    main()
