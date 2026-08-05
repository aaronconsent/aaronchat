# Hey Aaron! — image prompts (Recraft.ai)

Internal. Excluded from the public build. Every image slot on the new homepage, with a Recraft-ready
prompt. The founder shots are **you** — real Aaron — with the scene staged by AI, not stock, not a
made-up face. So these are **image-to-image / reference** jobs in Recraft, not text-to-image.

## The one-time setup that makes all of these work

Shoot 4–6 clean reference photos of yourself first. Ten minutes:
- Plain wall, window light (soft, from one side), no direct sun on your face.
- Front-on, three-quarter left, three-quarter right, one looking down/away.
- One in a plain work shirt, one in something a touch sharper. No sunglasses, no hat, even light.

In Recraft, use **Image to image** (or a style/character reference if your plan has it), drop 2–3 of those
references in, and run the scene prompt below. Generate a few, pick the one where your face is unmistakably
you and the light is doing something. Regenerate the ones that drift.

**House look — paste at the end of every prompt:**
> natural photography, soft directional daylight, warm neutral color grade, shallow but not extreme depth of
> field, fine film grain, photorealistic, shot on 50mm, no HDR, no oversaturation, no plastic skin, keep the
> subject's real face and likeness unchanged.

**Never:** swap your face for a generic model, add fake logos/badges, or generate a scene implying clients
or results that aren't real.

---

## Slot: `hero`  ·  16:9 wide  ·  file `brand/media/ha/hero.jpg`

The first thing every visitor sees. You, mid-call, at a real desk. Confident and a little amused — like you
just told someone their setup is bad but you can fix it.

> A candid environmental portrait of [Aaron — use references] in his late forties at a plain wooden desk in a
> small, tidy home office, phone to his ear mid-conversation, half-smiling, gesturing with his free hand at a
> laptop showing a simple website. Plain dark work shirt, sleeves pushed up. Warm window light from the left,
> soft shadow on the right of his face. Uncluttered background, one plant, a stack of paper. Leave clean
> negative space in the upper-right third. [house look]

Framing note: shoot/crop so the right third is quiet — the floating "20 yrs" card and the page's air sit there.

## Slot: `aaron-truck`  ·  4:5 portrait  ·  file `brand/media/ha/aaron-truck.jpg`

The "who you're hiring" section. Puts you physically in the customer's world so a contractor sees a peer, not
an agency.

> A three-quarter environmental portrait of [Aaron — use references] leaning on the open tailgate of a clean
> work pickup on a gravel lot at the edge of an East Texas pine treeline, late afternoon. A closed laptop and
> a phone rest on the tailgate beside him. Relaxed, direct look at the camera, slight smile, arms loosely
> crossed. Plain work shirt. Low golden sun raking from the left, long soft shadows, a little dust in the air.
> [house look]

---

## Optional later: AI capability demos (these can be pure text-to-image)

If you want a section that literally shows off the image generation as a service, these are fine as fully
AI-generated *because they're openly labeled as demos*, not as you or as real jobs. Frame them "made in
30 seconds with the same tool I'll use for your ads." Keep them tasteful, on-navy-brand, and clearly demo.
Examples to generate on demand:
- A gleaming service van parked in front of a suburban home at golden hour, magazine-quality, no text.
- A close, dramatic shot of a wrench and a smart thermostat on a clean workbench, hard side light.
- A "before/after" pair of a tired yard sign vs. a crisp modern one.

These are the "look what we can make" pieces, not the trust pieces. Don't mix them up: trust = real you,
demos = clearly labeled AI.

---

## Where each file plugs in

Once generated, drop the file at the path above and replace the matching `<div class="imgslot" data-slot="…">`
in `index.html` with:

```html
<img src="/brand/media/ha/hero.jpg" alt="Aaron on the phone at his desk"
     width="1280" height="720" fetchpriority="high" decoding="async">
```

Keep the hero image under ~200KB as WebP (rule 9 speed budget). The others can lazy-load
(`loading="lazy"`).
