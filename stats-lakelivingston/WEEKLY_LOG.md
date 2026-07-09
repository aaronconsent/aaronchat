# Weekly log

Reverse-chronological. Each entry names what changed, why, and what's queued
for next week.

## 2026-07-09 · Week 2 — the scorecard release

**What landed**
- **Per-business scorecards** (`/biz/<slug>/`) — 1,887 pages, one per business.
  Score dial + band, factor-by-factor breakdown (✓/✗ with points earned/max),
  top-3 fixes ranked by point gain with playbook copy, "where you rank" table
  (local rank, local median reviews, top-3 median), correction email + one-line
  Hey Aaron CTA. Print-friendly.
- **Find-your-business search** — global search on the home page (fetches
  `/search-index.json`, ~1,900 entries), plus a per-trade roster filter box.
- **The Playbook** — auto-generated per trade from live stats: claim rate,
  website gap, review medians, photo counts. "Here's the data → here's the move."
- **Methodology page** (`/methodology/`) — the six factors, weights, bands,
  data source, local-vs-regional rules. Trust anchor.
- **Roster hygiene** — `data/exclusions.yaml` category/name rules dropped 262
  junk rows (hardware stores, gas stations, rest areas, car washes, parks) that
  Google's category graph had surfaced as "plumbers"/"tree service"/etc.
- Home page rewritten owner-first: "How does your business stack up?"
- Repo hygiene: `docs/` no longer committed — the Pages workflow builds it.

**What's queued for next week**
- Re-run discovery for fresh review counts (weekly cadence).
- Curate remaining category edge cases (septic cos ranking in plumber medals).
- Consider: percentile bars on scorecards; town-level pages (e.g. /onalaska/).

## 2026-07-06 · Week 1 — scaffold ships

**What landed**
- Site skeleton: home + trade-page template + methodology (v0.1.0).
- Three trades stubbed: plumbers (8 template rows, insights written),
  HVAC + electricians (placeholders).
- CSS design system: cream ground, forest-green winning band, IBM Plex Mono
  tabular numerics, medal cards for the leaderboard.
- Social quotables JSON feed at `/social-quotables.json`.
- Deploy: `docs/` folder committed, GitHub Actions rebuilds on data changes.

**What's queued for next week**
- Verify all 8 plumber template rows against Google Business Profile.
  Rewrite the "#1 bar" once verified data is in.
- Add 5-10 real HVAC shops (Livingston, Onalaska, Willis).
- Add 3 new insights per verified trade — one gap, one opportunity, one quirk.

**Why we shipped without real plumber data**
Web-search was unavailable during scaffolding. Rows are marked
`research_status: template` so they render in an internal "gaps" section
only — nothing false is public. First real research pass turns eight
template rows into verified companies.
