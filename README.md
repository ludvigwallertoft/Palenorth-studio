# Pale North Studio – mockups & pins

Shared library for the LW AB agents (Tove, Pia, Nora). No print files are ever stored here – only room photos, the mockup tool and finished pin images (public, so Metricool can publish them).

- `rooms/` – free room photos with empty frames (Pexels licence: free for commercial use) + `rooms.json` (frame opening, style, mood).
- `tools/compose.py` – puts a print into a room: Pinterest pin 1000x1500 with caption, or Etsy listing image 2000x2000 (`--etsy`). Pure Python/Pillow, no AI, no credits.
- `pins/` – finished pins, named `<yyyymmdd>-<product-slug>-<room>.jpg`. Public URL: `https://raw.githubusercontent.com/ludvigwallertoft/palenorth-studio/main/pins/<file>`
- `art-previews/` – low-res previews (max 1000x1500) of our own prints, only for making mockups. Never the full print files.
- `tools/pins.py` – the pin pipeline: `make` (Tove), `link` + `next` + `mark` (Pia, scheduling via Metricool), `stats` + `variants` (Nora/Pia).
- `pins/pins.json` – every pin: product, motif, room, style, caption type, texts, link, status, scheduled time, Metricool id.
- `pins/strategy.json` – Nora's steering: room/caption weights (0 = stop), `more_of` (products to make more pins of), `stop` (products not to pin any more).
