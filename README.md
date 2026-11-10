# Pale North Studio – mockups & pins

Shared library for the LW AB agents (Tove, Pia, Nora). No print files are ever stored here – only room photos, the mockup tool and finished pin images (public, so Metricool can publish them).

- `rooms/` – free room photos with empty frames (Pexels licence: free for commercial use) + `rooms.json` (frame opening, style, mood).
- `tools/compose.py` – puts a print into a room: Pinterest pin 1000x1500 with caption, or Etsy listing image 2000x2000 (`--etsy`). Pure Python/Pillow, no AI, no credits.
- `pins/` – finished pins, named `<yyyymmdd>-<product-slug>-<room>.jpg`. Public URL: `https://raw.githubusercontent.com/ludvigwallertoft/palenorth-studio/main/pins/<file>`
- `art-previews/` – low-res previews (max 1000x1500) of our own prints, only for making mockups. Never the full print files.
- `tools/pins.py` – the pin pipeline: `make` (Tove), `link` + `next` + `mark` (Pia, scheduling via Metricool), `stats` + `variants` (Nora/Pia).
- `pins/pins.json` – every pin: product, motif, room, style, caption type, texts, link, status, scheduled time, Metricool id.
- `pins/strategy.json` – Nora's steering: room/caption weights (0 = stop), `more_of` (products to make more pins of), `stop` (products not to pin any more).

## Pinterest SEO (obligatoriskt för alla pins, från 2026-11-10)
Pinterest är en sökmotor. Det är sökorden som gör att folk hittar pinsen, inte följare.
- **Titel** (`--title`, max 100 tecken): det viktigaste sökordet först, så som folk skriver i Pinterests sökruta.
  Exempel: "Scandinavian Christmas Wall Art Printable – Minimalist Holiday Print".
- **Beskrivning** (`--desc`, max ~400 tecken): naturliga meningar med 2–3 sökord (t.ex. "christmas wall art printable",
  "scandinavian christmas decor", "minimalist holiday print", "winter wall art"), vad köparen får och att det är en digital fil.
  Skriv INGA hashtaggar själv: `pins.py next` lägger automatiskt till 3–5 specifika hashtaggar sist.
- **Alt-text** (`--alt`): en mening som beskriver bilden och innehåller sökordet.
- **Tavlor**: `pins.py next` väljer tavla själv efter säsong och motiv, och lägger aldrig samma tavla två gånger i rad.
  Jultavlorna (Christmas Wall Art Printables, Cozy Christmas Home Decor) används 1 nov–24 dec; Winter Wall Art jan–mars.
  Använd `boardId` och `text` från `next` oförändrade i Metricool. Skicka gärna `--board` till `mark`.
- **Säsong**: julprodukter måste vara ute senast i mitten av november. Pinterest behöver 2–4 veckor
  innan en pin börjar synas i sök.

## Ägarens regel: ingen text på bilderna (2026-11-10)
Pins är rena, eleganta rumsbilder. Ingen titel eller undertext bakas in i bilden – sökorden står bara i pin-titeln och beskrivningen.
