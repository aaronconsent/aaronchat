/* /insights — internal dashboard of every ZIP report run. Reads /api/insights (no auth).
   Activity, market intel, and auto-generated social / lead-gen angles. */
(function () {
  "use strict";
  var d = document, root = d.querySelector("[data-insights]");
  if (!root) return;
  var $ = function (s) { return root.querySelector(s); };
  // the Refresh button + "updated" stamp live in the page-hero, outside [data-insights]
  function setUpdated(txt) { var u = d.querySelector("[data-ins-updated]"); if (u) u.textContent = txt; }
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); };
  var money = function (n) { return n == null ? "—" : "$" + Math.round(n).toLocaleString("en-US"); };
  var num = function (n) { return n == null ? "—" : Math.round(n).toLocaleString("en-US"); };

  function ago(t) {
    var s = Math.max(0, (Date.now() - t) / 1000);
    if (s < 60) return "just now";
    if (s < 3600) return Math.floor(s / 60) + "m ago";
    if (s < 86400) return Math.floor(s / 3600) + "h ago";
    return Math.floor(s / 86400) + "d ago";
  }
  function place(e) {
    var p = [e.vcity, e.vregion].filter(Boolean).join(", ");
    if (!p) p = e.vcountry || "—";
    return p;
  }
  function tally(events, keyFn) {
    var m = {};
    events.forEach(function (e) { var k = keyFn(e); if (k == null || k === "") return; m[k] = (m[k] || 0) + 1; });
    return Object.keys(m).map(function (k) { return { k: k, n: m[k] }; }).sort(function (a, b) { return b.n - a.n; });
  }
  function bars(items, max, total) {
    if (!items.length) return '<p class="ins-empty">No data yet.</p>';
    return items.slice(0, max).map(function (r) {
      var pct = Math.max(3, Math.round(r.n / items[0].n * 100));
      return '<div class="ins-bar"><span class="ins-bar-k">' + esc(r.k) + '</span>' +
        '<span class="ins-bar-track"><i style="width:' + pct + '%"></i></span>' +
        '<span class="ins-bar-n">' + r.n + '</span></div>';
    }).join("");
  }

  function angles(events) {
    var out = [];
    var withGbp = events.filter(function (e) { return e.gbp && e.gbp.c != null; });
    var byTrade = tally(events, function (e) { return e.label; });
    if (byTrade[0]) out.push({ tag: "Most-run trade", txt: "<b>" + esc(byTrade[0].k) + "</b> is your most-looked-up trade (" + byTrade[0].n + " runs). Good candidate for the next case study or ad angle." });
    var tough = withGbp.slice().sort(function (a, b) { return b.gbp.c - a.gbp.c; })[0];
    if (tough) out.push({ tag: "Crowded market", txt: "<b>" + esc(tough.label) + "</b> in " + esc(tough.city || tough.state) + " has <b>" + tough.gbp.c + "</b> Map competitors. Post: “how a " + esc((tough.label || "").toLowerCase()) + " stands out when the map is packed.”" });
    var opp = withGbp.slice().sort(function (a, b) { return (a.gbp.s || 0) - (b.gbp.s || 0); })[0];
    if (opp) out.push({ tag: "Wide-open market", txt: "<b>" + esc(opp.city || opp.state) + "</b> " + esc((opp.label || "").toLowerCase()) + ": only <b>" + (opp.gbp.s || 0) + "</b> strong-reviewed competitors. Ripe for a “dominate Google Maps in a small market” pitch." });
    var pricey = events.filter(function (e) { return e.ads != null; }).sort(function (a, b) { return b.ads - a.ads; })[0];
    if (pricey) out.push({ tag: "Expensive leads", txt: "Priciest paid lead seen: <b>" + esc(pricey.label) + "</b> in " + esc(pricey.state) + " at <b>" + money(pricey.ads) + "</b>/lead on Google Ads. Lead-gen hook: “stop renting " + money(pricey.ads) + " clicks.”" });
    return out;
  }

  function render(data) {
    var ev = (data && data.events) || [];
    setUpdated(data && data.generatedAt ? "Updated " + ago(data.generatedAt) : "");
    if (!ev.length) {
      $("[data-ins-body]").innerHTML = '<div class="ins-empty-state"><h2>No lookups yet</h2>' +
        '<p>Run a report on the <a href="/plan/">growth plan</a> or the home-page calculator and it’ll show up here.</p></div>';
      return;
    }
    var uniqMarkets = {}; ev.forEach(function (e) { uniqMarkets[e.zip + "|" + e.state] = 1; });
    var live = ev.filter(function (e) { return e.live; }).length;
    var comps = ev.filter(function (e) { return e.gbp && e.gbp.c != null; }).map(function (e) { return e.gbp.c; });
    var avgComp = comps.length ? Math.round(comps.reduce(function (a, b) { return a + b; }, 0) / comps.length) : null;
    var byTrade = tally(ev, function (e) { return e.label; });
    var byState = tally(ev, function (e) { return e.state; });
    var byVisitor = tally(ev, function (e) { return place(e); });

    var tiles = [
      { l: "Report runs", v: num(ev.length) + (data.more ? "+" : ""), s: "showing latest" },
      { l: "Unique markets", v: num(Object.keys(uniqMarkets).length), s: "ZIP × state" },
      { l: "Top trade", v: byTrade[0] ? byTrade[0].k : "—", s: byTrade[0] ? byTrade[0].n + " runs" : "" },
      { l: "Avg Map competitors", v: avgComp == null ? "—" : num(avgComp), s: "GBP local pack" },
      { l: "Live-rate lookups", v: ev.length ? Math.round(live / ev.length * 100) + "%" : "—", s: "hit live CPL data" }
    ];

    var recent = ev.slice(0, 60).map(function (e) {
      return '<tr><td class="ins-t">' + ago(e.t) + '</td>' +
        '<td>' + esc(place(e)) + '</td>' +
        '<td><b>' + esc(e.label || e.trade) + '</b></td>' +
        '<td>' + esc(e.zip || "") + ' · ' + esc(e.city || e.state || "") + '</td>' +
        '<td class="ins-num">' + (e.gbp && e.gbp.c != null ? e.gbp.c : "—") + '</td>' +
        '<td class="ins-num">' + money(e.ads) + '</td>' +
        '<td class="ins-num">' + (e.gbp && e.gbp.p != null ? e.gbp.p : "—") + '</td></tr>';
    }).join("");

    $("[data-ins-body]").innerHTML =
      '<div class="ins-tiles">' + tiles.map(function (t) {
        return '<div class="ins-tile"><span class="ins-tl">' + esc(t.l) + '</span><b class="ins-tv">' + esc(t.v) + '</b><span class="ins-ts">' + esc(t.s) + '</span></div>';
      }).join("") + '</div>' +
      '<section class="ins-sec"><h2>Content &amp; lead-gen angles</h2><div class="ins-angles">' +
        angles(ev).map(function (a) { return '<div class="ins-angle"><span class="ins-angle-tag">' + esc(a.tag) + '</span><p>' + a.txt + '</p></div>'; }).join("") +
      '</div></section>' +
      '<div class="ins-cols">' +
        '<section class="ins-sec"><h2>Top trades</h2><div class="ins-barlist">' + bars(byTrade, 10) + '</div></section>' +
        '<section class="ins-sec"><h2>Top markets (state)</h2><div class="ins-barlist">' + bars(byState, 10) + '</div></section>' +
        '<section class="ins-sec"><h2>Who’s looking</h2><div class="ins-barlist">' + bars(byVisitor, 10) + '</div></section>' +
      '</div>' +
      '<section class="ins-sec"><h2>Recent report runs</h2><div class="ins-tablewrap"><table class="ins-table">' +
        '<thead><tr><th>When</th><th>Visitor</th><th>Trade</th><th>Market</th><th class="ins-num">Map comp.</th><th class="ins-num">Ads CPL</th><th class="ins-num">GBP leads</th></tr></thead>' +
        '<tbody>' + recent + '</tbody></table></div></section>';
  }

  function load() {
    setUpdated("Loading…");
    fetch("/api/insights").then(function (r) { return r.json(); }).then(render).catch(function () {
      $("[data-ins-body]").innerHTML = '<div class="ins-empty-state"><h2>Couldn’t load</h2><p>Try again in a moment.</p></div>';
    });
  }
  var rb = d.querySelector("[data-ins-refresh]"); if (rb) rb.addEventListener("click", load);
  load();
})();
