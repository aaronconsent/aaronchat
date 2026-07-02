#!/usr/bin/env python3
"""PageAdapter — the ContentSource for aaron.chat.

Reads static HTML pages under site/ and turns each into N social post variants
for each enabled platform. Runs OFFLINE via build_queue.py; the runtime just
reads the resulting queue.json.

Per engine-build-spec.md Part C: 'PageAdapter is real work — the one genuinely
new piece' when porting the booked-job pattern to a page-based site.

Uses only stdlib + BeautifulSoup4. No LLM calls.
"""
import datetime as dt
import fnmatch
import glob
import hashlib
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("PageAdapter requires beautifulsoup4. pip install beautifulsoup4")


# ---------- extraction ----------
def _text(el):
    return re.sub(r"\s+", " ", el.get_text(" ").strip()) if el else ""


def extract(path):
    """Return {url, title, description, canonical, h1, h2, lede, faq: [(q,a)]} or None."""
    with open(path, encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f, "html.parser")

    title = _text(soup.title) if soup.title else ""
    desc_el = soup.find("meta", attrs={"name": "description"})
    description = desc_el.get("content", "") if desc_el else ""
    canon_el = soup.find("link", rel="canonical")
    canonical = canon_el.get("href", "") if canon_el else ""

    pm_page = soup.find(id="pm-page")
    if not pm_page:
        return None  # Non-takeover page (e.g. root static Durable stub) — skip.

    h1 = _text(pm_page.find("h1"))
    h2 = _text(pm_page.find("h2"))
    lede_el = pm_page.find("p", class_="lede")
    lede = _text(lede_el)

    # Best-effort FAQ extraction from FAQPage schema (used on About / House Special)
    faq = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            import json as _json
            data = _json.loads(script.string or "{}")
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "FAQPage":
            for q in data.get("mainEntity", []):
                name = q.get("name", "")
                ans = q.get("acceptedAnswer", {}).get("text", "")
                if name and ans:
                    faq.append((name.strip(), ans.strip()))
            break  # only one FAQPage block per page

    return {
        "path": path,
        "url": canonical or _path_to_url(path),
        "title": title,
        "description": description,
        "h1": h1,
        "h2": h2,
        "lede": lede,
        "faq": faq,
    }


def _path_to_url(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    rel = rel.replace("site/", "", 1)
    if rel.endswith("index.html"):
        rel = rel[:-len("index.html")]
    return f"https://aaron.chat/{rel}"


# ---------- filtering ----------
def find_pages(cfg, root=None):
    """Yield paths matching cfg['content_source']['page_glob'], minus excludes."""
    root = root or ROOT
    cs = cfg.get("content_source", {})
    pattern = os.path.join(root, cs.get("page_glob", "site/**/index.html"))
    excludes = cs.get("exclude", [])

    for path in sorted(glob.glob(pattern, recursive=True)):
        rel = os.path.relpath(path, root)
        if any(fnmatch.fnmatch(rel, ex) or fnmatch.fnmatch(rel, ex.rstrip("/")) for ex in excludes):
            continue
        yield path


# ---------- voice-aware variant generation ----------
def _apply_voice(text, voice, platform):
    """Strip banned words, enforce hashtag caps, keep sentences short-ish. Deterministic."""
    banned = [w.lower() for w in voice.get("banned_words", [])]
    for w in banned:
        text = re.sub(rf"\b{re.escape(w)}\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    # Cap emoji per post (rough — count non-ASCII pictographs)
    max_em = voice.get("tone", {}).get("emoji_per_post", 1)
    emoji_re = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
    found = emoji_re.findall(text)
    if len(found) > max_em:
        keep = set(found[:max_em])
        text = "".join(c for c in text if not emoji_re.match(c) or c in keep and (keep.discard(c) or True))
    return text.strip()


def _hashtags(voice, platform, tags=None):
    approved = voice.get("hashtags", {}).get("approved", [])
    max_n = voice.get("hashtags", {}).get(f"{platform}_max", 3 if platform == "linkedin" else 1)
    picked = (tags or approved)[:max_n]
    return " ".join(f"#{t.lstrip('#')}" for t in picked)


def linkedin_variant(page, voice, variant_idx):
    """LinkedIn: 300-400 words. hook + body from h1/lede + CTA + hashtags."""
    hooks = voice.get("hooks", {}).get("linkedin", ["Here's what we ship for a service pro:"])
    hook = hooks[variant_idx % len(hooks)]

    body_lede = page.get("lede") or page.get("description") or page.get("h2") or ""
    body_h1 = page.get("h1") or page.get("title") or ""
    ctas = voice.get("cta", {}).get("variants", ["First year is free."])
    cta = ctas[variant_idx % len(ctas)]

    text = f"{hook}\n\n{body_h1}\n\n{body_lede}\n\n{cta}\n\nLink: {page['url']}\n\n{_hashtags(voice, 'linkedin')}"
    return _apply_voice(text, voice, "linkedin")


def x_variant(page, voice, variant_idx):
    """X: <= 270 chars total (leaves room for shortlink expansion). Hook + h1 + link + 1 tag."""
    hooks = voice.get("hooks", {}).get("x", ["Real talk on"])
    hook = hooks[variant_idx % len(hooks)]
    core = page.get("h1") or page.get("title") or page.get("description") or ""
    tag = _hashtags(voice, "x")
    # Reserve 24 chars for URL + spaces + tag padding
    max_core = 240 - len(hook) - len(tag) - len(page["url"]) - 8
    if len(core) > max(0, max_core):
        core = core[: max(0, max_core - 1)].rstrip() + "…"
    text = f"{hook} {core}\n{page['url']} {tag}".strip()
    return _apply_voice(text, voice, "x")


def variants_for(page, cfg, voice):
    """Yield (platform, text) for each enabled channel and variant index."""
    n = int(cfg.get("content_source", {}).get("variants_per_page", 2))
    platforms = [k for k, v in cfg.get("channels", {}).items() if v.get("enabled")]
    for platform in platforms:
        gen = {"linkedin": linkedin_variant, "x": x_variant}.get(platform)
        if not gen:
            continue
        for i in range(n):
            yield platform, i, gen(page, voice, i)


def make_item(page, platform, variant_idx, text, voice_version):
    _id_input = f"{page['url']}|{platform}|{variant_idx}"
    _id = hashlib.sha256(_id_input.encode()).hexdigest()[:12]
    return {
        "id": _id,
        "page_url": page["url"],
        "platform": platform,
        "variant": variant_idx,
        "text": text,
        "link": page["url"],
        "voice_version": voice_version,
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


# -------- CLI dry-run --------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to a single site/**/index.html to preview")
    ap.add_argument("--all", action="store_true", help="Preview against all matching pages")
    args = ap.parse_args()

    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
    voice = yaml.safe_load(open(os.path.join(ROOT, cfg["voice_ref"])))
    v_ver = voice.get("version", "0.0")

    if args.all:
        paths = list(find_pages(cfg))
        print(f"Would process {len(paths)} pages:")
        for p in paths[:8]:
            page = extract(p)
            if not page:
                print(f"  SKIP (no pm-page): {p}")
                continue
            print(f"  {page['url']}: title={page['title'][:50]!r}")
    elif args.path:
        page = extract(args.path)
        if not page:
            print(f"No pm-page block found in {args.path}"); sys.exit(1)
        print(f"URL:         {page['url']}")
        print(f"Title:       {page['title']}")
        print(f"Description: {page['description'][:120]}")
        print(f"H1:          {page['h1']}")
        print(f"Lede:        {page['lede'][:120]}")
        if page['faq']:
            print(f"FAQ:         {len(page['faq'])} Q&A pairs")
        print()
        for platform, i, text in variants_for(page, cfg, voice):
            print(f"--- {platform} variant {i} ({len(text)} chars) ---")
            print(text)
            print()
    else:
        ap.print_help()
