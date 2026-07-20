# Design

Captured from the existing system in `brand/style.css` (v2, July 2026). This documents what is already built and shipping — it is a conformance reference, not a proposal. The identity is locked; treat deviations as bugs unless Aaron says otherwise.

## Theme

Light, warm, paper-based. The organizing metaphor is a graded report card on a teacher's desk: worksheet paper, chalkboard green, red pen, gold star. It is deliberately *not* a dark "AI tool" theme and not an agency white-and-gradient theme — the surface should read as a physical document that has been marked up by a person.

The metaphor must stay sharp and adult. Chalkboard and red pen are the vocabulary; cartoon apples and crayon fonts are not.

## Color

Hex values as committed (not OKLCH — the system predates that convention and is not being migrated).

| Token | Value | Role |
|---|---|---|
| `--board` | `#1e3d31` | Chalkboard green. Primary brand color: header, footer, dark panels, headings. |
| `--board-2` | `#163026` | Deeper board, for layered dark surfaces. |
| `--board-tint` | `#2c5142` | Elevated / hover state on green. |
| `--paper` | `#f5f3ec` | Worksheet paper. Body background and card fill. |
| `--paper-2` | `#efece1` | Slightly deeper paper for adjacent surfaces. |
| `--white` | `#fdfdfb` | Raised card surface. Never pure `#fff`. |
| `--ink` | `#1c2321` | Warm off-black body text. Never pure `#000`. |
| `--pen` | `#d23c2e` | Red pen. Primary CTA, links, corrections, "you" markers. |
| `--pen-dark` | `#bd3427` | Pressed / hover red. |
| `--star` | `#e0b100` | Gold star. Highlights, top-3 medals, the "you" banner. |
| `--gold` | `#d9a441` | Softer gold for accents and focus rings. |
| `--chalk` / `--chalk-dim` | `#e8ede9` / `#b9c6bd` | Text on the board. |
| `--slate` | `#5d6a63` | Muted secondary text. |
| `--line` / `--line-2` | `#d8d4c6` / `rgba(30,61,49,.10)` | Ruled line on paper; hairline on cream. |
| `--pass` | `#2c7a4b` | Passing green — grade badges, "at an A" goals, checkmarks. |

**Strategy: committed.** Chalkboard green carries large surfaces (header, footer, dark CTA panels); red pen is the single action color and stays under ~10% of any view; gold is punctuation only.

Grade badge semantics: A `--pass`, B `#4a8a5f`, C `--star` (with `--board` text for contrast), D/F `--pen`. **The letter is always present** — color never carries the grade alone.

## Typography

Four families, each with one job. Loaded from Google Fonts.

- **Zilla Slab** (300–700) — display and all headings, plus numeric figures in stat tiles and rank numbers. The slab is the report-card voice; it does the identity work.
- **Public Sans** (400–700) — body copy, UI, forms. Neutral by design so the slab stays the character.
- **Caveat** (600–700) — handwriting, used only via `.hand` for the teacher's-margin-note effect. Sparingly; it is a garnish, never a heading.
- **IBM Plex Mono** (500–600) — data, scores, eyebrow labels, tabular figures.

Pairing is on a genuine contrast axis (slab serif + neutral sans + script + mono), not two similar sans faces.

Fluid scale `--step--1` → `--step-5` (clamp-based, ~1.2 → 1.333 ratio), topping out at 4.6rem — under the 6rem display ceiling. Headings: `line-height 1.08`, `letter-spacing -0.015em` (well inside the -0.04em floor), `text-wrap: balance`. Measure capped at `--measure: 66ch`.

## Layout

- Container `--container: 1120px`. The diagnose hero narrows to 1050px.
- Fluid spacing scale `--sp-3xs` → `--sp-3xl`, clamp-based from `--sp-m` up.
- Radii: `--r-sm` 8px, `--r` 12px, `--r-lg` 16px, `--r-xl` 22px.
- Shadows `--sh-1` / `--sh-2` / `--sh-lift` are all tinted with the board green rather than neutral black. `--sh-paper` (`4px 4px 0 var(--line)`) is the flat offset "stacked paper" shadow used on document-like cards.
- Alternating `.band` / `.band.flip` sections for long pages; `.bento` for the persona grid; `.tiers` for pricing.

## Components

Established and in use — reuse before inventing:

- `.btn` / `.btn-primary` — red pen primary, gold `:focus-visible` ring.
- `.rc-grade` + `.g-a` / `.g-b` / `.g-c` / `.g-f` — the grade badge, used on the dashboard, leaderboard rows and mini-cards.
- `.dash` — the report-card outcome dashboard: `.dash-head`, `.dash-rank`, `.dash-tiles` / `.dt` (stat tiles), `.dash-feats` / `.df` (plan features).
- `.rank-list` / `.rr` — the trade leaderboard row, with `.rr.top` (gold, top 3) and `.rr.is-you` (red border + "You" pin).
- `.mini-card`, `.diag` wizard steps, `.lead-form`, `.faq`, `.stat-row`, `.era-card`.
- Sticky condensing header `.site-head.is-stuck`; mobile `.mbar` call bar and `.m-nav` overlay, both built by `brand/nav.js`.

## Motion

Progressive-enhancement contract: reveal classes are gated behind `html.js`, so a no-JS or headless render always shows content. `nav.js` carries a rAF + 1.5s failsafe; the dashboard reveal is finalized by `setTimeout` so a backgrounded tab (where rAF is throttled to zero) can never leave content invisible.

`prefers-reduced-motion: reduce` is honored throughout and is not optional.

**Easing tokens.** `--ease-out: cubic-bezier(.22, 1, .36, 1)` for movement and `--ease-out-soft: cubic-bezier(.33, 1, .68, 1)` for opacity. Never use the built-in `ease` / `ease-in-out` on deliberate motion — they're too weak, and `ease-in` on UI is banned outright (it delays the moment the user watches most).

**Duration budget.** UI transitions stay under 300ms. Hovers 180–200ms, overlays ~280ms, the dashboard reveal 320ms. The scroll reveal (420ms) and the report-card count-up (950ms) are the two deliberate exceptions: both are once-per-visit reveals where the duration is the point, not latency.

**Hover motion is gated** behind `@media (hover: hover) and (pointer: fine)` — ungated, hover states stick after a tap on touch devices, which matters here because most traffic is a contractor on a phone.

**Group entrances stagger** (80–130ms between siblings) rather than firing as one block.

## Assets & caching

Every `/brand/*.css` and `/brand/*.js` reference is version-stamped `?v=N` sitewide. **Bump `N` in all HTML plus both Python generators (`scripts/build_services.py`, `scripts/build_portfolio.py`, `scripts/build_rankings.py`) on any CSS/JS change**, or edge caches serve stale assets. Currently at `v=23`.
