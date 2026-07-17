// Lead form → /api/contact (existing Worker + Resend). Fires Meta Lead event on success.
(function () {
  document.querySelectorAll("form.lead-form").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = form.querySelector(".form-status");
      var btn = form.querySelector("button[type=submit]");
      var f = new FormData(form);
      var trade = f.get("trade") || "";
      var payload = {
        name: f.get("name") || "",
        business: f.get("business") || "",
        phone: f.get("phone") || "",
        email: f.get("email") || "",
        message: "Report card request" + (trade ? " · Trade: " + trade : ""),
        _source: form.dataset.source || "toc-site",
        _gotcha: f.get("_gotcha") || ""
      };
      btn.disabled = true; btn.textContent = "Sending…";
      fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) {
          status.className = "form-status ok";
          status.textContent = "Got it — your report card and a call from Aaron are on the way.";
          form.reset();
          if (window.fbq) fbq("track", "Lead");
        } else {
          status.className = "form-status err";
          status.textContent = d.error || "Something went wrong — call or text 713-384-8985 instead.";
        }
      }).catch(function () {
        status.className = "form-status err";
        status.textContent = "Couldn't send — call or text 713-384-8985 instead.";
      }).finally(function () {
        btn.disabled = false; btn.textContent = form.dataset.btn || "Send me my report card";
      });
    });
  });
})();
