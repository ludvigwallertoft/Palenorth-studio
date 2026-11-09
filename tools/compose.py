"""Pale North mockup-pin builder (no AI, no credits).

Puts a print file into a framed room photo from rooms/ and saves a 1000x1500 Pinterest pin
(or a 2000x2000 Etsy listing image with --etsy).

  python3 tools/compose.py --room r07-12486418.jpg --art PRINT.jpg --out pins/x.jpg \
      --title "Nordic Cabin Line Art Print" --sub "instant download · Pale North Studio"
  python3 tools/compose.py --list            # rooms with style/mood tags

Rooms, frame openings and tags live in rooms/rooms.json. Add a room: put the photo in rooms/,
add an entry with "frame": [x0, y0, x1, y1] = the blank paper area inside the frame.
"""
import argparse, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOMS = json.load(open(os.path.join(ROOT, "rooms", "rooms.json")))
FONT = os.path.join(ROOT, "fonts", "Lora-Variable.ttf")
FONT_I = os.path.join(ROOT, "fonts", "Lora-Italic-Variable.ttf")
INK = (52, 56, 54, 255)


def warm(img):
    a = np.asarray(img).astype(float)
    a[..., 0] *= 1.045
    a[..., 2] *= 0.93
    a = a * 0.97 + 255 * 0.03
    img = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
    img = ImageEnhance.Contrast(img).enhance(1.03)
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    v = 1 - 0.13 * np.clip(d - 0.55, 0, 1) ** 1.5
    a = np.asarray(img).astype(float) * v[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))


def place(room_name, art_path):
    meta = ROOMS[room_name]
    x0, y0, x1, y1 = meta["frame"]
    x0 += 3; y0 += 3; x1 -= 3; y1 -= 3
    room = Image.open(os.path.join(ROOT, "rooms", room_name)).convert("RGB")
    art = Image.open(art_path).convert("RGB")
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    # cover the opening; print files have generous margins so a small even crop is fine
    s = max(bw / art.width, bh / art.height)
    aw, ah = int(art.width * s) + 1, int(art.height * s) + 1
    big = art.resize((aw, ah), Image.LANCZOS)
    paper = big.crop(((aw - bw) // 2, (ah - bh) // 2, (aw - bw) // 2 + bw, (ah - bh) // 2 + bh))
    paper = paper.filter(ImageFilter.GaussianBlur(0.4))
    r = np.asarray(room).astype(float)
    p = np.asarray(paper).astype(float) / 255.0
    orig = r[y0:y1 + 1, x0:x1 + 1].copy()
    # smooth lighting from the blank paper keeps the photo's light/shadow on the print
    light = np.asarray(Image.fromarray(orig.astype("uint8")).filter(ImageFilter.GaussianBlur(70))).astype(float)
    light = np.clip(light / np.percentile(light.mean(axis=2), 97), 0, 1) * 0.97
    new = 255 * light * p
    if meta.get("foreground"):
        lum = orig.mean(axis=2); sat = orig.max(axis=2) - orig.min(axis=2)
        m = ((lum > 185) & (sat < 40)).astype("uint8") * 255
        m = np.asarray(Image.fromarray(m).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(2))).astype(float)[..., None] / 255
        new = m * new + (1 - m) * orig
    r[y0:y1 + 1, x0:x1 + 1] = new
    return warm(Image.fromarray(np.clip(r, 0, 255).astype("uint8")))


def caption(img, title, sub, band_top):
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    d.rectangle([0, band_top, W, H], fill=(250, 246, 240, 238))
    k = W / 1000
    f1 = ImageFont.truetype(FONT, int(46 * k)); f2 = ImageFont.truetype(FONT_I, int(30 * k))
    for txt, f, y in ((title, f1, band_top + 30 * k), (sub or "", f2, band_top + 100 * k)):
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=INK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--room"); ap.add_argument("--art"); ap.add_argument("--out")
    ap.add_argument("--title"); ap.add_argument("--sub")
    ap.add_argument("--etsy", action="store_true", help="2000x2000 listing image, no caption")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, v in ROOMS.items():
            print(k, "|", v.get("style"), "|", v.get("mood"))
        return
    img = place(a.room, a.art)
    if a.etsy:
        w, h = img.size
        side = min(w, h)
        x0, y0, x1, y1 = ROOMS[a.room]["frame"]
        cy = min(max((y0 + y1) // 2, side // 2), h - side // 2)
        img = img.crop((0, cy - side // 2, side, cy + side // 2)).resize((2000, 2000), Image.LANCZOS)
    else:
        img = img.resize((1000, 1500), Image.LANCZOS)
        if a.title:
            caption(img, a.title, a.sub, 1325)
    img.convert("RGB").save(a.out, quality=90, optimize=True)
    print(a.out)


if __name__ == "__main__":
    main()
