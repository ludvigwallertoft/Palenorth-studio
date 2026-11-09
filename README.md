# Pale North Studio – mockups & pins

Shared library for the LW AB agents (Tove, Pia, Nora). No print files are ever stored here – only room photos, the mockup tool and finished pin images (public, so Metricool can publish them).

- `rooms/` – free room photos with empty frames (Pexels licence: free for commercial use) + `rooms.json` (frame opening, style, mood).
- `tools/compose.py` – puts a print into a room: Pinterest pin 1000x1500 with caption, or Etsy listing image 2000x2000 (`--etsy`). Pure Python/Pillow, no AI, no credits.
- `pins/` – finished pins, named `<yyyymmdd>-<product-slug>-<room>.jpg`. Public URL: `https://raw.githubusercontent.com/ludvigwallertoft/palenorth-studio/main/pins/<file>`
- `pins/log.csv` – one row per published pin: date, file, product, motif, style, room, Pinterest board, Metricool post id. Nora joins this with Metricool stats to decide what to make more of.
