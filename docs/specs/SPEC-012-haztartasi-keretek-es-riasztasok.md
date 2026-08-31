---
id: FEAT-012
title: Háztartási keretek és riasztások
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-012
---

# FEAT-012: Háztartási keretek és riasztások

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználó későn veszi észre, ha egy költési kategória megközelíti vagy túllépi a tervezett keretet.

Kanonikus források:
- `briefs/BRIEF-012-haztartasi-keretek-es-riasztasok.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/budgets-and-analytics.md`
- `docs/alerts.md`

Kapcsolódó domain-invariánsok: szerveroldali jogosultság, háztartási adatelkülönítés, explicit megerősítés, hibánál részleges állapot tilalma és ismételt kérés biztonsága.

## 3. Scope (Benne van / Nincs benne)

### Benne van

- A fenti történetekben megnevezett, jelenleg megfigyelhető felhasználói folyamatok.
- A sikeres, üres, hibás, részleges és jogosultság által korlátozott állapotok, ahol azok a jelenlegi működésben relevánsak.
- A felhasználói kontroll, a téves adatok javítása és a biztonságos újrapróbálás.

### Nincs benne

- A forrásban, tesztekben vagy működő felületen nem igazolt jövőbeli képességek.
- Új üzleti szabály, új integráció vagy a jelenlegi termék viselkedésének áttervezése.
- Technikai megvalósítás, belső komponensszerkezet vagy fejlesztési feladatlista.

## 4. Szereplők és előfeltételek

- ACT-012-01: háztartási tulajdonosként.
- ACT-012-02: háztartási felhasználóként.
- ACT-012-03: felhasználóként.

- PRE-012-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-012-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-012-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-012-01 [MUST]: Háztartási tulajdonosként szeretnék időszakos költési keretet létrehozni egy kategóriához, hogy előre szabályozzam a kiadásokat.
- REQ-012-02 [MUST]: Háztartási tulajdonosként szeretném a keretet módosítani vagy törölni, hogy kövessem a megváltozott terveket.
- REQ-012-03 [MUST]: Háztartási felhasználóként szeretném látni a felhasznált és fennmaradó összeget, hogy időben korrigálhassam a költést.
- REQ-012-04 [MUST]: Háztartási felhasználóként szeretnék figyelmeztetést kapni a beállított küszöb elérésekor vagy túllépésekor, hogy elkerüljem a váratlan hiányt.
- REQ-012-05 [MUST]: Felhasználóként szeretném a már kezelt figyelmeztetést nyugtázni, hogy a teendőlistámban csak az aktuális ügyek maradjanak.
- REQ-012-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-012-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-012-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-012-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-012-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-012-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-012-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-012-01: `page`, Page; Költségvetés-kezelő oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-012-02: `QuotaBar`, Component; Keret felhasználási mutató sáv; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-012-03: `NotificationPanel`, Dialog/Panel; Kerettúllépési figyelmeztetések; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretnék időszakos költési keretet létrehozni egy kategóriához, hogy előre szabályozzam a kiadásokat.
5. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném a keretet módosítani vagy törölni, hogy kövessem a megváltozott terveket.
6. A szereplő végrehajtja a következő felhasználói célt: Háztartási felhasználóként szeretném látni a felhasznált és fennmaradó összeget, hogy időben korrigálhassam a költést.
7. A szereplő végrehajtja a következő felhasználói célt: Háztartási felhasználóként szeretnék figyelmeztetést kapni a beállított küszöb elérésekor vagy túllépésekor, hogy elkerüljem a váratlan hiányt.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `BUDGET_SET` -> `SPEND_ACCUMULATING` -> `THRESHOLD_WARNING_80_PERCENT` -> `BUDGET_EXCEEDED_ALERT` -> `ACKNOWLEDGED`.
- `- `BUDGET_SET`` + folytatás -> ``SPEND_ACCUMULATING``
- ``SPEND_ACCUMULATING`` + folytatás -> ``THRESHOLD_WARNING_80_PERCENT``
- ``THRESHOLD_WARNING_80_PERCENT`` + folytatás -> ``BUDGET_EXCEEDED_ALERT``
- ``BUDGET_EXCEEDED_ALERT`` + folytatás -> ``ACKNOWLEDGED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-012-01: REQ-012-01 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretnék időszakos költési keretet létrehozni egy kategóriához, hogy előre szabályozzam a kiadásokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-02: REQ-012-02 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném a keretet módosítani vagy törölni, hogy kövessem a megváltozott terveket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-03: REQ-012-03 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási felhasználóként szeretném látni a felhasznált és fennmaradó összeget, hogy időben korrigálhassam a költést.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-04: REQ-012-04 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási felhasználóként szeretnék figyelmeztetést kapni a beállított küszöb elérésekor vagy túllépésekor, hogy elkerüljem a váratlan hiányt.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-05: REQ-012-05 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a már kezelt figyelmeztetést nyugtázni, hogy a teendőlistámban csak az aktuális ügyek maradjanak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-06: REQ-012-06 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-07: REQ-012-07 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-012-08: REQ-012-08 bizonyítása

Given a keretet tervező háztartási tulajdonos vagy felnőtt tag a szükséges előfeltételekkel
When a REQ-012-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-012-01: `GET /api/v2/budgets`
- Cél: Havi kategóriakeretek listája és aktuális egyenlege.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-012-02: `POST /api/v2/budgets`
- Cél: Új kategóriakeret létrehozása.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-012-03: `PUT /api/v2/budgets/{id}`
- Cél: Keretösszeg módosítása.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-012-04: `GET /api/v2/alerts`
- Cél: Aktív túllépési riasztások lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/budgets.py`: Költségvetési küszöbök számítása és 80% / 100% riasztáskiváltás.
- `app/alerts.py`: Riasztási események kezelése és prioritási sorrendje.
- `app/subscription_alerts.py`: Kritikus túllépési értesítések.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-012-01 -> `tests/test_budgets.py` (Unit/contract); scenario: AC-012-01.
- REQ-012-02 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-012-02.
- REQ-012-03 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-012-03.
- REQ-012-04 -> `tests/test_budgets.py` (Unit/contract); scenario: AC-012-04.
- REQ-012-05 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-012-05.
- REQ-012-06 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-012-06.
- REQ-012-07 -> `tests/test_budgets.py` (Unit/contract); scenario: AC-012-07.
- REQ-012-08 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-012-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
