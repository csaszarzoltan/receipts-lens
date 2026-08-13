# ReceiptLens lakossági fordulat (Consumer Pivot) — specifikáció

**Dátum**: 2026-08-13
**Státusz**: Tervezés kész → kanban átadás
**Scope**: frontend-first (UX/pozicionálás), a backend csak ott változik, ahol a lakossági ígéret megköveteli (auth, OCR-pontosság, family adatmodell)

---

## 0. Háttér — baráti review

A baráti termék-review (2026-08-13) fő diagnózisa:

- A ReceiptLens **nem egyértelmű, kinek készül**: egyszerre OCR API + kisvállalati költségkezelő + könyvelési export + jóváhagyási rendszer + családi app + előfizetés-figyelő + fejlesztői platform.
- A lakossági felhasználót NEM érdekli: approval flow, export preparation, accounting readiness, cost center, mapping version, tenant selector, audit chain, API key, webhook, integration health.
- A lakossági felhasználót érdekli: havi költés, „mire ment el a pénzem", lemondható előfizetések, áremelkedések, családi keret, biztonságos havi költhető összeg, garancia/visszaküldés, nyugta-keresés.
- Pozicionálás: **„A háztartásod intelligens nyugta- és kiadásasszisztense"** — a megtakarítást kell eladni, nem a nyugtafeldolgozást.
- 90 napos terv (1–30. nap: Personal/Family elsődleges, lakossági navigáció, új dashboard, családi fogalmak, PDF import, onboarding, fizetési fal, 10–15 tesztfelhasználó; 31–60. nap: érték — előfizetések/áremelkedések, megtakarítási összesítés, budget-előrejelzés, közös családi inbox, push/e-mail értesítések, garancia/visszaküldési határidő, tanuló kategorizálás; 61–90. nap: értékesíthető béta — Stripe, Personal/Family csomagok, privacy oldal, export + teljes adattörlés, monitoring, onboarding-mérés).

**A jelen tervezési doksi a barát tervét a saját, éles tesztelésből származó meglátásaimmal egészíti ki** — lásd 2. fejezet.

---

## 1. Döntés: irány

**ELFOGADVA**: a ReceiptLens lakossági/family fókuszú „háztartási pénzügyi asszisztenssé" fordul, a meglévő üzleti/könyvelési funkciók megmaradnak, de elrejtve (Business mód, később).

Ez NEM újraépítés — a meglévő képességek (OCR, kategorizálás, budget, előfizetés-felismerés, előrejelzés, anomália, értesítések, automatizálás, email-inbox, offline/PWA, l10n) 90%-a kell a lakossági termékhez is. Amit csinálunk: **átnevezés, átrendezés, kiegészítés** — nem újraírás.

---

## 2. A barát tervéhez fűzött kiegészítések (éles tesztelésből)

### 2.1. Validáció az ELSŐ hétre, nem a 30. napra

A barát a „10–15 tesztfelhasználó" rekrutálást a 30. napra teszi. **Ez túl késő.** Mielőtt 90 napot költünk a Personal/Family átalakításra, 1–2 hét alatt fel kell mérni, van-e kereslet a „drágulás-figyelő / lemondható előfizetés / családi költés" ígéretre. A 30 napos terv első mérföldköve a validáció, nem az építés.

### 2.2. OCR-pontosság = alapfeltétel, nem mellékes

A barát a technológiai alapot 8/10-re értékeli, és feltételezi, hogy az OCR stabil. **Éles tesztelésből: NEM az.** Ismert hibák:
- **BUG-001**: gyenge minőségű képeken `total=1.0` jön ki (hibás összeg) — a „megtakarítási összesítés" csak annyira jó, amennyire az adat pontos. **GIGO**: ha az OCR rossz, a bizalmi ígéret azonnal összeomlik.
- **BUG-009**: 2× Tesseract upload 300s+ terhelten (lassú, de nem halálos).

→ A consumer pivot első fázisába **kötelezően beletartozik az OCR-pontosság-javítás és a „bizonytalan összeg" jelzés** (konfidencia-szint a UI-ban, felhasználói megerősítés gyenge találatnál).

### 2.3. Valódi auth = a Family termék ELŐFELTÉTELE

A jelenlegi `X-Tenant-ID` header-es demó-auth-tal egy családi inbox NEM eladható. A „Háztartás tulajdonosa / Felnőtt / Gyermek / Csak megtekintés" szerepkörökhöz **jelszó nélküli belépés (magic link) + családi meghívók** kellenek. Ez nem utólagos tétel — ez az első fázis egyik legnagyobb blokkja.

### 2.4. „Mennyit költhetek még ma?" — a legjobb dashboard-ötlet

A „biztonságos havi költhető összeg" mutató (napi maradékkeret, budget-visszaszámlálás) a legerősebb visszatérési ok — ezt a P0 dashboard tartalmazza.

### 2.5. Üzleti funkciók elrejtése, nem törlése

A könyvelési/approval/export-prep funkciók **nem törlendők** (megtérülő B2B később), hanem:
- Kikerülnek a fő navigációból
- „Haladó / Business" szekcióba kerülnek, külön belépési ponttal
- A lakossági nézetben a szerepkörök átnevezve (lásd 3.2)

---

## 3. Cél-állapot: lakossági termék

### 3.1. Pozicionálás

- **Egy mondat**: „Fotózd le a nyugtát. Mi megmutatjuk, hol folyik el a pénzed — és hol takaríthatsz meg."
- **Eladott ígéret**: automatikus rendszerezés + családi költésfigyelés + drágulás-felismerés + megtakarítási tippek.
- **Két mód**: Personal/Family (elsődleges, lakossági) és Business (rejtett, később).

### 3.2. Szerepkör-átnevezés

| Jelenlegi | Lakossági |
|---|---|
| Owner / Admin | Háztartás tulajdonosa |
| Member / Editor | Felnőtt tag |
| Viewer | Gyermek / korlátozott tag |
| (új) | Csak megtekintés |
| Accountant / Bookkeeper | Könyvelő / tanácsadó (Business mód) |

### 3.3. Navigáció (P0)

| Jelenlegi (üzleti) | Lakossági (új) |
|---|---|
| Receipts | Vásárlások |
| Upload | Nyugta hozzáadása (kamera / galéria / PDF) |
| Review | Ellenőrzés („mi jött be rosszul?") |
| Budget | Háztartási keret |
| Subscriptions | Előfizetések (lemondásra érettek kiemelve) |
| Forecast | Előrejelzés |
| Reports | Összesítés / Kimutatások |
| Approvals | (rejtve → Business) |
| Exports | (rejtve → Business) |
| Accounting | (rejtve → Business) |
| Integrations | (rejtve → Business) |
| Automations | (rejtve → Business) |
| Inbox | Családi postafiók (megosztott) |
| Duplicates | Ismétlődések |

### 3.4. Új P0 dashboard (lakossági)

1. **„Mennyit költhetek még ma?"** — napi maradékkeret (budget-visszaszámlálás), a 2.4-es ötlet
2. **Havi költés** — „mire ment el a pénzem" kategóriánként (kördiagram/lista)
3. **Drágulás-figyelmeztetések** — „a tej 12%-kal drágult" (meglévő subscription price-increase motor kiterjesztése rendszeres vásárlásokra)
4. **Lemondható előfizetések** — kiemelt lista (meglévő motor, lakossági prezentáció)
5. **Családi keret-státusz** — közös háztartási keret, tagok szerinti bontás
6. **Legutóbbi nyugták** — gyors hozzáférés

---

## 4. Fázisok (kanban item-ek)

### Fázis 0 — Validáció (1–2 hét, párhuzamosan a F1-gyel)
- **V0.1**: 5–10 interjú / célzott megkérdezés a lakossági ígéretről („fizetnél-e havi 3–5€-ért a drágulás-figyelőért?")
- **V0.2**: landing oldal A/B (egy mondat + érték-ígéret), e-mail gyűjtés
- **Exit**: ≥60% pozitív szándék VAGY ≥10 e-mail

### Fázis 1 — Lakossági alap (P0)
- **F1.1**: Role-átnevezés + lakossági navigáció (3.3) + Business-szekció elrejtés
- **F1.2**: Új lakossági dashboard (3.4)
- **F1.3**: Auth: magic link / jelszó nélküli belépés + családi meghívók + role-szintű jogosultságok
- **F1.4**: OCR-pontosság: BUG-001 fix (gyenge képek `total=1.0`) + konfidencia-jelzés a UI-ban + felhasználói megerősítés gyenge találatnál
- **F1.5**: Onboarding flow (3 lépés: mi ez / kamera-hozzáférés / első nyugta)

### Fázis 2 — Érték (P0+)
- **F2.1**: Drágulás-figyelmeztetések rendszeres vásárlásokra (nem csak előfizetésekre)
- **F2.2**: Megtakarítási összesítés („ezzel jársz jobban, ha lemondod")
- **F2.3**: Budget-előrejelzés (meglévő forecast + budget motor, lakossági prezentáció)
- **F2.4**: Közös családi inbox (meglévő email-inbox, családi megosztás)
- **F2.5**: Push/e-mail értesítések (meglévő motor, lakossági csatornák)
- **F2.6**: Garancia/visszaküldési határidő emlékeztetők

### Fázis 3 — Értékesíthető béta (P1)
- **F3.1**: Stripe fizetési fal (Personal/Family csomagok)
- **F3.2**: Privacy oldal + export + teljes adattörlés
- **F3.3**: Monitoring + onboarding-mérés + konverziós/lemorzsolódási események

---

## 5. Mit NEM csinálunk (anti-scope)

- NEM újraírjuk az OCR motort
- NEM töröljük a könyvelési/approval/export funkciókat — elrejtjük
- NEM vezetünk be fizetést a P0-ban (csak F3-ban)
- NEM élesítjük a QBO integrációt a consumer pivot előtt (marad Business)
- NEM csinálunk mobil natív appot — PWA marad (meglévő)

---

## 6. Siker-mérőszámok

- **F1 végén**: a lakossági navigációban 0 üzleti szakkifejezés; az onboarding 3 lépésből áll; a dashboard 6 blokkja mind élő adatot mutat.
- **F2 végén**: ≥1 drágulás-figyelmeztetés / hét átlagos tesztelőnek; ≥1 lemondható előfizetés-javaslat / hónap; a megtakarítási összesítés ≥80%-ban pontos.
- **F3 végén**: 10–15 tesztfelhasználó, ≥5 aktív hetente; konverziós mérés beüzemelve.

---

## 7. Nyitott kérdések (a kanban chain előtt)

1. **Melyik fázis induljon először?** (Javaslat: F0 validáció + F1.1–F1.2 — lakossági navigáció + dashboard — párhuzamosan)
2. **Magic link email-szolgáltató**: SMTP van-e beállítva? (A subscription-alerts `send_email_notification()` soha nem volt meghívva — ez most előtérbe kerül.)
3. **Stripe**: van-e Stripe account? (F3-hoz kell)
