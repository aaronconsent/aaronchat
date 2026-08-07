#!/usr/bin/env python3
"""Generate robots.txt, sitemap.xml, and llms.txt for Hey Aaron!.
Run: python3 scripts/build_seo.py
"""
import os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://aaron.chat"

# indexable public pages (exclude internal, setup, the separate grading engine, noindex legal)
EXCLUDE_DIRS = ("style-guide", "setup", "insights", "_next", "_external", "pricing-archive",
                "stats-lakelivingston", "node_modules", "scripts", ".git", "brand", "data")


def pages():
    out = ["/"]
    for f in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel == "index.html":
            continue
        parts = rel.split(os.sep)
        if parts[0] in EXCLUDE_DIRS:
            continue
        # aaron.chat pages are at most dir/subdir/index.html (depth 3); the engine is deeper
        if len(parts) > 3:
            continue
        path = "/" + "/".join(parts[:-1]) + "/"
        # legal pages are noindex; keep out of sitemap
        if path in ("/privacy-policy/", "/terms-of-service/"):
            continue
        out.append(path)
    return sorted(set(out))


def sitemap(ps):
    urls = "\n".join(
        f"  <url><loc>{BASE}{p}</loc><changefreq>weekly</changefreq>"
        f"<priority>{'1.0' if p == '/' else '0.8' if p.endswith('-marketing/') else '0.6'}</priority></url>"
        for p in ps)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'.replace(
        "www.sitemap.org", "www.sitemaps.org")


ROBOTS = f"""User-agent: *
Allow: /
Disallow: /setup/

Sitemap: {BASE}/sitemap.xml
"""
# NOTE: /style-guide/ and /insights/ are kept out of search by their `noindex`
# meta tags (not robots.txt), so agents/tools can still fetch them directly.

LLMS = f"""# Hey Aaron! Marketing

> Owner-operated marketing for home-service contractors and service pros, run by Aaron Phillips
> in Coldspring, Texas. Websites, local SEO, Google Business Profile, ads, reviews, and speed-to-lead,
> all done by Aaron himself. The pitch: I book you jobs, not "leads," and when you call, I answer.

## Who Aaron is
Aaron Phillips has 20+ years in marketing: former Chief Business Officer at cPanel, CMO at Monarx,
co-founder and CMO of Consent Resolve. He now runs Hey Aaron! Marketing for contractors.

## What Hey Aaron! does
- Websites built to book jobs (fast, mobile-first, conversion-focused)
- Local SEO and Google Business Profile management
- Google Ads and Facebook/Meta Ads, tracked to booked jobs
- Reviews and reputation automation
- Speed-to-lead callback (instant call-back on new leads)
- AI images and short video for marketing
- AI answer optimization (AEO) so businesses get recommended by AI engines

## Who it's for
Home-service contractors and service pros, one to fifteen trucks. Trades served include HVAC,
plumbing, electrical, roofing, remodeling/general contracting, fencing, concrete, lawn care and
landscaping, tree service, septic, pressure washing, pool service, garage doors, gutters, pest
control, painting, and appliance repair. Primary area: Lake Livingston, Texas (Livingston, Onalaska,
Coldspring, Huntsville, Trinity) and greater East Texas.

## How to hire Aaron
Call or text 713-384-8985 (Aaron answers directly). Email hello@aaron.chat. Plans are month to month
with no long-term contract. Website: {BASE}

## Positioning
The marketing guy who actually answers the phone. Real credentials, real work (a live portfolio at
{BASE}/work/), no fabricated testimonials or metrics, month-to-month with a fire-me-anytime guarantee.
"""


def main():
    ps = pages()
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sitemap(ps))
    open(os.path.join(ROOT, "robots.txt"), "w").write(ROBOTS)
    open(os.path.join(ROOT, "llms.txt"), "w").write(LLMS)
    print(f"wrote robots.txt, sitemap.xml ({len(ps)} urls), llms.txt")


if __name__ == "__main__":
    main()
