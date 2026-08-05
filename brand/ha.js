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

  /* -------- funnel showpiece: continuous cinematic live feed -------------------- */
  (function funnel() {
    var sec = d.querySelector("[data-funnel]"); if (!sec) return;
    var phone = sec.querySelector('[data-feed="phone"]');
    var inbox = sec.querySelector('[data-feed="inbox"]');
    var elIn = sec.querySelector("[data-money-in]");
    var elOut = sec.querySelector("[data-money-out]");
    var elJobs = sec.querySelector("[data-jobs]");
    var elRoi = sec.querySelector("[data-roi]");
    var chart = sec.querySelector("[data-chart]");
    function fmt(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
    function ico(id) { return '<svg><use href="#' + id + '"/></svg>'; }

    // one "month" of events — loops forever. All action shows on the phone or in the inbox.
    // money:{k,amt} drives the dashboard stats only. in = revenue, out/ha = cost.
    var C = [
      { s: "phone", ic: "sms", a: "“Can you look at my AC today?”", b: "Livingston · just now" },
      { s: "inbox", kind: "lead", a: "New contact form", b: "“Need an AC install quote”", t: "now" },
      { s: "phone", ic: "mail", a: "Missed call → auto-text sent", b: "Onalaska · 2m" },
      { s: "inbox", kind: "ad", money: { k: "out", amt: 600 }, a: "Google Ads · receipt", b: "Campaign: AC installs", t: "now" },
      { s: "inbox", kind: "lead", a: "Google Ads lead", b: "Roof estimate request", t: "2m" },
      { s: "phone", booked: 1, ic: "ok", a: "Booked: panel upgrade", b: "Tue · 8:30 AM" },
      { s: "inbox", kind: "paid", money: { k: "in", amt: 5800 }, a: "Invoice #1042 paid", b: "+$5,800 · deposited today", t: "now" },
      { s: "inbox", kind: "lead", a: "Facebook lead form", b: "Kitchen remodel", t: "5m" },
      { s: "phone", ic: "sms", a: "“Need a plumber ASAP”", b: "Huntsville · text" },
      { s: "phone", booked: 1, ic: "ok", a: "Booked: kitchen remodel estimate", b: "Sat · 9:00 AM" },
      { s: "inbox", kind: "ad", money: { k: "out", amt: 400 }, a: "Facebook Ads · receipt", b: "Campaign: remodels", t: "6m" },
      { s: "inbox", kind: "lead", a: "New contact form", b: "“Gutters + fascia quote”", t: "8m" },
      { s: "phone", booked: 1, ic: "ok", a: "Booked: roof estimate", b: "Thu · 11:00 AM" },
      { s: "inbox", kind: "paid", money: { k: "in", amt: 6800 }, a: "Invoice #1043 paid", b: "+$6,800 · deposited today", t: "now" },
      { s: "phone", booked: 1, ic: "ok", a: "Booked: panel + EV charger", b: "Mon · 8:00 AM" },
      { s: "inbox", kind: "bill", money: { k: "ha", amt: 500 }, a: "Hey Aaron! · Website & Growth", b: "Your monthly bill · −$500", t: "1st" }
    ];

    var moneyIn = 0, moneyOut = 0, jobs = 0, idx = 0, tweens = {};

    // count-up that survives rapid re-fires (cancels the prior tween on the same element)
    function tween(el, key, from, to, dur, isInt) {
      var id = {}, begin = null;
      tweens[key] = id;
      function step(ts) {
        if (tweens[key] !== id) return;
        if (begin === null) begin = ts;
        var p = Math.min(1, (ts - begin) / dur), e = 1 - Math.pow(1 - p, 4), v = from + (to - from) * e;
        el.textContent = isInt ? Math.round(v) : fmt(v);
        if (p < 1) requestAnimationFrame(step); else tweens[key] = null;
      }
      requestAnimationFrame(step);
    }
    function flash(el, cls) { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }
    function setRoi() {
      var r = moneyOut > 0 ? moneyIn / moneyOut : 0;
      elRoi.textContent = "$" + (r >= 10 ? Math.round(r) : r.toFixed(1)) + " : $1";
    }

    // fixed-height feeds: max rows constant, so the boxes never resize as items stream.
    var MAX = 5;
    function trim(feed) {
      if (feed.children.length > MAX) {
        var first = feed.firstElementChild; first.classList.add("out");
        (function (n) { setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, 380); })(first);
      }
    }
    function pushPhone(ev) {
      var li = d.createElement("li");
      li.className = "fd-lead enter" + (ev.booked ? " booked" : "");
      li.innerHTML = '<span class="fd-ic ' + (ev.ic || "sms") + '">' + ico(ev.booked ? "i-check" : ev.ic === "mail" ? "i-phone" : "i-msg") + '</span><div><b>' + ev.a + '</b><span>' + ev.b + '</span></div>';
      phone.appendChild(li); trim(phone);
    }
    function pushInbox(ev) {
      var li = d.createElement("li");
      li.className = "ib-row enter" + (ev.kind ? " " + ev.kind : "") + (ev.booked ? " booked" : "");
      var badge = ev.kind === "paid" ? '<span class="ib-tag paid">PAID</span>'
        : ev.kind === "bill" ? '<span class="ib-tag bill">BILL</span>'
        : ev.kind === "ad" ? '<span class="ib-tag ad">ADS</span>' : '<span class="ib-unread"></span>';
      li.innerHTML = badge + '<div class="ib-em"><b>' + ev.a + (ev.booked ? " ✓" : "") + '</b><span>' + ev.b + '</span></div><span class="ib-time">' + (ev.t || "now") + '</span>';
      inbox.appendChild(li); trim(inbox);
    }
    function bookJob() { var j = jobs; jobs++; tween(elJobs, "jobs", j, jobs, 550, true); flash(elJobs, "pop"); }
    function pushBar(amt) {
      if (!chart) return;
      var b = d.createElement("span");
      b.className = "fbar"; b.style.setProperty("--h", Math.max(14, Math.min(100, Math.round(amt / 70))) + "%");
      chart.appendChild(b);
      if (chart.children.length > 16) chart.removeChild(chart.firstElementChild);
      void b.offsetWidth; b.classList.add("grow");
    }

    function tick() {
      var ev = C[idx % C.length]; idx++;
      if (ev.s === "phone") pushPhone(ev); else pushInbox(ev);
      if (ev.booked) bookJob();
      if (ev.money) {
        if (ev.money.k === "in") {
          var a = moneyIn; moneyIn += ev.money.amt; tween(elIn, "in", a, moneyIn, 900);
          flash(elIn, "flash-in"); flash(sec.querySelector(".fstat.in"), "hit"); pushBar(ev.money.amt);
        } else {
          var b = moneyOut; moneyOut += ev.money.amt; tween(elOut, "out", b, moneyOut, 800); flash(elOut, "flash-out");
        }
        setRoi();
      }
      // end of a month → brief reset, then keep rolling
      if (idx % C.length === 0) {
        setTimeout(function () {
          moneyIn = 0; moneyOut = 0; jobs = 0; tweens = {};
          elIn.textContent = fmt(0); elOut.textContent = fmt(0); elJobs.textContent = "0";
          elRoi.textContent = "$0 : $1";
          if (chart) chart.innerHTML = "";
          flash(sec.querySelector(".fdash"), "newmonth");
        }, 900);
      }
    }

    // reduced motion / no observer: show a static, representative frame — no loop.
    if (reduce || !("IntersectionObserver" in w)) {
      elIn && (elIn.textContent = fmt(12600)); elOut && (elOut.textContent = fmt(1500));
      elJobs && (elJobs.textContent = "7"); elRoi && (elRoi.textContent = "$8 : $1");
      sec.classList.add("playing");
      return;
    }

    var timer = null;
    function start() { if (timer) return; sec.classList.add("playing"); tick(); timer = w.setInterval(tick, 1150); }
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
})();
