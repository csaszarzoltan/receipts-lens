# Idea Evaluator & Rangsoroló — másolható runbook

> Összeveti a sok forrásból jött VOC-t + competitor scoringot, rangsorolt ötlet-listát ad, és előkészíti a további kidolgozást.

## Bemenet (összes, resilient)
- Hermes natív VOC táblák (web_search + agent-reach + jina/defuddle/browser — ami sikerült)
- Gemini VOC táblák (ha volt kvóta — ha nem, `no data — gemini quota` és kimarad, nem blokkol)
- Agy competitor/feature siker-score táblák (ha volt futás — ha nem, Hermes scoring pótolja)
- `competitor-news-monitor` / `competitor-profiling` raw ha van

Ha egy bemenet hiányzik: **ne blokkolj** — a meglevőből dolgozz, a hiányt jelöld: `no source — <miner>`.

## Lépések

### 1) Deduplikálás + klaszterezés
- Azonos verbatim vagy azonos URL → egybe von.
- Tematikus klaszter: `pain / JTBD / feature-gap` szerint csoportosít (pl. "Baugesuch alert késik", "Steuerfuss összehasonlítás", "zajtérkép hiány").
- Minden klaszterre: `előfordulás (hány forrás) × intenzitás (frustrated szavak aránya)` → `freq×intensity` score.

### 2) Ötlet-képzés
Minden klaszterből 1 ötlet-jelöltet formálj:
`Ötlet neve | JTBD (milyen job-ot old) | Pain (kinek fáj) | Bizonyíték (2-3 verbatim URL-lel) | Versenytárs-gap (van-e? ki nem adja)` 

### 3) Pontozás (1-5 rubrika — minden ötletre)

| Dimenzió | 1 | 5 | Forrás |
|---|---|---|---|
| **Kereslet** (freq×intensity) | 1-2 említés, gyenge érzelem | 6+ forrás, erős frustrated | VOC táblák |
| **Versenytárs-gap** | mindenki adja | senki nem adja (térkép-first, politika stb.) | competitor matrix |
| **Hatás (user value)** | nice-to-have | napi fájdalmat old | JTBD + trigger |
| **Megvalósíthatóság** | hónapok, külső függőség kockázatos | napok, stabil OGD/API | tech becslés (PyProj, Swisstopo VT, PARIS stb.) |
| **Bevétel/alternatíva nyomás** | ingyen megoldható máshol | fizetne érte / nincs alternatíva | pricing + alternative tag |

`Prioritás = 0.30*Kereslet + 0.25*Gap + 0.20*Hatás + 0.15*Megvalósíthatóság + 0.10*Bevétel`. Rangsorold csökkenő szerint.

### 4) Kimenet — két rész

#### A) Rangsorolt ötlet-lista (Backlog)
| Rank | Ötlet | freq×intensity | Gap | Hatás | Megvalósíthatóság | Prioritás | Top bizonyíték (URL) | Következő lépés |
|---|---|---|---|---|---|---|---|

#### B) Top 5 részletezés (grooming-ready)
Minden top ötletre:
- **1 mondat pitch** (kinek, mit old, miért jobb mint Houzy/smartconext)
- **3 bizonyító idézet** (verbatim + URL + dátum)
- **Kockázat** (pl. "20 napos Auflage ablak — áramló adat nem archív")
- **Következő kidolgozás**: `Research: docs/research/YYYY-MM-DD-{téma}.md` + `ADR: ADR-NNN` + `Kanban kártya cím + AC (max 3 file)`

### 5) Forrás-hűség
- Minden sorhoz ledger `[n]` + `Sources:` blokk (`sources.py render --cited-in draft.md`)
- Ha fact-check: `quote --from` + `verify --evidence --min-coverage 0.5`
- Soha ne parafrazálj idézetet — verbatim marad.

## Használat
```bash
# Hermes evaluator futtatás (példa):
# 1. Gyűjtsd a miner outputokat /tmp/voc-*.md-be
# 2. Futtasd ezt a runbookot analyst szerepben, a ledger közös legyen:
HERMES_CITATION_LEDGER=/tmp/ledger-deep-2026-08-26.json python ~/.hermes/skills/research/grounded-citations/scripts/sources.py list
```
