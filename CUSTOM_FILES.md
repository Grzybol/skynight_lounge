# CUSTOM_FILES.md — gdzie wgrywać własne pliki

Mapa wszystkich miejsc, których dotykasz przy podmianie sampla na własną grę.
Wszystkie ścieżki względem korzenia repo. `poc` = nasza gra.

---

## 1. GRAFIKA SYMBOLI I ANIMACJE (frontend)

### 1a. Pliki assetów — katalog docelowy
```
frontend/apps/poc/static/assets/
├── spines/     # animacje Spine (para .json skeleton + .atlas + .png). Symbole, big-win, intro FS, tło...
│   ├── symbols/    symbols2/    symbols3/   # symbole gry (h1..h5, l1..l5, W, S, M, explosion)
│   ├── loader/  bigwin/  fsIntro/  transition/  anticipation/  ...
├── sprites/    # sprite-sheety / atlasy PixiJS (.json + .png). UI, ramki, monety...
├── audio/      # dźwięki: sounds.json (mapa) + sounds.{mp3,ogg,m4a,ac3}
└── fonts/      # fonty bitmapowe (.xml + .png)
```

**Zasada:** wrzucasz pliki do odpowiedniego podkatalogu, zachowując parę
`skeleton.json + atlas + png` (Spine) albo `sheet.json + png` (sprites).

### 1b. Rejestracja assetu — MUSISZ dopisać/podmienić wpis
Plik: **`frontend/apps/poc/src/game/assets.ts`**
Każdy asset ma tu wpis mapujący nazwę logiczną → typ → ścieżkę. Przykład:
```ts
H1: {
  type: 'spine',                 // spine | sprite | sprites | spriteSheet | font | audio
  src: {
    atlas:    new URL('../../assets/spines/symbols/symbols.atlas', import.meta.url).href,
    skeleton: new URL('../../assets/spines/symbols/h1.json',       import.meta.url).href,
    scale: 2,
  },
},
```
- `preload: true` → asset ładowany przed startem (loader, tło, dźwięk).
- Nazwa klucza (`H1`, `W`, `S`...) musi zgadzać się z nazwą symbolu z matematyki (patrz §3).

---

## 2. DEFINICJA GRY — symbole, linie, bet-mody (frontend)

Plik: **`frontend/apps/poc/src/game/config.ts`**
- `symbols` — paytable każdego symbolu (wypłaty za 3/4/5-of-a-kind) + `special_properties`
  (`wild`, `scatter`, `multiplier`).
- `paylines` — 20 linii jako indeksy rzędów na kolejnych bębnach.
- `betModes` — `base` (koszt 1.0) i `bonus` (buy-bonus, koszt 100.0), RTP, `max_win`.
- `numReels`, `numRows`, `rtp`, `providerName`, `gameName`, `gameID` (u nas `0_0_poc`).

> ⚠️ `config.ts` musi być spójny z matematyką (`math/games/0_0_poc/game_config.py`) —
> te same nazwy symboli, paytable i bet-mody.

Dodatkowo do dotknięcia przy większych zmianach:
- `src/game/bookEventHandlerMap.ts` — mapowanie eventów z books na animacje.
- `src/game/typesBookEvent.ts` / `typesEmitterEvent.ts` — typy eventów.
- `src/components/*.svelte` — wygląd planszy, symboli, ekranów wygranych.

---

## 3. MATEMATYKA — bębny i paytable (backend)

### 3a. Taśmy bębnów (reels) — katalog docelowy
```
math/games/0_0_poc/reels/
├── BR0.csv     # Base Reels — paski symboli dla gry bazowej (kolumna = bęben)
├── FR0.csv     # Free Reels — paski dla free spinów
└── FRWCAP.csv  # wariant taśmy free (wild-cap)
```
CSV: każda kolumna to jeden bęben, każdy wiersz to symbol na taśmie (`H1`, `L2`, `W`, `S`...).
Podmieniasz zawartość, by zmienić częstotliwość symboli → wpływa na RTP i zmienność.

### 3b. Konfiguracja matematyki
Plik: **`math/games/0_0_poc/game_config.py`**
- paytable, definicje symboli (wild/scatter/multiplier), bet-mody, `game_id`, `rtp`.
- Logika gry: `game_calculations.py`, `game_executables.py`, `game_events.py`, `gamestate.py`.

### 3c. Generowanie wyników
```bash
cd math/games/0_0_poc && python run.py
```
Wynik ląduje w `math/games/0_0_poc/library/`:
- `books/` — skompresowane przebiegi spinów (.jsonl.zst) — to konsumuje RGS/frontend,
- `lookup_tables/` — tabele wag do losowania,
- `config_fe_0_0_poc.json` — config dla frontendu,
- `publish_files/` — paczka do uploadu na Stake Engine.

> Wymaga **Python 3.12+** i **Rust/Cargo** (dla optimizera). Aktualnie niezainstalowane.

---

## 4. Dane do lokalnego podglądu (bez RGS)

Plik: **`frontend/apps/poc/src/stories/data/`**
- `base_books.ts`, `bonus_books.ts` — przykładowe przebiegi spinów do Storybooka.
- Po wygenerowaniu prawdziwych books z matematyki możesz podmienić te przykłady.

---

## Kolejność przy podmianie sampla na własną grę
1. Zaprojektuj symbole + paytable → wpisz do `game_config.py` (math) i `config.ts` (frontend).
2. Ustaw taśmy bębnów w `reels/*.csv`, uruchom `run.py`, dostrój RTP/zmienność.
3. Wgraj grafiki/animacje do `static/assets/` i zarejestruj w `assets.ts`.
4. Dostrój komponenty/animacje w `src/components/` i `bookEventHandlerMap.ts`.
5. Podejrzyj w Storybooku (`pnpm run storybook --filter=poc`), potem build i upload.

---

## 5. Postać lounge — dopasowanie pixel-perfect

Nie należy do sample'a Stake Engine. Po imporcie SDK te liczby zginą razem z komponentem.
Źródło prawdy w kodzie:

`frontend/apps/poc/src/components/skyjump/loungeFigureTune.ts`

Podpięte w `SkyJumpBackground.svelte`. Scena logiczna: **1280×720**.

| Ustawienie | Wartość |
|---|---|
| Nudge stopy X (CSS px, minus = w lewo) | **-0.5** |
| Nudge stopy Y (CSS px, plus = w dół) | **3** |
| Rozciągnięcie stopy w górę (dół zostaje) | **2 px** |
| Skurcz stopy z każdej strony | 1 px |
| Zoom fotela stopy | 1.269 |
| Korekta szerokości stopy | 380/375 |
| Lift stopy (px źródła) | 3.45 |
| Środek fotela (źródło) | baza 782×900, stopa 834×931, oś X 608 |
| Przesunięcie postaci w dół | 120 px przy szerokości 1280 |
| Obrys nieprzezroczysty | L134 R1049 T162 B1362 w kadrze 1167×1556 |
| Podstawowa pętla | 8580 ms |
| Stopa | 6050 ms, ucięte ostatnie 500 ms postoju |
| Odstęp stopy | 2–6 pełnych pętli podstawowych (z reverse) |
| Fade-in / opóźnienie fade-out / fade-out | 200 / 260 / 150 ms |
| Piórko krawędzi (stdDeviation, tylko alfa) | 0.7 |

Assety w `frontend/apps/poc/src/assets/skyjump/backgrounds/`:
`midnight-lounge.jpg`, `lounge-figure.webp`, `stopa_plus.gif`, `smile_plus.gif`, `wow_plus.gif`.

GIF-y są za duże na jeden plik w GitHubie, więc w repo leżą jako osobne zipy (backup, gra ich nie ładuje):

```
asset-backup/lounge-gifs/smile_plus.gif.zip
asset-backup/lounge-gifs/stopa_plus.gif.zip
asset-backup/lounge-gifs/wow_plus.gif.zip
```

Rozpakuj je z powrotem obok pozostałych teł:

```powershell
Expand-Archive asset-backup\lounge-gifs\stopa_plus.gif.zip -DestinationPath frontend\apps\poc\src\assets\skyjump\backgrounds -Force
Expand-Archive asset-backup\lounge-gifs\smile_plus.gif.zip -DestinationPath frontend\apps\poc\src\assets\skyjump\backgrounds -Force
Expand-Archive asset-backup\lounge-gifs\wow_plus.gif.zip -DestinationPath frontend\apps\poc\src\assets\skyjump\backgrounds -Force
```

## Character animation V2 (supersedes the lounge figure files above)

See `docs/midnight-lounge-character-animation.md`. Runtime: `frontend/apps/poc/src/game/loungeCharacters/`, `components/skyjump/LoungeCharacter.svelte`. Assets: `static/assets/midnight-lounge/characters/` (built by `tools/midnight-lounge/build-character-anims.py`).
