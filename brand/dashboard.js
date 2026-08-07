/* Client dashboard demo — a real-shaped 12-month journey for a from-scratch contractor.
   Sample data (roofing). Renders KPIs, an animated SVG growth chart with action markers,
   an actions-&-results timeline, and the monthly plan (targets + hours). Everything is a
   labeled illustration. Later this same shape can be driven by a real client's numbers. */
(function () {
  "use strict";
  var d = document, root = d.querySelector("[data-dash]");
  if (!root) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s) { return root.querySelector(s); };

  // ---------- sample data: roofing co, month 1 → 12, built from zero ----------
  var TICKET = 8000; // ~average booked job value (roofing repair/replacement blend)
  var MONTHS = [
    { m: 1,  eyeballs: 1500,  leads: 2,  booked: 0.5, out: 500,  event: "Website & Local SEO went live", detail: "Custom, self-owned site on Cloudflare — indexed, blogging started. The foundation everything else stands on." },
    { m: 2,  eyeballs: 3500,  leads: 3,  booked: 1.0, out: 500 },
    { m: 3,  eyeballs: 11000, leads: 5,  booked: 1.5, out: 1000, event: "Turned on Social Media", detail: "7 networks, daily posts + reels. Eyeballs tripled in a single month and the brand started to show up everywhere." },
    { m: 4,  eyeballs: 15000, leads: 8,  booked: 2.5, out: 1000 },
    { m: 5,  eyeballs: 28000, leads: 13, booked: 4.0, out: 3300, event: "Started $2,000/mo Google Ads", detail: "Top-of-funnel demand on tap. Leads jumped from 8 to 13, and kept climbing as we tuned it." },
    { m: 6,  eyeballs: 31000, leads: 17, booked: 5.0, out: 3300 },
    { m: 7,  eyeballs: 34000, leads: 22, booked: 6.5, out: 6150, event: "Added Google LSA + Missed-Visitor Leads", detail: "$2,500 one-time LSA setup (Google Guarantee). Anonymous site visitors who never called now get captured as leads." },
    { m: 8,  eyeballs: 36000, leads: 25, booked: 7.5, out: 3650 },
    { m: 9,  eyeballs: 39000, leads: 28, booked: 8.5, out: 3650, event: "Newsletter list passed 2,000", detail: "The list we grew from every lead started paying off — repeat and referral jobs compounding for free." },
    { m: 10, eyeballs: 41000, leads: 30, booked: 9.0, out: 3650 },
    { m: 11, eyeballs: 43000, leads: 32, booked: 9.5, out: 3650 },
    { m: 12, eyeballs: 45000, leads: 34, booked: 10.0, out: 3650 }
  ];
  MONTHS.forEach(function (x) { x.in = Math.round(x.booked * TICKET); });

  function sum(k) { return MONTHS.reduce(function (a, x) { return a + x[k]; }, 0); }
  var T = { in: sum("in"), out: sum("out"), booked: sum("booked"), leads: sum("leads"), eyeballs: sum("eyeballs") };
  T.roas = T.in / T.out;
  T.cpbj = T.out / T.booked;

  // ---------- formatting ----------
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function moneyK(n) { n = Math.round(n); return n >= 1000 ? "$" + (Math.round(n / 100) / 10).toLocaleString("en-US") + "k" : "$" + n.toLocaleString("en-US"); }
  function num(n) { return Math.round(n).toLocaleString("en-US"); }
  function num1(n) { return (Math.round(n * 10) / 10).toLocaleString("en-US"); }

  // ---------- count-up tween ----------
  var tweens = {};
  function tween(el, to, fmt, key) {
    if (!el) return;
    if (reduce || d.hidden) { el.textContent = fmt(to); return; }
    var from = 0, begin = null, id = {}; tweens[key] = id;
    function step(ts) { if (tweens[key] !== id) return; if (begin === null) begin = ts;
      var p = Math.min(1, (ts - begin) / 900), e = 1 - Math.pow(1 - p, 4);
      el.textContent = fmt(from + (to - from) * e); if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(to); }
    requestAnimationFrame(step);
  }

  // ---------- KPIs ----------
  function renderKpis() {
    var hero = [
      { l: "Money in", v: money(T.in), s: "12-mo booked revenue", cls: "in", tv: T.in, fmt: moneyK },
      { l: "Money out", v: money(T.out), s: "all-in, including my fees", cls: "out", tv: T.out, fmt: moneyK },
      { l: "ROAS", v: (Math.round(T.roas * 10) / 10) + "×", s: "return on every dollar, after fees", cls: "roas", tv: T.roas, fmt: function (v) { return (Math.round(v * 10) / 10) + "×"; } }
    ];
    var sub = [
      { l: "Booked jobs", tv: T.booked, fmt: num1 },
      { l: "Leads", tv: T.leads, fmt: num },
      { l: "Cost / booked job", tv: T.cpbj, fmt: money },
      { l: "Total eyeballs", tv: T.eyeballs, fmt: num, cls: "eye" }
    ];
    $("[data-dash-kpis]").innerHTML =
      '<div class="dash-kpi-hero">' + hero.map(function (t) {
        return '<div class="dash-kpi big ' + t.cls + '"><span class="dk-l">' + t.l + '</span>' +
          '<b class="dk-v" data-kpi="' + t.l + '">' + (reduce ? t.v : "0") + '</b><span class="dk-s">' + t.s + '</span></div>';
      }).join("") + '</div>' +
      '<div class="dash-kpi-row">' + sub.map(function (t) {
        return '<div class="dash-kpi' + (t.cls ? " " + t.cls : "") + '"><span class="dk-l">' + t.l + '</span>' +
          '<b class="dk-v" data-kpi="' + t.l + '">' + (reduce ? t.fmt(t.tv) : "0") + '</b></div>';
      }).join("") + '</div>';
    hero.concat(sub).forEach(function (t) { tween(root.querySelector('[data-kpi="' + t.l + '"]'), t.tv, t.fmt, "k" + t.l); });
  }

  // ---------- chart ----------
  var METRICS = [
    { k: "in", label: "Money in", fmt: moneyK, tip: money },
    { k: "leads", label: "Leads", fmt: num, tip: num },
    { k: "booked", label: "Booked jobs", fmt: num1, tip: num1 },
    { k: "eyeballs", label: "Eyeballs", fmt: num, tip: num },
    { k: "out", label: "Money out", fmt: moneyK, tip: money }
  ];
  var current = "in";
  var W = 840, HT = 340, padL = 58, padR = 20, padT = 20, padB = 40;
  var plotW = W - padL - padR, plotH = HT - padT - padB;
  function xat(i) { return padL + (i / (MONTHS.length - 1)) * plotW; }

  function drawChart(mk) {
    var m = METRICS.filter(function (x) { return x.k === mk; })[0];
    var vals = MONTHS.map(function (x) { return x[mk]; });
    var max = Math.max.apply(null, vals) * 1.1 || 1;
    var yat = function (v) { return padT + plotH - (v / max) * plotH; };
    var pts = vals.map(function (v, i) { return [xat(i), yat(v)]; });
    var line = pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" ");
    var area = line + " L" + xat(MONTHS.length - 1).toFixed(1) + " " + (padT + plotH) + " L" + padL + " " + (padT + plotH) + " Z";

    // y gridlines + labels (4)
    var grid = "", ylab = "";
    for (var g = 0; g <= 4; g++) {
      var yv = max * g / 4, yy = yat(yv);
      grid += '<line x1="' + padL + '" y1="' + yy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + yy.toFixed(1) + '" class="dc-grid"/>';
      ylab += '<text x="' + (padL - 10) + '" y="' + (yy + 4).toFixed(1) + '" class="dc-ylab">' + m.fmt(yv) + '</text>';
    }
    // x labels
    var xlab = MONTHS.map(function (x, i) { return '<text x="' + xat(i).toFixed(1) + '" y="' + (HT - 12) + '" class="dc-xlab">' + x.m + '</text>'; }).join("");
    // event markers
    var marks = "", dots = "";
    MONTHS.forEach(function (x, i) {
      if (x.event) {
        var px = xat(i), py = yat(x[mk]);
        marks += '<line x1="' + px.toFixed(1) + '" y1="' + padT + '" x2="' + px.toFixed(1) + '" y2="' + (padT + plotH) + '" class="dc-evline"/>' +
          '<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="5.5" class="dc-evdot"/>';
      }
    });
    // hover hit points (all months)
    MONTHS.forEach(function (x, i) {
      dots += '<circle cx="' + xat(i).toFixed(1) + '" cy="' + yat(x[mk]).toFixed(1) + '" r="4" class="dc-dot"/>' +
        '<circle cx="' + xat(i).toFixed(1) + '" cy="' + yat(x[mk]).toFixed(1) + '" r="16" class="dc-hit" data-i="' + i + '"/>';
    });
    var end = pts[pts.length - 1];
    var svg = '<svg viewBox="0 0 ' + W + ' ' + HT + '" class="dc-svg" role="img" aria-label="12-month ' + m.label + '">' +
      '<defs><linearGradient id="dcfill" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="var(--primary-container)" stop-opacity="0.28"/>' +
      '<stop offset="1" stop-color="var(--primary-container)" stop-opacity="0"/></linearGradient></defs>' +
      grid + ylab + xlab + marks +
      '<path d="' + area + '" class="dc-area"/>' +
      '<path d="' + line + '" class="dc-line" data-line/>' +
      '<circle cx="' + end[0].toFixed(1) + '" cy="' + end[1].toFixed(1) + '" r="6" class="dc-end"/>' +
      dots + '</svg>' +
      '<div class="dc-tip" data-dc-tip hidden></div>';
    var host = $("[data-dash-chart]");
    host.innerHTML = svg;
    animateLine();
    wireHover(mk, m);
  }

  function animateLine() {
    if (reduce || d.hidden) return;
    var p = $("[data-line]"); if (!p || !p.getTotalLength) return;
    var len = p.getTotalLength();
    p.style.transition = "none"; p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
    // area + dots fade in
    var area = root.querySelector(".dc-area"), dots = root.querySelectorAll(".dc-dot,.dc-end,.dc-evdot,.dc-evline");
    if (area) { area.style.opacity = 0; }
    dots.forEach(function (el) { el.style.opacity = 0; });
    requestAnimationFrame(function () {
      p.style.transition = "stroke-dashoffset 1.05s cubic-bezier(.22,1,.36,1)"; p.style.strokeDashoffset = 0;
      if (area) { area.style.transition = "opacity .8s ease .2s"; area.style.opacity = 1; }
      dots.forEach(function (el) { el.style.transition = "opacity .5s ease .7s"; el.style.opacity = ""; });
    });
  }

  function wireHover(mk, m) {
    var tip = $("[data-dc-tip]"), host = $("[data-dash-chart]");
    root.querySelectorAll(".dc-hit").forEach(function (h) {
      h.addEventListener("mouseenter", function () {
        var i = +h.getAttribute("data-i"), x = MONTHS[i];
        var hostRect = host.getBoundingClientRect(), svg = host.querySelector("svg").getBoundingClientRect();
        var px = (xat(i) / W) * svg.width + (svg.left - hostRect.left);
        tip.innerHTML = '<span class="dc-tip-m">Month ' + x.m + '</span><b>' + m.tip(x[mk]) + '</b>' +
          (x.event ? '<span class="dc-tip-e">' + x.event + '</span>' : '');
        tip.hidden = false;
        tip.style.left = Math.max(4, Math.min(hostRect.width - tip.offsetWidth - 4, px - tip.offsetWidth / 2)) + "px";
      });
      h.addEventListener("mouseleave", function () { tip.hidden = true; });
    });
  }

  function renderMetrics() {
    $("[data-dash-metrics]").innerHTML = METRICS.map(function (m) {
      return '<button type="button" class="dash-mbtn' + (m.k === current ? " on" : "") + '" data-metric="' + m.k + '">' + m.label + '</button>';
    }).join("");
    root.querySelectorAll("[data-metric]").forEach(function (b) {
      b.addEventListener("click", function () {
        current = b.getAttribute("data-metric");
        root.querySelectorAll("[data-metric]").forEach(function (x) { x.classList.toggle("on", x === b); });
        drawChart(current);
      });
    });
  }

  // ---------- actions & results timeline ----------
  function renderTimeline() {
    var rows = MONTHS.filter(function (x) { return x.event; }).map(function (x) {
      return '<div class="dash-tl"><div class="dash-tl-badge">Mo ' + x.m + '</div><div class="dash-tl-body">' +
        '<b>' + x.event + '</b><p>' + x.detail + '</p></div></div>';
    });
    // add the closing result
    rows.push('<div class="dash-tl end"><div class="dash-tl-badge">Mo 12</div><div class="dash-tl-body">' +
      '<b>The machine is humming</b><p>From 2 leads a month to ' + MONTHS[11].leads + '. ' + num1(MONTHS[11].booked) +
      ' booked jobs, ' + money(MONTHS[11].in) + ' in booked work &mdash; on ' + money(MONTHS[11].out) + ' of spend.</p></div></div>');
    $("[data-dash-timeline]").innerHTML = rows.join("");
  }

  // ---------- monthly plan: targets + actions + hours ----------
  var PLAN_ACTIONS = [
    { name: "Website, Local SEO & Blogging", hrs: 12 },
    { name: "Google Business Profile", hrs: 2 },
    { name: "Review Autopilot", hrs: 2 },
    { name: "Missed-Visitor Leads", hrs: 2 },
    { name: "Weekly Newsletter", hrs: 2 },
    { name: "Social Media (7 networks)", hrs: 6 },
    { name: "Google Ads", hrs: 3 },
    { name: "Google LSA", hrs: 2 },
    { name: "CPA/CPL Optimization", hrs: 3 }
  ];
  function renderActions() {
    var last = MONTHS[11], totalHrs = PLAN_ACTIONS.reduce(function (a, x) { return a + x.hrs; }, 0);
    var targets = '<div class="dash-targets">' +
      '<div class="dash-target"><span>This month&rsquo;s target</span><b>' + last.leads + ' leads</b></div>' +
      '<div class="dash-target"><span>Booked jobs</span><b>' + num1(last.booked) + '</b></div>' +
      '<div class="dash-target"><span>Booked work</span><b>' + money(last.in) + '</b></div>' +
      '<div class="dash-target hrs"><span>My hours</span><b>~' + totalHrs + ' hrs</b></div></div>';
    var list = '<div class="dash-acts">' + PLAN_ACTIONS.map(function (a) {
      return '<div class="dash-act"><svg class="dash-check"><use href="#i-check"/></svg><span>' + a.name + '</span><span class="dash-act-hrs">~' + a.hrs + ' hrs</span></div>';
    }).join("") + '</div>';
    $("[data-dash-actions]").innerHTML = targets + list +
      '<p class="dash-fine">Tools &amp; credits (AI images, BrightLocal citations, hosting, review platform, ConsentResolve) are included &mdash; no extra charge.</p>';
  }

  renderKpis();
  renderMetrics();
  drawChart(current);
  renderTimeline();
  renderActions();
})();
