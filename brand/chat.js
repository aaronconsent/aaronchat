/* Chatwoot live-chat widget. Loaded sitewide via a <script src> tag so there is
   one place to edit or remove it. websiteToken is a public client identifier,
   safe to ship in the page. Remove this file's <script> tags to disable. */
(function (d, t) {
  var BASE_URL = "https://app.chatwoot.com";
  var g = d.createElement(t), s = d.getElementsByTagName(t)[0];
  g.src = BASE_URL + "/packs/js/sdk.js";
  g.async = true;
  s.parentNode.insertBefore(g, s);
  g.onload = function () {
    window.chatwootSDK.run({
      websiteToken: "U6Mnmn9RhwBcSsgurSss68vZ",
      baseUrl: BASE_URL
    });
  };
})(document, "script");
