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

  /* ---- competitive standing / FOMO (full card + action steps get emailed) ---- */
  function renderCard(d) {
    var wrap = $("#diag-card");
    if (!d.found) {
      wrap.innerHTML =
        '<div class="fomo notfound"><div class="fomo-head">' +
          '<div class="rc-grade g-f"><span>?</span></div>' +
          '<div class="rc-id"><p class="rc-when">Not in this week’s index</p><h3>We couldn’t find you.</h3></div></div>' +
          '<p class="fomo-magnet">That usually means you’re hard to find online — exactly what’s costing you jobs. Aaron will grade you by hand and send it over. Where do we reach you?</p></div>';
      return;
    }
    var g = d.grade, rc = d.rc, rk = d.rk, ld = d.ld;
    var head =
      '<div class="fomo-head"><div class="rc-grade ' + gradeClass(g) + '"><span>' + esc(g) + "</span></div>" +
      '<div class="rc-id"><p class="rc-when">Your grade' + (d.city ? " · " + esc(d.city) : "") + '</p><h3>' + esc(d.name) + "</h3></div></div>";
    var body = "";
    if (rk) {
      var ahead = Math.max(0, rk[0] - 1);
      body += '<p class="fomo-rank">You rank <b>#' + rk[0] + " of " + rk[1] + "</b> " + esc(rk[2]) + " around Lake Livingston.</p>";
      if (ahead > 0) body += '<p class="fomo-ahead"><b>' + ahead + " shop" + (ahead === 1 ? "" : "s") + " ahead of you</b> — winning the calls you’re not.</p>";
    } else {
      body += '<p class="fomo-rank">You’re graded <b>' + esc(g) + "</b>. The top shops in your trade near you are scoring <b>A+</b>.</p>";
    }
    if (ld && ld.n) {
      body += '<div class="fomo-leader"><span class="fl-ico">🏆</span><span>#1 in your trade near you: <b>' + esc(ld.n) + "</b> — " + esc(ld.g) + ", " + esc(ld.rv) + " reviews</span></div>";
    }
    if (rc && rc.rows) {
      var miss = rc.rows.filter(function (r) { return r[4] !== "ok"; });
      if (miss.length) {
        var names = miss.slice(0, 4).map(function (r) { return r[0]; }).join(", ");
        body += '<p class="fomo-fix">You’re losing points on <b>' + miss.length + " of " + rc.rows.length + "</b> factors: " + esc(names) + ".</p>";
      }
    }
    body += '<p class="fomo-magnet">Your full report card — every factor scored — plus the fastest fixes to climb is ready. Where do we send it?</p>';
    wrap.innerHTML = '<div class="fomo">' + head + body + "</div>";
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
