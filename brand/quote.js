/* Quote form -> /api/quote. Requires the consent checkbox, captures the page URL
   for the consent record, and fires a Meta Lead event on success. */
(function () {
  var form = document.getElementById("qform");
  if (!form) return;
  var status = form.querySelector(".form-status");
  var btn = form.querySelector(".qf-submit");

  function err(msg) {
    status.className = "form-status err";
    status.textContent = msg;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    status.className = "form-status";
    status.textContent = "";

    var f = new FormData(form);
    var name = (f.get("name") || "").trim();
    var phone = (f.get("phone") || "").trim();
    var email = (f.get("email") || "").trim();
    var contactConsent = form.querySelector("#q-consent-contact").checked;
    var marketingConsent = form.querySelector("#q-consent-marketing").checked;

    if (!name) return err("What's your name?");
    if (!phone || phone.replace(/\D/g, "").length < 10) return err("Add a phone number we can reach you at.");
    if (!email || !/\S+@\S+\.\S+/.test(email)) return err("That email looks off — mind double-checking it?");
    if (!contactConsent) return err("Please check the box so we're allowed to contact you.");

    var payload = {
      name: name,
      business: (f.get("business") || "").trim(),
      phone: phone,
      email: email,
      trade: (f.get("trade") || "").trim(),
      message: (f.get("message") || "").trim(),
      consent_contact: true,
      consent_marketing: marketingConsent,
      _page: location.href,
      _gotcha: f.get("_gotcha") || ""
    };

    btn.disabled = true;
    var label = btn.textContent;
    btn.textContent = "Sending…";

    fetch("/api/quote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.ok) {
          status.className = "form-status ok";
          status.textContent = "Got it. Aaron will get back to you within one business day.";
          form.reset();
          if (window.fbq) fbq("track", "Lead");
        } else {
          err(d.error || "Something went wrong. Call or text 713-384-8985 instead.");
        }
      })
      .catch(function () {
        err("Couldn't send. Call or text 713-384-8985 instead.");
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = label;
      });
  });
})();
