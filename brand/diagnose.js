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
  function cmpRow(label, you, ctx, bad) {
    return '<div class="fc-row' + (bad ? " bad" : "") + '"><span class="fc-l">' + esc(label) + "</span>" +
      '<span class="fc-you">' + esc(String(you)) + '</span><span class="fc-ctx">' + esc(ctx) + "</span></div>";
  }
  function hasFactor(rc, subj) {
    if (!rc || !rc.rows) return false;
    for (var i = 0; i < rc.rows.length; i++) if (rc.rows[i][0] === subj && rc.rows[i][4] === "ok") return true;
    return false;
  }
  function money(n) { return "$" + Number(n).toLocaleString(); }

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
    var g = d.grade, rc = d.rc, rk = d.rk, f = d.fomo, H = "";
    H += '<div class="fomo-head"><div class="rc-grade ' + gradeClass(g) + '"><span>' + esc(g) + "</span></div>" +
      '<div class="rc-id"><p class="rc-when">Your grade' + (d.city ? " · " + esc(d.city) : "") + '</p><h3>' + esc(d.name) + "</h3></div></div>";
    if (rk) {
      var ahead = Math.max(0, rk[0] - 1);
      H += '<p class="fomo-rank">You rank <b>#' + rk[0] + " of " + rk[1] + "</b> " + esc(rk[2]) + " around Lake Livingston." +
        (ahead > 0 ? ' <b class="hot">' + ahead + " ahead of you.</b>" : "") + "</p>";
    } else {
      H += '<p class="fomo-rank">You’re graded <b>' + esc(g) + "</b> — the shops winning your jobs are scoring <b>A+</b>.</p>";
    }
    if (f) {
      if (f.missed) {
        H += '<div class="fomo-money"><span class="fm-amt">≈ ' + money(f.missed) + "/mo</span>" +
          '<span class="fm-lbl">in booked jobs is going to shops ahead of you</span>' +
          '<span class="fm-sub">est. ' + f.leadsTop + " job-leads/mo for the #1 shop" + (f.ldn ? " (" + esc(f.ldn) + ")" : "") +
          " vs ~" + f.leadsYou + " for you · ~" + money(f.job) + "/job</span></div>";
      }
      var site = hasFactor(rc, "Working website");
      H += '<div class="fomo-cmp"><p class="fc-h">You vs the ' + f.n + " shops around the lake</p>" +
        cmpRow("Google reviews", f.yourRev, "market " + f.avgRev + " · top 5 " + f.top5Rev, f.yourRev < f.avgRev) +
        cmpRow("Listing photos", f.yourPh, "market avg " + f.avgPh, f.yourPh < f.avgPh) +
        cmpRow("Working website", site ? "Yes" : "No", f.pctSite + "% of rivals have one", !site) +
        cmpRow("Social posts / mo", "few", "winners post weekly", true) +
        cmpRow("Est. cost / booked job", money(f.cpjYou), "at an A: " + money(f.cpjTop), f.cpjYou > f.cpjTop) +
        "</div>";
      if (f.tactics && f.tactics.length) {
        H += '<div class="fomo-tac"><p class="fc-h">What the top 5 do that you don’t</p><ul>';
        f.tactics.forEach(function (t) { H += "<li>" + esc(t) + "</li>"; });
        H += "</ul></div>";
      }
      if (f.path && f.path.length) {
        H += '<div class="fomo-path"><p class="fc-h">Your climb — and what it takes</p>';
        f.path.forEach(function (p) {
          H += '<div class="fp-row"><span class="fp-g ' + gradeClass(p.g) + '">' + esc(p.g) + "</span>" +
            '<span class="fp-plan">' + esc(p.plan) + " plan</span>" +
            '<span class="fp-cost">~' + money(p.mo) + "/mo · " + esc(p.time) + "</span></div>";
        });
        H += "</div>";
      }
    }
    H += '<p class="fomo-magnet">Your full report card — every number above, scored and explained — plus your exact fix list is ready. Where do we send it?</p>';
    wrap.innerHTML = '<div class="fomo">' + H + "</div>";
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
