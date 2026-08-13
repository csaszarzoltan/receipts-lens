# User story US-023 — Lakossági dashboard (6 blokk, élő adat)

**Fázis**: F1.2 (docs/plans/consumer-pivot-2026-08-13.md, §3.4)
**Story-manager**: (kitöltésre vár — a story-manager profil nem elérhető ezen a
boardon; a story szövege a feature task (t_778034eb) implementációja közben
készült el, a consumer-pivot acceptance kritériumokból)
**Kapcsolódó task**: t_778034eb · **Review**: t_1716f63a (tech-lead)

---

## Felhasználói történet

> Lakossági felhasználóként (Háztartás tulajdonosa / Felnőtt tag) az
> **Áttekintés** oldalon egy pillantásból látom, hogy
> **mennyit költhetek még ma**, **mire ment el a pénzem ebben a hónapban**,
> **mi drágult**, **melyik előfizetésemet érdemes lemondani**,
> **mennyi maradt a közös háztartási keretből**, és **melyek a legutóbbi
> nyugtáim** — hogy a pénzügyeimet anélkül tudjam kézben tartani, hogy
> könyvelési vagy üzleti fogalmakkal találkoznám.

## Elfogadási kritériumok (BDD)

**GIVEN** a felhasználó belépett és van a háztartásában adat (nyugták, keret,
előfizetések)
**WHEN** megnyitja az Áttekintés (/dashboard) oldalt
**THEN** mind a 6 blokk élő adatot mutat (nincs placeholder):

1. **„Mennyit költhetek még ma?"** — a havi keret visszaszámolása: a
   hátralévő napokra jutó napi összeg (meglévő budget motor).
2. **„Mire ment el a pénzem?"** — havi költés kategóriánként, összeg és
   százalékos megoszlás (meglévő analytics).
3. **Drágulás-figyelmeztetések** — a meglévő előfizetés áremelkedés-motor
   jelzései (rendszeres vásárlásokra bővítés: F2.1).
4. **Lemondható előfizetések** — a meglévő motor listája, lakossági
   prezentációban, lejárati dátummal.
5. **Családi keret-státusz** — közös háztartási keret: keret / elköltve /
   maradék + tagok szerepkörökkel.
6. **Legutóbbi nyugták** — gyors hozzáférés a legfrissebb tételekhez.

**AND** a szövegezés lakossági nyelvezetű — üzleti szakkifejezés
(approval / export / accounting / cost center / tenant / api key / webhook /
readiness / work queue / OCR confidence) sehol nem jelenik meg.

**AND** ha nincs adat (nincs keret, nincs nyugta), a blokk üres állapotot
mutat, onboarding/első lépés CTA-val.

**AND** a sötét mód nem törik (nincs hardcoded szín a dashboard felületen).

**AND** `tsc --noEmit` 0 hibát ad.

## Technikai contract

- `GET /api/v1/consumer/dashboard` (X-Tenant-ID / X-Role kötelező, 401/403
  a meglévő auth contract szerint) — egyetlen kérés, hat blokk:
  `daily_remaining | monthly_by_category | price_alerts |
  cancellable_subscriptions | household | recent_receipts`.
- Aggregáló motor: `app/consumer_dashboard.py` — a meglévő
  budget/analytics/subscription/member/receipt motorokat hívja, nem ír át.
- Frontend: `frontend/app/(app)/dashboard/page.tsx` + típusok
  (`ConsumerDashboard`) + `getConsumerDashboard()` API függvény.
- Tesztek: `tests/test_us_023_consumer_dashboard_contract.py` (19 teszt,
  TestClient integrációval, üres-állapot és auth contract is).

## Kizárt scope (tudatos)

- **BUG-001** (gyenge kép `total=1.0`) → F1.4 (kész, 7d4339d).
- Drágulás-figyelmeztetés **rendszeres vásárlásokra** → F2.1 (a task body
  OPTIONÁLIS-nak jelölte, a motor jelenleg csak előfizetésekre tudja).
- Tagok szerinti **költés-bontás** → F1.3 auth után (per-tag tulajdonjog).
- Valódi családi szerepkörök → F1.3.
