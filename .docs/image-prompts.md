# Image prompts — aaron.chat

Every image slot on the site, with a generation-ready prompt. On-page placeholders carry a `data-slot`
matching the IDs below. When an asset is generated, drop it at the given path and replace the
`<div class="imgslot">` with an `<img>`.

Internal file. Excluded from the public build via `.assetsignore`.

---

## Before you generate anything

**Slots marked LIKENESS need a reference photo of Aaron.** Text-to-image cannot produce a specific
real person. Two workable routes:

- **OpenAI `gpt-image-1`** with the image-edit endpoint: pass 2 to 4 clear reference photos (front-on,
  three-quarter, good even light, no sunglasses, no heavy shadow) plus the prompt. Best likeness
  fidelity of the two, and it handles text-in-image well.
- **Recraft** image-to-image, or a Recraft style trained on a set of Aaron photos. Better for a
  consistent house look across many images; weaker at exact likeness from a single pass.

Shoot the references first: a plain wall, window light, three or four angles, one in a work shirt and
one in something sharper. Ten minutes with a phone is enough and it raises the ceiling on every
LIKENESS slot below.

**Slots marked CONCEPT need no reference** and can be generated straight from the prompt.

**House look, append to every prompt:** *natural photography, soft directional daylight, warm neutral
grade, muted desaturated palette leaning deep green and warm off-white, fine film grain, shallow but
not extreme depth of field, no lens flare, no HDR, no oversaturation, no plastic skin, photorealistic,
shot on 50mm.*

**Never generate:** fake client photos, fake testimonial headshots, stock-looking "team collaborating"
scenes, or any image implying customers or results we don't have. See `/style-guide/directives/`.

---

## Priority 1 — the connection shots

These do the heaviest lifting. A contractor is deciding whether to trust one specific person, and right
now the site shows a costume character instead of a man he could picture in his shop.

### `hero-aaron` — LIKENESS — 4:5 portrait — `brand/media/aaron-hero.jpg`

The single most important image on the site. Replaces the schoolteacher costume shot in the homepage hero.

> A candid environmental portrait of a man in his late forties standing beside a large dark green
> chalkboard in a plain room, turned three-quarters toward camera, mid-sentence, one hand still holding
> a piece of chalk at his side. He wears a plain dark work shirt, sleeves pushed up. Relaxed, direct,
> faintly amused expression, looking straight at the lens like he has just been asked a blunt question.
> On the chalkboard behind him, handwritten in chalk, a simple column of six short lines with tick marks
> beside them. Warm window light from the left, soft shadow on the right side of his face. Plain scuffed
> wall, no clutter, no props beyond the chalkboard.

Notes: no gown, no bow tie, no costume. The credibility comes from him looking like someone who works,
not from a schoolteacher gag. Leave clean negative space on the right third for the headline to sit over.

### `aaron-truck` — LIKENESS — 16:9 — `brand/media/aaron-truck.jpg`

For the About page and the founder band on the homepage. Puts him physically in the customer's world.

> The same man leaning against the open tailgate of a dusty pickup truck on a gravel lot at the edge of
> a pine treeline in East Texas, late afternoon. He is looking at a phone in one hand, slight frown of
> concentration, a laptop closed on the tailgate beside him. Plain work shirt. Golden low sun raking
> across from the left, long shadows, dust in the air. Wide shot with him occupying the left third.

### `aaron-desk` — LIKENESS — 1:1 — `brand/media/aaron-desk.jpg`

Small, for the About page and the emailed report-card signature.

> Close three-quarter portrait of the same man at a plain wooden desk in a small home office, a single
> monitor glowing off-frame to his left, a stack of paper report cards with red pen marks on them beside
> his elbow. He is mid-laugh, looking off-camera. Evening, warm lamp light, dark room behind him.

---

## Priority 2 — the AI capability showcase

**This is the section that proves the pitch.** Framed on-page as "every image on this site was generated
by the same stack that builds your website", these stop being a costume gag and become the argument.
Keep them to four. Seven was too many and diluted it.

Each is the same man teaching in a different century. Consistency of face across all four matters more
than any individual image, so generate them in one session from the same references.

### `era-1` — LIKENESS — 4:5 — `brand/media/era-scribe.jpg`
> The same man as an ancient scribe in a sunlit stone room, seated cross-legged with a clay tablet on his
> knee and a reed stylus, mid-explanation, gesturing at a row of marks scratched into the tablet. Linen
> robes. Hard shaft of sunlight from a high window, dust motes, deep shadow.

### `era-2` — LIKENESS — 4:5 — `brand/media/era-renaissance.jpg`
> The same man as a Renaissance workshop master in a dim studio, leaning over a large sheet of paper
> covered in geometric diagrams, holding a pair of dividers, explaining to someone off-frame. Dark wool
> doublet, ink-stained fingers. Single window light, Caravaggio-style falloff into darkness.

### `era-3` — LIKENESS — 4:5 — `brand/media/era-schoolhouse.jpg`
> The same man as a one-room prairie schoolhouse teacher in the 1890s, standing at a small blackboard
> with a wooden pointer, chalk dust on his dark waistcoat, mid-sentence. Rough plank walls, a wood stove,
> hard midday light through tall windows. Slightly faded, warm, period-photographic.

### `era-4` — LIKENESS — 4:5 — `brand/media/era-now.jpg`
> The same man in the present day in a plain room, standing at a large monitor showing a grid of coloured
> grade badges, gesturing at it with a red marker in his hand, looking back over his shoulder at the
> camera. Modern plain work shirt. Cool screen light on his face, warm lamp behind. Photorealistic.

Caption to run under the set: *Four centuries, one teacher. Every one of these was generated by the same
AI stack that builds your website. That is the point.*

---

## Priority 3 — service and page art

CONCEPT slots. No likeness needed. All should read as objects on a desk, not as icons or illustrations.

### `svc-website` — CONCEPT — 16:9 — `brand/media/svc-website.jpg`
> An overhead flat-lay on a scarred wooden workbench: a laptop showing a simple clean website, a
> carpenter's pencil, a folded tape measure, and a paper wireframe sketch with red pen corrections on it.
> Hard afternoon window light from the left, strong shadows.

### `svc-reviews` — CONCEPT — 16:9 — `brand/media/svc-reviews.jpg`
> An overhead flat-lay: a phone showing a five-star review, face up on a clipboard holding a work order,
> a stub of red pencil, and a coffee ring on the paper. Worn steel surface underneath.

### `svc-social` — CONCEPT — 16:9 — `brand/media/svc-social.jpg`
> An overhead flat-lay: a phone propped against a paint can, filming a small before-and-after pair of
> printed photographs on a workbench. Utility light, honest shadows.

### `svc-email` — CONCEPT — 16:9 — `brand/media/svc-email.jpg`
> An overhead flat-lay: a stack of plain envelopes on a desk, the top one open with a short typed letter
> visible, a rubber stamp and ink pad beside it. Warm side light.

### `svc-ads` — CONCEPT — 16:9 — `brand/media/svc-ads.jpg`
> A weathered hand-painted sign on the side of a rural East Texas building advertising a plumbing shop,
> photographed straight on in late afternoon light, pine trees reflected in a window at the edge of frame.

### `svc-gbp` — CONCEPT — 16:9 — `brand/media/svc-gbp.jpg`
> An overhead flat-lay: a paper map of a lake region with a single red pin pushed into it, a phone beside
> it showing a map pin, and a set of truck keys. Strong directional light.

### `svc-ai` — CONCEPT — 16:9 — `brand/media/svc-ai.jpg`
> A dark green chalkboard photographed straight on, covered edge to edge in handwritten chalk diagrams
> connecting small boxes with arrows, one box circled hard in red chalk. No people. Slight chalk haze.

### `report-card-hero` — CONCEPT — 16:9 — `brand/media/report-card-hero.jpg`
> A single paper report card lying on a truck dashboard in daylight, a red pen resting across it, a
> letter grade circled in red at the top. Shot at a low three-quarter angle, windshield glare at the top
> edge, pine trees out of focus beyond the glass.

---

## Keep as-is

`brand/media/portfolio/*.jpg` are real automated screenshots of live client sites. They are evidence we
built the work. Do not replace them with generated imagery.
