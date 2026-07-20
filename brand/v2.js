/* v2 — cinematic homepage behaviour.
   No libraries. Reveals use IntersectionObserver with a failsafe so content is
   never gated on a transition; parallax is native CSS scroll-timeline where the
   browser supports it. Everything degrades to a static, readable page. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- grain: generate the noise tile once, as a data URI ---- */
  (function grain() {
    var n = 128, c = document.createElement("canvas");
    c.width = c.height = n;
    var x = c.getContext("2d"), d = x.createImageData(n, n), p = d.data;
    for (var i = 0; i < p.length; i += 4) {
      var v = (Math.random() * 255) | 0;
      p[i] = p[i + 1] = p[i + 2] = v; p[i + 3] = 22;
    }
    x.putImageData(d, 0, 0);
    document.documentElement.style.setProperty("--noise", "url(" + c.toDataURL() + ")");
  })();

  /* ---- reveals: observe, then hard-failsafe so nothing can stay hidden ---- */
  var rises = [].slice.call(document.querySelectorAll(".rise"));
  function showAll() { rises.forEach(function (el) { el.classList.add("in"); }); }
  if (reduce || !("IntersectionObserver" in window)) {
    showAll();
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
    rises.forEach(function (el) { io.observe(el); });
    setTimeout(showAll, 2500);   // if anything never fires, it still shows
  }

  /* ---- pipeline: highlight the step in the middle of the viewport ---- */
  var steps = [].slice.call(document.querySelectorAll(".pipe-step"));
  if (steps.length && !reduce && "IntersectionObserver" in window) {
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { e.target.classList.toggle("in", e.isIntersecting); });
    }, { rootMargin: "-42% 0px -42% 0px" });
    steps.forEach(function (el) { so.observe(el); });
  } else { steps.forEach(function (el) { el.classList.add("in"); }); }

  /* ---- before / after: a real range input so it is keyboard + AT usable ---- */
  var ba = document.querySelector(".ba");
  if (ba) {
    var range = ba.querySelector(".ba-range");
    var set = function (v) { ba.style.setProperty("--split", v + "%"); };
    range.addEventListener("input", function () { set(this.value); });
    set(range.value);
  }

  /* ---- playground: the prompt toy ---- */
  var toy = document.querySelector("[data-toy]");
  if (toy) {
    var out = toy.querySelector(".toy-out");
    var chips = [].slice.call(toy.querySelectorAll(".chip"));
    var run = toy.querySelector(".btn2");
    var LOOKS = {
      "Astronaut": ["a cracked visor reflecting a subdivision at dawn", "EVA tether drifting past a satellite dish", "moondust on a work boot"],
      "Cowboy": ["dust devil rolling past a service truck", "hat brim shadow across one eye, hard noon sun", "spurs on the tailgate of a flatbed"],
      "Samurai": ["rain on lacquered armour, lanterns behind", "a blade held low, steam rising off the street", "cherry blossom stuck to a wet pauldron"],
      "Cyborg": ["chrome jaw catching a green terminal glow", "cable braid running under the collar", "one human eye, one aperture"]
    };
    var GRADE = ["shot on 35mm, halation, deep shadow", "anamorphic 2.39:1, practical light only", "high-contrast, single key, no fill"];
    var pick = function (a) { return a[(Math.random() * a.length) | 0]; };
    var current = "Astronaut";
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
        c.setAttribute("aria-pressed", "true");
        current = c.textContent.trim();
        render();
      });
    });
    function render() {
      out.textContent = current.toUpperCase() + " AARON — " + pick(LOOKS[current] || LOOKS.Astronaut) +
        ", " + pick(GRADE) + ".";
    }
    run.addEventListener("click", render);
    render();
  }

  /* ---- wall: drag to scroll with a pointer, arrows still work ---- */
  var wall = document.querySelector(".wall");
  if (wall) {
    var down = false, sx = 0, sl = 0;
    wall.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "touch") return;      // let native touch scrolling do its job
      down = true; sx = e.clientX; sl = wall.scrollLeft; wall.setPointerCapture(e.pointerId);
      wall.style.cursor = "grabbing";
    });
    wall.addEventListener("pointermove", function (e) {
      if (!down) return; wall.scrollLeft = sl - (e.clientX - sx);
    });
    ["pointerup", "pointercancel"].forEach(function (t) {
      wall.addEventListener(t, function () { down = false; wall.style.cursor = ""; });
    });
  }
})();
