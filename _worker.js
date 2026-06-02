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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/contact") {
      return handleContact(request, env);
    }
    // Everything else: serve the static asset (HTML, CSS, JS, images).
    return env.ASSETS.fetch(request);
  },
};
