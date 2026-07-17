# Facebook Ads plan — Top of Class Marketing (2026-07)

The site is ads-ready: Meta Pixel base code is on every page (activate by replacing
`PASTE_PIXEL_ID` in each page head — or give Claude the Pixel ID and it's a one-commit
swap), lead forms fire `fbq('track','Lead')` on success, and the two trade landing
pages exist as dedicated ad destinations with no nav exits.

## Campaign structure (start at $20-30/day total)

**Campaign 1 · Lead — HVAC** → aaron.chat/hvac-marketing/
- Audience: 25-mi radius around Livingston + Huntsville, interests HVAC/small-biz
  OR just broad 35-60 (Meta's targeting finds owners; the creative self-selects)
- Creative angle A (the grade): "We graded all 48 HVAC companies around Lake
  Livingston. Yours included. See your grade free — no signup."
- Creative angle B (the gap): "The #3 HVAC shop in Polk County has 484 reviews.
  The median has 20. That gap is the whole game — here's yours."

**Campaign 2 · Lead — Plumbing** → aaron.chat/plumber-marketing/
- Angle A: "44% of Lake Livingston plumbers have no website. Homeowners skip them.
  We graded all 66 shops — look yours up free."
- Angle B (rank callout): "Where does your shop rank out of 66? We already know.
  Free report card, 30 seconds."

**Campaign 3 · Retargeting** (once pixel has 30+ days of traffic)
- Audience: visited /report-card/ or a landing page, didn't submit
- Creative: founding-five offer ("half rate, six months, five shops, honest reason —
  we need local case studies. Three seats left.")

## Creative production notes

- The report-card visual IS the creative: screenshot real (anonymized or permission'd)
  scorecards from stats.lakelivingston.aaron.chat — the C- card with the red F rows
  stops thumbs. Print-styled cards photographed on a work bench beat digital mockups.
- Video: 15-sec screen-record of typing a business name into the search and the grade
  appearing. Native, low-fi, no music needed.
- Every ad promises the FREE card, never the retainer. The retainer is sold in the
  walkthrough, not the ad.

## Measurement

- `?src=` UTM params per campaign (e.g. /hvac-marketing/?src=fb-grade-a)
- Lead event = form submit; also track tel: clicks later if volume warrants
- Kill rule: any ad set > $40 spend with zero Leads gets paused; budget shifts to winner
- The real KPI is walkthroughs booked, not Leads — track in a simple sheet until CRM

## Sequencing

1. Aaron creates/confirms Pixel in Meta Business Manager → hand ID to Claude → live in one commit
2. Launch Campaigns 1+2 at $10-15/day each, 2 creatives per campaign
3. Week 2: kill losers, double winners, add retargeting when audience > 200
4. First close funds everything else — a single $750/mo client = ~2 months of ad budget
