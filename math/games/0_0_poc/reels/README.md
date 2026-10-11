# Drop-zone: taśmy bębnów (reels) gry `0_0_poc`

Pliki CSV definiujące paski symboli na bębnach. **Kolumna = jeden bęben**,
**wiersz = symbol** na taśmie (np. `H1`, `L2`, `W`, `S`).

- `BR0.csv`    — Base Reels (gra bazowa).
- `FR0.csv`    — Free Reels (free spiny).
- `FRWCAP.csv` — wariant taśmy free (wild-cap).

Zmiana częstotliwości symboli na taśmach wpływa na RTP i zmienność.
Po edycji uruchom `python ../run.py`, żeby przeliczyć books i lookup tables.

Nazwy symboli muszą zgadzać się z paytable w `../game_config.py`
oraz z frontendem (`frontend/apps/poc/src/game/config.ts`).

Pełna instrukcja: patrz `CUSTOM_FILES.md` w korzeniu repo.
