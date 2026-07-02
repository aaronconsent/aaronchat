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

// ============================================================================
// OAuth registry — one entry per provider that supports "Connect via OAuth"
// Instead of the user copy-pasting tokens, they configure the app once
// (oauth_app:<provider> in KV), click Connect, and the callback captures the
// tokens automatically.
// ============================================================================

const OAUTH_PROVIDERS = {
  meta: {
    label: "Meta (Facebook + Instagram + Threads)",
    // App credentials the user pastes into oauth_app:meta before clicking Connect
    app_fields: ["client_id", "client_secret"],
    // OAuth 2.0 endpoints
    authorize_url: "https://www.facebook.com/v18.0/dialog/oauth",
    token_url: "https://graph.facebook.com/v18.0/oauth/access_token",
    scopes: [
      "pages_manage_posts",
      "pages_read_engagement",
      "pages_show_list",
      "instagram_content_publish",
      "business_management",
    ],
    // After exchange: list pages, pick first, get long-lived + page tokens + IG account
    async post_exchange({ access_token, app }) {
      // Exchange short-lived user token for long-lived (60-day) token
      const llParams = new URLSearchParams({
        grant_type: "fb_exchange_token",
        client_id: app.client_id,
        client_secret: app.client_secret,
        fb_exchange_token: access_token,
      });
      const llRes = await fetch(`https://graph.facebook.com/v18.0/oauth/access_token?${llParams}`);
      const llData = await llRes.json();
      if (!llRes.ok) throw new Error(`long-lived exchange failed: ${JSON.stringify(llData).slice(0, 300)}`);
      const longToken = llData.access_token;

      // Get pages the user manages
      const pagesRes = await fetch(`https://graph.facebook.com/v18.0/me/accounts?access_token=${longToken}`);
      const pagesData = await pagesRes.json();
      if (!pagesRes.ok || !pagesData.data?.length) {
        throw new Error("no pages accessible with this token — check app permissions");
      }
      const page = pagesData.data[0]; // { id, name, access_token }

      // Get IG business account linked to the page (if any)
      let igUserId = "";
      try {
        const igRes = await fetch(
          `https://graph.facebook.com/v18.0/${page.id}?fields=instagram_business_account&access_token=${page.access_token}`
        );
        const igData = await igRes.json();
        igUserId = igData.instagram_business_account?.id || "";
      } catch (_) {}

      return {
        env_body: [
          `META_APP_ID=${app.client_id}`,
          `META_APP_SECRET=${app.client_secret}`,
          `META_PAGE_ID=${page.id}`,
          `META_PAGE_NAME=${page.name}`,
          `META_PAGE_TOKEN=${page.access_token}`,
          `META_LONG_LIVED_USER_TOKEN=${longToken}`,
          `META_IG_USER_ID=${igUserId}`,
          `META_THREADS_USER_ID=${igUserId}`, // Threads uses IG user id
        ].join("\n"),
        summary: `Page: ${page.name} (${page.id}) · IG: ${igUserId || "not linked"}`,
      };
    },
  },

  google: {
    label: "Google (Blogger + YouTube + GBP)",
    app_fields: ["client_id", "client_secret"],
    authorize_url: "https://accounts.google.com/o/oauth2/v2/auth",
    token_url: "https://oauth2.googleapis.com/token",
    scopes: [
      "https://www.googleapis.com/auth/youtube.upload",
      "https://www.googleapis.com/auth/youtube.readonly",
      "https://www.googleapis.com/auth/blogger",
      "https://www.googleapis.com/auth/business.manage",
    ],
    extra_params: { access_type: "offline", prompt: "consent" },
    async post_exchange({ access_token, refresh_token, app }) {
      // List blogs
      let bloggerBlogId = "";
      try {
        const blogsRes = await fetch("https://www.googleapis.com/blogger/v3/users/self/blogs", {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        const blogsData = await blogsRes.json();
        bloggerBlogId = blogsData.items?.[0]?.id || "";
      } catch (_) {}

      // List YouTube channels
      let ytChannelId = "";
      try {
        const ytRes = await fetch(
          "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
          { headers: { Authorization: `Bearer ${access_token}` } }
        );
        const ytData = await ytRes.json();
        ytChannelId = ytData.items?.[0]?.id || "";
      } catch (_) {}

      // GBP accounts (may be blocked pending quota)
      let gbpAccountId = "";
      try {
        const gbpRes = await fetch(
          "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
          { headers: { Authorization: `Bearer ${access_token}` } }
        );
        const gbpData = await gbpRes.json();
        gbpAccountId = gbpData.accounts?.[0]?.name?.replace("accounts/", "") || "";
      } catch (_) {}

      return {
        env_body: [
          `GOOGLE_CLIENT_ID=${app.client_id}`,
          `GOOGLE_CLIENT_SECRET=${app.client_secret}`,
          `GOOGLE_REFRESH_TOKEN=${refresh_token || ""}`,
          `GOOGLE_BLOGGER_BLOG_ID=${bloggerBlogId}`,
          `GOOGLE_YOUTUBE_CHANNEL_ID=${ytChannelId}`,
          `GOOGLE_GBP_ACCOUNT_ID=${gbpAccountId}`,
        ].join("\n"),
        summary: `Blogger: ${bloggerBlogId || "none"} · YT: ${ytChannelId || "none"} · GBP: ${gbpAccountId || "none/quota-pending"}`,
      };
    },
  },

  tumblr: {
    label: "Tumblr",
    app_fields: ["client_id", "client_secret", "blog"],
    // Tumblr uses OAuth 2.0 now (they call app credentials "consumer key/secret")
    authorize_url: "https://www.tumblr.com/oauth2/authorize",
    token_url: "https://api.tumblr.com/v2/oauth2/token",
    scopes: ["basic", "write", "offline_access"],
    async post_exchange({ access_token, refresh_token, app }) {
      return {
        env_body: [
          `TUMBLR_CONSUMER_KEY=${app.client_id}`,
          `TUMBLR_CONSUMER_SECRET=${app.client_secret}`,
          `TUMBLR_ACCESS_TOKEN=${access_token}`,
          `TUMBLR_REFRESH_TOKEN=${refresh_token || ""}`,
          `TUMBLR_BLOG=${app.blog || ""}`,
        ].join("\n"),
        summary: `Blog: ${app.blog || "(not set)"}`,
      };
    },
  },

  mastodon: {
    label: "Mastodon",
    // Mastodon is per-instance. User pastes just the instance URL; we dynamically
    // register a client app on that instance to get client_id/client_secret, then
    // run the OAuth flow.
    app_fields: ["instance"],
    // authorize_url and token_url are per-instance — filled in dynamically.
    scopes: ["read:accounts", "write:statuses"],
    dynamic_registration: true,
    async post_exchange({ access_token, app }) {
      let handle = "";
      try {
        const meRes = await fetch(`${app.instance}/api/v1/accounts/verify_credentials`, {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        const meData = await meRes.json();
        handle = meData.username ? `@${meData.username}@${new URL(app.instance).host}` : "";
      } catch (_) {}
      return {
        env_body: [
          `MASTODON_INSTANCE=${app.instance}`,
          `MASTODON_CLIENT_ID=${app.client_id}`,
          `MASTODON_CLIENT_SECRET=${app.client_secret}`,
          `MASTODON_ACCESS_TOKEN=${access_token}`,
          `MASTODON_HANDLE=${handle}`,
        ].join("\n"),
        summary: `Handle: ${handle}`,
      };
    },
  },
};

// ---- OAuth state helpers ----
async function signState(provider, env) {
  const nonce = crypto.randomUUID();
  const expiresAt = Date.now() + 10 * 60 * 1000; // 10-min TTL
  const payload = `${provider}|${nonce}|${expiresAt}`;
  const sig = await sha256Hex(payload + "|" + (env.SETUP_PASSWORD || ""));
  return btoa(`${payload}|${sig}`).replace(/=+$/, "");
}

async function verifyState(state, env) {
  try {
    const raw = atob(state);
    const parts = raw.split("|");
    if (parts.length !== 4) return null;
    const [provider, nonce, expiresAt, sig] = parts;
    if (Number(expiresAt) < Date.now()) return null;
    const expected = await sha256Hex(`${provider}|${nonce}|${expiresAt}|` + (env.SETUP_PASSWORD || ""));
    if (expected !== sig) return null;
    return { provider, nonce, expiresAt };
  } catch (_) {
    return null;
  }
}

// ---- KV helpers for OAuth app config ----
async function loadOauthApp(env, provider) {
  const raw = await env.SETUP_KV.get(`oauth_app:${provider}`);
  return raw ? JSON.parse(raw) : null;
}

async function saveOauthApp(env, provider, appConfig) {
  await env.SETUP_KV.put(`oauth_app:${provider}`, JSON.stringify(appConfig));
}

// ---- POST /api/setup/oauth-app — save/read OAuth app credentials ----

async function handleOauthAppSave(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { provider, app } = await request.json().catch(() => ({}));
  if (!provider || !OAUTH_PROVIDERS[provider]) return json({ ok: false, error: "unknown provider" }, 400);
  if (!app || typeof app !== "object") return json({ ok: false, error: "app object required" }, 400);
  // Validate required fields
  const required = OAUTH_PROVIDERS[provider].app_fields;
  for (const f of required) {
    if (!app[f]) return json({ ok: false, error: `missing app.${f}` }, 400);
  }
  await saveOauthApp(env, provider, app);
  return json({ ok: true, provider });
}

async function handleOauthAppGet(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  const url = new URL(request.url);
  const provider = url.searchParams.get("provider");
  if (!provider || !OAUTH_PROVIDERS[provider]) return json({ ok: false, error: "unknown provider" }, 400);
  const app = await loadOauthApp(env, provider);
  // Never return client_secret in cleartext — mask for confirmation display
  const masked = app
    ? Object.fromEntries(Object.entries(app).map(([k, v]) => [k, /secret|password/i.test(k) ? "•".repeat(8) : v]))
    : null;
  return json({ ok: true, app: masked });
}

// ---- GET /oauth/:provider/start — kick off OAuth flow ----

async function handleOauthStart(request, env, provider) {
  const authErr = await requireSession(request, env);
  if (authErr) {
    // Redirect to login preserving intent
    const url = new URL(request.url);
    const target = encodeURIComponent(`/oauth/${provider}/start`);
    return Response.redirect(`${url.origin}/setup/login/?next=${target}`, 302);
  }
  const spec = OAUTH_PROVIDERS[provider];
  if (!spec) return new Response(`Unknown OAuth provider: ${provider}`, { status: 404 });
  const app = await loadOauthApp(env, provider);
  if (!app) {
    return new Response(
      `<h1>OAuth app not configured</h1><p>Save app credentials for <b>${provider}</b> in the wizard first, then click Connect again.</p><p><a href="/setup/">← back to wizard</a></p>`,
      { status: 400, headers: { "Content-Type": "text/html" } }
    );
  }
  const url = new URL(request.url);
  const redirectUri = `${url.origin}/oauth/${provider}/callback`;
  const state = await signState(provider, env);
  const scopes = spec.scopes.join(",");
  // Special-case dynamic app registration (Mastodon per-instance)
  let authorizeBase = spec.authorize_url;
  let clientId = app.client_id;
  let clientSecret = app.client_secret;
  if (spec.dynamic_registration && !clientId) {
    // Register a client app on the instance right now
    if (!app.instance) {
      return new Response("Mastodon needs an instance URL", { status: 400 });
    }
    const regRes = await fetch(`${app.instance}/api/v1/apps`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_name: "aaron.chat Connect Wizard",
        redirect_uris: redirectUri,
        scopes: spec.scopes.join(" "),
        website: url.origin,
      }),
    });
    const regData = await regRes.json();
    if (!regRes.ok || !regData.client_id) {
      return new Response(`Mastodon app registration failed: ${JSON.stringify(regData).slice(0, 300)}`, {
        status: 500,
      });
    }
    clientId = regData.client_id;
    clientSecret = regData.client_secret;
    // Persist back for the callback
    await saveOauthApp(env, provider, { ...app, client_id: clientId, client_secret: clientSecret });
    authorizeBase = `${app.instance}/oauth/authorize`;
  }
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: spec === OAUTH_PROVIDERS.mastodon ? spec.scopes.join(" ") : scopes,
    state,
    ...(spec.extra_params || {}),
  });
  return Response.redirect(`${authorizeBase}?${params.toString()}`, 302);
}

// ---- GET /oauth/:provider/callback — receive code, exchange, store ----

async function handleOauthCallback(request, env, provider) {
  const spec = OAUTH_PROVIDERS[provider];
  if (!spec) return new Response(`Unknown OAuth provider: ${provider}`, { status: 404 });
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const errorParam = url.searchParams.get("error");
  const errorDesc = url.searchParams.get("error_description");

  if (errorParam) {
    return htmlPage(
      `OAuth cancelled or denied`,
      `<p>${errorParam}: ${errorDesc || ""}</p><p><a href="/setup/">← back to wizard</a></p>`
    );
  }
  if (!code || !state) {
    return htmlPage("Missing code or state", `<p><a href="/setup/">← back to wizard</a></p>`);
  }
  const stateData = await verifyState(state, env);
  if (!stateData || stateData.provider !== provider) {
    return htmlPage("Invalid state", `<p>State expired or tampered. <a href="/oauth/${provider}/start">Try again</a></p>`);
  }
  const app = await loadOauthApp(env, provider);
  if (!app) return htmlPage("App config missing", `<p><a href="/setup/">← back to wizard</a></p>`);

  // Special case for Mastodon token URL (per-instance)
  const tokenUrl = spec === OAUTH_PROVIDERS.mastodon ? `${app.instance}/oauth/token` : spec.token_url;

  const redirectUri = `${url.origin}/oauth/${provider}/callback`;
  const body = new URLSearchParams({
    client_id: app.client_id,
    client_secret: app.client_secret,
    code,
    redirect_uri: redirectUri,
    grant_type: "authorization_code",
  });

  const tRes = await fetch(tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body: body.toString(),
  });
  const tData = await tRes.json().catch(() => ({}));
  if (!tRes.ok || !tData.access_token) {
    return htmlPage(
      `${provider}: token exchange failed`,
      `<pre style="max-width:640px;white-space:pre-wrap">${JSON.stringify(tData, null, 2).slice(0, 1200)}</pre><p><a href="/setup/">← back to wizard</a></p>`
    );
  }

  try {
    const post = await spec.post_exchange({
      access_token: tData.access_token,
      refresh_token: tData.refresh_token,
      app,
    });
    await env.SETUP_KV.put(`secret:${provider}`, post.env_body);
    const existing = (await env.SETUP_KV.get(`channel:${provider}`, "json")) || {};
    const chState = {
      ...existing,
      status: "connected",
      connected_at: existing.connected_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
      oauth_summary: post.summary,
    };
    await env.SETUP_KV.put(`channel:${provider}`, JSON.stringify(chState));

    return htmlPage(
      `${spec.label}: connected ✓`,
      `<p><b>${post.summary}</b></p>
       <p>Credentials stored in Cloudflare KV under <code>secret:${provider}</code>. The GitHub Actions workflow will fetch them at the next run.</p>
       <p><a href="/setup/" class="btn">← back to wizard</a></p>`
    );
  } catch (ex) {
    return htmlPage(
      `${provider}: post-exchange failed`,
      `<pre style="max-width:640px;white-space:pre-wrap">${(ex.message || String(ex)).slice(0, 1200)}</pre><p><a href="/setup/">← back to wizard</a></p>`
    );
  }
}

function htmlPage(title, bodyHtml) {
  return new Response(
    `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
     <style>body{font-family:"Bitter",Georgia,serif;background:#fffaf0;color:#3a2a20;padding:40px 32px;max-width:820px;margin:0 auto;}
     h1{font-family:"Alfa Slab One",serif;font-weight:400;color:#5b3427;font-size:1.6rem;}
     a{color:#a82b22;border-bottom:1px dotted #a82b22;text-decoration:none;}
     code{background:#fff7e0;padding:2px 6px;border-radius:4px;color:#a82b22;font-size:.9em;}
     pre{background:#fff7e0;padding:14px;border-radius:8px;overflow:auto;font-size:.85rem;}
     .btn{display:inline-block;background:#a82b22;color:#fffaf0;padding:10px 18px;border-radius:8px;text-decoration:none;border:2px solid #5b3427;box-shadow:3px 3px 0 #5b3427;margin-top:12px;}
     </style></head><body>
     <h1>${title}</h1>${bodyHtml}</body></html>`,
    { status: 200, headers: { "Content-Type": "text/html" } }
  );
}

// ============================================================================
// Capability probes — read-only API calls that verify a stored secret works.
// Each returns { ok: bool, status: "verified"|"failed", detail: string }.
// Runs against the parsed env-file body pulled from secret:<provider>.
// ============================================================================

function parseEnvBody(body) {
  const out = {};
  if (!body) return out;
  for (const line of body.split("\n")) {
    const s = line.trim();
    if (!s || s.startsWith("#") || !s.includes("=")) continue;
    const idx = s.indexOf("=");
    out[s.slice(0, idx).trim()] = s.slice(idx + 1).trim();
  }
  return out;
}

const PROBES = {
  async buffer(env, e) {
    if (!e.BUFFER_TOKEN) return { ok: false, detail: "BUFFER_TOKEN missing" };
    const body = JSON.stringify({
      query: `query($i: ChannelsInput!){ channels(input:$i){ id service displayName } }`,
      variables: { i: { organizationId: e.BUFFER_ORG } },
    });
    const r = await fetch("https://api.buffer.com", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${e.BUFFER_TOKEN}`,
        "Content-Type": "application/json",
      },
      body,
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.errors) return { ok: false, detail: `Buffer ${r.status}: ${JSON.stringify(d).slice(0, 200)}` };
    const chs = d.data?.channels || [];
    const services = chs.map((c) => c.service).filter(Boolean);
    return { ok: true, detail: `${chs.length} channels: ${services.join(", ") || "(none)"}` };
  },

  async bluesky(env, e) {
    if (!e.BLUESKY_HANDLE || !e.BLUESKY_APP_PASSWORD) {
      return { ok: false, detail: "BLUESKY_HANDLE + BLUESKY_APP_PASSWORD required" };
    }
    const r = await fetch("https://bsky.social/xrpc/com.atproto.server.createSession", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: e.BLUESKY_HANDLE, password: e.BLUESKY_APP_PASSWORD }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.accessJwt) return { ok: false, detail: `Bluesky ${r.status}: ${d.error || d.message || "auth failed"}` };
    return { ok: true, detail: `Signed in as ${d.handle} (did: ${d.did?.slice(0, 24)}…)` };
  },

  async telegraph(env, e) {
    if (!e.TELEGRAPH_ACCESS_TOKEN) {
      return {
        ok: true,
        detail: "No token stored yet — publisher will bootstrap one on first post. That's fine.",
        soft: true,
      };
    }
    const r = await fetch(`https://api.telegra.ph/getAccountInfo?access_token=${e.TELEGRAPH_ACCESS_TOKEN}`);
    const d = await r.json().catch(() => ({}));
    if (!d.ok) return { ok: false, detail: `Telegraph: ${d.error || "invalid token"}` };
    return { ok: true, detail: `Author: ${d.result?.short_name || "?"} · Views: ${d.result?.page_count || 0} pages` };
  },

  async meta(env, e) {
    const token = e.META_PAGE_TOKEN || e.META_LONG_LIVED_USER_TOKEN;
    if (!token) return { ok: false, detail: "META_PAGE_TOKEN or META_LONG_LIVED_USER_TOKEN required" };
    const r = await fetch(`https://graph.facebook.com/v18.0/debug_token?input_token=${token}&access_token=${token}`);
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.data) return { ok: false, detail: `Meta ${r.status}: ${d.error?.message || "debug_token failed"}` };
    const scopes = d.data.scopes?.slice(0, 5).join(", ") || "(no scopes)";
    const app = d.data.app_id ? `app ${d.data.app_id}` : "";
    const expires = d.data.expires_at
      ? d.data.expires_at === 0
        ? "never"
        : new Date(d.data.expires_at * 1000).toISOString().slice(0, 10)
      : "?";
    return { ok: true, detail: `${app} · expires ${expires} · scopes: ${scopes}` };
  },

  async google(env, e) {
    if (!e.GOOGLE_REFRESH_TOKEN || !e.GOOGLE_CLIENT_ID || !e.GOOGLE_CLIENT_SECRET) {
      return { ok: false, detail: "GOOGLE_CLIENT_ID + CLIENT_SECRET + REFRESH_TOKEN all required" };
    }
    // Exchange refresh_token for a live access_token
    const params = new URLSearchParams({
      client_id: e.GOOGLE_CLIENT_ID,
      client_secret: e.GOOGLE_CLIENT_SECRET,
      refresh_token: e.GOOGLE_REFRESH_TOKEN,
      grant_type: "refresh_token",
    });
    const rr = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });
    const rd = await rr.json().catch(() => ({}));
    if (!rr.ok || !rd.access_token) return { ok: false, detail: `Google refresh failed: ${rd.error_description || rd.error || rr.status}` };
    // Test one API: YouTube channel list
    const yt = await fetch("https://www.googleapis.com/youtube/v3/channels?part=id&mine=true", {
      headers: { Authorization: `Bearer ${rd.access_token}` },
    });
    const ytd = await yt.json().catch(() => ({}));
    if (!yt.ok) return { ok: false, detail: `YouTube probe ${yt.status}: ${ytd.error?.message || "?"}` };
    return {
      ok: true,
      detail: `Refresh token live · scope=${(rd.scope || "").split(" ").length} scopes · YT channels: ${ytd.items?.length || 0}`,
    };
  },

  async tumblr(env, e) {
    if (!e.TUMBLR_ACCESS_TOKEN) return { ok: false, detail: "TUMBLR_ACCESS_TOKEN required" };
    const r = await fetch("https://api.tumblr.com/v2/user/info", {
      headers: { Authorization: `Bearer ${e.TUMBLR_ACCESS_TOKEN}` },
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.response?.user) return { ok: false, detail: `Tumblr ${r.status}: ${d.meta?.msg || "?"}` };
    const blogs = d.response.user.blogs?.map((b) => b.name).join(", ") || "(none)";
    return { ok: true, detail: `User: ${d.response.user.name} · blogs: ${blogs}` };
  },

  async mastodon(env, e) {
    if (!e.MASTODON_INSTANCE || !e.MASTODON_ACCESS_TOKEN) {
      return { ok: false, detail: "MASTODON_INSTANCE + MASTODON_ACCESS_TOKEN required" };
    }
    const r = await fetch(`${e.MASTODON_INSTANCE}/api/v1/accounts/verify_credentials`, {
      headers: { Authorization: `Bearer ${e.MASTODON_ACCESS_TOKEN}` },
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.username) return { ok: false, detail: `Mastodon ${r.status}: ${d.error || "?"}` };
    return { ok: true, detail: `@${d.username}@${new URL(e.MASTODON_INSTANCE).host} · ${d.followers_count || 0} followers` };
  },

  async telegram(env, e) {
    if (!e.TELEGRAM_BOT_TOKEN) return { ok: false, detail: "TELEGRAM_BOT_TOKEN required" };
    const r = await fetch(`https://api.telegram.org/bot${e.TELEGRAM_BOT_TOKEN}/getMe`);
    const d = await r.json().catch(() => ({}));
    if (!d.ok) return { ok: false, detail: `Telegram: ${d.description || "auth failed"}` };
    return { ok: true, detail: `Bot: @${d.result.username} (${d.result.first_name})` };
  },

  async github_pages(env, e) {
    if (!e.GH_PAGES_PAT || !e.GH_PAGES_REPO) {
      return { ok: false, detail: "GH_PAGES_PAT + GH_PAGES_REPO required" };
    }
    const r = await fetch(`https://api.github.com/repos/${e.GH_PAGES_REPO}`, {
      headers: {
        Authorization: `Bearer ${e.GH_PAGES_PAT}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "aaron-chat-connect-wizard",
      },
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return { ok: false, detail: `GitHub ${r.status}: ${d.message || "?"}` };
    return { ok: true, detail: `Repo: ${d.full_name} · default branch: ${d.default_branch} · size: ${d.size} KB` };
  },

  async resend(env, e) {
    if (!e.RESEND_API_KEY) return { ok: false, detail: "RESEND_API_KEY required" };
    const r = await fetch("https://api.resend.com/audiences", {
      headers: { Authorization: `Bearer ${e.RESEND_API_KEY}` },
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return { ok: false, detail: `Resend ${r.status}: ${d.message || "?"}` };
    return { ok: true, detail: `${d.data?.length || 0} audiences configured` };
  },
};

async function handleProbe(request, env) {
  const authErr = await requireSession(request, env);
  if (authErr) return authErr;
  if (!env.SETUP_KV) return json({ ok: false, error: "SETUP_KV not bound" }, 500);
  if (request.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);
  const { provider } = await request.json().catch(() => ({}));
  if (!provider || !PROBES[provider]) return json({ ok: false, error: `no probe for ${provider}` }, 400);
  const body = await env.SETUP_KV.get(`secret:${provider}`);
  if (!body) return json({ ok: false, error: "no stored secret to probe" }, 400);
  const parsed = parseEnvBody(body);
  let result;
  try {
    result = await PROBES[provider](env, parsed);
  } catch (ex) {
    result = { ok: false, detail: `probe threw: ${(ex.message || String(ex)).slice(0, 200)}` };
  }
  // Update KV: on success flip status to verified
  const existing = (await env.SETUP_KV.get(`channel:${provider}`, "json")) || {};
  const state = {
    ...existing,
    status: result.ok ? "verified" : (existing.status === "not_started" ? "in_progress" : existing.status),
    last_probe_at: new Date().toISOString(),
    last_probe_ok: !!result.ok,
    last_probe_detail: result.detail || "",
  };
  await env.SETUP_KV.put(`channel:${provider}`, JSON.stringify(state));
  return json({ ok: !!result.ok, status: state.status, detail: result.detail, soft: !!result.soft, state });
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
    if (url.pathname === "/api/setup/probe") return handleProbe(request, env);
    if (url.pathname === "/api/secrets") return handleFetchSecrets(request, env);

    // OAuth wizard routes
    if (url.pathname === "/api/setup/oauth-app" && request.method === "POST") {
      return handleOauthAppSave(request, env);
    }
    if (url.pathname === "/api/setup/oauth-app" && request.method === "GET") {
      return handleOauthAppGet(request, env);
    }
    const oauthStart = url.pathname.match(/^\/oauth\/([a-z_]+)\/start$/);
    if (oauthStart) return handleOauthStart(request, env, oauthStart[1]);
    const oauthCb = url.pathname.match(/^\/oauth\/([a-z_]+)\/callback$/);
    if (oauthCb) return handleOauthCallback(request, env, oauthCb[1]);

    // Setup UI (auth-gated)
    if (url.pathname === "/setup" || url.pathname.startsWith("/setup/")) {
      return handleSetupUi(request, env);
    }

    // Everything else: serve the static asset (HTML, CSS, JS, images).
    return env.ASSETS.fetch(request);
  },
};
