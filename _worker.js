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

// ============================================================================
// Tier-2 Connect Wizard — /setup + /api/setup/*
// Stores wizard state + credentials in Cloudflare KV (SETUP_KV binding).
// Authenticated by SETUP_PASSWORD (Worker env var) → HttpOnly signed cookie.
// GitHub Actions workflow fetches credentials via /api/secrets (bearer token).
// ============================================================================

const COOKIE_NAME = "pm_setup_session";
const COOKIE_TTL = 60 * 60 * 24 * 7; // 7 days

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function signSession(env) {
  const nonce = crypto.randomUUID();
  const expiresAt = Date.now() + COOKIE_TTL * 1000;
  const payload = `${nonce}|${expiresAt}`;
  const sig = await sha256Hex(payload + "|" + (env.SETUP_PASSWORD || ""));
  return `${payload}|${sig}`;
}

async function verifySession(cookieVal, env) {
  if (!cookieVal) return false;
  const parts = cookieVal.split("|");
  if (parts.length !== 3) return false;
  const [nonce, expiresAt, sig] = parts;
  if (Number(expiresAt) < Date.now()) return false;
  const expected = await sha256Hex(nonce + "|" + expiresAt + "|" + (env.SETUP_PASSWORD || ""));
  return expected === sig;
}

function getCookie(request, name) {
  const cookie = request.headers.get("cookie") || "";
  for (const p of cookie.split(";")) {
    const [k, ...v] = p.trim().split("=");
    if (k === name) return decodeURIComponent(v.join("="));
  }
  return null;
}

function setCookie(name, value) {
  return `${name}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${COOKIE_TTL}`;
}

function clearCookie(name) {
  return `${name}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;
}

async function requireSession(request, env) {
  const cookieVal = getCookie(request, COOKIE_NAME);
  const ok = await verifySession(cookieVal, env);
  if (!ok) return json({ ok: false, error: "unauthorized" }, 401);
  return null;
}

// ---- /api/setup routes ----

async function handleSetupLogin(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { password } = await request.json().catch(() => ({}));
  if (!env.SETUP_PASSWORD) return json({ ok: false, error: "SETUP_PASSWORD not configured" }, 500);
  if (!password || password !== env.SETUP_PASSWORD) {
    return json({ ok: false, error: "bad password" }, 401);
  }
  const sess = await signSession(env);
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      "Set-Cookie": setCookie(COOKIE_NAME, sess),
    },
  });
}

async function handleSetupLogout() {
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Set-Cookie": clearCookie(COOKIE_NAME),
    },
  });
}

async function handleSetupState(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  const { keys } = await env.SETUP_KV.list({ prefix: "channel:" });
  const channels = {};
  for (const k of keys) {
    const val = await env.SETUP_KV.get(k.name, "json");
    channels[k.name.replace("channel:", "")] = val || {};
  }
  return json({ ok: true, channels });
}

async function handleSetupSaveSecret(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { channel, secret_body, notes } = await request.json().catch(() => ({}));
  if (!channel || !secret_body) {
    return json({ ok: false, error: "channel + secret_body required" }, 400);
  }
  if (secret_body.length > 8192) {
    return json({ ok: false, error: "secret_body too large" }, 400);
  }
  // Store the raw multi-line env-file body under secret:<channel>
  await env.SETUP_KV.put(`secret:${channel}`, secret_body);
  // Update per-channel state under channel:<channel>
  const existing = (await env.SETUP_KV.get(`channel:${channel}`, "json")) || {};
  const state = {
    ...existing,
    status: "connected",
    connected_at: existing.connected_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
    notes: notes ?? existing.notes ?? "",
  };
  await env.SETUP_KV.put(`channel:${channel}`, JSON.stringify(state));
  return json({ ok: true, channel, state });
}

async function handleSetupClearSecret(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { channel } = await request.json().catch(() => ({}));
  if (!channel) return json({ ok: false, error: "channel required" }, 400);
  await env.SETUP_KV.delete(`secret:${channel}`);
  const existing = (await env.SETUP_KV.get(`channel:${channel}`, "json")) || {};
  const state = { ...existing, status: "not_started", connected_at: null, updated_at: new Date().toISOString() };
  await env.SETUP_KV.put(`channel:${channel}`, JSON.stringify(state));
  return json({ ok: true, channel });
}

async function handleSetupSaveNote(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { channel, notes } = await request.json().catch(() => ({}));
  if (!channel) return json({ ok: false, error: "channel required" }, 400);
  const existing = (await env.SETUP_KV.get(`channel:${channel}`, "json")) || {};
  const state = { ...existing, notes: notes ?? "", updated_at: new Date().toISOString() };
  await env.SETUP_KV.put(`channel:${channel}`, JSON.stringify(state));
  return json({ ok: true, channel, state });
}

// ---- /api/secrets — GitHub Actions consumer endpoint ----
// Auth: bearer token that matches env.SECRETS_FETCH_TOKEN. Returns all stored
// channel secret bodies keyed by channel name. Workflow writes each into
// secrets/<channel>.env at run time.

async function handleFetchSecrets(request, env) {
  const auth = request.headers.get("authorization") || "";
  const token = auth.replace(/^Bearer\s+/i, "");
  if (!env.SECRETS_FETCH_TOKEN) {
    return json({ ok: false, error: "SECRETS_FETCH_TOKEN not configured" }, 500);
  }
  if (!token || token !== env.SECRETS_FETCH_TOKEN) {
    return json({ ok: false, error: "unauthorized" }, 401);
  }
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  const { keys } = await env.SETUP_KV.list({ prefix: "secret:" });
  const secrets = {};
  for (const k of keys) {
    const val = await env.SETUP_KV.get(k.name);
    if (val) secrets[k.name.replace("secret:", "")] = val;
  }
  return json({ ok: true, secrets });
}

// ---- Setup UI gating ----
// /setup and /setup/* — if no session cookie, serve the login page.
async function handleSetupUi(request, env) {
  const url = new URL(request.url);
  const cookieVal = getCookie(request, COOKIE_NAME);
  const authed = await verifySession(cookieVal, env);
  // Login page is always accessible
  if (url.pathname === "/setup/login" || url.pathname === "/setup/login/") {
    return env.ASSETS.fetch(new Request(new URL("/setup/login/index.html", url.origin), request));
  }
  if (!authed) {
    // Redirect to login preserving the target
    const target = encodeURIComponent(url.pathname + url.search);
    return Response.redirect(`${url.origin}/setup/login/?next=${target}`, 302);
  }
  return env.ASSETS.fetch(request);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Existing routes
    if (url.pathname === "/api/contact") return handleContact(request, env);
    if (url.pathname === "/api/order") return handleOrder(request, env);

    // Wizard routes
    if (url.pathname === "/api/setup/login") return handleSetupLogin(request, env);
    if (url.pathname === "/api/setup/logout") return handleSetupLogout();
    if (url.pathname === "/api/setup/state") return handleSetupState(request, env);
    if (url.pathname === "/api/setup/secret") return handleSetupSaveSecret(request, env);
    if (url.pathname === "/api/setup/secret/clear") return handleSetupClearSecret(request, env);
    if (url.pathname === "/api/setup/note") return handleSetupSaveNote(request, env);
    if (url.pathname === "/api/secrets") return handleFetchSecrets(request, env);

    // Setup UI (auth-gated)
    if (url.pathname === "/setup" || url.pathname.startsWith("/setup/")) {
      return handleSetupUi(request, env);
    }

    // Everything else: serve the static asset (HTML, CSS, JS, images).
    return env.ASSETS.fetch(request);
  },
};
