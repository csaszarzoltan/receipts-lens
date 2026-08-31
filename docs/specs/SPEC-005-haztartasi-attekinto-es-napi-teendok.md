---
id: FEAT-005
title: Háztartási áttekintő és napi teendők
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-005
---

# FEAT-005: Háztartási áttekintő és napi teendők

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználónak egyetlen helyen kell látnia a pénzügyi helyzetét és a következő fontos teendőket.

Kanonikus források:
- `briefs/BRIEF-005-haztartasi-attekinto-es-napi-teendok.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/stories/US-001-dashboard-megnyitas.md`
- `docs/consolidated-v1-workspace.md`

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

- ACT-005-01: háztartási felhasználóként.
- ACT-005-02: új háztartás tagjaként.
- ACT-005-03: felhasználóként.

- PRE-005-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-005-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-005-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-005-01 [MUST]: Háztartási felhasználóként szeretném látni az aktuális költést, keretállapotot és feldolgozási helyzetet, hogy gyorsan megértsem a háztartás pénzügyi állapotát.
- REQ-005-02 [MUST]: Háztartási felhasználóként szeretném a bizonytalan vagy jóváhagyásra váró tételeket kiemelve látni, hogy először a figyelmet igénylő ügyeket intézzem el.
- REQ-005-03 [MUST]: Háztartási felhasználóként szeretnék az összesítőből közvetlenül a kapcsolódó nyugtához vagy feladathoz jutni, hogy kevés lépésből intézkedhessek.
- REQ-005-04 [MUST]: Új háztartás tagjaként szeretnék hasznos üres állapotot látni, hogy tudjam, melyik első művelet hoz létre adatot.
- REQ-005-05 [MUST]: Felhasználóként szeretném tudni, mikor frissült utoljára az összesítés, hogy helyesen értelmezzem az adatokat.
- REQ-005-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-005-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-005-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-005-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-005-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-005-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-005-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-005-01: `page`, Page; Fő vezérlőpult; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-005-02: `KpiCard`, Component; Havi költés és átlag mutató kártyák; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-005-03: `QuotaBar`, Component; Havi kvótahasználat sáv; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-005-04: `NotificationPanel`, Dialog/Panel; Értesítési és teendő panel; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Háztartási felhasználóként szeretném látni az aktuális költést, keretállapotot és feldolgozási helyzetet, hogy gyorsan megértsem a háztartás pénzügyi állapotát.
5. A szereplő végrehajtja a következő felhasználói célt: Háztartási felhasználóként szeretném a bizonytalan vagy jóváhagyásra váró tételeket kiemelve látni, hogy először a figyelmet igénylő ügyeket intézzem el.
6. A szereplő végrehajtja a következő felhasználói célt: Háztartási felhasználóként szeretnék az összesítőből közvetlenül a kapcsolódó nyugtához vagy feladathoz jutni, hogy kevés lépésből intézkedhessek.
7. A szereplő végrehajtja a következő felhasználói célt: Új háztartás tagjaként szeretnék hasznos üres állapotot látni, hogy tudjam, melyik első művelet hoz létre adatot.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `DASHBOARD_LOADING` -> `DATA_AGGREGATED` -> `ACTION_REQUIRED_HIGHLIGHTED` -> `ITEM_NAVIGATED`.
- `- `DASHBOARD_LOADING`` + folytatás -> ``DATA_AGGREGATED``
- ``DATA_AGGREGATED`` + folytatás -> ``ACTION_REQUIRED_HIGHLIGHTED``
- ``ACTION_REQUIRED_HIGHLIGHTED`` + folytatás -> ``ITEM_NAVIGATED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-005-01: REQ-005-01 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási felhasználóként szeretném látni az aktuális költést, keretállapotot és feldolgozási helyzetet, hogy gyorsan megértsem a háztartás pénzügyi állapotát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-02: REQ-005-02 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási felhasználóként szeretném a bizonytalan vagy jóváhagyásra váró tételeket kiemelve látni, hogy először a figyelmet igénylő ügyeket intézzem el.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-03: REQ-005-03 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási felhasználóként szeretnék az összesítőből közvetlenül a kapcsolódó nyugtához vagy feladathoz jutni, hogy kevés lépésből intézkedhessek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-04: REQ-005-04 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új háztartás tagjaként szeretnék hasznos üres állapotot látni, hogy tudjam, melyik első művelet hoz létre adatot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-05: REQ-005-05 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném tudni, mikor frissült utoljára az összesítés, hogy helyesen értelmezzem az adatokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-06: REQ-005-06 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-07: REQ-005-07 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-005-08: REQ-005-08 bizonyítása

Given a bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne a szükséges előfeltételekkel
When a REQ-005-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-005-01: `GET /api/v2/dashboard/summary`
- Cél: Összesített KPI mutatók.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-005-02: `GET /api/v2/dashboard/kpis`
- Cél: Kategória és költségvetési aggregációk.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-005-03: `GET /api/v2/dashboard/actions`
- Cél: Függőben lévő jóváhagyási és ellenőrzési teendők.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/consumer_dashboard.py`: Háztartási KPI-k és akciólista generálása.
- `app/dashboard.py`: Vezérlőpult adatösszesítés.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-005-01 -> `tests/test_us_001_dashboard.py` (Unit/contract); scenario: AC-005-01.
- REQ-005-02 -> `tests/test_us_023_consumer_dashboard_contract.py` (Unit/contract); scenario: AC-005-02.
- REQ-005-03 -> `tests/test_consolidated_workspace.py` (Unit/contract); scenario: AC-005-03.
- REQ-005-04 -> `tests/test_us_001_dashboard.py` (Unit/contract); scenario: AC-005-04.
- REQ-005-05 -> `tests/test_us_023_consumer_dashboard_contract.py` (Unit/contract); scenario: AC-005-05.
- REQ-005-06 -> `tests/test_consolidated_workspace.py` (Unit/contract); scenario: AC-005-06.
- REQ-005-07 -> `tests/test_us_001_dashboard.py` (Unit/contract); scenario: AC-005-07.
- REQ-005-08 -> `tests/test_us_023_consumer_dashboard_contract.py` (Unit/contract); scenario: AC-005-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
