# Twilio A2P 10DLC — resubmission packet

Internal. Copy the relevant parts into the Twilio campaign resubmission. Last updated 2026-07-23.

## The fix, in one line

SMS consent now appears **exactly once** on every form — a standalone, optional, unchecked,
**marketing-only** checkbox. No form bundles marketing SMS consent with any other consent.

---

## 1. Direct links to every form that collects a mobile number

- **Quote form (primary opt-in):** https://aaron.chat/quote/
- **Report card request:** https://aaron.chat/report-card/  (SMS opt-in appears on the final step, "Where do we send it?", after entering a business name)
- **HVAC landing lead form:** https://aaron.chat/hvac-marketing/
- **Plumbing landing lead form:** https://aaron.chat/plumber-marketing/

There is no scheduling form. All appointment setting happens by phone or in the reply email.

Supporting policy pages (linked from every consent checkbox):
- **Privacy Policy (SMS section):** https://aaron.chat/privacy-policy/#sms
- **Terms of Service (SMS section):** https://aaron.chat/terms-of-service/#sms

## 2. Screenshots to attach

Screenshot each URL above so the reviewer can see both the **mobile-number field** and the
**marketing SMS consent checkbox** in the same frame. Easiest capture: open the URL, scroll so the
form fills the screen. On /report-card/, type any business name, click through to the final step.

Each screenshot shows: the mobile phone input, then the optional "Text messages only" checkbox with
its full disclosure.

## 3. Required consent disclosure (this is the exact on-page language)

The **marketing** opt-in is its own checkbox, unchecked by default, and reads:

> **Optional. Text messages only.** I agree to receive **recurring automated marketing text messages**
> (promotions, offers, tips) from Hey Aaron! Marketing at the mobile number I provided. Consent is not
> a condition of any purchase. Message frequency varies. Message and data rates may apply. Reply
> **STOP** to unsubscribe, **HELP** for help. See our Privacy Policy and Terms.

The **required** contact checkbox (quote form only) is separate and covers **phone and email only** —
it does not mention SMS, so nothing is combined:

> **Required.** I agree that Hey Aaron! Marketing may contact me about this request by phone call and
> email at the number and address I provided.

## 4. Opt-out language

Every consent block states: **"Reply STOP to unsubscribe, HELP for help."** The quote form also repeats
below the button: "You can opt out of texts any time by replying STOP." The Privacy Policy and Terms SMS
sections both document STOP/HELP and that opt-in data is never shared.

---

## Paste this into the campaign's opt-in / "how do end users consent" field

> End users opt in to marketing text messages through a dedicated, optional, unchecked checkbox on our
> web forms (primary: https://aaron.chat/quote/). This marketing SMS consent is collected separately
> from any other consent: a separate required checkbox covers phone and email contact only and never
> mentions SMS, so marketing consent is never bundled with informational or transactional consent. The
> marketing checkbox states the sender name (Hey Aaron! Marketing), that messages are recurring
> automated marketing messages, that consent is not a condition of purchase, that message frequency
> varies, that message and data rates may apply, and includes "Reply STOP to unsubscribe, HELP for
> help," with links to our Privacy Policy and Terms. Consent applies only to this sender and this
> marketing campaign. We store a per-submission consent record (timestamp, IP, user agent, page URL,
> and the exact consent text version shown).

## Sample messages (match these to your campaign's sample-message field)

- Marketing: "Hey Aaron! Marketing: New this month — free website audit for Lake Livingston HVAC
  shops. Reply STOP to opt out, HELP for help."
- Marketing: "Hey Aaron! Marketing: Your competitors added 12 reviews last month. Want the game plan?
  Reply STOP to opt out."

## Notes

- Consent version currently recorded: **2026-07-23** (constant `QUOTE_CONSENT_VERSION` in `_worker.js`).
- If a reviewer still objects, the objection is almost always a mismatch between the campaign
  *description* text and the page. Make the description above match the live page word-for-word.
- Not legal advice — built to the CTIA / carrier A2P checklist.

