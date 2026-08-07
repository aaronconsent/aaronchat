/* Growth-Plan dashboard — interactive "see how I make this better" model.
   Runs only on /plan/. Reads the trade's LIVE per-market numbers from /api/lead-cost,
   layers the sourced reference model (embedded in #plan-ref), and recomputes on every
   toggle/slider change. Every output is a PROJECTION, labeled as an illustration. */
(function () {
  "use strict";
  var d = document, w = window;
  var root = d.querySelector("[data-plan]"); if (!root) return;
  var reduce = w.matchMedia && w.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var REF = {};
  try { REF = JSON.parse(d.getElementById("plan-ref").textContent); } catch (e) { REF = {}; }

  // ---- read ?zip & ?trade ----
  var qs = new URLSearchParams(w.location.search);
  var zip = (qs.get("zip") || "").replace(/\D/g, "").slice(0, 5);
  var trade = (qs.get("trade") || "hvac").toLowerCase();

  // ---- national fallback CPLs/book (if the live call fails) ----
  var FALLBACK = {
    google_ads: { cpl: 130, bookRate: 0.30 }, google_lsa: { cpl: 53, bookRate: 0.44 },
    facebook: { cpl: 41, bookRate: 0.16 }, organic: { cpl: 7, bookRate: 0.05 }
  };
  var market = { tradeLabel: "your trade", market: "", live: false, ch: FALLBACK, blended: 0.30, socialLeads: 11, gbp: null, set: false };

  // ---- model coefficients (all documented in the on-page "how this is modeled") ----
  var reach = (REF.reach || {});
  function rper(k, def) { return (reach[k] && reach[k].impressions_per_dollar) || def; }
  function rmon(k, def) { return (reach[k] && reach[k].monthly_impressions) || def; }
  var REACH$ = { ads: rper("google_ads", 2.5), lsa: rper("lsa", 1), fb: rper("meta", 90) };
  var REACH_MON = { web: rmon("organic_web", 3000), gbp: rmon("gbp", 1400), social: rmon("organic_social", 1200) };
  var L = (REF.lifts || {});
  function lift(k, field, def) { return (L[k] && L[k][field]) || def; }
  var FAST = lift("speed_to_lead", "booking_multiplier", 1.8);
  var REVIEWS = 1 + lift("reviews", "conversion_lift_pct", 25) / 100;
  var CRO = 1 + lift("website_cro", "conversion_lift_pct", 20) / 100;
  var GBP_LIFT = lift("gbp", "lead_lift_pct", 30) / 100;
  var MULTI_LIFT = lift("multichannel", "lead_lift_pct", 40) / 100;
  var EMAIL = 1 + lift("email_repeat", "revenue_lift_pct", 15) / 100;
  var mix = REF.budget_mix || { search: 0.30, lsa: 0.20, social: 0.12 };

  // combine lifts with an overlap discount (never stack straight through), cap the multiplier
  function combine(mults, cap) {
    var extra = 0; for (var i = 0; i < mults.length; i++) extra += (mults[i] - 1);
    return Math.min(cap, 1 + 0.6 * extra);
  }

  // ---- services (toggles) ----
  var SERVICES = [
    { id: "web", label: "Website & local SEO", group: "Website & Growth", kind: "owned", on: true, locked: true },
    { id: "gbp", label: "Google Business Profile", group: "Website & Growth", kind: "owned", on: false },
    { id: "reviews", label: "Review Autopilot", group: "Website & Growth", kind: "lift", on: false },
    { id: "resolve", label: "Missed-Visitor Leads", group: "Website & Growth", kind: "owned", on: false },
    { id: "newsletter", label: "Weekly Newsletter", group: "Website & Growth", kind: "owned", on: false },
    { id: "social", label: "Managed Content & Posting", group: "Social Media", kind: "owned", on: false },
    { id: "ads", label: "Google Ads", group: "Paid ads", kind: "paid", on: false },
    { id: "lsa", label: "Google LSA", group: "Paid ads", kind: "paid", on: false },
    { id: "fb", label: "Facebook / Instagram ads", group: "Paid ads", kind: "paid", on: false }
  ];
  var state = { budget: 0, on: {} };
  SERVICES.forEach(function (s) { state.on[s.id] = s.on; });

  // ---- the model ----
  function compute() {
    var on = state.on, ch = market.ch, adSpend = state.budget;
    var paid = [];
    if (on.ads) paid.push({ k: "ads", ck: "google_ads", w: mix.search });
    if (on.lsa) paid.push({ k: "lsa", ck: "google_lsa", w: mix.lsa });
    if (on.fb) paid.push({ k: "fb", ck: "facebook", w: mix.social });
    var wsum = paid.reduce(function (a, p) { return a + p.w; }, 0) || 1;

    // lift multipliers depend only on toggles. Quality lifts (reviews, CRO) raise the BOOKING rate;
    // volume lifts (GBP, multichannel) raise LEAD count. Both overlap-discounted + capped.
    var qualExtra = (on.reviews ? (REVIEWS - 1) : 0) + (on.web ? (CRO - 1) : 0);
    var bookMult = Math.min(1.6, 1 + 0.45 * qualExtra);
    var isMulti = (paid.length + (on.web ? 1 : 0) + (on.social ? 1 : 0)) >= 3;
    var volExtra = (isMulti ? MULTI_LIFT : 0);  // GBP is no longer a flat lift — it's a predicted leads channel below
    var leadMult = Math.min(1.35, 1 + 0.40 * volExtra);
    var BOOK_CEIL = 0.60;  // no channel books above 60%, even fully optimized — keeps it honest
    function effBook(br) { return Math.min(BOOK_CEIL, br * bookMult); }

    var AD_LABEL = { ads: ["Google Ads", "Google"], lsa: ["Google LSA", "Google"], fb: ["Facebook / Instagram ads", "Meta"] };
    var rows = [], adLines = [], leads = 0, booked = 0, eyeballs = 0, siteVisitors = 0;
    paid.forEach(function (p) {
      var spend = adSpend * (p.w / wsum);
      if (spend >= 1) adLines.push({ label: AD_LABEL[p.k][0], dest: AD_LABEL[p.k][1], amt: spend });
      var cpl = (ch[p.ck] && ch[p.ck].cpl) || FALLBACK[p.ck].cpl;
      var br = (ch[p.ck] && ch[p.ck].bookRate) || FALLBACK[p.ck].bookRate;
      var ld = spend / cpl, bk = ld * effBook(br), eye = spend * (REACH$[p.k] || 1);
      leads += ld; booked += bk; eyeballs += eye; siteVisitors += ld / 0.10; // ~10% of clicks become leads
      rows.push({ label: labelFor(p.ck), leads: ld, spend: spend, eyeballs: eye, booked: bk });
    });

    // owned channels
    if (on.web) { eyeballs += REACH_MON.web; var owl = 6, owb = owl * effBook(market.blended || 0.30); leads += owl; booked += owb; siteVisitors += 250; rows.push({ label: "Website / SEO (organic)", leads: owl, spend: 0, eyeballs: REACH_MON.web, booked: owb }); } // books at THIS trade's inbound rate — tailored per lookup
    var gbpLeads = 0, gbpBooked = 0;
    if (on.gbp) {
      eyeballs += REACH_MON.gbp;
      var gbpPot = (market.gbp && market.gbp.potential) ? market.gbp.potential : 8;  // live local-pack prediction; 8 fallback if Maps unavailable
      gbpLeads = gbpPot * (on.reviews ? 1 : 0.55);   // you can't hold Maps rank without review velocity
      gbpBooked = gbpLeads * effBook(market.blended || 0.30);
      rows.push({ label: "Google Business Profile", leads: gbpLeads, spend: 0, eyeballs: REACH_MON.gbp, booked: gbpBooked });
    }
    var socialLeads = 0, socialBooked = 0;
    if (on.social) {
      var socEye = 8000;                                       // 500-700 posts/mo + 3 reels/day drives real reach
      socialLeads = market.socialLeads || 11;                  // ~10-12/mo, weighted by this trade's social affinity
      socialBooked = socialLeads * effBook(market.blended || 0.30);  // inbound — books at the trade's blended rate
      eyeballs += socEye;
      rows.push({ label: "Managed Content & Posting", leads: socialLeads, spend: 0, eyeballs: socEye, booked: socialBooked });
    }

    // volume lift scales the paid+organic side (more calls in) — applied to leads AND their booked jobs
    var totalLeads = leads * leadMult;
    var bookedJobs = booked * leadMult;

    // resolved anonymous visitors ride on top: cheap, low-booking, NOT amplified by the lifts
    var resolved = 0, resolvedBooked = 0, resolveCost = 0;
    if (on.resolve && (on.web || paid.length)) {
      resolved = Math.round(0.12 * siteVisitors);           // ~12% of anonymous traffic identified
      resolvedBooked = resolved * 0.05;                     // resolved visitors book low (~1 in 20)
      resolveCost = resolved * 7;                           // real money — $7/resolved visitor
      totalLeads += resolved; bookedJobs += resolvedBooked;
      rows.push({ label: "Missed-Visitor Leads", leads: resolved, spend: resolveCost, eyeballs: 0, booked: resolvedBooked });
    }
    // GBP + social leads ride on top too — they're their own channels, not amplified by the lead lift
    totalLeads += socialLeads + gbpLeads; bookedJobs += socialBooked + gbpBooked;

    // Weekly Newsletter (part of Website & Growth — no extra fee). List starts at 1,000 and grows
    // each month by the leads that email or get resolved; at ~12 months that compounds. Weekly sends
    // → opens → clicks → warm inbound leads (repeat/referral), booked at the trade's inbound rate.
    var nlLeads = 0, nlBooked = 0, nlList = 0;
    if (on.newsletter) {
      var monthlyAdds = Math.round(0.6 * totalLeads);        // ~60% of leads give an email / are resolved
      nlList = 1000 + 12 * monthlyAdds;                      // base 1,000 + ~12 months of growth
      var sends = nlList * 4;                                // weekly
      var opens = sends * 0.35;                              // ~35% open rate (home-services email)
      var clicks = sends * 0.025;                            // ~2.5% click-through of sends
      nlLeads = clicks * 0.05;                               // ~5% of clickers inquire (warm list)
      nlBooked = nlLeads * effBook(market.blended || 0.30);  // warm/repeat → books at the trade's inbound rate
      totalLeads += nlLeads; bookedJobs += nlBooked; eyeballs += Math.round(opens);
      rows.push({ label: "Weekly Newsletter", leads: nlLeads, spend: 0, eyeballs: Math.round(opens), booked: nlBooked });
    }
    totalLeads = Math.round(totalLeads);

    // budget: ad spend + resolution spend + Aaron's fee (fully transparent)
    var fee = [];
    var ownedOn = on.web || on.gbp || on.reviews || on.resolve;  // web is locked on, so this is always true
    if (ownedOn) fee.push({ label: "Website & Growth", amt: 500 });
    if (on.social) fee.push({ label: "Social Media", amt: 500 });
    if (paid.length && adSpend > 0) fee.push({ label: "Ad management (15% of ad spend)", amt: Math.round(adSpend * 0.15) });
    var feeTotal = fee.reduce(function (a, f) { return a + f.amt; }, 0);
    var totalSpend = adSpend + resolveCost + feeTotal;
    var cpbj = bookedJobs > 0 ? totalSpend / bookedJobs : 0;

    // "autopilot" anchor: one expensive channel, no lifts — straight off the rate board (Google Ads cost per booked job)
    var anchorCh = ch.google_ads || FALLBACK.google_ads;
    var anchorCpbj = (anchorCh.cpl && anchorCh.bookRate) ? anchorCh.cpl / anchorCh.bookRate : 0;

    return {
      adSpend: adSpend, resolveCost: resolveCost, fee: fee, feeTotal: feeTotal, adLines: adLines, totalSpend: totalSpend, anchorCpbj: anchorCpbj,
      leads: Math.round(totalLeads), bookedJobs: bookedJobs, cpbj: cpbj, eyeballs: Math.round(eyeballs),
      rows: rows.sort(function (a, b) { return b.eyeballs + b.leads * 500 - (a.eyeballs + a.leads * 500); })
    };
  }
  function labelFor(ck) { return ({ google_ads: "Google Ads", google_lsa: "Google LSA", facebook: "Facebook ads" })[ck] || ck; }

  // ---- rendering ----
  var $ = function (s) { return root.querySelector(s); };
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function big(n) { return n >= 1000 ? "$" + (Math.round(n / 100) / 10).toLocaleString("en-US") + "k" : "$" + Math.round(n).toLocaleString("en-US"); }
  function num(n) { return Math.round(n).toLocaleString("en-US"); }

  var tweens = {};
  function tween(el, to, fmt, key) {
    if (!el) return;
    // reduced-motion, or a hidden/background tab (rAF is paused there) → set the final value outright
    if (reduce || d.hidden) { el.textContent = fmt(to); el.setAttribute("data-v", to); return; }
    var from = parseFloat(el.getAttribute("data-v") || "0"), begin = null, id = {}; tweens[key] = id;
    function step(ts) { if (tweens[key] !== id) return; if (begin === null) begin = ts;
      var p = Math.min(1, (ts - begin) / 550), e = 1 - Math.pow(1 - p, 4), v = from + (to - from) * e;
      el.textContent = fmt(v); if (p < 1) requestAnimationFrame(step); else { el.textContent = fmt(to); el.setAttribute("data-v", to); } }
    requestAnimationFrame(step);
  }

  function setDash() {
    ["[data-o-cpbj]", "[data-o-jobs]", "[data-o-leads]", "[data-o-eyeballs]", "[data-o-pay]", "[data-o-getn]"].forEach(function (s) {
      var el = $(s); if (el) { el.textContent = "—"; el.removeAttribute("data-v"); }
    });
    var a = $("[data-o-anchor]"); if (a) a.hidden = true;
    ["[data-o-pay-rows]", "[data-o-get-rows]"].forEach(function (s) { var el = $(s); if (el) el.innerHTML = ""; });
    var cb = $("[data-o-channels]"); if (cb) cb.innerHTML = "";
  }

  function render() {
    var awaitEl = $("[data-plan-await]");
    if (!market.set) { if (awaitEl) awaitEl.hidden = loading; setDash(); return; }
    if (awaitEl) awaitEl.hidden = true;
    var r = compute();
    var anchorWrap = $("[data-o-anchor]");
    if (anchorWrap) anchorWrap.hidden = false;  // static "Real Stats, Real Results" note — shown whenever a market is set
    tween($("[data-o-jobs]"), r.bookedJobs, function (v) { return (Math.round(v * 10) / 10).toLocaleString("en-US"); }, "jobs");
    tween($("[data-o-cpbj]"), r.cpbj, money, "cpbj");
    tween($("[data-o-leads]"), r.leads, num, "leads");
    tween($("[data-o-eyeballs]"), r.eyeballs, num, "eye");
    function feerow(label, val) { return '<div class="pl-feerow"><span>' + label + '</span><b>' + val + '</b></div>'; }
    // "What you pay" — everything: my fees, ad spend per channel, and resolution
    var payRows = [];
    r.fee.forEach(function (f) { payRows.push(feerow(f.label + ' <span class="pl-fee-dest">&rarr; me</span>', money(f.amt))); });
    r.adLines.forEach(function (a) { payRows.push(feerow(a.label + ' <span class="pl-fee-dest">&rarr; ' + a.dest + '</span>', money(a.amt))); });
    if (r.resolveCost > 0) payRows.push(feerow('Missed-Visitor Leads <b>$7 &times; resolved</b>', money(r.resolveCost)));
    var payEl = $("[data-o-pay-rows]"); if (payEl) payEl.innerHTML = payRows.join("");
    tween($("[data-o-pay]"), r.totalSpend, money, "pay");
    // "What you get" — leads per source (biggest first)
    var getRows = r.rows.filter(function (x) { return Math.round(x.leads) >= 1; }).sort(function (a, b) { return b.leads - a.leads; });
    var getEl = $("[data-o-get-rows]");
    if (getEl) getEl.innerHTML = getRows.map(function (x) { return feerow(x.label, Math.round(x.leads).toLocaleString("en-US")); }).join("");
    tween($("[data-o-getn]"), r.leads, function (v) { return Math.round(v).toLocaleString("en-US") + " leads"; }, "getn");
    // channel breakdown bars (by eyeballs)
    var maxEye = Math.max.apply(null, r.rows.map(function (x) { return x.eyeballs; }).concat([1]));
    var cb = $("[data-o-channels]");
    if (cb) cb.innerHTML = r.rows.map(function (x) {
      var pct = Math.max(2, Math.round(x.eyeballs / maxEye * 100));
      return '<div class="pl-chrow"><span class="pl-chname">' + x.label + '</span>' +
        '<span class="pl-chbar"><i style="width:' + pct + '%"></i></span>' +
        '<span class="pl-chval">' + num(x.eyeballs) + ' seen &middot; ' + (x.leads >= 1 ? Math.round(x.leads) + ' leads' : '&mdash;') + '</span></div>';
    }).join("");
  }

  // ---- build controls ----
  function buildControls() {
    var wrap = $("[data-plan-toggles]"); if (!wrap) return;
    var groups = {};
    SERVICES.forEach(function (s) { (groups[s.group] = groups[s.group] || []).push(s); });
    wrap.innerHTML = Object.keys(groups).map(function (g) {
      return '<div class="plan-tgroup"><h4>' + g + '</h4>' + groups[g].map(function (s) {
        return '<label class="plan-toggle' + (s.locked ? " locked" : "") + '"><input type="checkbox" data-svc="' + s.id + '"' +
          (state.on[s.id] ? " checked" : "") + (s.locked ? " disabled" : "") + '>' +
          '<span class="plan-sw"></span><span class="plan-tlabel">' + s.label +
          (s.locked ? ' <span class="plan-lock">always on</span>' : '') + '</span></label>';
      }).join("") + '</div>';
    }).join("");
    wrap.querySelectorAll("[data-svc]:not([disabled])").forEach(function (cb) {
      cb.addEventListener("change", function () { state.on[cb.getAttribute("data-svc")] = cb.checked; render(); });
    });
  }
  function wireBudget() {
    var sl = $("[data-plan-budget]"), out = $("[data-plan-budgetval]");
    if (!sl) return;
    sl.value = state.budget;
    function upd() { state.budget = parseInt(sl.value, 10); if (out) out.textContent = money(state.budget); render(); }
    sl.addEventListener("input", upd); upd();
  }

  // ---- init ----
  function setSubtitle() {
    var st = d.querySelector("[data-plan-sub]"), ms = $("[data-plan-marketsub]");  // hero sub lives outside [data-plan]
    if (st) st.textContent = !market.set ? "your trade"
      : market.tradeLabel + (market.market ? " · " + market.market : "") + (market.live ? " · live rates" : " · national avg");
    if (ms) ms.textContent = !market.set ? "not set yet"
      : market.tradeLabel + (market.market ? " · " + market.market : "");
  }

  var mForm = $("[data-plan-market] form"), mStatus = $("[data-gate-status]"), mBar = $("[data-plan-bar]");
  var mZip = mForm && mForm.querySelector("[name=zip]"), mTrade = mForm && mForm.querySelector("[name=trade]");

  var loading = false;
  // fetch a market and recompute (used on load with URL params AND on sidebar submit)
  function runMarket(z, t, focusOnFail) {
    loading = true;
    if (mBar) mBar.hidden = false;
    if (mStatus) mStatus.hidden = true;
    var go = $("[data-plan-marketgo]"); if (go) go.disabled = true;
    if (!market.set) render();  // hide the await note while we load
    return fetch("/api/lead-cost?zip=" + encodeURIComponent(z) + "&trade=" + encodeURIComponent(t))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        loading = false;
        if (mBar) mBar.hidden = true;
        if (go) go.disabled = false;
        if (data && data.ok) {
          var ch = {}; data.channels.forEach(function (c) { ch[c.key] = { cpl: c.cpl, bookRate: c.bookRate }; });
          market = { tradeLabel: data.tradeLabel, market: data.market, live: data.live, ch: ch, blended: data.blended || 0.30, socialLeads: data.socialLeads || 11, gbp: data.gbp || null, set: true };
          zip = z; trade = t;
          if (mStatus) mStatus.hidden = true;
          if (w.history && w.history.replaceState) w.history.replaceState(null, "", "/plan/?zip=" + encodeURIComponent(z) + "&trade=" + encodeURIComponent(t));
          setSubtitle(); render();
        } else if (mStatus) { mStatus.hidden = false; mStatus.textContent = (data && data.error) || "Couldn't pull that one — try again."; }
      })
      .catch(function () { loading = false; if (mBar) mBar.hidden = true; if (go) go.disabled = false; render(); if (mStatus) { mStatus.hidden = false; mStatus.textContent = "Network hiccup — give it another go."; } });
  }

  buildControls(); wireBudget();

  if (mForm) mForm.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var z = (mZip.value || "").replace(/\D/g, "").slice(0, 5), t = mTrade.value;
    if (z.length !== 5) { if (mStatus) { mStatus.hidden = false; mStatus.textContent = "Enter a 5-digit ZIP."; } mZip.focus(); return; }
    runMarket(z, t, true);
  });

  // load: if we arrived with a market (e.g. from the home-page rate board), pre-fill and calculate
  // straight away — no form step. Otherwise sit in the await state until they run one here.
  if (/^\d{5}$/.test(zip)) {
    if (mZip) mZip.value = zip;
    if (mTrade) mTrade.value = trade;
    setSubtitle(); render();          // await/dashes until the fetch lands
    runMarket(zip, trade, false);
  } else {
    setSubtitle(); render();          // await state
    if (mZip) try { mZip.focus(); } catch (e) {}
  }
})();
