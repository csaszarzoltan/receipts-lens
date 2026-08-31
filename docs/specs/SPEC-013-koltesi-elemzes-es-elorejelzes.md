---
id: FEAT-013
title: Költési elemzés és előrejelzés
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-013
---

# FEAT-013: Költési elemzés és előrejelzés

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A múltbeli adatok önmagukban nem mutatják meg könnyen a trendeket és a várható jövőbeli terhelést.

Kanonikus források:
- `briefs/BRIEF-013-koltesi-elemzes-es-elorejelzes.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/budgets-and-analytics.md`

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

- ACT-013-01: felhasználóként.

- PRE-013-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-013-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-013-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-013-01 [MUST]: Felhasználóként szeretném időszak és kategória szerint látni a költéseimet, hogy felismerjem a fontos trendeket.
- REQ-013-02 [MUST]: Felhasználóként szeretném összehasonlítani a tényleges költést a keretekkel, hogy lássam, hol tértem el a tervtől.
- REQ-013-03 [MUST]: Felhasználóként szeretném a várható költést és annak bizonytalanságát megtekinteni, hogy megalapozottabban tervezzek.
- REQ-013-04 [MUST]: Felhasználóként szeretném tudni, ha kevés adat miatt az előrejelzés nem megbízható, hogy ne kezeljem biztos tényként.
- REQ-013-05 [MUST]: Felhasználóként szeretnék üres időszaknál is érthető magyarázatot és következő lépést kapni, hogy tudjam, milyen adat szükséges az elemzéshez.
- REQ-013-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-013-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-013-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-013-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-013-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-013-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-013-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-013-01: `page`, Page; Költéselemző és előrejelző képernyő; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-013-02: `Charts`, Component; Idősoros és kategóriadiagramok; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném időszak és kategória szerint látni a költéseimet, hogy felismerjem a fontos trendeket.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném összehasonlítani a tényleges költést a keretekkel, hogy lássam, hol tértem el a tervtől.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a várható költést és annak bizonytalanságát megtekinteni, hogy megalapozottabban tervezzek.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném tudni, ha kevés adat miatt az előrejelzés nem megbízható, hogy ne kezeljem biztos tényként.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `ANALYTICS_PERIOD_SELECTED` -> `HISTORICAL_TREND_CALCULATED` -> `PROJECTION_GENERATED` -> `CHART_RENDERED`.
- `- `ANALYTICS_PERIOD_SELECTED`` + folytatás -> ``HISTORICAL_TREND_CALCULATED``
- ``HISTORICAL_TREND_CALCULATED`` + folytatás -> ``PROJECTION_GENERATED``
- ``PROJECTION_GENERATED`` + folytatás -> ``CHART_RENDERED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-013-01: REQ-013-01 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném időszak és kategória szerint látni a költéseimet, hogy felismerjem a fontos trendeket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-02: REQ-013-02 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném összehasonlítani a tényleges költést a keretekkel, hogy lássam, hol tértem el a tervtől.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-03: REQ-013-03 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a várható költést és annak bizonytalanságát megtekinteni, hogy megalapozottabban tervezzek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-04: REQ-013-04 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném tudni, ha kevés adat miatt az előrejelzés nem megbízható, hogy ne kezeljem biztos tényként.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-05: REQ-013-05 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék üres időszaknál is érthető magyarázatot és következő lépést kapni, hogy tudjam, milyen adat szükséges az elemzéshez.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-06: REQ-013-06 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-07: REQ-013-07 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-013-08: REQ-013-08 bizonyítása

Given a felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál a szükséges előfeltételekkel
When a REQ-013-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-013-01: `GET /api/v2/analytics/spending`
- Cél: Időszaki költési statisztikák és kategóriabontás.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-013-02: `GET /api/v2/forecast/monthly`
- Cél: Hóvégi várható költés és trend becslés.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/analytics.py`: Aggregált költési idősorok és kategóriaarányok.
- `app/forecast.py`: Idősoros trendanalízis, szezonalitás és előrejelzési sáv.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-013-01 -> `tests/test_analytics.py` (Unit/contract); scenario: AC-013-01.
- REQ-013-02 -> `tests/test_forecast.py` (Unit/contract); scenario: AC-013-02.
- REQ-013-03 -> `tests/test_analytics.py` (Unit/contract); scenario: AC-013-03.
- REQ-013-04 -> `tests/test_forecast.py` (Unit/contract); scenario: AC-013-04.
- REQ-013-05 -> `tests/test_analytics.py` (Unit/contract); scenario: AC-013-05.
- REQ-013-06 -> `tests/test_forecast.py` (Unit/contract); scenario: AC-013-06.
- REQ-013-07 -> `tests/test_analytics.py` (Unit/contract); scenario: AC-013-07.
- REQ-013-08 -> `tests/test_forecast.py` (Unit/contract); scenario: AC-013-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
