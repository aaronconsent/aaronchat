# Design

The Hey Aaron! visual system, in `brand/ha.css` (v1, ported from the Google Stitch "Contractor Elite"
system into clean CSS for speed). This is a conformance reference — the identity is set; treat deviations
as bugs. The old chalkboard/report-card system (`brand/style.css`) is retired.

## Theme

Corporate-modern with a performance edge. "Blue-collar professionalism": deep institutional navy, a
numbers-first hierarchy, clean structure, results-oriented. Light surfaces, one dark trust strip, a subtle
grid texture on the hero for precision. Not warm, not playful-cute; confident and legible.

## Color (exact tokens in `ha.css`)

| Token | Value | Role |
|---|---|---|
| `--primary` | `#002f62` | deepest navy (button hover, gradients) |
| `--primary-container` | `#074588` | header, primary buttons, the brand navy |
| `--primary-tint` | `#e7eefb` | pale navy wash behind card icons |
| `--tertiary` | `#7a4a12` | burnt orange for text/links (darkened to AA) |
| `--tertiary-bright` | `#b4610c` | accent fills, focus ring |
| `--surface` / `--surface-low` | `#f9f9fe` / `#f3f3f9` | page bg / alt-section bg |
| `--white` | `#ffffff` | cards |
| `--dark` | `#23252b` | trust strip + footer |
| `--ink` / `--ink-variant` | `#16181c` / `#3b414b` | body / secondary text (AA) |
| `--good` | `#1f6b23` | checks, success |
| `--danger` | `#ba1a1a` | errors |

Strategy: **committed** — navy carries the header, footer, CTAs, and dark bands; burnt-orange is a rare
accent (links, focus, tier labels). All text pairings verified ≥ AA; CTA/link colors darkened from the raw
Stitch values so they pass.

## Typography

**Inter only** (400/500/600/700), the Stitch choice — utilitarian, legible for data. Headings 700, tight
`letter-spacing: -0.02em`, `text-wrap: balance`. Fluid scale: `--d-xl` hero, `--d-lg` section heads,
`--h-md` card/sub heads, `--body-lg` lede, `--body` copy, `--caps` uppercase labels. Loaded via one Google
Fonts request with a system-ui fallback (self-host one woff2 later for the strict speed budget).

## The logo

`.ha-logo` — the Hey Aaron! wordmark as a static inline SVG (viewBox `0 -6 749 140`, `fill: currentColor`,
aspect ~5.35:1). White in the navy header/footer. It's the supplied hand-built letterform geometry, pixel-
identical; do not substitute a font.

## Layout

Container `--max: 1200px`, fluid `--gut` gutter, `.sec` sections at `clamp(52px, 8vw, 96px)` vertical
rhythm. `.split` for two-column media/text. Corporate soft radii: buttons 4px, cards 8–16px, pills full.
Tonal layering (surface vs white cards) + targeted shadows `--sh-sm/md/lg`; cards lift `-3px` on hover.

## Components

- **Buttons**: `.btn-call` (navy fill, phone icon, lift+glow), `.btn-ghost` (orange outline), `.btn-white`
  (on navy), `.btn-lg`. One dominant CTA per viewport.
- **Header**: sticky navy, wordmark left, nav, white call pill; mobile toggle → full-screen menu.
- **Cards** `.card`: 4px top-border accent (navy on hover), circular tinted icon, used for services.
- **Trust strip** `.trust`: dark band of real credentials (no fake logos).
- **Tiers** `.tier`: pricing cards, `.pop` highlights one; check-list features.
- **FAQ** `.faq`: native `<details>`, orange chevron.
- **Conversion UI**: `.callbar` (sticky mobile call/text, shows after 200px), `.floatcall` (desktop),
  `.cbw` callback widget (navy gradient), `.quiz` 3-tap stepper, `.ha-modal` exit-intent.
- **Icons**: inline SVG symbol sprite (`#i-phone`, `#i-check`, …) — no icon font.
- **Image slots** `.imgslot`: honest hatched placeholders; founder shots are real Aaron staged with AI
  (see `.docs/heyaaron-image-prompts.md`), never stock.

## Motion

`.reveal` scroll-reveal, gated behind `html.js` with a `setTimeout` failsafe so nothing ships hidden.
`prefers-reduced-motion` honored throughout. Hover lifts on cards/buttons. Exit-intent is desktop-only,
true mouseleave-at-top, once per session. Easing `--ease` (`cubic-bezier(.22,1,.36,1)`); keep UI motion
under ~300ms except once-per-visit reveals.

## Conversion + tracking (behavioral, in `ha.js`)

Call-first everywhere; DTR message-match via `?trade=/?city=/?region=` (sanitized textContent, runs before
analytics); tracking spine captures gclid/fbclid/utm to sessionStorage and attaches to lead payloads; every
CTA carries `data-cta-location`. Quiz + callback → `/api/lead`. Staffed-hours availability line.

## Assets & caching

`ha.css` / `ha.js` version-stamped `?v=N` (currently 100). Bump on any change. The old `style.css` system
is retired but still present for the internal `/style-guide/` pages only.
