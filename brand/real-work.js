/* Real Work hub — trade filter (Tier A) + honest live-stat hydration.
   Live [data-live] values come ONLY from STATS_ENDPOINT. No endpoint (or a
   missing key) => the row collapses. No fabricated numbers ever ship; the
   "live" chip only ever means "pulled right now". Fixed verified outcomes
   (Jurassic 3,500, Dosey 600+) are hard-coded in markup with a "verified"
   stamp and no live chip. */
(function () {
  "use strict";
  var d = document;

  // ---------- trade filter (Tier A only) ----------
  var grid = d.getElementById("rw-grid");
  if (grid) {
    var cards = [].slice.call(grid.querySelectorAll(".rw-card"));
    var chips = [].slice.call(d.querySelectorAll(".rw-chip"));
    var empty = d.getElementById("rw-empty");
    var emptyTrade = d.getElementById("rw-empty-trade");
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        c.setAttribute("aria-pressed", "true");
        var trade = c.getAttribute("data-trade"), visible = 0;
        cards.forEach(function (card) {
          var ok = (trade === "all" || card.getAttribute("data-trade") === trade);
          card.classList.toggle("rw-hidden", !ok);
          if (ok) visible++;
        });
        if (empty) {
          empty.classList.toggle("show", visible === 0);
          if (visible === 0 && emptyTrade) emptyTrade.textContent = c.textContent.toLowerCase();
        }
      });
    });
  }

  // ---------- live stats ----------
  // PRODUCTION: point STATS_ENDPOINT at the stats.aaron.chat Worker (cached JSON,
  // shape { "g4.gbp.calls_30d": "29", ... }). Until then it's null and every live
  // row collapses — the page stands on real screenshots, verified numbers, and
  // click-through-and-check links.
  var STATS_ENDPOINT = null;

  function hydrate(data) {
    d.querySelectorAll("[data-live]").forEach(function (el) {
      var v = data && data[el.getAttribute("data-live")];
      if (v) { el.textContent = v; return; }
      var row = el.closest(".rw-row");
      if (row) row.style.display = "none";
    });
    // collapse any live-rows box left with no visible rows
    d.querySelectorAll(".rw-rows[data-property]").forEach(function (box) {
      var any = [].slice.call(box.querySelectorAll(".rw-row")).some(function (r) {
        return r.style.display !== "none";
      });
      if (!any) box.style.display = "none";
    });
  }

  if (STATS_ENDPOINT) {
    fetch(STATS_ENDPOINT).then(function (r) { return r.json(); }).then(hydrate).catch(function () { hydrate(null); });
  } else {
    hydrate(null);
  }
})();
