#!/usr/bin/env python3
"""Generate the published style guide at /style-guide/.

Renders the locked design system + voice as browsable pages, built with the
very system they document. Noindex — public so Aaron can hand a client the URL,
but never in search results competing with the real pages.

Sources of truth (do not restate, read):
  .docs/voice.md   -> /style-guide/voice/
  brand/style.css  -> tokens parsed live for the color + type pages
Run after any token change:  python3 scripts/build_styleguide.py
"""
import os, re, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "style-guide")
CSS = os.path.join(ROOT, "brand/style.css")
VOICE = os.path.join(ROOT, ".docs/voice.md")
VER = "24"

PAGES = [
    ("", "Style guide", "The locked system: voice, color, type, components, motion, and the rules that don't bend."),
    ("voice", "Voice", "Who we're talking to, how we sound, the banned list, and the canonical facts."),
    ("directives", "Directives", "The non-negotiables. Read these before writing a line of copy or code."),
    ("color", "Color", "Every token, its job, and its measured contrast."),
    ("typography", "Typography", "Four families, one job each, and the fluid scale."),
    ("components", "Components", "The built vocabulary. Reuse before inventing."),
    ("motion", "Motion", "Easing tokens, the duration budget, and the rules that keep it honest."),
]


def esc(s):
    return H.escape(str(s or ""))


# ----------------------------------------------------------------- tokens
def tokens():
    css = open(CSS, encoding="utf-8").read()
    root = re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)
    out = {}
    for m in re.finditer(r"(--[\w-]+):\s*([^;]+);(?:\s*/\*\s*(.*?)\s*\*/)?", root):
        out[m.group(1)] = (m.group(2).strip(), (m.group(3) or "").strip())
    return out


def hex2rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(hex2rgb(a)), lum(hex2rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------------------------- md -> html
def md(text):
    """Minimal markdown renderer — enough for voice.md. No dependencies."""
    lines = text.split("\n")
    out, i = [], 0
    in_ul = False

    def inline(s):
        s = esc(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        return s

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    while i < len(lines):
        ln = lines[i].rstrip()
        st = ln.strip()
        if not st:
            close_ul(); i += 1; continue
        if st == "---":
            close_ul(); out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)", st)
        if m:
            close_ul()
            lvl = len(m.group(1))
            tag = {1: "h1", 2: "h2", 3: "h3", 4: "h4"}[lvl]
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append(f'<{tag} id="{slug}">{inline(m.group(2))}</{tag}>')
            i += 1; continue
        # table
        if st.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            close_ul()
            hdr = [c.strip() for c in st.strip("|").split("|")]
            out.append('<div class="sg-tablewrap"><table><thead><tr>' +
                       "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue
        if re.match(r"^[-*]\s+", st) or re.match(r"^\d+\.\s+", st):
            if not in_ul:
                out.append("<ul class=\"sg-list\">"); in_ul = True
            out.append("<li>" + inline(re.sub(r"^([-*]|\d+\.)\s+", "", st)) + "</li>")
            i += 1; continue
        close_ul()
        buf = [st]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|[-*]\s|\||---$|\d+\.\s)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    close_ul()
    return "\n".join(out)


# ------------------------------------------------------------------ chrome
def nav(active):
    items = []
    for slug, title, _ in PAGES:
        href = "/style-guide/" + (slug + "/" if slug else "")
        cls = ' class="on"' if slug == active else ""
        items.append(f'<a href="{href}"{cls}>{esc(title)}</a>')
    return '<nav class="sg-nav">' + "".join(items) + "</nav>"


def page(slug, title, desc, body):
    up = "Style guide" if slug else None
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.add('js')</script>
<title>{esc(title)} · Top of Class Style Guide</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<link rel="stylesheet" href="/brand/style.css?v={VER}">
<link rel="stylesheet" href="/brand/styleguide.css?v={VER}">
</head>
<body class="sg-page">
<header class="site-head">
  <div class="wrap">
    <a class="logo" href="/"><span class="mark">A+</span> Top of Class Marketing</a>
    <nav class="site-nav"><a href="/style-guide/">Style guide</a><a class="cta" href="/">Back to site</a></nav>
  </div>
</header>

<div class="sg-head">
  <div class="wrap">
    {'<a class="sg-up" href="/style-guide/">&larr; Style guide</a>' if up else ''}
    <h1>{esc(title)}</h1>
    <p class="sg-desc">{esc(desc)}</p>
    {nav(slug)}
  </div>
</div>

<main class="wrap sg-main">
{body}
</main>

<footer class="site-foot">
  <div class="wrap cols">
    <div><span class="hand">Top of Class Marketing</span><p>Internal reference. Not indexed.</p></div>
    <div><p><a href="/style-guide/">Style guide index</a> · <a href="/">aaron.chat</a></p></div>
  </div>
</footer>
<script src="/brand/nav.js?v={VER}" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------- pages
def p_index():
    cards = []
    for slug, title, desc in PAGES[1:]:
        cards.append(f'<a class="sg-card" href="/style-guide/{slug}/"><h3>{esc(title)}</h3>'
                     f'<p>{esc(desc)}</p><span class="sg-go">Open &rarr;</span></a>')
    return f"""
<section class="sg-sec">
  <p class="sg-lede">This is the system aaron.chat is built from. It exists so every page, email and post
  sounds like the same company and looks like the same company. When something here conflicts with what's
  on a page, this wins and the page is the bug.</p>
  <div class="sg-grid">{''.join(cards)}</div>
</section>
<section class="sg-sec">
  <h2>How to use it</h2>
  <p>Writing copy: open <a href="/style-guide/voice/">Voice</a>, paste Block A into the prompt, add Block C
  whenever the copy states a fact. Building a page: check <a href="/style-guide/components/">Components</a>
  before inventing anything, and hold the <a href="/style-guide/directives/">Directives</a>.</p>
  <p>Source files, for agents and editors: <code>.docs/voice.md</code> (voice), <code>DESIGN.md</code>
  (visual system), <code>PRODUCT.md</code> (strategy). This site renders them; it does not replace them.</p>
</section>
"""


def p_voice():
    return '<section class="sg-sec sg-prose">' + md(open(VOICE, encoding="utf-8").read()) + "</section>"


def p_directives():
    rules = [
        ("Never fabricate proof",
         "No invented testimonials, no client outcome metrics, no \"300% more calls.\" We are pre-first-client "
         "for marketing services and the copy must never imply otherwise. Every number traces to public data or "
         "a documented model. One invented number poisons the whole proposition, because the proposition is that "
         "the grade is honest.", "hard"),
        ("Label anything modeled",
         "Leads per month, cost per lead, cost per booked job and revenue-left-on-the-table are projections from "
         "tunable constants in <code>scripts/build_lookup.py</code>. They ship with \"est.\" or \"we project\" "
         "attached, every time. Never dressed up as measurement.", "hard"),
        ("WCAG 2.2 AA, treated as the floor",
         "Body text 4.5:1, large text 3:1, visible keyboard focus on everything interactive, a "
         "<code>prefers-reduced-motion</code> alternative for every animation. The audience is 40+ reading a "
         "phone outdoors in Texas daylight. AA is where we start, not where we aim.", "hard"),
        ("Meaning never rides on color alone",
         "Grade badges always carry the letter. Status is never green-vs-red with nothing else to read.", "hard"),
        ("Three plans, no offers",
         "$300 Enrolled, $600 Honor Roll, $1,200 Top of Class. Month to month. No founding-five, no free first "
         "year, no scarcity claims. If a page still shows an old offer, the page is wrong.", "hard"),
        ("Bump the asset version",
         "Every <code>/brand/*.css</code> and <code>/brand/*.js</code> reference is stamped <code>?v=N</code>. "
         "Change either file and you bump N across all HTML plus the Python generators, or the edge serves stale "
         "assets to everyone.", "process"),
        ("Internal docs never get served",
         "<code>PRODUCT.md</code>, <code>DESIGN.md</code>, <code>.claude</code>, <code>.impeccable</code> and "
         "<code>.docs</code> are in <code>.assetsignore</code>. The repo root is the served directory, so anything "
         "not excluded is public. Verify with a curl after deploying.", "process"),
        ("Reveals enhance, never gate",
         "Content is visible by default; motion is added on top. Reveal classes sit behind <code>html.js</code> and "
         "every JS-driven animation has a <code>setTimeout</code> finaliser, because a backgrounded tab throttles "
         "<code>requestAnimationFrame</code> to zero and would otherwise ship a blank section.", "process"),
    ]
    out = []
    for t, b, kind in rules:
        out.append(f'<div class="sg-rule sg-rule--{kind}"><h3>{esc(t)}</h3><p>{b}</p></div>')
    return f"""
<section class="sg-sec">
  <p class="sg-lede">Two kinds of rule. <b>Hard</b> rules protect the brand's credibility and are not
  negotiable without Aaron. <b>Process</b> rules stop the site breaking in ways that are hard to notice.</p>
  {''.join(out)}
</section>
<section class="sg-sec">
  <h2>Anti-references</h2>
  <p>What this must never look like. Each of these would cost us the argument we're making.</p>
  <div class="sg-anti">
    <div><h4>Generic SaaS / AI startup</h4><p>Purple-blue gradients, glass cards, 3D blobs, stock teams at
    laptops. It would make real grading data look invented.</p></div>
    <div><h4>Big-city agency polish</h4><p>The Dallas or Houston firm look. We are positioned against it;
    resembling it defeats the point.</p></div>
    <div><h4>Cheap contractor template</h4><p>The Wix look our prospects already have. We must visibly out-class
    the sites we grade.</p></div>
    <div><h4>Literal schoolhouse clip-art</h4><p>Cartoon apples and crayon fonts. The report-card metaphor has to
    stay sharp and adult, or the grade stops reading as a real judgment.</p></div>
  </div>
</section>
"""


def p_color():
    T = tokens()
    groups = [
        ("Brand", ["--board", "--board-2", "--board-tint", "--pen", "--pen-dark", "--pen-text", "--star", "--gold", "--pass"]),
        ("Surface", ["--paper", "--paper-2", "--white"]),
        ("Text", ["--ink", "--slate", "--chalk", "--chalk-dim"]),
        ("Line", ["--line", "--line-2"]),
    ]
    out = []
    for name, keys in groups:
        rows = []
        for k in keys:
            if k not in T:
                continue
            val, note = T[k]
            sw = f'<span class="sg-sw" style="background:{val}"></span>'
            c = ""
            if val.startswith("#"):
                on_paper = contrast(val, T["--paper"][0])
                on_board = contrast(val, T["--board"][0])
                c = (f'<span class="sg-cx">on paper <b>{on_paper:.1f}:1</b></span>'
                     f'<span class="sg-cx">on board <b>{on_board:.1f}:1</b></span>')
            rows.append(f'<li class="sg-tok">{sw}<span class="sg-tokname"><code>{esc(k)}</code>'
                        f'<span class="sg-tokval">{esc(val)}</span></span>'
                        f'<span class="sg-toknote">{esc(note)}</span>{c}</li>')
        out.append(f'<h2>{name}</h2><ul class="sg-toks">{"".join(rows)}</ul>')
    return f"""
<section class="sg-sec">
  <p class="sg-lede">Strategy is <b>committed</b>: chalkboard green carries the large surfaces, red pen is the
  single action color and stays under about a tenth of any view, gold is punctuation. Contrast is measured, not
  assumed. Body text needs 4.5:1 and large text needs 3:1.</p>
  <p class="sg-note sg-warn"><b>Use <code>--pen-text</code> for red text, not <code>--pen</code>.</b>
  <code>--pen</code> measures 4.27:1 on paper, which fails AA for body-size text. It stays the fill and border
  color (buttons, the &ldquo;You&rdquo; pin, badges); anything set in red type uses <code>--pen-text</code> at
  5.13:1. Caught by auditing this page's own numbers.</p>
  {''.join(out)}
</section>
<section class="sg-sec">
  <h2>Grade badges</h2>
  <p>Semantic and fixed. The letter is always present, so the grade never depends on color being perceived.</p>
  <div class="sg-badges">
    <div class="rc-grade g-a"><span>A</span></div><div class="rc-grade g-b"><span>B</span></div>
    <div class="rc-grade g-c"><span>C</span></div><div class="rc-grade g-f"><span>F</span></div>
  </div>
</section>
"""


def p_typography():
    T = tokens()
    steps = [(k, v[0]) for k, v in T.items() if k.startswith("--step-")]
    specimens = "".join(
        f'<div class="sg-spec"><span class="sg-speclbl"><code>{esc(k)}</code></span>'
        f'<span class="sg-specimen" style="font-size:var({k})">More booked jobs.</span></div>'
        for k, _ in steps)
    fams = [
        ("Zilla Slab", '"Zilla Slab", Georgia, serif', "Display and every heading, plus stat figures and rank "
         "numbers. The slab does the identity work."),
        ("Public Sans", '"Public Sans", system-ui, sans-serif', "Body copy, UI, forms. Deliberately neutral so "
         "the slab keeps the character."),
        ("Caveat", '"Caveat", cursive', "Handwriting, via <code>.hand</code> only. The teacher's margin note. "
         "A garnish, never a heading."),
        ("IBM Plex Mono", '"IBM Plex Mono", monospace', "Data, scores, tabular figures. Earns its place on "
         "numbers; it is not a decorative label font."),
    ]
    fam_html = "".join(
        f'<div class="sg-fam"><span class="sg-famname" style="font-family:{f[1]}">{esc(f[0])}</span>'
        f'<p>{f[2]}</p><span class="sg-famspec" style="font-family:{f[1]}">'
        f'ABCDEFGHIJKLM abcdefghijklm 0123456789 $300 #29 of 32</span></div>' for f in fams)
    return f"""
<section class="sg-sec">
  <h2>Four families, one job each</h2>
  <p>Paired on a real contrast axis: slab serif, neutral sans, script, mono. Never two similar sans faces.</p>
  {fam_html}
</section>
<section class="sg-sec">
  <h2>The scale</h2>
  <p>Fluid <code>clamp()</code> from <code>--step--1</code> to <code>--step-5</code>, topping out at 4.6rem.
  Headings get <code>text-wrap: balance</code>, <code>line-height 1.08</code> and
  <code>letter-spacing -0.015em</code>. Body measure is capped at 66 characters.</p>
  {specimens}
</section>
"""


def p_components():
    return """
<section class="sg-sec">
  <h2>Buttons</h2>
  <div class="sg-demo"><a class="btn btn-primary" href="#">Get my free report card</a>
  <a class="btn btn-ghost" href="#">See the live grades &rarr;</a></div>
  <p class="sg-note">Red pen primary, one per view. Gold focus ring. Hover lift is gated behind
  <code>@media (hover: hover)</code> so it never sticks after a tap on a phone.</p>
</section>
<section class="sg-sec">
  <h2>Leaderboard row</h2>
  <ol class="rank-list sg-demo-list">
    <li class="rr top" style="--sc:94%"><span class="rr-n">1</span><span class="rr-grade g-a">A</span>
      <span class="rr-main"><span class="rr-name">Example Plumbing Co.</span>
      <span class="rr-meta">&#9733; 4.9 &middot; 412 reviews &middot; Livingston</span></span>
      <span class="rr-score">94</span></li>
    <li class="rr is-you" style="--sc:48%"><span class="rr-n">29</span><span class="rr-grade g-c">C</span>
      <span class="rr-main"><span class="rr-name">Your Shop</span>
      <span class="rr-meta">&#9733; 4.6 &middot; 11 reviews &middot; Onalaska</span></span>
      <span class="rr-score">48</span></li>
  </ol>
  <p class="sg-note">Top three take the gold border. The visitor's own row takes the red border and the
  &ldquo;You&rdquo; pin, driven by <code>?you=&lt;slug&gt;</code>. The faint fill behind each row is the score.</p>
</section>
<section class="sg-sec">
  <h2>Report-card dashboard</h2>
  <div class="dash is-in sg-demo-dash">
    <div class="dash-head"><div class="rc-grade g-c"><span>C</span></div>
      <div class="dash-id"><p class="rc-when">Your grade &middot; Onalaska</p><h3>Your Shop</h3>
      <span class="dash-rank">#29 of 32 plumbers around the lake</span></div></div>
    <p class="dash-lbl">Work with us &mdash; here's what changes</p>
    <div class="dash-tiles">
      <div class="dt"><span class="dt-big">1/100<sup>th</sup></span>
        <span class="dt-vs"><b>$300</b><i>vs</i><s>$30,000</s></span>
        <span class="dt-sub">the cost of a serious online presence</span></div>
      <div class="dt"><span class="dt-big">16&times; faster</span><span class="dt-chip">Build in 3 days</span>
        <span class="dt-sub">to build, update and get you seen</span></div>
    </div>
  </div>
  <p class="sg-note sg-warn"><b>Known debt.</b> This screen is the conversion surface and currently reads as a
  generic card dashboard rather than a graded document. Slated for a rebuild against the report-card metaphor:
  ruled rows, a stamped grade, margin annotations. Do not copy this layout into new work.</p>
</section>
<section class="sg-sec">
  <h2>Form fields</h2>
  <div class="diag-step sg-demo"><input type="text" placeholder="Your business name or website"></div>
  <p class="sg-note">16px minimum on inputs, always &mdash; anything smaller triggers zoom-on-focus in iOS Safari.
  Focus is a board-green ring, never a removed outline.</p>
</section>
"""


def p_motion():
    return """
<section class="sg-sec">
  <h2>Easing</h2>
  <p>Two tokens. The built-in <code>ease</code> is too weak for deliberate motion, and <code>ease-in</code> on UI
  is banned outright because it delays the exact moment someone is watching.</p>
  <div class="sg-ease">
    <div><code>--ease-out</code><span>cubic-bezier(.22, 1, .36, 1)</span><p>Movement: transforms, reveals, lifts.</p>
      <div class="sg-ball" style="--e:var(--ease-out)"></div></div>
    <div><code>--ease-out-soft</code><span>cubic-bezier(.33, 1, .68, 1)</span><p>Opacity and color.</p>
      <div class="sg-ball" style="--e:var(--ease-out-soft)"></div></div>
  </div>
  <p class="sg-note">Hover a swatch to run it.</p>
</section>
<section class="sg-sec">
  <h2>Duration budget</h2>
  <div class="sg-tablewrap"><table>
    <thead><tr><th>What</th><th>Duration</th><th>Why</th></tr></thead>
    <tbody>
      <tr><td>Hover, focus, small state</td><td>180&ndash;200ms</td><td>Feels instant, still reads as motion.</td></tr>
      <tr><td>Overlays, mobile nav</td><td>~280ms</td><td>Enough to track a larger surface arriving.</td></tr>
      <tr><td>Dashboard reveal</td><td>320ms</td><td>Staggered 90&ndash;130ms between siblings.</td></tr>
      <tr><td>Scroll reveal</td><td>420ms</td><td>Deliberate exception. Once per visit.</td></tr>
      <tr><td>Report-card count-up</td><td>950ms</td><td>Deliberate exception. The duration is the point:
        the number has to be readable while it climbs.</td></tr>
    </tbody>
  </table></div>
  <p class="sg-note">Under 300ms is the rule. The two exceptions above are once-per-visit reveals, argued
  individually. A third exception needs the same argument.</p>
</section>
<section class="sg-sec">
  <h2>Non-negotiable</h2>
  <ul class="sg-list">
    <li><b>Reduced motion.</b> Every animation needs a <code>prefers-reduced-motion</code> path. Not decoration.</li>
    <li><b>Hover gating.</b> All hover motion sits behind <code>@media (hover: hover) and (pointer: fine)</code>.
      Ungated, a hover state sticks after a tap, and most of our traffic is a phone.</li>
    <li><b>GPU only.</b> Animate <code>transform</code> and <code>opacity</code>. Animating width, height, padding
      or margin causes layout thrash.</li>
    <li><b>Never gate content on a transition.</b> Transitions pause in background tabs and headless renderers.
      Content is visible by default; motion is additive, with a <code>setTimeout</code> finaliser behind it.</li>
    <li><b>One orchestrated moment beats scattered ones.</b> Fading in every section identically is a reflex,
      not a design.</li>
  </ul>
</section>
"""


BUILDERS = {"": p_index, "voice": p_voice, "directives": p_directives, "color": p_color,
            "typography": p_typography, "components": p_components, "motion": p_motion}


def main():
    n = 0
    for slug, title, desc in PAGES:
        d = os.path.join(OUT, slug) if slug else OUT
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page(slug, title, desc, BUILDERS[slug]()))
        n += 1
    print(f"wrote {n} style-guide pages to /style-guide/")


if __name__ == "__main__":
    main()
