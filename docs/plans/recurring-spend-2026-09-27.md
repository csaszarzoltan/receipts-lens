# Ismétlődő költés + megtakarítási visszacsatolás — FEATURE SPEC

**Dátum:** 2026-09-27
**Státusz:** SPEC — kód nélkül, jóváhagyásra vár
**Forrás:** `docs/plans/consumer-pivot-2026-08-13.md` F2 fázis (gap: F2.1, F2.2 üres) + `feature-research-2026-09-26.md` 3. szakasz (F2.1+F2.2 javaslat, P0/P1/P2 sorrend)
**Scope:** F2.1 + F2.2 egyben — nulla új adatgyűjtés, meglévő `receipts` újraértelmezése

> Megjegyzés: a 3 biztonsági javítás (`API-1` production-auth gate, `API2-6` job-auth, a 2 auth-új `/v1` útvonal) már kész (`6e08624`, `46829b7`, `26663d0`). E terv nem érinti őket.

---

## 1. CÉL

Háztartási felhasználó (Háztartás tulajdonosa / Felnőtt tag) a már lefotózott nyugtáiból automatikusan látja, mely költése ismétlődik hetente/havonta, és mennyit takarítana meg lemondással vagy ritkítással — hogy a ReceiptLens adatgyűjtőből megtakarítási asszisztenssé váljon.

---

## 2. FELHASZNÁLÓI TÖRTÉNETEK

| Történet | Cím | Pivot |
|---|---|---|
| F2.1 | Ismétlődő vásárlások felismerése | F2.1 |
| F2.1b | Drágulás-jelzés rendszeres vásárláson | F2.1 második fele |
| F2.2 | Megtakarítási összesítés | F2.2 |
| F2.2b | Lemondásra érett tétel kiemelése | F2.2 második fele |

> A `F2.1b` a `F2.1` pivot-tétele második fele
> (docs/plans/consumer-pivot-2026-08-13.md:125), nem új sorszám.
> A `F2.2b` a `F2.2` pivot-tétele második fele
> (docs/plans/consumer-pivot-2026-08-13.md:126), nem új sorszám.

### F2.1 — Ismétlődő vásárlások felismerése

> Háztartási felhasználóként látom, melyik kereskedőnél költök rendszeresen (heti/havi ismétlődés), hogy felismerjem a láthatatlan fix kiadásaimat.

**Elfogadási kritérium (példa):**
GIVEN 4 hét alatt ≥3 `receipts` azonos normalizált `merchant`-tel és `tenant_id`-val, WHEN `GET /api/v1/analytics/recurring` hívás, THEN a válaszban az adott `merchant` `occurrences >= 3`, `frequency: weekly` és `avg_amount` szerepel.

### F2.1b — Drágulás-jelzés rendszeres vásárláson

> A `F2.1b` a `F2.1` pivot-tétele második fele
> (docs/plans/consumer-pivot-2026-08-13.md:125), nem új sorszám.

> Háztartási felhasználóként értesülök, ha egy rendszeres vásárlásom ára az átlaghoz képest nőtt, hogy időben válthassak.

**Elfogadási kritérium (példa):**
GIVEN egy `merchant` utolsó `amount` értéke > `avg_amount * 1.1`, WHEN a recurring lista lekérdezése, THEN az adott tétel `price_trend: up` és `delta_pct >= 10`.

### F2.2 — Megtakarítási összesítés

> Háztartási felhasználóként egy számban látom: „ennyit spórolnál, ha ezt lemondod / ritkítod", hogy döntéshez ne kelljen számolnom.

**Elfogadási kritérium (példa):**
GIVEN a `receipts` alapján számolt kategória-átlag, WHEN `GET /api/v1/analytics/savings-summary` hívás, THEN `potential_saving = actual - avg_by_category` és `currency: USD` szerepel, üres háztartásnál `potential_saving: 0`.

### F2.2b — Lemondásra érett tétel kiemelése

> A `F2.2b` a `F2.2` pivot-tétele második fele
> (docs/plans/consumer-pivot-2026-08-13.md:126), nem új sorszám.

> Háztartási felhasználóként a legnagyobb megtakarítást hozó 1–2 tétel kiemelve jelenik meg, hogy egy koppintással cselekedhessek.

**Elfogadási kritérium (példa):**
GIVEN ≥2 ismétlődő tétel, WHEN savings-summary lekérdezése, THEN `top_candidates` max 2 elem, `merchant` szerint rendezve `potential_saving` csökkenő sorrendben.

---

## 3. NEM-CÉL

- NEM új adatgyűjtés, NEM új `receipts` mező bekérése a felhasználótól.
- NEM OCR-újraírás, NEM kategorizáló tanítás (a meglévő motor marad).
- NEM QBO / Stripe / push-kézbesítés ebben a specben (F2.5, F3.1 külön).
- NEM családi tag szerinti bontás (F1.3 utáni per-tag tulajdonjog kell hozzá).
- NEM írás a `receipts` táblába — mindkét endpoint read-only aggregáció.
- NEM külső ár-összehasonlítás vagy ajánló-motor.

---

## 4. ADATMODELL

**A meglévő `receipts` séma elég a P0/P1-hez — új oszlop nem kell.**

- Tábla: `receipts(receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, payload TEXT NOT NULL, original_payload TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL)` (`app/platform.py:79`; `CREATE INDEX ix_receipts_tenant ON receipts(tenant_id, receipt_id)` `app/platform.py:83`).
- A `payload` JSON már tartalmazza: `merchant`, `amount`/`total`, `date`, `items[].category` — az ismétlődés `(merchant, amount, date)` hármasból csoportosítással kinyerhető (lásd kutatás 3.§ „zero új adatgyűjtés").
- Normalizálás: `merchant` lowercased+trim, `amount` = `total || sum(items.price)`, `date` ISO `YYYY-MM-DD`.
- Index: meglévő `ix_receipts_tenant ON receipts(tenant_id, receipt_id)` elég; külön `(tenant_id, merchant, date)` index opcionális P1-ben ha lassul.
- Olvasás: `ProductService.list_reviews(actor, ...)` (`app/product_service.py:181`) — a `WHERE tenant_id=?` szűrés **az `actor.tenant_id`-ből** jön, nem külön paraméterből, szóval a tenant-izoláció be van építve. A számítás a `SpendingAnalytics` mintájára épül (`app/analytics.py:48`, a `SpendingGroup`/`TrendPoint` mellett). P2-ben opcionális `recurring_cache` materializált nézet csak teljesítményre, nem funkcionális feltétel.

**Indoklás:** a F2.1+F2.2 értéke éppen az, hogy nincs migráció és nincs új írási útvonal — csak olvasás + aggregáció a meglévő `tenant_id`-szűrt adaton.

---

## 5. API-KONTRAKT

Mindkét endpoint auth-olt, tenant-kötött — a `_resolve_tenant_from_auth` / `api_v1_actor` mintája szerint (`app/api.py:286`, `410`).

| Tulajdonság | `GET /api/v1/analytics/recurring` | `GET /api/v1/analytics/savings-summary` |
|---|---|---|
| Auth | `Depends(api_v1_actor)` — `Authorization` vagy `X-Tenant-ID`+`X-Role`; hiány → `401`, rossz role → `403`; productionben `_is_production` gate él | azonos |
| Tenant-kötés | `actor.tenant_id` alapján `receipts` szűrés; más `tenant_id` adata soha nem látszik | azonos |
| Query | `?period=30d|90d` (default `90d`), `?frequency=weekly|monthly|all` | `?period=30d|90d` (default `30d`) |
| Válasz 200 | `{ period, items: [{ merchant, occurrences, frequency, avg_amount, last_amount, delta_pct, price_trend }], currency }` | `{ period, potential_saving, total_spent, avg_by_category, top_candidates: [{ merchant, potential_saving }], currency }` |
| Üres állapot | `{ items: [] }` — nem 404, onboarding CTA-t a frontend ad | `{ potential_saving: 0, top_candidates: [] }` |
| Hibák | `401` auth nélkül, `422` érvénytelen `period`/`frequency` | `401`/`422` azonos |

Példa (recurring): `GET /api/v1/analytics/recurring?period=90d` → `{ "period": "90d", "currency": "USD", "items": [{ "merchant": "Tesco", "occurrences": 5, "frequency": "weekly", "avg_amount": 42.10, "last_amount": 48.30, "delta_pct": 14.7, "price_trend": "up" }] }`

---

## 6. INCREMENTUMOK — P0 / P1 / P2

### P0 — Heti ismétlődők listája + „ennyivel több mint az átlag" (F2.1 mag)

- **Ad:** `GET /api/v1/analytics/recurring` működik; `merchant` szerinti csoportosítás, `occurrences`, `frequency` (heti: ≥3/4 hét), `avg_amount`/`last_amount`/`delta_pct` a meglévő `receipts` alapján.
- **Nem ad:** `savings-summary` endpoint, megtakarítási kumulált szám, értesítés-kézbesítés.
- **RED teszt:** `tests/test_red_recurring_p0_contract.py` — auth nélkül `401`, más `tenant_id` nem látszik, üres háztartás `items: []`, heti ismétlődő detektálása.

### P1 — Megtakarítási visszacsatolás (F2.2)

- **Ad:** `GET /api/v1/analytics/savings-summary` — `(actual - avg_by_category)` kumulált `potential_saving` + `top_candidates` (max 2) a P0 recurring-jelre építve; read-only, nincs új tábla.
- **Nem ad:** push/e-mail kézbesítés (F2.5), Stripe-fal (F3.1).
- **RED teszt:** `tests/test_red_savings_p1_contract.py` — `potential_saving` számítása, üres állapot `0`, tenant-izoláció, `422` érvénytelen `period`-ra.

### P2 — Értesítés-kézbesítés előkészítése (F2.5 híd)

- **Ad:** a P0/P1 számítására épülő értesítési trigger-jel (pl. `price_trend: up` vagy `potential_saving` küszöb) — a meglévő értesítési motorhoz illesztve, de kézbesítés nélkül (a kézbesítés F2.5 külön spec).
- **Nem ad:** Stripe fizetési fal, QBO-integráció, per-tag bontás.
- **RED teszt:** `tests/test_red_recurring_p2_notify_contract.py` — küszöb feletti drágulás trigger-jelet ad, küszöb alatt nem, auth/tenant contract változatlan.

---
