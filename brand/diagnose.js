/* Top of Class Marketing — report-card diagnose flow (the key conversion).
   4 steps: look up the shop (with live autocomplete) → show its FULL report card
   inline (no leaving the site) → book Aaron → offer a free Claude-built preview. */
(function () {
  "use strict";
  var root = document.getElementById("diag");
  if (!root) return;

  var state = { q: "", card: null, when: "", name: "", phone: "", email: "", build: null };
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
    if (focusable && n > 1) { try { focusable.focus(); } catch (e) {} }
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

  /* ---- inline report card (rendered on aaron.chat; no off-site link) ---- */
  function renderCard(d) {
    var wrap = $("#diag-card");
    if (!d.found) {
      wrap.innerHTML =
        '<div class="rc-inline notfound"><div class="rc-head">' +
          '<div class="rc-grade g-f"><span>?</span></div>' +
          '<div class="rc-id"><p class="rc-when">Not in this week’s index</p>' +
          "<h3>We couldn’t find you.</h3></div></div>" +
          "<p class=\"lede\">That usually means you’re hard to find online — which is exactly what’s costing you jobs. Aaron will grade you by hand and walk you through it.</p></div>";
      return;
    }
    var rc = d.rc;
    var meta = d.rating ? "★ " + esc(d.rating) + (d.reviews ? " · " + esc(d.reviews) + " reviews" : "") : "";
    if (rc && rc.tot) meta += (meta ? " · " : "") + esc(rc.tot[1]);
    var head =
      '<div class="rc-head">' +
        '<div class="rc-grade ' + gradeClass(d.grade) + '"><span>' + esc(d.grade) + "</span></div>" +
        '<div class="rc-id"><p class="rc-when">Report card' + (d.city ? " · " + esc(d.city) : "") + "</p>" +
        "<h3>" + esc(d.name) + "</h3>" + (meta ? '<span class="rc-meta">' + meta + "</span>" : "") +
        "</div></div>";
    var body = "";
    if (rc && rc.rows && rc.rows.length) {
      body += '<ul class="rc-rows">';
      rc.rows.forEach(function (r) {
        var st = r[4] === "ok" ? "ok" : (r[4] === "miss" ? "miss" : "warn");
        body +=
          '<li class="' + st + '">' +
            '<span class="rc-subj">' + esc(r[0]) + "</span>" +
            '<span class="rc-found">' + esc(r[1]) + "</span>" +
            '<span class="rc-pts">' + esc(r[2]) + "</span>" +
            '<span class="rc-rg">' + esc(r[3]) + "</span>" +
          "</li>";
      });
      body +=
        '<li class="rc-total"><span class="rc-subj">Overall</span>' +
        '<span class="rc-found">' + esc(rc.tot ? rc.tot[0] : "") + "</span>" +
        '<span class="rc-pts">' + esc(rc.tot ? rc.tot[1] : "") + "</span>" +
        '<span class="rc-rg">' + esc(d.grade) + "</span></li></ul>";
      if (rc.cmt) body += '<p class="rc-cmt">' + esc(rc.cmt) + "</p>";
    } else {
      body += '<p class="lede">' + verdict(d.grade) + "</p>";
    }
    wrap.innerHTML = '<div class="rc-inline">' + head + body + "</div>";
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
        if (d.found) { state.business = d.name; state.grade = d.grade; state.city = d.city; state.domain = d.slug; }
        else { state.business = payload.q || state.q; }
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
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { err(e3, "Add a valid email so Aaron can reach you."); return; }
      err(e3, "");
      state.name = name; state.email = email; state.phone = phone;
      show(4);
    }
    else if (el.hasAttribute("data-build")) { state.build = el.getAttribute("data-build") === "1"; submit(); }
  });

  /* ---- final submit ---- */
  function submit() {
    var e4 = $(".diag-step[data-s='4'] .diag-err");
    var payload = {
      q: state.q, business: state.business || "", domain: state.domain || "", grade: state.grade || "",
      city: state.city || "", when: state.when || "", name: state.name, phone: state.phone,
      email: state.email, buildWebsite: state.build,
    };
    root.querySelectorAll("[data-build]").forEach(function (b) { b.disabled = true; });
    fetch("/api/diagnose", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) { err(e4, d.error || "Couldn't send — call or text 713-384-8985."); root.querySelectorAll("[data-build]").forEach(function (b) { b.disabled = false; }); return; }
        if (window.fbq) fbq("track", "Lead");
        var h = $("#diag-done-h"), p = $("#diag-done-p");
        if (state.build) {
          h.textContent = "We're already sketching your site. 🎨";
          p.textContent = "Your report card and a call from Aaron are on the way — and we're building you a free website preview to look at, usually within the hour.";
        } else {
          h.textContent = "You're all set. ✅";
          p.textContent = "Your report card and a call from Aaron are on the way. Worst case, you leave with a list of free fixes and his number.";
        }
        show(5);
      })
      .catch(function () { err(e4, "Couldn't send — call or text 713-384-8985."); root.querySelectorAll("[data-build]").forEach(function (b) { b.disabled = false; }); });
  }
})();
