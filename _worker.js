// _worker.js — Cloudflare Pages "advanced mode" entry point.
// Handles POST /api/contact (form submissions via Resend) and falls through
// to the static assets for everything else.
//
// Required env var (Pages > Settings > Environment variables, Production):
//   RESEND_API_KEY  (secret) — your Resend API key
// Optional (defaults below):
//   CONTACT_TO    — where leads are delivered (default hello@aaron.chat)
//   CONTACT_FROM  — verified Resend sender (default forms@aaron.chat)
//
// Note: the CONTACT_FROM domain must be verified in Resend before delivery
// works. For a fast pre-verification test, set
//   CONTACT_FROM="Hey Aaron! <onboarding@resend.dev>"
// (Resend's shared sender only delivers to the account-owner's address.)

const FALLBACK_ERR = "Sorry, something went wrong. Please call 713-384-8985.";

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function clean(v, max) {
  return (v == null ? "" : String(v)).trim().slice(0, max);
}

async function handleContact(request, env) {
  if (request.method !== "POST") {
    return json({ ok: false, error: "Method not allowed" }, 405);
  }
  try {
    const ct = request.headers.get("content-type") || "";
    let d = {};
    if (ct.includes("application/json")) {
      d = await request.json();
    } else {
      const form = await request.formData();
      for (const [k, v] of form.entries()) d[k] = v;
    }

    // Honeypot — silently accept so bots think they succeeded
    if (clean(d._gotcha, 100)) return json({ ok: true });

    const name = clean(d.name, 200);
    const email = clean(d.email, 200);
    const phone = clean(d.phone, 50);
    const business = clean(d.business, 200);
    const website = clean(d.website, 300);
    const message = clean(d.message, 5000);
    const source = clean(d._source, 100) || "website";

    if (!name || !email || (!message && !business)) {
      return json({ ok: false, error: "Please fill in your name, email, and a message." }, 400);
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return json({ ok: false, error: "Please enter a valid email address." }, 400);
    }
    if (!env.RESEND_API_KEY) {
      return json({ ok: false, error: "Email is not configured yet." }, 500);
    }

    const lines = [
      `New submission from the ${source} form on aaron.chat`,
      "",
      `Name: ${name}`,
      `Email: ${email}`,
      phone ? `Phone: ${phone}` : null,
      business ? `Business: ${business}` : null,
      website ? `Current website: ${website}` : null,
      "",
      "Message:",
      message || "(none)",
    ].filter((l) => l !== null);

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: env.CONTACT_FROM || "Hey Aaron! Website <forms@aaron.chat>",
        to: [env.CONTACT_TO || "hello@aaron.chat"],
        reply_to: email,
        subject: `New ${source} lead: ${name}`,
        text: lines.join("\n"),
      }),
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      console.log("Resend error", res.status, detail);
      return json({ ok: false, error: FALLBACK_ERR }, 502);
    }

    return json({ ok: true });
  } catch (err) {
    console.log("contact handler error", err && err.message);
    return json({ ok: false, error: FALLBACK_ERR }, 500);
  }
}

// ============================================================
// /api/order — multi-step site-plan intake → generate Claude prompt → email
// ============================================================

function buildSitePlanPrompt(d) {
  const list = (v) => Array.isArray(v) ? v : (v ? String(v).split(/\r?\n|,/).map(s => s.trim()).filter(Boolean) : []);
  const services = list(d.services);
  const offers = Array.isArray(d.offers) ? d.offers : (d.offers ? [d.offers] : []);
  const areas = list(d.otherAreas);

  const lines = [];
  lines.push("# Build a Service-Pro Marketing Site");
  lines.push("");
  lines.push("Model this on **https://aaron.chat** (the Hey Aaron! Marketing static site): a fast, mobile-first, statically-deployable site with a clear local-services menu, Combo Plates, and one offer story end-to-end. Reuse that pricing model — House Special (Year 1 free), $250/mo House Plate, à la carte services, and three Combo Plates (Get-Found, Phone-Ringer, Regulars) — unless I tell you otherwise.");
  lines.push("");
  lines.push("## The business");
  lines.push(`- **Name:** ${d.businessName || "(not provided)"}`);
  lines.push(`- **Owner:** ${d.ownerName || "(not provided)"}`);
  lines.push(`- **Trade:** ${d.trade || "(not provided)"}`);
  if (d.years) lines.push(`- **Years in business:** ${d.years}`);
  if (d.tagline) lines.push(`- **Tagline / one-liner:** ${d.tagline}`);
  lines.push(`- **Brand voice:** ${d.voice || "Down-to-Earth"}`);
  lines.push("");
  lines.push("## Service area");
  lines.push(`- **Main town:** ${d.mainCity || "(not provided)"}, ${d.state || "Texas"}`);
  if (areas.length) lines.push(`- **Also serving:** ${areas.join(", ")}`);
  if (areas.length >= 5) lines.push(`- Build a dedicated **\`/locations/<town>/\`** page for each town and a sitewide "Areas We Serve" footer linking all of them.`);
  lines.push("");
  lines.push("## Public contact (use these exactly on the site)");
  lines.push(`- **Phone:** ${d.publicPhone || "(not provided)"}`);
  lines.push(`- **Email:** ${d.publicEmail || "(not provided)"}`);
  if (d.address) lines.push(`- **Address:** ${d.address}`);
  else lines.push(`- **Address:** Service-area business — no public storefront address.`);
  lines.push("");
  lines.push("## Services to highlight (give each its own /services/<slug>/ page)");
  if (services.length) services.forEach((s, i) => lines.push(`${i+1}. ${s}`));
  else lines.push("- (none specified — ask)");
  if (offers.length) {
    lines.push("");
    lines.push("## Trust signals to feature site-wide");
    offers.forEach(o => lines.push(`- ${o}`));
  }
  if (d.differentiator) {
    lines.push("");
    lines.push("## What sets them apart (use this in About + hero copy)");
    lines.push(`> ${d.differentiator}`);
  }
  lines.push("");
  lines.push("## Existing assets to pull from");
  lines.push(`- **Current website:** ${d.existingSite || "(none)"}`);
  lines.push(`- **Google Business Profile:** ${d.gbpUrl || "(needs setup)"}`);
  lines.push(`- **Facebook page:** ${d.facebookUrl || "(needs setup)"}`);
  lines.push(`- **Logo:** ${d.logo || "Have one I love"}`);
  lines.push("");
  lines.push("## Order");
  lines.push(`- **Starting plan:** ${d.plan || "House Special — Free Year"}`);
  lines.push(`- **Launch urgency:** ${d.urgency || "Within 2 weeks"}`);
  if (d.notes) {
    lines.push("");
    lines.push("## Notes from the owner");
    lines.push(d.notes);
  }
  lines.push("");
  lines.push("## What to build (deliverables)");
  lines.push("1. Static, mobile-first site, Cloudflare Pages deployable (same _headers / _redirects / .assetsignore conventions as aaron.chat).");
  lines.push("2. **Pages:** `/` (home with hero + menu teaser + Phone-Ringer featured card), `/about/`, `/pricing/` (the menu), `/get-started/` (working contact form via Cloudflare Pages Function + Resend), `/order/` (this same 9-step wizard), `/services/<slug>/` for each service above, `/who-we-help/<trade>/` if relevant, `/locations/<town>/` for each service area, `/plans/get-found-plate/` + `/plans/phone-ringer-plate/` + `/plans/regulars-plate/`, `/404.html`.");
  lines.push("3. **Menu model:** House Special (Free Year), House Plate ($250/mo), à la carte services with monthly prices, three Combo Plates, Sides, FAQ. Use the diner-menu aesthetic (cream/brown/gold/red) for the pricing page and combo landings; site-wide green theme for nav/footer.");
  lines.push("4. **Voice:** match the brand voice above. Write outcome-first copy. Hero on each page leads with the customer's problem and how this business fixes it.");
  lines.push("5. **Schema.org:** `ProfessionalService` site-wide with NAP, `Service` per service page, `OfferCatalog` on indexable pages, `Product` for Combo Plates. Include `areaServed`.");
  lines.push("6. **Performance + SEO:** self-referencing canonicals everywhere, sitemap.xml (exclude noindex pages), robots.txt + llms.txt, OpenGraph + Twitter tags per page, optimized images (resize to ≤1920px, recompress), Cloudflare cache headers (1yr immutable on assets), security headers.");
  lines.push("7. **Local SEO:** real local content per location page (≤60% similarity between pages), neighbor-town cross-links, town-specific FAQs if the owner provides them.");
  lines.push("8. **Forms:** working contact + multi-step order form, both POSTing to a `_worker.js` Cloudflare Pages Worker that uses Resend for email. Honeypot + email validation. No real Stripe links until the owner provides them — order CTAs route to the contact form with the chosen plate pre-filled.");
  lines.push("9. **Sticky CTA:** dismissible \"Claim Free Year\" floating pill bottom-left, with localStorage memory.");
  lines.push("");
  lines.push("## Acceptance");
  lines.push("- All pages 200 OK; sitemap valid; canonical correct; LocalBusiness schema validates in Google's Rich Results test.");
  lines.push("- Mobile audit clean: viewport, tap targets ≥48px, no horizontal overflow.");
  lines.push("- Contact + order forms submit successfully via the worker.");
  lines.push("- One offer story end-to-end (no leftover legacy population-tier pricing).");
  lines.push("");
  lines.push("---");
  lines.push(`*Submitted by ${d.ownerName || "(owner)"} for ${d.businessName || "(business)"} on ${new Date().toISOString().slice(0,10)}. Call back at ${d.ownerPhone || d.publicPhone || ""}.*`);
  return lines.join("\n");
}

async function handleOrder(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "Method not allowed" }, 405);
  try {
    const ct = request.headers.get("content-type") || "";
    let d = {};
    if (ct.includes("application/json")) d = await request.json();
    else {
      const form = await request.formData();
      for (const [k, v] of form.entries()) {
        if (d[k] != null) d[k] = Array.isArray(d[k]) ? [...d[k], v] : [d[k], v];
        else d[k] = v;
      }
    }
    // honeypot — accept silently if filled
    if (clean(d._gotcha, 100)) return json({ ok: true, prompt: "(skipped)" });

    const required = ["ownerName","ownerEmail","ownerPhone","businessName","trade","mainCity","publicPhone","publicEmail","services","differentiator"];
    for (const k of required) {
      if (!d[k] || (typeof d[k] === "string" && !d[k].trim())) {
        return json({ ok: false, error: `Missing required field: ${k}` }, 400);
      }
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(String(d.ownerEmail).trim())) {
      return json({ ok: false, error: "Please enter a valid email address." }, 400);
    }

    const prompt = buildSitePlanPrompt(d);
    const subject = `New site-build plan: ${clean(d.businessName, 100)} (${clean(d.trade, 60)}) — ${clean(d.mainCity, 60)}`;
    const summary = [
      `New site-plan request from ${clean(d.ownerName, 200)}`,
      "",
      `Business:      ${clean(d.businessName, 200)}`,
      `Trade:         ${clean(d.trade, 60)}`,
      `Main town:     ${clean(d.mainCity, 100)}, ${clean(d.state, 60) || "Texas"}`,
      `Public phone:  ${clean(d.publicPhone, 50)}`,
      `Owner phone:   ${clean(d.ownerPhone, 50)}`,
      `Owner email:   ${clean(d.ownerEmail, 200)}`,
      `Plan:          ${clean(d.plan, 100)}`,
      `Urgency:       ${clean(d.urgency, 60)}`,
      "",
      "─── Full Claude prompt below ───",
      "",
      prompt,
    ].join("\n");

    if (!env.RESEND_API_KEY) {
      // No key yet — still return the generated prompt so the wizard can show it
      return json({ ok: true, prompt, warning: "Email not configured yet, but here's the plan." });
    }

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: env.CONTACT_FROM || "Hey Aaron! Website <forms@aaron.chat>",
        to: [env.CONTACT_TO || "hello@aaron.chat"],
        reply_to: String(d.ownerEmail).trim(),
        subject,
        text: summary,
      }),
    });
    if (!res.ok) {
      console.log("Resend order error", res.status, await res.text().catch(() => ""));
      // Still return the prompt so the customer keeps it
      return json({ ok: true, prompt, warning: "Saved your plan but the email send hiccuped. We'll follow up directly." });
    }
    return json({ ok: true, prompt });
  } catch (err) {
    console.log("order handler error", err && err.message);
    return json({ ok: false, error: "Something went wrong. Please call 713-384-8985." }, 500);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/contact") {
      return handleContact(request, env);
    }
    if (url.pathname === "/api/order") {
      return handleOrder(request, env);
    }
    // Everything else: serve the static asset (HTML, CSS, JS, images).
    return env.ASSETS.fetch(request);
  },
};
