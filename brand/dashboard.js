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
  // Costs are itemized and reconcile with the pricing page:
  //   fees  = Website&Growth $500/mo + Social $500/mo (from mo 3) + 15% ad management + one-time $2,500 LSA setup (mo 7)
  //   ad    = Google Ads $2,000/mo (from mo 5) + Google LSA $2,000/mo (from mo 7) — paid to Google, not to me
  //   tools = ConsentResolve visitor resolution (~$350/mo from mo 7)
  var MONTHS = [
    { m: 1,  eyeballs: 800,   leads: 1,  booked: 0,   ad: 0,    fees: 500,  tools: 0,   event: "Website & Local SEO went live", detail: "Custom, self-owned site on Cloudflare — indexed, blogging started. It's quiet on purpose: this is the foundation, and you're investing about $500 to build it." },
    { m: 2,  eyeballs: 2500,  leads: 2,  booked: 0,   ad: 0,    fees: 500,  tools: 0 },
    { m: 3,  eyeballs: 9000,  leads: 4,  booked: 1,   ad: 0,    fees: 1000, tools: 0,   event: "Social on + first jobs from search & referral", detail: "Google Business Profile and early search visibility start producing calls; social builds the trust that helps them close. The first roofing jobs land and you cross into profit (a bumpier line than this in real life — organic is slower than paid)." },
    { m: 4,  eyeballs: 13000, leads: 7,  booked: 2,   ad: 0,    fees: 1000, tools: 0 },
    { m: 5,  eyeballs: 26000, leads: 12, booked: 3.5, ad: 2000, fees: 1300, tools: 0,   event: "Started $2,000/mo Google Ads", detail: "Top-of-funnel demand on tap. Ad spend steps up to $2,000/mo (plus my 15% management) — and the booked work steps up faster." },
    { m: 6,  eyeballs: 30000, leads: 16, booked: 4.5, ad: 2000, fees: 1300, tools: 0 },
    { m: 7,  eyeballs: 33000, leads: 21, booked: 6,   ad: 4000, fees: 4100, tools: 350, event: "Added Google LSA + Missed-Visitor follow-up", detail: "A one-time $2,500 LSA setup (Google Guarantee) plus a ~$2,000/mo Local Services Ads budget. Identified return visitors get added to remarketing and follow-up too — a few extra touchpoints a month, not a lead firehose." },
    { m: 8,  eyeballs: 35000, leads: 24, booked: 7,   ad: 4000, fees: 1600, tools: 350 },
    { m: 9,  eyeballs: 38000, leads: 27, booked: 8,   ad: 4000, fees: 1600, tools: 350, event: "Repeat & referral work compounding", detail: "The list we grew from every lead and past customer (a few hundred by now — not thousands) starts paying off, with repeat and referral jobs stacking on top, for free." },
    { m: 10, eyeballs: 40000, leads: 29, booked: 8.5, ad: 4000, fees: 1600, tools: 350 },
    { m: 11, eyeballs: 42000, leads: 31, booked: 9,   ad: 4000, fees: 1600, tools: 350 },
    { m: 12, eyeballs: 44000, leads: 33, booked: 9.5, ad: 4000, fees: 1600, tools: 350 }
  ];
  MONTHS.forEach(function (x) { x.out = x.ad + x.fees + x.tools; x.in = Math.round(x.booked * TICKET); x.net = x.in - x.out; });

  function sum(k) { return MONTHS.reduce(function (a, x) { return a + x[k]; }, 0); }
  var T = { in: sum("in"), out: sum("out"), booked: sum("booked"), leads: sum("leads"), eyeballs: sum("eyeballs"), ad: sum("ad"), fees: sum("fees"), tools: sum("tools") };
  T.roas = T.in / T.out;
  T.cpbj = T.out / T.booked;
  T.net = T.in - T.out;

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
      { l: "Money in", v: money(T.in), s: "12-mo revenue booked (contracted, not yet collected)", cls: "in", tv: T.in, fmt: moneyK },
      { l: "Money out", v: money(T.out), s: moneyK(T.ad) + " ad spend + " + moneyK(T.fees + T.tools) + " fees & tools", cls: "out", tv: T.out, fmt: moneyK },
      { l: "ROAS", v: (Math.round(T.roas * 10) / 10) + "×", s: "revenue-to-spend · ≈" + (Math.round(T.roas * 0.27 * 10) / 10) + "× on gross profit after ~27% roofing margin", cls: "roas", tv: T.roas, fmt: function (v) { return (Math.round(v * 10) / 10) + "×"; } }
    ];
    var sub = [
      { l: "Net gain", tv: T.net, fmt: money, cls: "net" },
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

  // ---------- conservative floor (the honest "what's realistic" counterweight) ----------
  // Sourced from the Aug-2026 benchmark audit (25th-percentile cold-start, paid channels only).
  var FLOOR = { leads: 90, jobs: 11, rev: 66000 };
  function renderFloor() {
    var el = $("[data-dash-floor]"); if (!el) return;
    function row(l, show, floor) {
      return '<div class="dash-floor-row"><span class="dfl-l">' + l + '</span>' +
        '<span class="dfl-show">' + show + '</span><span class="dfl-arrow">→</span>' +
        '<span class="dfl-floor">' + floor + '</span></div>';
    }
    el.innerHTML =
      '<div class="dash-floor-head"><h3>What&rsquo;s realistic: the conservative floor</h3>' +
      '<p>The showcase above is an <b>above-median</b> run. Here&rsquo;s the honest other end &mdash; a conservative, from-zero year that a typical new roofer hits with <b>average</b> execution and a funded budget. These are the numbers I&rsquo;d actually stand behind, not the illustration.</p></div>' +
      '<div class="dash-floor-cols"><div class="dash-floor-labels"><span></span><span class="dfl-cap show">Illustration (above-median)</span><span></span><span class="dfl-cap floor">Conservative floor</span></div>' +
      row("Leads (12 mo)", num(T.leads), num(FLOOR.leads)) +
      row("Booked jobs (12 mo)", num1(T.booked), num(FLOOR.jobs)) +
      row("Booked revenue (12 mo)", money(T.in), money(FLOOR.rev)) +
      '</div>' +
      '<p class="dash-floor-fine">Floor assumes a funded <b>&ge;$2,000/mo</b> ad budget and fast lead response. Only <b>paid</b> channels (Google Ads, Local Services Ads) are counted toward it &mdash; SEO, social, newsletter, and visitor-ID are real, but too slow or traffic-dependent to promise in year one. Revenue is booked, not collected; after roofing margins, profit is a fraction of it.</p>';
  }

  // ---------- chart ----------
  var METRICS = [
    { k: "booked", label: "Booked jobs", fmt: num1, tip: num1 },
    { k: "in", label: "Money in", fmt: moneyK, tip: money },
    { k: "leads", label: "Leads", fmt: num, tip: num },
    { k: "eyeballs", label: "Eyeballs", fmt: num, tip: num },
    { k: "out", label: "Money out", fmt: moneyK, tip: money }
  ];
  var current = "booked", sel = MONTHS.length - 1, playTimer = null;
  var W = 840, HT = 340, padL = 58, padR = 20, padT = 20, padB = 40;
  var plotW = W - padL - padR, plotH = HT - padT - padB;
  function xat(i) { return padL + (i / (MONTHS.length - 1)) * plotW; }
  function cumThrough(k, upto) { var s = 0; for (var i = 0; i <= upto; i++) s += MONTHS[i][k]; return s; }

  function drawChart() {
    var mk = current, m = METRICS.filter(function (x) { return x.k === mk; })[0];
    var vals = MONTHS.map(function (x) { return x[mk]; });
    var max = Math.max.apply(null, vals) * 1.1 || 1;
    var yat = function (v) { return padT + plotH - (v / max) * plotH; };
    var pts = vals.map(function (v, i) { return [xat(i), yat(v)]; });
    function pathFrom(a, b) { return pts.slice(a, b + 1).map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" "); }
    var solid = pathFrom(0, sel);
    var faint = sel < pts.length - 1 ? pathFrom(sel, pts.length - 1) : "";
    var area = solid + " L" + pts[sel][0].toFixed(1) + " " + (padT + plotH) + " L" + padL + " " + (padT + plotH) + " Z";

    var grid = "", ylab = "";
    for (var g = 0; g <= 4; g++) { var yv = max * g / 4, yy = yat(yv);
      grid += '<line x1="' + padL + '" y1="' + yy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + yy.toFixed(1) + '" class="dc-grid"/>';
      ylab += '<text x="' + (padL - 10) + '" y="' + (yy + 4).toFixed(1) + '" class="dc-ylab">' + m.fmt(yv) + '</text>'; }
    var xlab = MONTHS.map(function (x, i) { return '<text x="' + xat(i).toFixed(1) + '" y="' + (HT - 12) + '" class="dc-xlab' + (i === sel ? " on" : "") + '">' + x.m + '</text>'; }).join("");
    var ev = "";
    MONTHS.forEach(function (x, i) { if (x.event) ev += '<circle cx="' + xat(i).toFixed(1) + '" cy="' + yat(x[mk]).toFixed(1) + '" r="5" class="dc-evdot"/>'; });
    var px = xat(sel), py = yat(MONTHS[sel][mk]);
    var head = '<line x1="' + px.toFixed(1) + '" y1="' + padT + '" x2="' + px.toFixed(1) + '" y2="' + (padT + plotH) + '" class="dc-playline"/>' +
      '<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="6.5" class="dc-head"/>';
    var hits = MONTHS.map(function (x, i) { return '<circle cx="' + xat(i).toFixed(1) + '" cy="' + yat(x[mk]).toFixed(1) + '" r="16" class="dc-hit" data-i="' + i + '"/>'; }).join("");

    $("[data-dash-chart]").innerHTML =
      '<svg viewBox="0 0 ' + W + ' ' + HT + '" class="dc-svg" role="img" aria-label="' + m.label + ' through month ' + (sel + 1) + '">' +
      '<defs><linearGradient id="dcfill" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="var(--primary-container)" stop-opacity="0.28"/>' +
      '<stop offset="1" stop-color="var(--primary-container)" stop-opacity="0"/></linearGradient></defs>' +
      grid + ylab + xlab +
      (faint ? '<path d="' + faint + '" class="dc-line faint"/>' : "") +
      '<path d="' + area + '" class="dc-area"/>' +
      '<path d="' + solid + '" class="dc-line"/>' + ev + head + hits + '</svg>';

    $("[data-dash-chart]").querySelectorAll(".dc-hit").forEach(function (h) {
      h.addEventListener("click", function () { stopPlay(); setMonth(+h.getAttribute("data-i")); });
    });
  }

  function animateInitial() {
    if (reduce || d.hidden) return;
    var p = root.querySelector("[data-dash-chart] .dc-line:not(.faint)");
    if (!p || !p.getTotalLength) return;
    var len = p.getTotalLength();
    p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
    requestAnimationFrame(function () { p.style.transition = "stroke-dashoffset 1.1s cubic-bezier(.22,1,.36,1)"; p.style.strokeDashoffset = 0; });
  }

  // ---------- month stepper ----------
  function renderMonths() {
    $("[data-dash-months]").innerHTML =
      '<button type="button" class="dash-mo-nav" data-mo-prev aria-label="Previous month">&lsaquo;</button>' +
      '<div class="dash-mo-tabs">' + MONTHS.map(function (x, i) {
        return '<button type="button" class="dash-mo-tab' + (i === sel ? " on" : "") + (x.event ? " ev" : "") + '" data-mo="' + i + '" aria-label="Month ' + x.m + (x.event ? ", " + x.event : "") + '">' + x.m + '</button>';
      }).join("") + '</div>' +
      '<button type="button" class="dash-mo-nav" data-mo-next aria-label="Next month">&rsaquo;</button>' +
      '<button type="button" class="dash-mo-play" data-mo-play><span class="dash-play-i">&#9654;</span><span class="dash-play-t">Play</span></button>';
    root.querySelectorAll("[data-mo]").forEach(function (b) { b.addEventListener("click", function () { stopPlay(); setMonth(+b.getAttribute("data-mo")); }); });
    $("[data-mo-prev]").addEventListener("click", function () { stopPlay(); setMonth(Math.max(0, sel - 1)); });
    $("[data-mo-next]").addEventListener("click", function () { stopPlay(); setMonth(Math.min(MONTHS.length - 1, sel + 1)); });
    $("[data-mo-play]").addEventListener("click", play);
  }
  function syncMonthTabs() { root.querySelectorAll("[data-mo]").forEach(function (b) { b.classList.toggle("on", +b.getAttribute("data-mo") === sel); }); }

  function netFmt(n) { return (n < 0 ? "−$" : "+$") + Math.abs(Math.round(n)).toLocaleString("en-US"); }
  function renderMonthDetail() {
    var x = MONTHS[sel];
    var cin = cumThrough("in", sel), cout = cumThrough("out", sel), cbk = cumThrough("booked", sel), cld = cumThrough("leads", sel), cey = cumThrough("eyeballs", sel);
    var roas = cout ? (Math.round(cin / cout * 10) / 10) : 0;
    var netCum = cin - cout;
    function rw(l, v) { return '<div class="dash-md-row"><span>' + l + '</span><b>' + v + '</b></div>'; }
    var milestone = x.event
      ? '<div class="dash-md-ev"><svg class="dash-md-flag"><use href="#i-bolt"/></svg><div><b>' + x.event + '</b><p>' + x.detail + '</p></div></div>'
      : '<div class="dash-md-ev muted"><svg class="dash-md-flag"><use href="#i-trend"/></svg><div><b>Steady growth</b><p>Momentum from the pieces already running &mdash; more eyeballs, more leads, more booked work.</p></div></div>';
    var netStrip = '<div class="dash-md-net ' + (netCum >= 0 ? "gain" : "loss") + '">' +
      '<div class="dash-md-net-i"><span>Net this month</span><b>' + netFmt(x.net) + '</b></div>' +
      '<div class="dash-md-net-i main"><span>Net so far &middot; months 1&ndash;' + x.m + '</span><b>' + netFmt(netCum) + '</b>' +
      '<em>' + (netCum >= 0 ? "in the black" : "still investing") + '</em></div></div>';
    var cad = cumThrough("ad", sel), cfees = cumThrough("fees", sel), ctools = cumThrough("tools", sel);
    var splitStrip = '<div class="dash-md-split"><h5>Where the money out went &middot; months 1&ndash;' + x.m + '</h5>' +
      '<div class="dash-md-splitrow"><span>Ad spend <em>&rarr; Google</em></span><b>' + money(cad) + '</b></div>' +
      '<div class="dash-md-splitrow"><span>My fees <em>&rarr; me</em></span><b>' + money(cfees) + '</b></div>' +
      (ctools > 0 ? '<div class="dash-md-splitrow"><span>Tools <em>ConsentResolve</em></span><b>' + money(ctools) + '</b></div>' : '') +
      '<div class="dash-md-splitrow total"><span>Total money out</span><b>' + money(cout) + '</b></div></div>';
    $("[data-dash-monthdetail]").innerHTML =
      '<div class="dash-md-head"><span class="dash-md-mo">Month ' + x.m + '</span><span class="dash-md-of">of 12</span></div>' + milestone + netStrip + splitStrip +
      '<div class="dash-md-grid">' +
        '<div class="dash-md-group"><h5>This month</h5>' +
          rw("Money in", money(x.in)) + rw("Money out", money(x.out)) + rw("Leads", num(x.leads)) + rw("Booked jobs", num1(x.booked)) + rw("Eyeballs", num(x.eyeballs)) + '</div>' +
        '<div class="dash-md-group running"><h5>Running total &middot; months 1&ndash;' + x.m + '</h5>' +
          rw("Money in", money(cin)) + rw("Money out", money(cout)) + rw("ROAS (after fees)", roas + "×") + rw("Leads", num(cld)) + rw("Booked jobs", num1(cbk)) + rw("Eyeballs", num(cey)) + '</div>' +
      '</div>';
  }

  function setMonth(i) { sel = i; syncMonthTabs(); drawChart(); renderMonthDetail(); }
  var PLAY_HTML = '<span class="dash-play-i">&#9654;</span><span class="dash-play-t">Play</span>';
  var PAUSE_HTML = '<span class="dash-play-i">&#10073;&#10073;</span><span class="dash-play-t">Pause</span>';
  function stopPlay() { if (playTimer) { clearInterval(playTimer); playTimer = null; } var b = $("[data-mo-play]"); if (b) { b.classList.remove("on"); b.innerHTML = PLAY_HTML; } }
  function play() {
    if (playTimer) { stopPlay(); return; }
    var b = $("[data-mo-play]"); if (b) { b.classList.add("on"); b.innerHTML = PAUSE_HTML; }
    if (sel >= MONTHS.length - 1) setMonth(0);
    playTimer = setInterval(function () { if (sel >= MONTHS.length - 1) { stopPlay(); return; } setMonth(sel + 1); }, 850);
  }

  // ---------- guided walkthrough: a real moving-spotlight product tour ----------
  // Each step spotlights a specific element (sel), sets the chart month (mo) and
  // metric, and the coach card repositions itself beside whatever is highlighted.
  var STEPS = [
    { sel: ".dash-kpi-hero", mo: 11, metric: "in", title: "Start with the scoreboard", body: "Twelve months on one screen: <b>$472k booked</b>, <b>$47.8k spent</b>, and a <b>9.9× return</b> after my fees. Everything below shows exactly how it got here." },
    { sel: ".dash-kpi.out", mo: 11, title: "Every dollar out &mdash; itemized", body: "No mystery retainer. <b>$28k</b> of this went straight to Google as ad spend; the rest is my fees and tools. You always see the split." },
    { sel: ".dash-months", mo: 0, metric: "in", title: "You&rsquo;re in the driver&rsquo;s seat", body: "Click any month &mdash; or hit <b>Play</b> &mdash; to watch the business build. I&rsquo;ll walk you through the turning points." },
    { sel: ".dash-chart", mo: 0, title: "Month 1 &mdash; the foundation", body: "Your custom site goes live; local SEO and blogging kick off. About <b>$500</b> in, nothing booked yet. Quiet on purpose &mdash; this is groundwork." },
    { sel: ".dash-md-net", mo: 1, title: "Month 2 &mdash; the low point", body: "Cumulative net bottoms out at <b>&minus;$1,000</b>. This is the deepest you ever go. You&rsquo;re investing, not losing." },
    { sel: ".dash-chart", mo: 2, title: "Month 3 &mdash; crossover to profit", body: "Social Media flips on, eyeballs jump, and the first roofing jobs close. You cross into the black at <b>+$6,000</b> &mdash; and never look back." },
    { sel: ".dash-chart", mo: 4, title: "Month 5 &mdash; pour on fuel", body: "We turn on <b>$2,000/mo Google Ads</b>. Spend steps up &mdash; but the booked work steps up faster." },
    { sel: ".dash-chart", mo: 6, title: "Month 7 &mdash; capture the rest", body: "Google LSA plus Missed-Visitor Leads. Now even anonymous visitors who never picked up the phone get captured as leads." },
    { sel: ".dash-floor", mo: 11, title: "And the honest floor", body: "The showcase is an above-median run. This is the <b>conservative floor</b> &mdash; ~90 leads and ~11 booked jobs from a funded, from-zero year. The numbers I&rsquo;d actually stand behind." },
    { sel: ".dash-timeline", mo: 11, title: "Every move, on the record", body: "Each play we ran &mdash; logged with what it cost and what it returned. No black boxes, ever." },
    { sel: ".dash-cta", mo: 11, metric: "in", title: "Month 12 &mdash; the payoff", body: "<b>$472k booked</b> on <b>~$48k spent</b>. That&rsquo;s <b>~$424,000 net</b> and a <b>9.9× return</b>, after everything. Want to see your version?" }
  ];
  var tourEls = null, tourStep = 0, tourActive = false, tourRaf = 0, onTourMove = null;
  function syncMetricBtns() { root.querySelectorAll("[data-metric]").forEach(function (x) { x.classList.toggle("on", x.getAttribute("data-metric") === current); }); }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function stepEl(i) { var s = STEPS[i]; return root.querySelector(s.sel) || d.querySelector(s.sel); }

  function buildTourDom() {
    if (tourEls) return tourEls;
    var spot = d.createElement("div"); spot.className = "dash-spot"; spot.hidden = true; spot.setAttribute("aria-hidden", "true");
    var card = d.createElement("div"); card.className = "dash-tour-card"; card.hidden = true;
    card.setAttribute("role", "dialog"); card.setAttribute("aria-label", "Dashboard walkthrough");
    card.innerHTML = '<span class="dash-tour-arrow" aria-hidden="true"></span>' +
      '<button type="button" class="dash-tour-x" aria-label="Close walkthrough">&times;</button>' +
      '<div class="dash-tour-step" data-tour-step></div><h4 data-tour-title></h4><p data-tour-body></p>' +
      '<div class="dash-tour-foot"><div class="dash-tour-dots" data-tour-dots></div>' +
      '<div class="dash-tour-nav"><button type="button" class="dash-tour-back" data-tour-back>Back</button>' +
      '<button type="button" class="dash-tour-next" data-tour-next>Next</button></div></div>';
    d.body.appendChild(spot); d.body.appendChild(card);
    card.querySelector(".dash-tour-x").addEventListener("click", endTour);
    card.querySelector("[data-tour-back]").addEventListener("click", function () { if (tourStep > 0) goStep(tourStep - 1); });
    card.querySelector("[data-tour-next]").addEventListener("click", function () { if (tourStep >= STEPS.length - 1) endTour(); else goStep(tourStep + 1); });
    d.addEventListener("keydown", function (e) { if (!tourActive) return; if (e.key === "Escape") endTour(); else if (e.key === "ArrowRight") { if (tourStep < STEPS.length - 1) goStep(tourStep + 1); } else if (e.key === "ArrowLeft") { if (tourStep > 0) goStep(tourStep - 1); } });
    tourEls = { spot: spot, card: card };
    return tourEls;
  }

  function positionTour() {
    if (!tourActive || !tourEls) return;
    var el = stepEl(tourStep), spot = tourEls.spot, card = tourEls.card;
    if (!el) { spot.style.opacity = "0"; return; }
    var r = el.getBoundingClientRect();
    var pad = (STEPS[tourStep].pad != null) ? STEPS[tourStep].pad : 12;
    var top = r.top - pad, left = r.left - pad, w = r.width + pad * 2, h = r.height + pad * 2;
    spot.style.opacity = "1";
    spot.style.top = top + "px"; spot.style.left = left + "px"; spot.style.width = w + "px"; spot.style.height = h + "px";

    var de = d.documentElement;
    var vw = de.clientWidth || window.innerWidth, vh = de.clientHeight || window.innerHeight, gap = 16, SAFE = 14;
    var botSafe = vw <= 860 ? 70 : SAFE;                 // leave room for the sticky call bar
    var cw = card.offsetWidth, ch = card.offsetHeight;
    var below = vh - (top + h), above = top, rightSp = vw - (left + w), leftSp = left;
    var place, cx, cy;
    if (below >= ch + gap + botSafe) { place = "bottom"; cy = top + h + gap; cx = clamp(left + w / 2 - cw / 2, SAFE, vw - cw - SAFE); }
    else if (above >= ch + gap + SAFE) { place = "top"; cy = top - gap - ch; cx = clamp(left + w / 2 - cw / 2, SAFE, vw - cw - SAFE); }
    else if (rightSp >= cw + gap + SAFE) { place = "right"; cx = left + w + gap; cy = clamp(top + h / 2 - ch / 2, SAFE, vh - ch - botSafe); }
    else if (leftSp >= cw + gap + SAFE) { place = "left"; cx = left - gap - cw; cy = clamp(top + h / 2 - ch / 2, SAFE, vh - ch - botSafe); }
    else { place = "center"; cx = clamp(left + w / 2 - cw / 2, SAFE, vw - cw - SAFE); cy = clamp(vh - ch - botSafe, SAFE, vh - ch - SAFE); }
    // final safety net: the card must always stay fully on-screen, even mid-scroll
    cx = clamp(cx, SAFE, Math.max(SAFE, vw - cw - SAFE));
    cy = clamp(cy, SAFE, Math.max(SAFE, vh - ch - botSafe));
    card.setAttribute("data-place", place);
    card.style.left = cx + "px"; card.style.top = cy + "px";

    // point the arrow at the target's center along the shared edge
    var arrow = card.querySelector(".dash-tour-arrow");
    if (place === "top" || place === "bottom") { arrow.style.left = clamp(left + w / 2 - cx, 20, cw - 20) + "px"; arrow.style.top = ""; }
    else if (place === "left" || place === "right") { arrow.style.top = clamp(top + h / 2 - cy, 20, ch - 20) + "px"; arrow.style.left = ""; }
  }

  function ensureVisible(el) {
    var r = el.getBoundingClientRect(), vh = window.innerHeight, c = r.top + r.height / 2;
    // scroll only when the target sits outside the comfortable middle band
    if (r.height < vh && (c < vh * 0.26 || c > vh * 0.74)) el.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
    else if (r.height >= vh && r.top > vh * 0.3) el.scrollIntoView({ block: "start", behavior: reduce ? "auto" : "smooth" });
  }

  function goStep(i) {
    tourStep = i; var s = STEPS[i], c = buildTourDom().card;
    if (s.metric) { current = s.metric; syncMetricBtns(); }
    if (typeof s.mo === "number") setMonth(s.mo);
    c.querySelector("[data-tour-step]").textContent = "Step " + (i + 1) + " of " + STEPS.length;
    c.querySelector("[data-tour-title]").innerHTML = s.title;
    c.querySelector("[data-tour-body]").innerHTML = s.body;
    c.querySelector("[data-tour-dots]").innerHTML = STEPS.map(function (_, j) { return '<button type="button" class="' + (j === i ? "on" : "") + '" data-tour-dot="' + j + '" aria-label="Step ' + (j + 1) + '"></button>'; }).join("");
    c.querySelectorAll("[data-tour-dot]").forEach(function (dot) { dot.addEventListener("click", function () { goStep(+dot.getAttribute("data-tour-dot")); }); });
    c.querySelector("[data-tour-back]").disabled = (i === 0);
    c.querySelector("[data-tour-next]").innerHTML = (i >= STEPS.length - 1) ? "Finish" : "Next &rarr;";
    var el = stepEl(i);
    if (el) { ensureVisible(el); positionTour(); setTimeout(positionTour, reduce ? 0 : 380); }
  }

  function startTour() {
    stopPlay(); buildTourDom(); tourActive = true; root.classList.add("tour-on"); d.body.classList.add("dash-tour-open");
    tourEls.spot.hidden = false; tourEls.card.hidden = false;
    onTourMove = function () { if (tourRaf) return; tourRaf = requestAnimationFrame(function () { tourRaf = 0; positionTour(); }); };
    window.addEventListener("scroll", onTourMove, true); window.addEventListener("resize", onTourMove);
    setTimeout(function () { tourEls.spot.classList.add("show"); tourEls.card.classList.add("show"); }, 20);
    goStep(0);
  }

  function endTour() {
    if (!tourActive) return; tourActive = false; root.classList.remove("tour-on"); d.body.classList.remove("dash-tour-open");
    if (onTourMove) { window.removeEventListener("scroll", onTourMove, true); window.removeEventListener("resize", onTourMove); onTourMove = null; }
    if (!tourEls) return;
    tourEls.spot.classList.remove("show"); tourEls.card.classList.remove("show");
    setTimeout(function () { if (!tourActive && tourEls) { tourEls.spot.hidden = true; tourEls.card.hidden = true; } }, 300);
  }

  function renderMetrics() {
    $("[data-dash-metrics]").innerHTML = METRICS.map(function (m) {
      return '<button type="button" class="dash-mbtn' + (m.k === current ? " on" : "") + '" data-metric="' + m.k + '">' + m.label + '</button>';
    }).join("");
    root.querySelectorAll("[data-metric]").forEach(function (b) {
      b.addEventListener("click", function () {
        current = b.getAttribute("data-metric");
        root.querySelectorAll("[data-metric]").forEach(function (x) { x.classList.toggle("on", x === b); });
        drawChart();
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
      '<b>The machine is humming</b><p>From a standing start to ' + MONTHS[11].leads + ' leads a month. ' + num1(MONTHS[11].booked) +
      ' booked jobs, ' + money(MONTHS[11].in) + ' in booked work &mdash; on ' + money(MONTHS[11].out) + ' spent that month.</p></div></div>');
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
  renderFloor();
  renderMetrics();
  renderMonths();
  drawChart();
  renderMonthDetail();
  animateInitial();
  renderTimeline();
  renderActions();
  var tb = $("[data-tour-launch]"); if (tb) tb.addEventListener("click", startTour);
})();
