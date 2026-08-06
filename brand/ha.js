/* Hey Aaron! — conversion spine. No dependencies.
   Order matters: DTR message-match runs BEFORE anything analytics-ish (rule 8/3). */
(function () {
  "use strict";
  var d = document, w = window;
  var reduce = w.matchMedia && w.matchMedia("(prefers-reduced-motion: reduce)").matches;
  d.documentElement.classList.add("js");

  /* -------- 1. DTR message match (rule 3): sanitize + textContent only -------- */
  (function dtr() {
    var p = new URLSearchParams(location.search);
    function clean(s) { return (s || "").replace(/[^\w \-,&']/g, "").trim().slice(0, 40); }
    var map = { trade: clean(p.get("trade")), city: clean(p.get("city")), region: clean(p.get("region")) };
    d.querySelectorAll("[data-dtr]").forEach(function (el) {
      var key = el.getAttribute("data-dtr");
      if (map[key]) el.textContent = map[key];        // sensible default stays otherwise
    });
    w.__dtr = map;
  })();

  /* -------- 8. tracking spine: capture click/utm ids once, attach to payloads ---- */
  var TRACK = (function () {
    var KEY = "ha_track";
    var stored = {};
    try { stored = JSON.parse(sessionStorage.getItem(KEY) || "{}"); } catch (e) {}
    var p = new URLSearchParams(location.search);
    ["gclid", "fbclid", "wbraid", "gbraid", "msclkid", "utm_source", "utm_medium",
     "utm_campaign", "utm_term", "utm_content"].forEach(function (k) {
      if (p.get(k)) stored[k] = p.get(k).slice(0, 200);
    });
    if (!stored.landing) stored.landing = location.pathname + location.search;
    if (!stored.first_seen) stored.first_seen = "" + Math.floor(Date.now() / 1000);
    stored.trade = w.__dtr && w.__dtr.trade || stored.trade || "";
    try { sessionStorage.setItem(KEY, JSON.stringify(stored)); } catch (e) {}
    return stored;
  })();

  /* -------- CTA location logging (rule 8): every data-cta-location click -------- */
  d.addEventListener("click", function (e) {
    var el = e.target.closest("[data-cta-location]");
    if (el && w.fbq) { try { fbq("trackCustom", "CTAClick", { location: el.getAttribute("data-cta-location") }); } catch (_) {} }
  });

  /* -------- mobile nav -------- */
  var toggle = d.querySelector(".nav-toggle");
  if (toggle) toggle.addEventListener("click", function () {
    var open = d.body.classList.toggle("m-open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
  d.querySelectorAll(".site-nav a").forEach(function (a) {
    a.addEventListener("click", function () { d.body.classList.remove("m-open"); });
  });

  /* -------- 1. sticky mobile call bar + floating desktop call, after 200px ------- */
  var bar = d.querySelector(".callbar"), floatc = d.querySelector(".floatcall");
  if (bar) d.body.classList.add("has-callbar");
  var shown = false;
  function onScroll() {
    var past = w.scrollY > 200;
    if (past === shown) return;
    shown = past;
    if (bar) bar.classList.toggle("show", past);
    if (floatc) floatc.classList.toggle("show", past);
  }
  w.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* -------- 4. honest availability line, staffed-hours aware (America/Chicago) --- */
  (function avail() {
    var el = d.querySelector("[data-avail]"); if (!el) return;
    var now = new Date();
    // Central time hour without pulling a tz lib
    var hr = parseInt(now.toLocaleString("en-US", { hour: "2-digit", hour12: false, timeZone: "America/Chicago" }), 10);
    var day = now.toLocaleString("en-US", { weekday: "short", timeZone: "America/Chicago" });
    var weekday = ["Mon", "Tue", "Wed", "Thu", "Fri"].indexOf(day) > -1;
    var openNow = weekday && hr >= 8 && hr < 18;
    el.querySelector("[data-avail-text]").textContent = openNow
      ? "Aaron's answering now."
      : "Leave a message and Aaron calls you back first thing, 8am Central.";
    var live = el.querySelector(".live");
    if (live && !openNow) live.style.background = "#c3c6d2";
  })();

  /* -------- reveals (failsafe) -------- */
  var rises = [].slice.call(d.querySelectorAll(".reveal"));
  function showAll() { rises.forEach(function (el) { el.classList.add("in"); }); }
  if (reduce || !("IntersectionObserver" in w)) showAll();
  else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
    rises.forEach(function (el) { io.observe(el); });
    setTimeout(showAll, 2600);
  }

  /* -------- 7. quiz qualifier -------- */
  var quiz = d.querySelector("[data-quiz]");
  if (quiz) {
    var steps = [].slice.call(quiz.querySelectorAll(".quiz-step"));
    var prog = [].slice.call(quiz.querySelectorAll(".quiz-prog i"));
    var state = { trade: "", need: "", phone: "" };
    var at = 0;
    function go(n) {
      at = n;
      steps.forEach(function (s, i) { s.classList.toggle("on", i === n); });
      prog.forEach(function (p, i) { p.classList.toggle("on", i <= n); });
      var focusable = steps[n].querySelector("button, input, a");
      if (focusable) focusable.focus({ preventScroll: true });
    }
    quiz.querySelectorAll("[data-q='trade'] .quiz-opt").forEach(function (b) {
      b.addEventListener("click", function () { state.trade = b.textContent.trim(); go(1); });
    });
    quiz.querySelectorAll("[data-q='need'] .quiz-opt").forEach(function (b) {
      b.addEventListener("click", function () { state.need = b.textContent.trim(); go(2); });
    });
    var submit = quiz.querySelector("[data-q-submit]");
    var err = quiz.querySelector(".quiz-err");
    if (submit) submit.addEventListener("click", function () {
      var phone = (quiz.querySelector("[data-q-phone]").value || "").trim();
      if (phone.replace(/\D/g, "").length < 10) { err.textContent = "Add a number Aaron can actually reach you at."; return; }
      err.textContent = ""; state.phone = phone;
      submit.disabled = true; submit.textContent = "Sending…";
      var payload = Object.assign({ _type: "quiz" }, state, { track: TRACK });
      fetch("/api/lead", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(function (r) { return r.json(); })
        .then(function () { go(3); if (w.fbq) fbq("track", "Lead"); })
        .catch(function () { go(3); })
        .finally(function () { submit.disabled = false; submit.textContent = "Get my callback"; });
    });
  }

  /* -------- 2. callback widget ("call me in 28 seconds") ------------------------- */
  var cbw = d.querySelector("[data-callback]");
  if (cbw) {
    var cform = cbw.querySelector("form");
    var cstatus = cbw.querySelector(".status");
    cform.addEventListener("submit", function (e) {
      e.preventDefault();
      var phone = (cform.querySelector("input[name=phone]").value || "").trim();
      if (phone.replace(/\D/g, "").length < 10) { cstatus.className = "status err"; cstatus.textContent = "That number looks short — mind checking it?"; return; }
      var btn = cform.querySelector("button"); btn.disabled = true; var t = btn.textContent; btn.textContent = "Calling…";
      fetch("/api/lead", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ _type: "callback", phone: phone, track: TRACK }) })
        .then(function (r) { return r.json(); })
        .then(function (dd) {
          cstatus.className = "status ok";
          cstatus.textContent = dd && dd.ok ? "Got it. Aaron will call you in about 28 seconds." : "Got it — Aaron will call you right back.";
          cform.reset(); if (w.fbq) fbq("track", "Lead");
        })
        .catch(function () { cstatus.className = "status err"; cstatus.textContent = "Couldn't send — just call 713-384-8985."; })
        .finally(function () { btn.disabled = false; btn.textContent = t; });
    });
  }

  /* -------- 9. exit intent: true desktop mouseleave at top, once per session ----- */
  (function exitIntent() {
    if (reduce) return;
    var modal = d.querySelector("[data-exit]"); if (!modal) return;
    var fine = w.matchMedia("(pointer:fine)").matches && w.innerWidth > 860;
    if (!fine) return;
    try { if (sessionStorage.getItem("ha_exit")) return; } catch (e) {}
    function open() {
      try { sessionStorage.setItem("ha_exit", "1"); } catch (e) {}
      modal.hidden = false; d.removeEventListener("mouseout", onOut);
      var c = modal.querySelector("[data-exit-close]"); if (c) c.focus();
    }
    function onOut(e) { if (!e.relatedTarget && e.clientY <= 0) open(); }
    d.addEventListener("mouseout", onOut);
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.closest("[data-exit-close]")) modal.hidden = true;
    });
    d.addEventListener("keydown", function (e) { if (e.key === "Escape") modal.hidden = true; });
  })();

  /* -------- "does your phone look like this?" — lock-screen lead feed ----------- */
  (function funnel() {
    var sec = d.querySelector("[data-funnel]"); if (!sec) return;
    var feed = sec.querySelector('[data-feed="phone"]');
    var elCount = sec.querySelector("[data-count]");
    var lock = sec.querySelector(".lock");
    if (!feed) return;
    function ico(id) { return '<svg><use href="#' + id + '"/></svg>'; }

    // one "day" of notifications — loops forever. kind sets icon + tint; lead:1 counts toward "new today".
    var C = [
      { kind: "text", lead: 1, ic: "i-msg", a: "New customer", b: "“Can you come look at my AC today?”" },
      { kind: "call", lead: 1, ic: "i-phone", a: "Missed call → auto-text sent", b: "“Thanks for calling! What do you need done?”" },
      { kind: "book", ic: "i-check", a: "Booked — AC install estimate", b: "Tomorrow · 8:30 AM · Livingston" },
      { kind: "text", lead: 1, ic: "i-msg", a: "New customer", b: "“How soon could you start on a re-roof?”" },
      { kind: "call", lead: 1, ic: "i-phone", a: "Missed call → auto-text sent", b: "“Sorry I missed you — text me your address?”" },
      { kind: "book", ic: "i-check", a: "Booked — panel upgrade", b: "Wed · 9:00 AM · Onalaska" },
      { kind: "text", lead: 1, ic: "i-msg", a: "New customer", b: "“Do you do weekends? Kitchen’s a mess.”" },
      { kind: "call", lead: 1, ic: "i-phone", a: "Missed call → auto-text sent", b: "“What’s going on and where are you at?”" },
      { kind: "book", ic: "i-check", a: "Booked — roof repair", b: "Thu · 11:00 AM · Huntsville" },
      { kind: "text", lead: 1, ic: "i-msg", a: "New customer", b: "“Neighbor said you fixed theirs — my turn?”" },
      { kind: "call", lead: 1, ic: "i-phone", a: "Missed call → auto-text sent", b: "“Happy to help — what day works for you?”" },
      { kind: "book", ic: "i-check", a: "Booked — panel + EV charger", b: "Mon · 8:00 AM · Coldspring" }
    ];

    var count = 0, idx = 0;
    function flash(el, cls) { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }

    // fixed-height stack: constant max, so the phone never resizes as notifications land.
    var MAX = 4;
    function trim() {
      if (feed.children.length > MAX) {
        var first = feed.firstElementChild; first.classList.add("out");
        (function (n) { setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, 360); })(first);
      }
    }
    function push(ev) {
      var li = d.createElement("li");
      li.className = "lock-note enter " + ev.kind;
      li.innerHTML = '<span class="ln-ic ' + ev.kind + '">' + ico(ev.ic) + '</span>' +
        '<div class="ln-b"><b>' + ev.a + '</b><span>' + ev.b + '</span></div><span class="ln-time">now</span>';
      feed.appendChild(li); trim();
    }

    function tick() {
      var ev = C[idx % C.length]; idx++;
      push(ev);
      if (lock) flash(lock, "buzz");
      if (ev.lead && elCount) { count++; elCount.textContent = count; flash(elCount, "pop"); }
      // end of a "day" -> quietly reset the counter so it stays believable, keep rolling
      if (idx % C.length === 0) {
        setTimeout(function () { count = 0; if (elCount) elCount.textContent = "0"; }, 700);
      }
    }

    // reduced motion / no observer: show a static, representative frame — no loop.
    if (reduce || !("IntersectionObserver" in w)) {
      if (elCount) elCount.textContent = "9";
      sec.classList.add("playing");
      return;
    }

    var timer = null;
    function start() { if (timer) return; sec.classList.add("playing"); tick(); timer = w.setInterval(tick, 1250); }
    function stop() { if (timer) { w.clearInterval(timer); timer = null; } }
    // in view now? (rect test — reliable even where IO callbacks are throttled)
    function inView() {
      var r = sec.getBoundingClientRect(), h = w.innerHeight || d.documentElement.clientHeight;
      return r.top < h * 0.75 && r.bottom > h * 0.25;
    }
    // primary: IntersectionObserver drives start/stop as it scrolls in and out.
    if ("IntersectionObserver" in w) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) start(); else stop(); });
      }, { threshold: 0.2 }).observe(sec);
    }
    // fallback: scroll/resize + first-paint check, so it never sits frozen if IO is late.
    function poke() { if (inView()) start(); }
    w.addEventListener("scroll", poke, { passive: true });
    w.addEventListener("resize", poke, { passive: true });
    requestAnimationFrame(function () { requestAnimationFrame(poke); });
  })();

  /* -------- lead-cost calculator ---------------------------------------------- */
  (function leadcost() {
    var root = d.querySelector("[data-lcalc]"); if (!root) return;
    var form = root.querySelector("form");
    var zipEl = root.querySelector("[data-lc-zip]");
    var tradeEl = root.querySelector("[data-lc-trade]");
    var goEl = root.querySelector("[data-lc-go]");
    var statusEl = root.querySelector("[data-lc-status]");
    var grid = root.querySelector("[data-lc-results]");
    var marketEl = root.querySelector("[data-lc-market]");
    var srcEl = root.querySelector("[data-lc-sources]");
    var methEl = root.querySelector("[data-lc-methodology]");
    function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }

    // national sample shown before the visitor runs their own (no API call on load)
    var SAMPLE = {
      tradeLabel: "HVAC", market: "national average", live: false, as_of: "2025", statsUrl: "/stats/",
      channels: [
        { key: "google_ads", label: "Google Ads", cpl: 128, unit: "per lead", tier: "firm", source: "LocaliQ 2025" },
        { key: "google_lsa", label: "Google LSA", cpl: 51, unit: "per lead", tier: "firm", source: "SearchLight 2026" },
        { key: "facebook", label: "Facebook Ads", cpl: 41, unit: "per lead", tier: "directional", source: "LocaliQ FB 2025" },
        { key: "organic", label: "Organic", cpl: 7, unit: "per lead", tier: "flat" }
      ],
      sources: [
        { label: "Google Ads — LocaliQ Home Services Search Benchmarks 2025", url: "https://localiq.com/blog/home-services-search-advertising-benchmarks/" },
        { label: "Google LSA — SearchLight Digital 2026", url: "https://searchlightdigital.io/google-local-service-ads-cost-per-lead/" },
        { label: "Facebook — LocaliQ Facebook Ad Benchmarks 2025", url: "https://localiq.com/blog/facebook-advertising-benchmarks/" }
      ],
      methodology: "Example figures for HVAC, national average. Enter your ZIP and trade to localize."
    };
    var TIERWORD = { firm: "Firm benchmark", directional: "Directional estimate", proxy: "Proxy — adjacent trade", na: "Not available", flat: "" };

    function tween(el, to) {
      if (reduce) { el.textContent = money(to); return; }
      var begin = null, dur = 750;
      function step(ts) { if (begin === null) begin = ts; var p = Math.min(1, (ts - begin) / dur), e = 1 - Math.pow(1 - p, 4);
        el.textContent = money(to * e); if (p < 1) requestAnimationFrame(step); }
      requestAnimationFrame(step);
    }

    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

    function render(data) {
      grid.innerHTML = "";
      data.channels.forEach(function (c) {
        var na = c.na || c.cpl == null;
        var isOrg = c.key === "organic";
        var card = d.createElement("div");
        card.className = "lc-card" + (na ? " na" : "");
        var tag = isOrg ? ""
          : na ? '<span class="lc-tag">Not offered</span>'
          : c.live ? '<span class="lc-tag live"><span class="ld"></span>Live</span>'
          : '<span class="lc-tag">Benchmark</span>';
        var big = na ? '<b class="lc-cpl">N/A</b>'
          : (c.cpl === 0 ? '<b class="lc-cpl">$0</b>' : '<b class="lc-cpl" data-to="' + c.cpl + '">$0</b>');
        var tier = (!isOrg && !na && c.tier && TIERWORD[c.tier]) ? '<span class="lc-tierline tier-' + esc(c.tier) + '">' + TIERWORD[c.tier] + '</span>' : "";
        card.innerHTML = tag + '<span class="lc-ch">' + esc(c.label) + '</span>' + big +
          '<span class="lc-unit">' + esc(c.unit) + '</span>' + tier;
        grid.appendChild(card);
      });
      grid.querySelectorAll("[data-to]").forEach(function (el) { tween(el, parseInt(el.getAttribute("data-to"), 10)); });
      marketEl.textContent = data.live ? ("Live · " + data.tradeLabel + " · " + data.market + " · " + data.as_of)
        : (data.market ? (data.tradeLabel + " · " + data.market + " · " + data.as_of) : "");
      // disclosure: this trade's per-channel tier + the primary sources + link to the full method
      var tierline = data.channels.filter(function (c) { return c.key !== "organic"; }).map(function (c) {
        return esc(c.label) + " — " + (c.na ? "N/A" : (TIERWORD[c.tier] || "benchmark")) + (c.source ? " (" + esc(c.source) + ")" : "");
      }).join(" · ");
      var links = (data.sources || []).map(function (s) { return '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) + '</a>'; }).join("");
      srcEl.innerHTML = '<p class="lc-tiers">' + tierline + '</p>' + links +
        '<a class="lc-statslink" href="' + esc(data.statsUrl || "/stats/") + '">Full per-trade table &amp; how I calculate this &rarr;</a>';
      methEl.textContent = data.methodology || "";
    }

    render(SAMPLE);

    function setStatus(msg, on) { if (!statusEl) return; statusEl.hidden = !on; statusEl.textContent = msg || ""; }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var zip = (zipEl.value || "").replace(/\D/g, "").slice(0, 5);
      var trade = tradeEl.value;
      if (zip.length !== 5) { setStatus("Enter a 5-digit ZIP.", true); zipEl.focus(); return; }
      setStatus("Pulling your market's numbers…", true); goEl.disabled = true; goEl.classList.add("loading");
      fetch("/api/lead-cost?zip=" + encodeURIComponent(zip) + "&trade=" + encodeURIComponent(trade))
        .then(function (r) { return r.json(); })
        .then(function (data) {
          goEl.disabled = false; goEl.classList.remove("loading");
          if (!data || !data.ok) { setStatus((data && data.error) || "Couldn't pull that one — try again.", true); return; }
          setStatus("", false); render(data);
        })
        .catch(function () { goEl.disabled = false; goEl.classList.remove("loading"); setStatus("Network hiccup — give it another go.", true); });
    });
  })();
})();
