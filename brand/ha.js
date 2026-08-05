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

  /* -------- funnel showpiece: count-up + play trigger ---------------------------- */
  (function funnel() {
    var sec = d.querySelector("[data-funnel]"); if (!sec) return;
    function fmt(n, prefix) { return (prefix || "") + Math.round(n).toLocaleString("en-US"); }
    var played = false;
    function play() {
      if (played) return; played = true;
      sec.classList.add("playing");           // triggers CSS entrances + bar fill
      if (reduce) return;                      // reduced motion: leave final numbers as-is
      sec.querySelectorAll("[data-count-to]").forEach(function (el) {
        var to = parseFloat(el.getAttribute("data-count-to"));
        var prefix = el.getAttribute("data-prefix") || "";
        var dur = 1650, start = null;
        el.textContent = fmt(0, prefix);
        function step(ts) {
          if (start === null) start = ts;
          var p = Math.min(1, (ts - start) / dur);
          var eased = 1 - Math.pow(1 - p, 3);  // ease-out cubic
          el.textContent = fmt(to * eased, prefix);
          if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(to, prefix);
        }
        requestAnimationFrame(step);
      });
    }
    if (reduce || !("IntersectionObserver" in w)) { play(); return; }
    var io2 = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { play(); io2.disconnect(); } });
    }, { threshold: 0.35 });
    io2.observe(sec);
  })();
})();
