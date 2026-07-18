/* Top of Class Marketing — site chrome enhancements.
   Sticky-header state, accessible mobile menu, mobile sticky call bar,
   and fire-once scroll reveals. Pure vanilla, progressive: the page works
   fully without it. */
(function () {
  "use strict";
  var head = document.querySelector(".site-head");
  var nav = document.querySelector(".site-nav");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- sticky header state via a sentinel (no scroll listener) ---- */
  if (head && "IntersectionObserver" in window) {
    var sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "position:absolute;top:0;height:1px;width:1px;";
    document.body.prepend(sentinel);
    new IntersectionObserver(function (e) {
      head.classList.toggle("is-stuck", !e[0].isIntersecting);
    }, { threshold: 0 }).observe(sentinel);
  }

  /* ---- mobile menu built from the desktop nav ---- */
  if (head && nav) {
    var toggle = document.createElement("button");
    toggle.className = "nav-toggle";
    toggle.setAttribute("aria-label", "Open menu");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "m-nav");
    toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>';
    head.querySelector(".wrap").appendChild(toggle);

    var overlay = document.createElement("nav");
    overlay.className = "m-nav";
    overlay.id = "m-nav";
    overlay.hidden = true;
    var top = document.createElement("div");
    top.className = "m-top";
    var brand = document.querySelector(".logo");
    top.innerHTML = (brand ? '<span class="logo" style="pointer-events:none">' + brand.innerHTML + "</span>" : "") +
      '<button class="m-close" aria-label="Close menu">&times;</button>';
    overlay.appendChild(top);
    // clone the nav links
    nav.querySelectorAll("a").forEach(function (a) {
      var c = a.cloneNode(true);
      overlay.appendChild(c);
    });
    var foot = document.createElement("div");
    foot.className = "m-foot";
    foot.innerHTML = 'Call or text <a href="tel:+17133848985">713-384-8985</a><br>' +
      '<a href="mailto:hello@aaron.chat">hello@aaron.chat</a>';
    overlay.appendChild(foot);
    document.body.appendChild(overlay);

    var closeBtn = overlay.querySelector(".m-close");
    var lastFocus = null;
    var focusables = function () { return overlay.querySelectorAll('a[href],button'); };

    function open() {
      lastFocus = document.activeElement;
      overlay.hidden = false;
      requestAnimationFrame(function () { overlay.classList.add("open"); });
      toggle.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
      var f = focusables(); if (f.length) f[0].focus();
    }
    function close() {
      overlay.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
      setTimeout(function () { overlay.hidden = true; }, reduce ? 0 : 280);
      if (lastFocus) lastFocus.focus();
    }
    toggle.addEventListener("click", function () {
      toggle.getAttribute("aria-expanded") === "true" ? close() : open();
    });
    closeBtn.addEventListener("click", close);
    overlay.addEventListener("click", function (ev) {
      if (ev.target.tagName === "A") close();
    });
    document.addEventListener("keydown", function (ev) {
      if (overlay.hidden) return;
      if (ev.key === "Escape") { close(); return; }
      if (ev.key === "Tab") {
        var f = focusables(); if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) { last.focus(); ev.preventDefault(); }
        else if (!ev.shiftKey && document.activeElement === last) { first.focus(); ev.preventDefault(); }
      }
    });
  }

  /* ---- mobile sticky call / CTA bar ---- */
  if (nav) {
    var ctaLink = nav.querySelector("a.cta");
    var ctaHref = ctaLink ? ctaLink.getAttribute("href") : "/report-card/";
    var ctaText = "Free report card"; // keep the sticky-bar label short + punchy
    var bar = document.createElement("div");
    bar.className = "mbar";
    bar.innerHTML =
      '<a class="mbar-call" href="tel:+17133848985">' +
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M6.6 10.8a15.9 15.9 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.4.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.5-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 .8-.3 1.1l-2.2 2.1Z"/></svg>' +
        "Call / Text</a>" +
      '<a class="mbar-cta" href="' + ctaHref + '">' + ctaText + "</a>";
    document.body.appendChild(bar);
    document.body.classList.add("has-mbar");
  }

  /* ---- fire-once scroll reveals ---- */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el, i) {
      el.style.transitionDelay = (i % 6) * 60 + "ms";
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }
})();
