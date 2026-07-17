#!/usr/bin/env python3
"""Generate stylized Photo Avatar 'looks' (images) of Aaron via HeyGen.

Trains the photo-avatar group's generation model if needed, then generates a
look from a text prompt (outfit + scene), downloads the images, opens the folder.

Key: macOS Keychain service 'heygen-aaron', account 'aaron' (never printed).
Usage: python3 heygen_look.py "<prompt>" [orientation] [pose]
  orientation: horizontal | vertical | square   (default horizontal)
  pose: half_body | close_up | full_body        (default half_body)
"""
import subprocess, json, urllib.request, urllib.error, time, os, sys

GROUP = "10c7ced9c03342d88dbae490bf48271c"  # "Real Aaron" photo-avatar group
OUTDIR = os.path.expanduser("~/GIT/aaron-chat-mirror/site/brand/media/looks")

HG = subprocess.run(["security", "find-generic-password", "-s", "heygen-aaron",
                     "-a", "aaron", "-w"], capture_output=True, text=True).stdout.strip()


def api(url, data=None):
    h = {"X-Api-Key": HG, "Content-Type": "application/json"}
    r = urllib.request.Request(url, data=(json.dumps(data).encode() if data is not None else None), headers=h)
    try:
        return json.loads(urllib.request.urlopen(r, timeout=120).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:400]}


DONE = ("ready", "completed", "success")


def ensure_trained(max_attempts=4):
    for attempt in range(1, max_attempts + 1):
        st = api(f"https://api.heygen.com/v2/photo_avatar/train/status/{GROUP}")
        status = st.get("data", {}).get("status")
        print(f"[train] attempt {attempt}: current status = {status}")
        if status in DONE:
            return True
        # (re)submit training
        print(f"[train] attempt {attempt}: submitting training…")
        d = api("https://api.heygen.com/v2/photo_avatar/train", {"group_id": GROUP})
        if d.get("_http"):
            raise SystemExit(f"[train] submit HTTP {d['_http']}: {d['_body']}")
        # poll this attempt (~35 min max)
        for i in range(140):
            time.sleep(15)
            st = api(f"https://api.heygen.com/v2/photo_avatar/train/status/{GROUP}")
            data = st.get("data", {})
            status = data.get("status")
            print(f"[train] a{attempt}[{i}] {status}")
            if status in DONE:
                return True
            if status in ("error", "failed"):
                msg = (data.get("error_msg") or "").lower()
                print(f"[train] errored: {data.get('error_msg')}")
                if "transient" in msg or "try again" in msg:
                    print("[train] transient — will resubmit")
                    break  # -> outer loop resubmits
                raise SystemExit("[train] non-transient failure: " + str(data.get("error_msg")))
    raise SystemExit(f"[train] exhausted {max_attempts} attempts")


def generate_look(prompt, orientation="horizontal", pose="half_body"):
    body = {"group_id": GROUP, "prompt": prompt, "orientation": orientation,
            "pose": pose, "style": "Realistic"}
    print("[look] submitting generation…")
    d = api("https://api.heygen.com/v2/photo_avatar/look/generate", body)
    if d.get("_http"):
        raise SystemExit(f"[look] submit HTTP {d['_http']}: {d['_body']}")
    gen = d.get("data", {})
    gid = gen.get("generation_id") or gen.get("id")
    print("[look] generation_id:", gid)
    imgs = None
    for i in range(50):
        time.sleep(10)
        s = api(f"https://api.heygen.com/v2/photo_avatar/generation/{gid}")
        sd = s.get("data", {})
        status = sd.get("status")
        print(f"[look] [{i}] {status}")
        if status in ("success", "completed"):
            imgs = sd.get("image_url_list") or sd.get("image_urls") or []
            break
        if status in ("failed", "error"):
            raise SystemExit("[look] failed: " + json.dumps(sd)[:300])
    if not imgs:
        raise SystemExit("[look] no images / timeout")
    os.makedirs(OUTDIR, exist_ok=True)
    existing = len([f for f in os.listdir(OUTDIR) if f.endswith(".jpg")])
    paths = []
    for n, u in enumerate(imgs, existing + 1):
        p = os.path.join(OUTDIR, f"professor-aaron-{n}.jpg")
        open(p, "wb").write(urllib.request.urlopen(u, timeout=120).read())
        paths.append(p)
        print("[look] saved", p, os.path.getsize(p) // 1024, "KB")
    subprocess.run(["open", OUTDIR])
    return paths


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "wearing a fitted charcoal tweed blazer over a crisp white button-down shirt, "
        "confident warm smile, standing in a bright modern classroom in front of a large "
        "green chalkboard covered with hand-drawn white letters 'A+', simple bar charts and "
        "a small house doodle. Cinematic warm side lighting, shallow depth of field, sharp "
        "editorial photography, professional and approachable")
    orientation = sys.argv[2] if len(sys.argv) > 2 else "horizontal"
    pose = sys.argv[3] if len(sys.argv) > 3 else "half_body"
    ensure_trained()
    generate_look(prompt, orientation, pose)
    print("DONE")
