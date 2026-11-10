"""Pin pipeline for Pale North (Tove makes pins, Pia schedules, Nora steers). Pure Python, no AI.

All pins live in pins/pins.json (a list). Status flow:
  vantar-lank  -> made by Tove, product not yet live on Etsy (no listing link)
  klar         -> has an Etsy link, waiting to be scheduled
  schemalagd   -> scheduled in Metricool (has metricool_id + scheduled time)
Steering lives in pins/strategy.json (edited by Nora every Monday from Metricool stats).

Commands
  python3 tools/pins.py make  --slug SLUG --art PREVIEW.jpg --motif NAME --title T --sub S --desc D --alt A [--n 5]
  python3 tools/pins.py link  --slug SLUG --url ETSY_LISTING_URL
  python3 tools/pins.py next  [--n 6]        # klar pins + suggested times (max 3/day, 08:41/14:23/20:37 Stockholm)
  python3 tools/pins.py mark  --file F --id METRICOOL_ID --time 2026-11-20T08:41:00 --board BOARD_ID
  `next` already returns SEO text (keywords + 3-5 hashtags at the end) and a season-aware board: use them as-is.
  python3 tools/pins.py stats --metricool STATS.json   # join Metricool pin stats -> per product/motif/room/caption
  python3 tools/pins.py variants --slug SLUG --n 3     # extra pins of a winning product in rooms/captions not used yet
"""
import argparse, datetime as dt, json, os, random, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINS = os.path.join(ROOT, "pins", "pins.json")
STRAT = os.path.join(ROOT, "pins", "strategy.json")
ROOMS = json.load(open(os.path.join(ROOT, "rooms", "rooms.json")))
RAW = "https://raw.githubusercontent.com/ludvigwallertoft/palenorth-studio/main/pins/"
SLOTS = ["08:41", "14:23", "20:37"]
BOARD = "243124148573324395"  # Pinterest board "Printable Wall Art"


def load(p, default):
    return json.load(open(p)) if os.path.exists(p) else default


def save(p, data):
    json.dump(data, open(p, "w"), indent=1, ensure_ascii=False)


def strategy():
    return load(STRAT, {"room_weight": {}, "caption_weight": {}, "more_of": [], "stop": [], "notes": ""})


def pick_rooms(n, exclude=()):
    st = strategy()
    rooms = [r for r in ROOMS if st["room_weight"].get(r, 1) > 0 and r not in exclude]
    rooms.sort(key=lambda r: -st["room_weight"].get(r, 1) * (0.8 + 0.4 * random.random()))
    return rooms[:n]


CAPTIONS = {
    "standard": lambda t, s: (t, s),
    "notitle": lambda t, s: (None, None),
}


def pick_board(motif_text=""):
    st = strategy()
    boards = st.get("boards") or {BOARD: "Printable Wall Art"}
    w = st.get("board_weight", {})
    opts = [b for b in boards if w.get(b, 1) > 0]
    # winter motifs also go to the Winter Wall Art board
    if "winter" in motif_text.lower():
        opts += [b for b, n in boards.items() if "winter" in n.lower()]
    return random.choice(opts) if opts else BOARD


# --- Pinterest SEO -----------------------------------------------------------
# Pinterest is a search engine: keywords in title, description, alt text and board
# name do most of the work. 3-5 specific hashtags go at the END of the description.
TAGS = [  # (trigger words, hashtag) - first matches win, max 5 per pin
    (("christmas", "xmas", "holiday", "noel", "santa"), "#christmasdecor"),
    (("christmas", "xmas", "holiday"), "#christmasprintables"),
    (("winter", "snow", "spruce", "birch", "cabin"), "#winterdecor"),
    (("line art", "line drawing", "minimalist"), "#minimalistwallart"),
    (("nordic", "scandinavian", "cabin", "birch", "spruce"), "#scandinaviandecor"),
    (("funny", "playful", "humor", "quote", "cat", "dog", "coffee"), "#funnywallart"),
    (("kitchen", "coffee", "wine"), "#kitchenwallart"),
    (("bathroom",), "#bathroomwallart"),
    (("bedroom",), "#bedroomdecor"),
]
BASE_TAGS = ["#printablewallart", "#digitaldownload"]


def hashtags(text, n=5):
    t = text.lower()
    out = []
    for words, tag in TAGS:
        if tag not in out and any(w in t for w in words):
            out.append(tag)
    for tag in BASE_TAGS:
        if tag not in out:
            out.append(tag)
    return out[:n]


def active_sale(when=None):
    """strategy.json "sales": [{"from": "2026-11-10", "to": "2026-11-22", "text": "...", "title": "..."}]"""
    d = (when or dt.datetime.now()).date().isoformat()
    for s_ in strategy().get("sales", []):
        if s_["from"] <= d <= s_["to"]:
            return s_
    return None


def sale_title(title, when=None):
    s_ = active_sale(when)
    if s_ and len(title) + len(s_["title"]) + 3 <= 100:
        return f"{title} | {s_['title']}"
    return title[:100]


def seo_text(p, board="", when=None):
    """Keyword-rich description + 3-5 hashtags at the end (max 500 chars). Active sale line first."""
    desc = p["desc"].strip()
    s_ = active_sale(when)
    if s_:
        desc = s_["text"] + " " + desc
    if "printable" not in desc.lower():
        desc += " Printable wall art."
    bname = strategy().get("boards", {}).get(board, "").lower()
    if "christmas" in bname and "christmas" not in desc.lower():
        desc += " A calm touch of cozy Scandinavian Christmas decor, and an easy last-minute holiday gift."
        p = dict(p, desc=desc + " christmas")
    tags = " ".join(hashtags(" ".join([p["title"], p["desc"], p.get("motif", ""), p.get("slug", "")])))
    return (desc[: 499 - len(tags)].rstrip() + "\n\n" + tags)[:500]


def christmas_season(d=None):
    d = d or dt.date.today()
    return (d.month == 11) or (d.month == 12 and d.day <= 24)


def pick_board_for(p, recent=()):
    """Choose a board when the pin is scheduled: matching season boards get priority,
    and the same board is not used twice in a row."""
    st = strategy()
    boards = st.get("boards") or {BOARD: "Printable Wall Art"}
    w = st.get("board_weight", {})
    text = " ".join([p["title"], p["desc"], p.get("motif", ""), p.get("slug", "")]).lower()
    opts = []
    for b, name in boards.items():
        n = name.lower()
        if w.get(b, 1) <= 0:
            continue
        if "christmas" in n and not christmas_season():
            continue
        weight = w.get(b, 1)
        if "christmas" in n and any(k in text for k in ("christmas", "xmas", "holiday")):
            weight *= 4
        elif "christmas" in n and any(k in text for k in ("winter", "snow", "spruce", "cabin", "birch")):
            weight *= 1.5
        elif "christmas" in n:
            continue
        if "winter" in n and any(k in text for k in ("winter", "snow", "spruce", "cabin", "birch")):
            weight *= 2
        if "bedroom" in n and "bedroom" not in text and "r0" not in p.get("room", ""):
            weight *= 0.8
        if recent and b == recent[-1]:
            weight *= 0.1
        opts.append((b, weight))
    if not opts:
        return BOARD
    return random.choices([b for b, _ in opts], weights=[x for _, x in opts])[0]


def pick_caption():
    st = strategy()
    opts = [c for c in CAPTIONS if st["caption_weight"].get(c, 1) > 0]
    w = [st["caption_weight"].get(c, 1) for c in opts]
    return random.choices(opts, weights=w)[0]


def compose(room, art, out, title, sub):
    cmd = ["python3", os.path.join(ROOT, "tools", "compose.py"), "--room", room, "--art", art, "--out", out]
    if title:
        cmd += ["--title", title, "--sub", sub or ""]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def make(a, rooms=None):
    pins = load(PINS, [])
    if a.slug in strategy()["stop"]:
        print("STOP: product is on the stop list in strategy.json"); return
    used = {p["room"] for p in pins if p["slug"] == a.slug and p["motif"] == a.motif}
    rooms = rooms or pick_rooms(a.n, exclude=used)
    link = next((p["link"] for p in pins if p["slug"] == a.slug and p.get("link")), "")
    today = dt.date.today().strftime("%Y%m%d")
    for room in rooms:
        cap = pick_caption()
        t, s = CAPTIONS[cap](a.title, a.sub)
        fn = f"{today}-{a.slug}-{a.motif}-{room[:3]}-{cap}.jpg"
        compose(room, a.art, os.path.join(ROOT, "pins", fn), t, s)
        pins.append({"file": fn, "slug": a.slug, "motif": a.motif, "room": room, "style": ROOMS[room].get("style"),
                     "caption": cap, "title": a.title, "desc": a.desc, "alt": a.alt, "board": pick_board(a.slug + " " + a.title),
                     "link": link, "status": "klar" if link else "vantar-lank", "scheduled": "", "metricool_id": ""})
        print(fn)
    save(PINS, pins)


def link(a):
    pins = load(PINS, [])
    n = 0
    for p in pins:
        if p["slug"] == a.slug and p["status"] == "vantar-lank":
            p["link"] = a.url; p["status"] = "klar"; n += 1
    save(PINS, pins); print(f"{n} pins ready")


def next_slots(pins, n):
    taken = {p["scheduled"] for p in pins if p["scheduled"]}
    now = dt.datetime.now() + dt.timedelta(hours=1)
    last = max([dt.datetime.fromisoformat(t) for t in taken] + [now])
    day = (last if last > now else now).date()
    out = []
    while len(out) < n:
        for s in SLOTS:
            t = dt.datetime.fromisoformat(f"{day}T{s}:00")
            if t > now and t > last and t.isoformat() not in taken:
                out.append(t.isoformat())
                if len(out) == n:
                    break
        day += dt.timedelta(days=1)
    return out


def nxt(a):
    pins = load(PINS, [])
    ready = [p for p in pins if p["status"] == "klar" and p["slug"] not in strategy()["stop"]]
    # interleave products so the same print is not shown twice in a row
    ready.sort(key=lambda p: (sum(1 for q in pins if q["slug"] == p["slug"] and q["status"] == "schemalagd"), p["file"]))
    times = next_slots(pins, min(a.n, len(ready)))
    recent = [q["board"] for q in sorted(pins, key=lambda q: q["scheduled"] or "") if q["scheduled"]][-3:]
    for p, t in zip(ready, times):
        b = pick_board_for(p, recent)
        recent.append(b)
        p["board"] = b  # remembered so stats can be split per board
        print(json.dumps({"file": p["file"], "time": t, "media": RAW + p["file"], "pinTitle": sale_title(p["title"], dt.datetime.fromisoformat(t)),
                          "text": seo_text(p, b, dt.datetime.fromisoformat(t)), "alt": p["alt"], "boardId": b, "pinLink": p["link"]},
                         ensure_ascii=False))
    save(PINS, pins)


def mark(a):
    pins = load(PINS, [])
    for p in pins:
        if p["file"] == a.file:
            p["status"] = "schemalagd"; p["metricool_id"] = str(a.id); p["scheduled"] = a.time
            if a.board:
                p["board"] = a.board
    save(PINS, pins); print("ok")


def stats(a):
    """Metricool rows (Pinterest posts connector) saved as JSON list of objects that have at least
    a timestamp and impressions/saves/pinClicks/outboundClicks. Joined to pins.json on scheduled time (±20 min)."""
    rows = json.load(open(a.metricool))
    if isinstance(rows, dict):  # accept {"data": [...]} too
        rows = rows.get("data") or rows.get("rows") or next((v for v in rows.values() if isinstance(v, list)), [])
    pins = [p for p in load(PINS, []) if p["scheduled"]]
    for p in pins:
        p["_t"] = dt.datetime.fromisoformat(p["scheduled"])
    agg = {}
    matched = 0
    for r in rows:
        if isinstance(r, list):  # Metricool returns positional rows in the order requested:
            # PIPO02 (YYYYMMDDHHMMSS), PIPO03 title, PIPO08 impressions, PIPO09 saves, PIPO10 pin clicks, PIPO11 outbound
            r = dict(zip(["timestamp", "title", "impressions", "saves", "pinClicks", "outboundClicks"], r))
        ts = str(r.get("timestamp") or r.get("PIPO02") or "")
        try:
            t = dt.datetime.strptime(ts[:14], "%Y%m%d%H%M%S") if ts[:14].isdigit() else dt.datetime.fromisoformat(ts[:19].replace(" ", "T"))
        except ValueError:
            continue
        best, gap = None, 1e9
        for off in (0, 1, -1, 2):  # Metricool may report UTC; we store Stockholm time
            tt = t + dt.timedelta(hours=off)
            for p in pins:
                g = abs((p["_t"] - tt).total_seconds())
                if g < gap:
                    best, gap = p, g
        if not best or gap > 1200:
            continue
        matched += 1
        alias = {"impressions": "PIPO08", "saves": "PIPO09", "pinClicks": "PIPO10", "outboundClicks": "PIPO11"}
        m = {k: float(r.get(k, r.get(alias[k], 0)) or 0) for k in alias}
        for dim in ("slug", "motif", "room", "style", "caption"):
            key = (dim, best[dim])
            s = agg.setdefault(key, {"pins": 0, "impressions": 0, "saves": 0, "pinClicks": 0, "outboundClicks": 0})
            s["pins"] += 1
            for k, v in m.items():
                s[k] += v
    print(f"matched {matched}/{len(rows)} Metricool rows")
    print("dimension | value | pins | impr/pin | saves/pin | outbound/pin")
    for (dim, val), s in sorted(agg.items(), key=lambda kv: (kv[0][0], -kv[1]["impressions"] / kv[1]["pins"])):
        n = s["pins"]
        print(f"{dim} | {val} | {n} | {s['impressions']/n:.0f} | {s['saves']/n:.1f} | {s['outboundClicks']/n:.2f}")


def variants(a):
    pins = load(PINS, [])
    base = next((p for p in pins if p["slug"] == a.slug), None)
    if not base:
        print("unknown product"); return
    art = os.path.join(ROOT, "art-previews", f"{a.slug}-{base['motif']}.jpg")
    motifs = sorted({p["motif"] for p in pins if p["slug"] == a.slug})
    made = 0
    for motif in motifs:
        art = os.path.join(ROOT, "art-previews", f"{a.slug}-{motif}.jpg")
        if not os.path.exists(art):
            continue
        src = next(p for p in pins if p["slug"] == a.slug and p["motif"] == motif)
        used = {p["room"] for p in pins if p["slug"] == a.slug and p["motif"] == motif}
        free = pick_rooms(len(ROOMS), exclude=used) or pick_rooms(1)
        ns = argparse.Namespace(slug=a.slug, motif=motif, art=art, title=src["title"], sub="instant download · Pale North Studio",
                                desc=src["desc"], alt=src["alt"], n=1)
        make(ns, rooms=free[:1])
        made += 1
        if made >= a.n:
            break


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    for f in ("slug", "art", "motif", "title", "sub", "desc", "alt", "url", "file", "id", "time", "metricool", "board"):
        ap.add_argument("--" + f)
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    {"make": make, "link": link, "next": nxt, "mark": mark, "stats": stats, "variants": variants}[a.cmd](a)
