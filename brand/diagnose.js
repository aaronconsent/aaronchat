/* Top of Class Marketing — report-card diagnose flow (the key conversion).
   4 steps: look up the shop (with live autocomplete) → show its FULL report card
   inline (no leaving the site) → book Aaron → offer a free Claude-built preview. */
(function () {
  "use strict";
  var root = document.getElementById("diag");
  if (!root) return;

  var state = { q: "", card: null, slug: "", domain: "", grade: "", city: "", rankStr: "", business: "", when: "", name: "", phone: "", email: "", build: null };
  var $ = function (s, r) { return (r || root).querySelector(s); };
  var steps = root.querySelectorAll(".diag-step");
  var bars = root.querySelectorAll(".diag-prog span");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function show(n) {
    steps.forEach(function (el) { el.hidden = el.getAttribute("data-s") !== String(n); });
    bars.forEach(function (b, i) { b.classList.toggle("on", i < Math.min(n, 4)); });
    root.setAttribute("data-step", n);
    var focusable = $(".diag-step[data-s='" + n + "'] input, .diag-step[data-s='" + n + "'] button");
    if (focusable && n > 1) { try { focusable.focus({ preventScroll: true }); } catch (e) { try { focusable.focus(); } catch (e2) {} } }
  }
  function err(el, msg) { el.textContent = msg; el.hidden = !msg; }
  function gradeClass(g) {
    var c = (g || "").charAt(0).toUpperCase();
    if (c === "A") return "g-a"; if (c === "B") return "g-b"; if (c === "C") return "g-c"; return "g-f";
  }
  function verdict(g) {
    var c = (g || "").charAt(0).toUpperCase();
    if (c === "A") return "You're already near the top of the class — now we protect the lead and pull further ahead.";
    if (c === "B") return "Solid, but there's clear daylight between you and #1. That gap is winnable.";
    if (c === "C") return "Middle of the pack — which means a focused few weeks can move you up fast.";
    return "There's a lot of easy ground to gain here. Good news: that's the fastest kind to win.";
  }

  /* the four headline deliverables of the entry plan — these mirror the
     "Enrolled" bullets on /pricing/; keep the two in sync. */
  var FEATS = [
    ["Your website, handled", "Built, hosted and secured — unlimited updates, never a change fee"],
    ["Social + blog on autopilot", "3 channels posted for you, plus fresh ranking content every week"],
    ["Found on Google &amp; in AI answers", "Your Google profile managed, SEO + AI Engine Optimization for ChatGPT and AI Overviews"],
    ["1,000 outreach emails a month", "Automated — plus your monthly report card: your grade, your rank, your rivals"]
  ];

  /* ---- outcome dashboard (full card + action steps get emailed) ---- */
  function renderCard(d) {
    var wrap = $("#diag-card");
    if (!d.found) {
      wrap.innerHTML =
        '<div class="dash notfound"><div class="dash-head">' +
          '<div class="rc-grade g-f"><span>?</span></div>' +
          '<div class="dash-id"><p class="rc-when">Not in this week’s index</p><h3>We couldn’t find you.</h3></div></div>' +
          '<p class="fomo-magnet">That usually means you’re hard to find online — exactly what’s costing you jobs. Aaron will grade you by hand and send it over. Where do we reach you?</p></div>';
      return;
    }
    var g = d.grade, rk = d.rk, f = d.fomo || {};
    var rankTxt = rk ? ("#" + rk[0] + " of " + rk[1] + " " + rk[2] + " around the lake") : "";
    var rankHtml = rankTxt
      ? (f.trslug
          ? '<a class="dash-rank" href="/report-card/' + f.trslug + "/?you=" + encodeURIComponent(d.slug) + '" target="_blank" rel="noopener">' + esc(rankTxt) + " ↗</a>"
          : '<span class="dash-rank">' + esc(rankTxt) + "</span>")
      : "";
    var H = '<div class="dash-head"><div class="rc-grade ' + gradeClass(g) + '"><span>' + esc(g) + "</span></div>" +
      '<div class="dash-id"><p class="rc-when">Your grade' + (d.city ? " · " + esc(d.city) : "") + '</p><h3>' + esc(d.name) + "</h3>" + rankHtml + "</div></div>";

    H += '<p class="dash-lbl">Work with us — here’s what changes</p><div class="dash-tiles">' +
      '<div class="dt" style="--dly:0ms"><span class="dt-big">1/100<sup>th</sup></span>' +
        '<span class="dt-vs"><b class="dt-n" data-to="299" data-money="1">$0</b><i>vs</i><s class="dt-n" data-to="30000" data-money="1">$0</s></span>' +
        '<span class="dt-sub">the cost of a serious online presence — an AI stack does the work of a whole agency</span></div>' +
      '<div class="dt" style="--dly:120ms"><span class="dt-big"><span class="dt-n" data-to="16" data-suffix="×">0×</span> faster</span>' +
        '<span class="dt-chip">Build in 3 days</span>' +
        '<span class="dt-sub">to build, update and get you seen</span></div>' +
      '<div class="dt" style="--dly:240ms"><span class="dt-big"><span class="dt-n" data-to="100" data-suffix="%">0%</span> Automated</span>' +
        '<span class="dt-sub">website, social, email outreach &amp; brand voice — one well-oiled machine with your personal touch</span></div>' +
      "</div>";

    H += '<p class="dash-lbl">Everything in the $299/mo plan</p><div class="dash-feats">';
    for (var i = 0; i < FEATS.length; i++) {
      H += '<div class="df" style="--dly:' + (380 + i * 90) + 'ms"><span class="df-t">' + FEATS[i][0] +
        '</span><span class="df-s">' + FEATS[i][1] + "</span></div>";
    }
    H += "</div>";
    H += '<p class="fomo-magnet">Your full report card + the exact plan to get there is ready. Where do we send it?</p>';
    wrap.innerHTML = '<div class="dash">' + H + "</div>";
    animateDash(wrap.querySelector(".dash"));
  }

  /* ---- stat animation: staggered tile reveal + count-up figures ---- */
  function animateDash(root) {
    if (!root) return;
    // rAF is throttled to zero in a backgrounded tab, so every step is also
    // driven/finalised by a setTimeout — the stats can never be left at $0.
    var reduce = (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) ||
      document.visibilityState === "hidden";
    setTimeout(function () { root.classList.add("is-in"); }, 20);
    Array.prototype.forEach.call(root.querySelectorAll(".dt-n"), function (el, i) {
      var to = Number(el.getAttribute("data-to")) || 0;
      var money = el.getAttribute("data-money") === "1";
      var suf = el.getAttribute("data-suffix") || "";
      function fmt(v) { return (money ? "$" + v.toLocaleString() : String(v)) + suf; }
      function done() { el.textContent = fmt(to); }
      if (reduce) { done(); return; }
      el.textContent = fmt(0);
      var t0 = null, dur = 950, delay = 320 + i * 130, raf = window.requestAnimationFrame;
      setTimeout(function () {
        if (!raf) return done();
        raf(function tick(ts) {
          if (t0 === null) t0 = ts;
          var p = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(Math.round(to * e));
          if (p < 1) raf(tick);
        });
      }, delay);
      setTimeout(done, delay + dur + 400); // failsafe: snap to the real number
    });
  }

  /* ---- lookup (used by form submit + autocomplete pick) ---- */
  var lookupForm = $(".diag-lookup");
  var qInput = $("#diag-q");
  function runLookup(payload) {
    var e1 = $(".diag-step[data-s='1'] .diag-err");
    err(e1, "");
    var btn = lookupForm.querySelector("button");
    btn.disabled = true; var t = btn.textContent; btn.textContent = "Grading…";
    fetch("/api/lookup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        state.card = d;
        if (d.found) {
          state.business = d.name; state.grade = d.grade; state.city = d.city;
          state.slug = d.slug; state.domain = d.domain || "";
          state.rankStr = d.rk ? ("#" + d.rk[0] + " of " + d.rk[1] + " " + d.rk[2]) : "";
        } else { state.business = payload.q || state.q; state.slug = ""; state.rankStr = ""; }
        renderCard(d); show(2);
      })
      .catch(function () { err(e1, "Something hiccuped — try again, or just book a call below."); })
      .finally(function () { btn.disabled = false; btn.textContent = t; });
  }
  lookupForm.addEventListener("submit", function (e) {
    e.preventDefault();
    closeSug();
    var q = qInput.value.trim();
    if (!q) { err($(".diag-step[data-s='1'] .diag-err"), "Type your website or business name."); return; }
    state.q = q; runLookup({ q: q });
  });

  /* ---- autocomplete: a live sneak-preview of matching shops + their grade ---- */
  var sug = document.createElement("div");
  sug.className = "diag-suggest"; sug.hidden = true;
  lookupForm.appendChild(sug);
  var sugItems = [], sugIdx = -1, sugTimer = null;
  function closeSug() { sug.hidden = true; sug.innerHTML = ""; sugItems = []; sugIdx = -1; }
  function hl() { sug.querySelectorAll(".sug-item").forEach(function (b, i) { b.classList.toggle("on", i === sugIdx); }); }
  function pick(it) { if (!it) return; qInput.value = it.name; state.q = it.name; closeSug(); runLookup({ slug: it.slug }); }
  function renderSug(items) {
    sugItems = items; sugIdx = -1;
    if (!items.length) { closeSug(); return; }
    sug.innerHTML = items.map(function (it, i) {
      return '<button type="button" class="sug-item" data-i="' + i + '">' +
        '<span class="sug-grade ' + gradeClass(it.grade) + '">' + esc(it.grade) + "</span>" +
        '<span class="sug-name">' + esc(it.name) + "</span>" +
        '<span class="sug-city">' + esc(it.city || "") + "</span></button>";
    }).join("");
    sug.hidden = false;
  }
  qInput.addEventListener("input", function () {
    var q = qInput.value.trim();
    clearTimeout(sugTimer);
    if (q.length < 2) { closeSug(); return; }
    sugTimer = setTimeout(function () {
      fetch("/api/suggest?q=" + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(function (d) { if (qInput.value.trim().length >= 2) renderSug(d.items || []); })
        .catch(function () {});
    }, 160);
  });
  qInput.addEventListener("keydown", function (e) {
    if (sug.hidden) return;
    if (e.key === "ArrowDown") { e.preventDefault(); sugIdx = Math.min(sugIdx + 1, sugItems.length - 1); hl(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); sugIdx = Math.max(sugIdx - 1, 0); hl(); }
    else if (e.key === "Enter") { if (sugIdx >= 0) { e.preventDefault(); pick(sugItems[sugIdx]); } }
    else if (e.key === "Escape") { closeSug(); }
  });
  sug.addEventListener("mousedown", function (e) {
    var b = e.target.closest(".sug-item"); if (!b) return;
    e.preventDefault(); pick(sugItems[Number(b.getAttribute("data-i"))]);
  });
  document.addEventListener("click", function (e) {
    if (!sug.contains(e.target) && e.target !== qInput) closeSug();
  });

  /* ---- nav buttons ---- */
  root.addEventListener("click", function (e) {
    var el = e.target.closest("[data-next],[data-back],[data-when],[data-next3],[data-build]");
    if (!el) return;
    if (el.hasAttribute("data-next")) { show(3); }
    else if (el.hasAttribute("data-back")) { show(Number(root.getAttribute("data-step")) - 1 || 1); }
    else if (el.hasAttribute("data-when")) {
      state.when = el.getAttribute("data-when");
      root.querySelectorAll("[data-when]").forEach(function (b) { b.classList.toggle("sel", b === el); });
    }
    else if (el.hasAttribute("data-next3")) {
      var name = $("#diag-name").value.trim(), email = $("#diag-email").value.trim(), phone = $("#diag-phone").value.trim();
      var e3 = $(".diag-step[data-s='3'] .diag-err");
      if (!name) { err(e3, "What's your name?"); return; }
      if (!email) { err(e3, "Add your email so we can send your report."); return; }
      if (!/\S+@\S+\.\S+/.test(email)) { err(e3, "That email looks off — mind double-checking it?"); return; }
      err(e3, "");
      state.name = name; state.email = email; state.phone = phone;
      var btn = el; btn.disabled = true; var t = btn.textContent; btn.textContent = "Sending…";
      postDiagnose({ report: true, lead: true, buildWebsite: false })
        .then(function (d) {
          if (!d || !d.ok) { err(e3, (d && d.error) || "Couldn't send — call or text 713-384-8985."); return; }
          if (window.fbq) fbq("track", "Lead");
          show(4);
        })
        .catch(function () { err(e3, "Couldn't send — call or text 713-384-8985."); })
        .finally(function () { btn.disabled = false; btn.textContent = t; });
    }
    else if (el.hasAttribute("data-build")) {
      state.build = el.getAttribute("data-build") === "1";
      if (state.build) postDiagnose({ buildWebsite: true, report: false, lead: false }).catch(function () {});
      var h = $("#diag-done-h"), p = $("#diag-done-p");
      if (state.build) {
        h.textContent = "On its way — plus we’re building your site. 🎨";
        p.textContent = "Your report card + action plan is headed to " + state.email + ", and we’re building you a free website preview to look at — usually within the hour.";
      } else {
        h.textContent = "Check your inbox. ✅";
        p.textContent = "Your report card + action plan is on its way to " + state.email + ". Want Aaron to walk you through it? Call or text 713-384-8985.";
      }
      show(5);
    }
  });

  /* ---- POST the diagnose lead / report request ---- */
  function postDiagnose(extra) {
    var payload = {
      q: state.q, business: state.business || "", domain: state.domain || "", slug: state.slug || "",
      grade: state.grade || "", rank: state.rankStr || "", city: state.city || "", when: state.when || "",
      name: state.name, phone: state.phone, email: state.email,
    };
    for (var k in extra) payload[k] = extra[k];
    return fetch("/api/diagnose", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); });
  }
})();
