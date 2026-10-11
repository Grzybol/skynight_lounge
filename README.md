# PoC Slot — Stake Engine (lines / 5×3)

Proof of Concept gry slotowej pod platformę **Stake Engine** (stake.com / stake.jp),
zbudowany na oficjalnych SDK Stake. Baza: przykładowa gra `lines` (5 bębnów × 3 rzędy,
20 linii wypłacających, wild, scatter, free spiny).

Aktywna prezentacja to **Garden Bounty**. Stan vs pełna gra na stake.com i plan
rozwoju: `docs/STAKE_COM_READINESS.md`, `docs/STAKE_COM_ROADMAP.md`.

Celem PoC jest **działający szkielet z jasno wydzielonymi katalogami**, do których
później wgrywasz własne grafiki, animacje, dźwięki i matematykę.

---

## Struktura projektu

```
slot_game/
├── frontend/                 # Fork oficjalnego web-sdk (Svelte 5 + PixiJS 8 + Turborepo)
│   ├── apps/
│   │   ├── poc/              # ⭐ NASZA GRA (kopia sample 'lines')
│   │   │   ├── src/game/     #   logika: config, symbole, eventy, dźwięk
│   │   │   ├── src/components/  # komponenty Svelte (plansza, symbol, wygrane...)
│   │   │   ├── src/stories/data/ # przykładowe "books" (dane do lokalnego podglądu)
│   │   │   └── static/assets/  # ⭐ TU WGRYWASZ GRAFIKI/DŹWIĘKI (patrz CUSTOM_FILES.md)
│   │   ├── lines, ways, cluster, scatter, price, number-picker  # referencyjne sample
│   └── packages/             # współdzielone paczki SDK (pixi-svelte, komponenty, utils)
│
├── math/                     # Fork oficjalnego math-sdk (Python + Rust optimizer)
│   └── games/
│       ├── 0_0_poc/          # ⭐ NASZA MATEMATYKA (kopia sample '0_0_lines')
│       │   ├── game_config.py  # paytable, bet-mody, RTP, definicja gry
│       │   ├── reels/*.csv     # ⭐ TU WGRYWASZ TAŚMY BĘBNÓW (paski symboli)
│       │   └── run.py          # generuje books + lookup tables + configi
│       └── 0_0_lines, 0_0_cluster, ...  # referencyjne sample
│
├── CUSTOM_FILES.md           # ⭐ mapa: co gdzie wgrywać podczas dalszego developmentu
└── README.md                 # ten plik
```

`⭐` = miejsca, których dotykasz w dalszym developmencie. Reszta to niezmieniony SDK.

---

## Architektura (jak to działa)

Stake Engine rozdziela **matematykę** (backend, deterministyczna, audytowalna) od
**prezentacji** (frontend, tylko animuje wynik):

```
  math-sdk (Python)                 RGS (Stake)              web-sdk (frontend)
  ─────────────────                 ───────────              ──────────────────
  reels + paytable   ──generuje──>  books (.jsonl)  ──API──> BookEvents (JSON)
  run.py                            lookup tables            │
                                    config_fe.json           ├─ bookEventHandlerMap
                                    index.json               │   (reveal, setWin, ...)
                                                             ├─ EmitterEvents
                                                             └─ komponenty Svelte/Pixi
```

- **Book** = pełny przebieg jednego spinu jako lista eventów (`reveal`, `setTotalWin`,
  `finalWin`, free-spiny itp.). Matematyka generuje miliony gotowych books; RGS losuje
  jeden i wysyła do frontendu.
- Frontend jest **bezstanowy**: dostaje book, mapuje eventy przez `bookEventHandlerMap.ts`
  na wewnętrzne `EmitterEvents`, a komponenty tylko je animują.
- Do lokalnego podglądu bez RGS służą przykładowe books w `src/stories/data/`.

---

## Szybki start

### Wymagania
- **Node 22.16+** (masz 22.11 — działa, choć SDK ostrzega) + **pnpm 10.5** (zainstalowany lokalnie w `~/.npm-global`)
- Do matematyki: **Python 3.12+** oraz **Rust/Cargo** (optimizer) — *nie zainstalowane, patrz niżej*

### Frontend — podgląd gry lokalnie (Storybook, z przykładowymi danymi)
```bash
cd frontend
pnpm install                       # jednorazowo
pnpm run storybook --filter=poc    # -> http://localhost:6010
```
W Storybooku: sekcja `MODE_BASE` → `book/random` → przycisk **Action** odtwarza spin.

### Frontend — dev server (wymaga RGS / parametrów sesji)
```bash
cd frontend
pnpm run dev --filter=poc          # -> http://localhost:3010
```
Bez podłączonego RGS zobaczysz błąd `authenticate: Failed to fetch` — to normalne,
gra próbuje autoryzować sesję. Do pracy nad wizualiami używaj Storybooka.

### Frontend — build produkcyjny (paczka do uploadu na Stake Engine)
```bash
cd frontend
pnpm run build --filter=poc        # wynik w apps/poc/build/
```

### Math — generowanie books (opcjonalne, wymaga Python 3.12 + Rust)
```bash
cd math
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cd games/0_0_poc && python run.py  # wynik w games/0_0_poc/library/
```

---

## Uwagi środowiskowe (Windows + OneDrive)

- Projekt leży w folderze OneDrive. pnpm domyślnie używa symlinków w `node_modules`,
  co powoduje `EPERM` przy synchronizacji OneDrive. Naprawione w `frontend/.npmrc`
  przez `node-linker=hoisted` (płaski układ, jak npm).
- Skrypt `storybook` sampli używa bashowej składni env (`PUBLIC_CHROMATIC=true ...`),
  która nie działa na Windows. W naszym `apps/poc` naprawione przez `cross-env`.
- Jeśli `pnpm install` zgłasza `EBUSY` — ubij działające procesy node (`taskkill //F //IM node.exe`)
  i ponów.

---

## Źródła / dokumentacja
- Web SDK: https://github.com/StakeEngine/web-sdk
- Math SDK: https://github.com/StakeEngine/math-sdk
- Docs: https://stakeengine.github.io/math-sdk/
- Program dla developerów: https://engine.stake.com/
