# Teljes fordítás — kutatás (2026-08-27)

## Probléma
`frontend/lib/i18n.ts` 509 kulcs ×10 locale: `en` (509) és `hu` (509, 1% angol maradék) + `de` (3% maradék) kész, de `fr/es/it/pt/nl/pl/ro` (7 nyelv) 47% angol maradék (~233 kulcs/locat `hu != en && loc == en`). A felhasználó azt látja hogy francia/spanyol stb. választásnál is angol felirat jön (pl. `Status`, `PWA`, `Connect ReceiptLens…`).

## Mérés
- 5217 sor, egy fájl 509 kulcs. `truly untranslated = hu!=en && loc==en` → fr 244, es 234, it 235, pt 233, nl 240, pl 234, ro 233.

## Megvizsgált opciók

| Szempont | A) Monolit bővítés (i18n.ts-ben 7 nyelv pótlása) | B) Fájl felbontás (locale JSON-ok, pl. `/messages/fr.json`) + loader | C) Gépi fordítás (API) batch |
|---|---|---|---|
| Leírás | A meglévő 10-locale objektumban `fr`…`ro` `en_add` másolt értékei helyett valódi fordítások beírása (patch hullámban). | `lib/i18n.ts` → `messages/{locale}.json` + async loader, Next `dynamic` import. | Külső API (DeepL/Google) egy lépésben lefordítja a hiányzó 7×233 sort. |
| Előny | Nulla architektúra-váltás, E2E azonnal zöld, egy diffben reviewzható batch-enként, rollback triviális. | Skálázható 20+ nyelvre, kisebb bundle, szerkeszthetőbb fordítóknak. | Gyors, nem kell ember. |
| Hátrány | Nagy diff ( ~1600 sor), egy fájl nő. | Loader + async, hydration/compress bonyolódik, E2E `suppressHydrationWarning` növekedik, migration kockázat. | Minőség bizonytalan (pénzügyi terminológia: "duplicate", "confidence", "reconciliation"), díj, review mégis kell. |
| E2E | Kiváló — ugyanaz az `us_006 anti-HU 38` + `us_007` contract, csak értékek változnak. | Jó, de plusz async edge. | Jó, de minőség kézi fixet igényel. |
| Lean | Lean — kis repo (<30k sor), egy fájl még 400 alatt? (jelenleg 5217 sor — már over, de nem blocker, felbontás később). | Nem lean most — 10 nyelv kis termékben over-engineering. | Nem lean — külső függőség. |
| Kockázat | Alacsony — csak értékcsere, commitonként 1-2 nyelv, build `TSC` fogja. | Közepes — router/layout érintés. | Közepes (terminológia). |

## Döntés
**A) Monolit bővítés batch-enként.** 2 batch: B1 `fr/es/it` (3×233), B2 `pt/nl/pl/ro` (4×233). Mindegyik után `TSC 0 BUILD 0` + `E2E us_006/us_007` anti-HU valamint manuális `fr` spot-check (landing h1 nem marad `Scan receipts`). `de` (15 maradék) és `hu` (6) finomítás opcionális utána, nem blocker. Későbbi felbontás (B-terv) ADR-ben nyitható ha 20+ nyelvre megyünk.

## Validálás
- `truly untranslated` 233 → 0 mind a 7 nyelven.
- `E2E us_006 30×10` + `us_007 51` továbbra is `passed` (anti-HU nem törik).
- Új `us_009_translation_completeness.spec.ts` (opcionális, lean): 7 nyelv × 3 kulcs `fr != en` assert.
