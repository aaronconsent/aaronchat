# stats.lakelivingston.aaron.chat

Weekly-updated competitive research on service businesses working around Lake
Livingston, Texas. Published by Hey Aaron! Marketing to serve as (a) a real
resource contractors bookmark and (b) an authority signal for aaron.chat's
entity graph.

## Structure

    data/
      site.yaml               site config + trade order
      methodology.yaml        how presence-score is computed
      trades/<key>.yaml       one file per trade (companies, insights, #1 bar)
    scripts/
      build.py                YAML → HTML (writes docs/)
    templates/
      base.html               shared layout
    assets/
      style.css               diner-adjacent, data-forward styling
    docs/                     ← GitHub Pages serves this folder

## Build locally

    python3 scripts/build.py

## Deploy

GitHub Pages, custom domain `stats.lakelivingston.aaron.chat`. Two setup steps
you own on first deploy:

1. **DNS**: point `stats.lakelivingston.aaron.chat` at `<username>.github.io`
   via a Cloudflare CNAME (proxy OFF while GitHub is issuing the cert).
2. **Repo settings**: Settings → Pages → Source = "Deploy from a branch",
   Branch = `main`, Folder = `/docs`. The `docs/CNAME` file is regenerated on
   every build from `data/site.yaml`.

The `.github/workflows/build-stats.yml` workflow auto-rebuilds `docs/` on push
to any `data/**` or `scripts/build.py` file, and commits the regenerated HTML
back to `main` so Pages picks it up.

## Weekly editing loop

Every Monday:

1. Open `data/trades/<current-trade>.yaml`.
2. Look up each `research_status: template` row on Google Business Profile.
   Fill in `website`, `reviews_count`, `avg_rating`, `last_review_iso`,
   `summary`, flip `research_status: verified`.
3. Rewrite `number_one_bar` if the top-3 median moved.
4. Update `insights[]` with 1-3 new findings for the week. Set
   `social_ready: true` on the ones we want aaron.chat's Mastodon/Bluesky/X
   feeds to quote.
5. `python3 scripts/build.py` locally to preview, then commit.
6. Log what changed in `WEEKLY_LOG.md`.

## What aaron.chat pulls from this

`docs/social-quotables.json` is a machine-readable feed of every insight
tagged `social_ready: true`. The aaron.chat social pipeline reads it and
generates credibility-mode posts linking back to the trade page — closes the
loop between "we do the research" and "the research shows up in feeds".
