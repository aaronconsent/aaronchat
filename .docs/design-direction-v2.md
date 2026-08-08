# aaron.chat — Design Direction v2
**A design document to argue with, not a conformance reference.**
Drafted 2026-08-08 · supersedes `DESIGN.md` **only on Aaron's approval** · no code written yet

---

## 0. What this is, and why it exists

`DESIGN.md` today opens with: *"This is a conformance reference — the identity is set; treat deviations as bugs."* And `ha.css` opens with: *"Ported from the Google Stitch 'Contractor Elite' system… Visual system preserved exactly."*

That is the whole diagnosis. **The identity was never designed — it was generated, ported, and frozen**, and every request since has been "add to it in its own language." This document does the job that never got done: it makes the hard visual decisions explicitly, argues for them, and turns them into rules a build can be checked against.

Nothing here ships until Aaron signs off. Argue with §3, §4, and §5 first — everything downstream depends on them.

---

## 1. The diagnosis (verified, not asserted)

I looked at the category rather than assuming it.

| Site | What it looks like |
|---|---|
| **Scorpion** (home services) | Corporate blue + white, sans throughout, six-item icon/thumbnail service grid, partner logo bar, testimonial carousel, minimal radius |
| **Hook Agency** (contractor marketing) | Near-white + acid neon-green accent, geometric sans, 4-column icon feature cards, 4-column client logo bar, stat counters ("$240M+", "200+"), numbered process cards |
| **aaron.chat today** | Navy `#074588` + burnt orange, **Inter**, 3–4 icon-card service grid, centered section heads, uniformly rounded white cards on tinted bands |

aaron.chat is sitting squarely in the Scorpion lane. It is the **first-order category reflex**: if you asked anyone to guess what a contractor-marketing site looks like, they'd describe our current homepage.

Worse, our own Brass & Pine spec — written for a different client — bans, by name, the things this site is built from: Inter as a default tell, three-column icon-card grids, centered-everything, uniform border-radius.

**What the site does get right and must keep:** no fake testimonials, no invented metrics, no fake partner badges, real Aaron photos only. That integrity lock is the brand's actual asset and nothing here weakens it.

---

## 2. Who this is for (unchanged, restated)

Mike. One to fifteen trucks, East Texas, 17 trades. On his phone, between jobs, dirty hands, four minutes. He has been sold to badly before and he verifies the way his customers verify him: he looks you up and checks whether you're real.

The design's job is not to impress Mike. It's to **read as true at a glance**, and to survive the ten seconds where he decides whether this is another agency front.

---

## 3. The concept — "Evidence, not advertising"

> The site should look like a **record of work that happened**, not an ad for work that might.

Everything true about this brand points one direction: live sites, real numbers, go check. Receipts. Month-to-month, fire me. Published prices. No fake proof. The visual system should encode that — the design equivalent of a straight answer. Think **field report, work order, inspection ticket, ledger** — documents whose entire job is to be *verifiable*.

Concretely that means: paper and ink rather than tinted-navy brochure; hairline rules rather than floating cards; **numbers set in mono because monospaced figures read as counted, not claimed**; left-aligned document hierarchy rather than centered marketing symmetry; one stamped signal color used like a mark of approval.

### What I considered and rejected (argue here if you disagree)

- **(A) Keep corporate navy, just execute it better.** Rejected — it *is* the category default, now verified against Scorpion. Better execution of the reflex is still the reflex.
- **(B) Rugged workwear** — Carhartt brown, hazard yellow, condensed caps, caution-tape, distressed textures. Rejected on three grounds: it's the obvious *second-order* reflex (the thing you pick when avoiding corporate); it's cosplay — Aaron is a marketer, not a tradesman, and wearing the customer's uniform reads as pandering to the exact guy who's allergic to being handled; and **Booked Job already owns that lane** in the portfolio (orange/yellow/asphalt, Anton, caution tape). Two brands, one costume, is a problem.
- **(C) Acid-accent minimal** — Hook Agency's neon-on-white. Rejected: it's the saturated startup/AI default, and it reads *agency-cool*, which is precisely the signal Mike distrusts.

---

## 4. Color — "Ink & Iron" (the decision to argue with)

A paper ground, a true ink, one stamped signal color, one deep field for dark bands. **No navy anywhere.**

| Token | Value | Role |
|---|---|---|
| `--paper` | `#F2F2EF` | page ground — a real off-white, very slightly *cool/neutral*, deliberately **not** warm cream |
| `--paper-raised` | `#FAFAF8` | raised surfaces (what cards become) |
| `--ink` | `#15171A` | body text, headlines — near-black, faintly cool |
| `--ink-soft` | `#484D55` | secondary text, captions |
| `--rule` | `#D2D2CC` | hairline rules — the primary structural device |
| `--iron` | `#A63A1E` | **the signal color.** Iron-oxide red: a stamp, a red pen, a surveyor's mark, East Texas clay |
| `--iron-deep` | `#8A2E16` | small-text/AA-critical variant |
| `--field` | `#1E2A24` | deep pine-slate — dark bands, footer |
| `--verified` | `#1F6B23` | reserved, semantic only: verified/live/true (already in use, keep) |
| `--alert` | `#B4231C` | reserved, semantic only: errors |

**Usage laws**
- **Iron is precious.** Primary CTAs, one accent per fold, active states, key numbers, rules that matter. Target **≤8% of any viewport**. Never as a large fill, never as a gradient.
- **Paper dominates.** Long-form and most sections sit on `--paper`. `--field` is for punctuation — one or two bands per page, max.
- **Rules, not shadows.** Hairline `--rule` is how structure gets expressed. Shadows shrink to near-nothing (one soft lift on genuinely interactive cards).
- **Green stays semantic.** `--verified` never becomes decorative; it means *this is confirmed true*. That's the honesty machinery from the Real Work hub and the dashboard, and it only works if it's never used for flavor.

**The one real tradeoff, flagged:** iron-red is adjacent to error-red. That's why `--alert` is a distinctly different, cooler red and errors also carry an icon + label, never color alone. If you'd rather not spend the identity on red at all, the credible alternate is **"Ink & Pine"** — same structure, `--field` green promoted to the accent. Safer, more regional, less alarm-adjacent; also less distinctive, and closer to Brass & Pine's territory.

**Contrast (WCAG 2.2 AA — to be verified numerically at build, not eyeballed):** ink-on-paper is the workhorse pair and clears AAA comfortably. `--iron` on paper is intended for large text/UI and CTA fills with white labels; `--iron-deep` is the small-text variant. Every pair gets computed and published on the style guide.

---

## 5. Typography — three voices

Inter is out. It's the #1 default tell, it's what the Stitch mockup handed us, and it's carrying every single word on the site today.

| Role | Face | Why |
|---|---|---|
| **Display** — headlines | **Newsreader** *(variable, Google Fonts, OFL)* | A newspaper serif. Newspapers are the cultural shorthand for *"this is a record of what happened"* — the concept in one typeface. Sturdy and readable, not fashion-serif. **Verify variable axes + weights at build.** |
| **Body / UI** | **Public Sans** *(variable, Google Fonts, OFL, based on Libre Franklin)* | The **U.S. Web Design System** typeface — literally engineered for public records and government documents. Plainspoken, neutral, institutional-honest. Not a default tell. *Caveat: the USWDS repo notes it is no longer actively maintained; it's a stable OFL release, which is fine, but worth knowing.* |
| **Numbers / meta** | a **mono** with tabular figures (JetBrains Mono or Geist Mono — pick at build) | Prices, stats, phone numbers, dates, months, the `01/02/03` markers. **Monospaced numerals are the single strongest "counted, not claimed" signal available.** This is the receipts move. |

Serif display + sans body + mono numerals is a real three-axis contrast system, not two grotesques pretending to be different.

**Scale (fluid, clamp-based; final values set at build):** display XL for hero, a clear step down to section heads (the current site's `--d-lg`/`--sec-h` gap is roughly right and can carry over), body at 16–17px minimum — Mike is 40+ and outdoors, this is non-negotiable — measure capped at 65–70ch, headlines 14–22ch.

**Laws:** headlines tight-tracked and **left-aligned**; mono for every figure, always with `font-variant-numeric: tabular-nums`; uppercase labels get real letterspacing; one display face used with intent.

---

## 6. Layout laws

1. **Left-aligned by default.** Centered section heads are **banned** except the single final CTA per page. Centered everything is what makes the current site read brochure instead of document.
2. **Asymmetry quota: ≥50% of sections** break symmetry — 2+1 grids, one oversized item, off-grid pull images, margin captions.
3. **Rhythm variety per page:** at least one full-bleed edge-to-edge section, one deliberately short section, one off-grid moment. *Variety in vertical rhythm is most of why custom sites feel custom.*
4. **Radius discipline: near-square.** 2–4px on cards and inputs, one documented exception (the call CTA stays pill — it's a phone button and roundness reads tappable). No uniform 12–16px rounding.
5. **Rules over shadows.** Hairlines carry structure. Shadow budget: one subtle lift, on interactive cards only.
6. **Icon-card grids are banned** (see §8). Services get an editorial treatment — a numbered list, a 2+1 layout, or typographic rows.
7. Mobile keeps the sticky call bar in the thumb zone. Tap targets ≥44px. That part already works; don't regress it.

---

## 7. Motion

Named tokens, so nothing ships on default `ease`:

- `--ease-standard: cubic-bezier(0.4, 0, 0.2, 1)` — UI state changes
- `--ease-entrance: cubic-bezier(0.16, 1, 0.3, 1)` — reveals, 0.4–0.6s
- `--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1)` — tactile press/hover
- `--ease-editorial: cubic-bezier(0.39, 0.24, 0.3, 1)` — long image/number reveals

Durations: micro 0.2–0.3s · entrances 0.4–0.6s · editorial 0.6–1.2s.

**Discipline:** *earn every animation.* If it doesn't guide the eye or reward attention, cut it. Every animation needs a `prefers-reduced-motion` alternative. **Reveals must enhance an already-visible default** — never gate content visibility on a class-triggered transition (it silently ships blank sections in headless renderers and hidden tabs; we've hit exactly this bug already).

---

## 8. THE BANNED LIST

The load-bearing section. If I'm about to write one of these, I rewrite the element instead.

**Typography & color**
- ❌ Inter, Roboto, Open Sans, Space Grotesk, Poppins, Montserrat
- ❌ Navy `#002f62` / `#074588` as a brand color, anywhere
- ❌ Gradient text (`background-clip: text`)
- ❌ Any blue→violet / cyan→purple gradient
- ❌ Warm cream/sand/beige body grounds and the token names that come with them (`--cream`, `--sand`, `--bone`, `--parchment`)

**Layout & components**
- ❌ Three- or four-column icon-card grids (icon + heading + paragraph, repeated)
- ❌ Centered section heads (except one final CTA per page)
- ❌ Uniform 12–16px rounding on everything
- ❌ Floating white cards with drop shadows as the default container
- ❌ Colored side-stripe borders (`border-left: 3px solid`) as accent
- ❌ Tiny uppercase tracked eyebrow above *every* section — one deliberate use is voice, on every section it's scaffolding
- ❌ Numbered markers (01/02/03) unless the content genuinely **is** an ordered sequence *(the trade-page playbooks qualify — those stay)*
- ❌ Emoji as section markers or bullets

**Proof & content (existing integrity lock — reaffirmed)**
- ❌ Stock photography of generic contractors; **real Aaron photos only**
- ❌ Fabricated testimonials, invented metrics, fake partner/certification badges, "AS SEEN IN" logo bars
- ❌ Stat counters presenting unverified numbers as fact
- ❌ Live-data chips on anything not actually pulled live *(the `verified` vs `live` distinction from the Real Work hub is now a system-wide rule)*

**Copy**
- ❌ The locked banned lexicon in `brand/voice-guide.md` (unchanged; voice is already locked and this document does not touch it)
- ❌ **The competitor-swap test:** if you can drop a competitor's name into the sentence and it still reads true, rewrite it.

---

## 9. Definition of Done — the build must self-verify

**Distinctiveness**
- [ ] Zero Inter/Roboto/Poppins/Montserrat; Newsreader + Public Sans + mono in use
- [ ] Zero navy; `--iron` present and **≤8% of any viewport**
- [ ] No icon-card grid anywhere; ≥50% of sections asymmetric
- [ ] Every section head left-aligned except one final CTA
- [ ] Near-square radius system with exactly one documented exception
- [ ] Every number set in mono with tabular figures
- [ ] Per page: one full-bleed, one short section, one off-grid moment
- [ ] Custom easing tokens only — no default `ease`
- [ ] Copy passes competitor-swap; zero banned-lexicon hits
- [ ] **Self-critique pass: list 5 things a senior designer would reject, then fix them**

**Technical**
- [ ] Every color pair computed against WCAG 2.2 AA and published on `/style-guide`
- [ ] `prefers-reduced-motion` honored; no content gated behind a reveal transition
- [ ] Fonts self-hosted woff2, subset, preloaded, `font-display: swap`; no CLS
- [ ] LCP < 2.0s, CLS < 0.05, INP < 200ms on mid-range Android
- [ ] Tap targets ≥44px; sticky call bar reachable one-thumb at 375px
- [ ] All 60+ generated pages regenerate clean; no stale `?v=` versions
- [ ] Schema intact; no SEO/link-equity regressions

---

## 10. Migration path (the honest engineering part)

Brass & Pine was greenfield. This is a live site: **60+ pages, all generated by Python from a token-driven stylesheet, with real SEO equity and a Meta pixel.** That's mostly good news — because everything is tokens + generators, a palette and type swap **propagates automatically**. The expensive part is components and composition, not color.

- **Phase 0 — `/style-guide` first.** Rebuild the style guide from the new tokens as the single source of truth. *This is the structural move that prevents drift:* components inherit the system instead of re-deciding it. Nothing else starts until this exists.
- **Phase 1 — Tokens.** Swap palette + type in `ha.css`. Cheap, propagates everywhere, biggest single visual delta. Ends with a full-site contrast + visual audit.
- **Phase 2 — Components.** Kill the icon-card grid, un-center the section heads, rules-over-shadows, radius discipline. Touches every generator; do it generator-by-generator with a regenerate + diff after each.
- **Phase 3 — Composition.** Per-page rhythm: full-bleed moments, asymmetric sections, the off-grid beat. Highest-value pages first (`/`, `/work/`, `/pricing/`, then the 17 trade pages).
- **Rollback:** every phase is one commit and one `?v=` bump; `DESIGN.md` v1 stays in git as the record of what it was.

---

## 11. Open questions — decide these before Phase 0

1. **Red or green?** "Ink & Iron" (iron-oxide red stamp) as recommended, or the safer "Ink & Pine" (green accent)? This is the identity call and it's yours.
2. **How far does this go?** Full re-skin of all 60+ pages, or prove it on `/` + `/work/` first and decide from there? *(My recommendation: prove it on two pages. Cheaper to argue with something real than with this document.)*
3. **Newsreader specifically** — I want a look at it set at hero size in your wordmark's company before committing. The wordmark is hand-built SVG geometry and doesn't change; the display face has to sit next to it without fighting.
4. **Anything here you actively hate?** That's more useful to me than agreement — a rejected direction with a reason is how the next draft gets sharper.

---

## 12. Confidence & risks

**Confidence: 7.5/10** that this produces a genuinely distinctive site that still converts — conditional on Phase 0 happening first and on real photography of Aaron.

**Ranked risks**
1. **Photography.** Same as Brass & Pine's #1 risk. Paper-and-ink with great real photos of Aaron on job sites is excellent; with placeholder or AI imagery it's a nice empty document. This is the highest-leverage non-code investment.
2. **Serif display in a trade category is a real bet.** It could read law-firm rather than field-report if the face or weight is wrong. Mitigation: prove it on two pages before committing 60.
3. **Red-as-brand vs. red-as-error.** Managed by a distinct `--alert` plus icon+label on errors, but it's a genuine constraint to live with.
4. **Conversion regression.** The current site is tuned (one dominant CTA, call-first, sticky bar). None of that changes structurally — but re-skins can quietly hurt conversion. Keep the CTA hierarchy and phone prominence *exactly* as-is through all three phases.
5. **Scope.** Phase 2 touches every generator. Real work, easy to underestimate.

**What would raise confidence to 9:** a real photo shoot of Aaron, and Phase 0 + two proof pages reviewed side-by-side against today's design.
