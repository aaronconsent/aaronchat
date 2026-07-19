/* Top of Class Marketing — report-card diagnose flow (the key conversion).
   4 steps: look up the shop → show its live report card → book Aaron →
   offer a free Claude-built website preview. Vanilla, progressive. */
(function () {
  "use strict";
  var root = document.getElementById("diag");
  if (!root) return;

  var state = { q: "", card: null, when: "", name: "", phone: "", email: "", build: null };
  var $ = function (s, r) { return (r || root).querySelector(s); };
  var steps = root.querySelectorAll(".diag-step");
  var bars = root.querySelectorAll(".diag-prog span");

  function show(n) {
    steps.forEach(function (el) { el.hidden = el.getAttribute("data-s") !== String(n); });
    bars.forEach(function (b, i) { b.classList.toggle("on", i < Math.min(n, 4)); });
    root.setAttribute("data-step", n);
    var focusable = $(".diag-step[data-s='" + n + "'] input, .diag-step[data-s='" + n + "'] button");
    if (focusable && n > 1) { try { focusable.focus(); } catch (e) {} }
    if (typeof root.scrollIntoView === "function" && n > 1) root.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function err(el, msg) { el.textContent = msg; el.hidden = !msg; }

  function gradeClass(g) {
    var c = (g || "").charAt(0).toUpperCase();
    if (c === "A") return "g-a";
    if (c === "B") return "g-b";
    if (c === "C") return "g-c";
    return "g-f";
  }
  function verdict(g) {
    var c = (g || "").charAt(0).toUpperCase();
    if (c === "A") return "You're already near the top of the class — now we protect the lead and pull further ahead.";
    if (c === "B") return "Solid, but there's clear daylight between you and #1. That gap is winnable.";
    if (c === "C") return "Middle of the pack — which means a focused few weeks can move you up fast.";
    return "There's a lot of easy ground to gain here. Good news: that's the fastest kind to win.";
  }

  function renderCard(d) {
    var wrap = $("#diag-card");
    if (d.found) {
      var stars = d.rating ? '<span class="rc-meta">★ ' + d.rating + (d.reviews ? " · " + d.reviews + " reviews" : "") + "</span>" : "";
      wrap.innerHTML =
        '<div class="diag-rc">' +
          '<div class="rc-grade ' + gradeClass(d.grade) + '"><span>' + d.grade + "</span></div>" +
          '<div class="rc-body">' +
            '<p class="rc-when">Graded this week' + (d.city ? " · " + d.city : "") + "</p>" +
            "<h3>" + d.name + "</h3>" + stars +
            '<a class="rc-link" href="' + d.cardUrl + '" target="_blank" rel="noopener">See your full report card ↗</a>' +
          "</div>" +
        "</div>" +
        '<p class="lede">' + verdict(d.grade) + "</p>";
    } else {
      wrap.innerHTML =
        '<div class="diag-rc notfound">' +
          '<div class="rc-grade g-f"><span>?</span></div>' +
          '<div class="rc-body"><h3>We couldn’t find you in this week’s index.</h3>' +
          "<p>That usually means you’re hard to find online — which is exactly what’s costing you jobs. That’s the good news: it’s very fixable.</p></div>" +
        "</div>" +
        '<p class="lede">Let’s get you on the board. Aaron will grade you by hand and walk you through it.</p>';
    }
  }

  /* ---- Step 1: lookup ---- */
  var lookupForm = $(".diag-lookup");
  lookupForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = $("#diag-q").value.trim();
    var e1 = $(".diag-step[data-s='1'] .diag-err");
    if (!q) { err(e1, "Type your website or business name."); return; }
    err(e1, "");
    state.q = q;
    var btn = lookupForm.querySelector("button");
    btn.disabled = true; var t = btn.textContent; btn.textContent = "Grading…";
    fetch("/api/lookup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ q: q }) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        state.card = d;
        if (d.found) { state.business = d.name; state.grade = d.grade; state.city = d.city; state.domain = d.slug; }
        else { state.business = q; }
        renderCard(d);
        show(2);
      })
      .catch(function () { err(e1, "Something hiccuped — try again, or just book a call below."); })
      .finally(function () { btn.disabled = false; btn.textContent = t; });
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
    else if (el.hasAttribute("data-build")) {
      state.build = el.getAttribute("data-build") === "1";
      submit();
    }
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
