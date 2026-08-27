# ADR-003: Teljes fordítás (7 nyelv maradék)

- **Dátum:** 2026-08-27
- **Státusz:** accepted
- **Szerző:** analyst (research: `docs/research/2026-08-27-full-translation.md`)
- **Kanban:** [aaa bbb] — két feladat (2/2)

## Kontextus
10 nyelvből `en/hu/de` kész, `fr/es/it/pt/nl/pl/ro` (7 nyelv) ~47% angol maradék (`hu!=en && loc==en` → fr 244, nl 240, stb.). Francia/spanyol stb. választásnál is angol felirat látszik.

## Döntés
**Monolit bővítés** `frontend/lib/i18n.ts`-ben batch-enként: B1 `fr/es/it` (3× ~233 truly untranslated), B2 `pt/nl/pl/ro` (4× ~233). Csak értékcsere, commitonként 1 batch, `TSC 0 BUILD 0` gate. Fájl felbontás (JSON loader) későbbre halasztva (over-engineering 10 nyelvre).

- Validálás: `truly untranslated` 233 → 0 mind a 7 nyelven, `E2E us_006 30×10` + `us_007 51` zöld, spot-check fr landing `Scan receipts` → `Numérisez`.
- Opcionális utána: `de` 15 + `hu` 6 maradék finomítás.

## Elvetve

| Opció | Miért nem |
|---|---|
| Locale JSON + async loader | Nem lean 10 nyelvre, migration kockázat |
| Gépi fordítás batch | Terminológia kockázat (duplicate/confidence/reconciliation) |

## Következmény
- Fejlesztő: `i18n.ts` 7 nyelv patch, commit/batch, `TSC 0 BUILD 0`.
- Validálás: `truly untranslated 0`, E2E zöld, manuális `fr` spot.

## Kapcsolódó
- Research: `docs/research/2026-08-27-full-translation.md`
- Kód: `frontend/lib/i18n.ts` (509 kulcs ×10)
- Következő ADR: —
