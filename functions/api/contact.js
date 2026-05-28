// Cloudflare Pages Function — handles contact/lead form submissions and
// emails them via Resend. Route: POST /api/contact
//
// Required Cloudflare env vars (Pages > Settings > Environment variables):
//   RESEND_API_KEY  (secret)  — your Resend API key
// Optional (sensible defaults below):
//   CONTACT_TO      — where leads are delivered (default hello@aaron.chat)
//   CONTACT_FROM    — verified Resend sender (default forms@aaron.chat)
//
// NOTE: the CONTACT_FROM domain must be verified in Resend before delivery
// works. For a quick test before verifying aaron.chat, set
// CONTACT_FROM="Hey Aaron! <onboarding@resend.dev>" (only sends to the
// Resend account owner's address).

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

function clean(v, max) {
  return (v == null ? "" : String(v)).trim().slice(0, max);
}

export async function onRequestPost({ request, env }) {
  try {
    const ct = request.headers.get("content-type") || "";
    let d = {};
    if (ct.includes("application/json")) {
      d = await request.json();
    } else {
      const form = await request.formData();
      for (const [k, v] of form.entries()) d[k] = v;
    }

    // Honeypot — silently accept (so bots think they succeeded)
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

    if (!env.RESEND_API_KEY) {
      return json({ ok: false, error: "Email is not configured yet." }, 500);
    }

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
      return json({ ok: false, error: "We couldn't send your message. Please call 713-384-8985." }, 502);
    }

    return json({ ok: true });
  } catch (err) {
    console.log("contact function error", err && err.message);
    return json({ ok: false, error: "Something went wrong. Please call 713-384-8985." }, 500);
  }
}

// Reject non-POST methods cleanly
export async function onRequestGet() {
  return json({ ok: false, error: "Method not allowed" }, 405);
}
