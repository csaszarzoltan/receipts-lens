---
id: FEAT-029
title: OCR-minőség és adminisztratív diagnosztika
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-029
---

# FEAT-029: OCR-minőség és adminisztratív diagnosztika

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felismerési küszöbök ellenőrizetlen módosítása túl sok hibás adatot engedhet automatikusan tovább.

Kanonikus források:
- `briefs/BRIEF-029-ocr-minoseg-es-adminisztrativ-diagnosztika.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/ocr-pipeline.md`

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

- ACT-029-01: minőségért felelős adminisztrátorként.

- PRE-029-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-029-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-029-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-029-01 [MUST]: Minőségért felelős adminisztrátorként szeretném az aktív felismerési profilt és küszöböket áttekinteni, hogy tudjam, milyen szabályok érvényesek.
- REQ-029-02 [MUST]: Minőségért felelős adminisztrátorként szeretnék címkézett mintákon értékelést futtatni, hogy mérjem a tévesen biztosnak jelölt mezők kockázatát.
- REQ-029-03 [MUST]: Minőségért felelős adminisztrátorként szeretném az értékelés eredményét és mintanagyságát látni, hogy megfelelő bizonyíték alapján döntsek.
- REQ-029-04 [MUST]: Minőségért felelős adminisztrátorként szeretném csak sikeres értékelés után közzétenni az új küszöböket, hogy ne romoljon észrevétlenül a felhasználói adatminőség.
- REQ-029-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-029-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-029-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-029-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-029-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-029-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-029-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-029-01: `page`, Page; OCR minőségellenőrző diagnosztikai felület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Minőségért felelős adminisztrátorként szeretném az aktív felismerési profilt és küszöböket áttekinteni, hogy tudjam, milyen szabályok érvényesek.
5. A szereplő végrehajtja a következő felhasználói célt: Minőségért felelős adminisztrátorként szeretnék címkézett mintákon értékelést futtatni, hogy mérjem a tévesen biztosnak jelölt mezők kockázatát.
6. A szereplő végrehajtja a következő felhasználói célt: Minőségért felelős adminisztrátorként szeretném az értékelés eredményét és mintanagyságát látni, hogy megfelelő bizonyíték alapján döntsek.
7. A szereplő végrehajtja a következő felhasználói célt: Minőségért felelős adminisztrátorként szeretném csak sikeres értékelés után közzétenni az új küszöböket, hogy ne romoljon észrevétlenül a felhasználói adatminőség.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `QUALITY_DASHBOARD_OPENED` -> `BENCHMARK_TRIGGERED` -> `SAMPLE_EVALUATED` -> `METRICS_REPORT_DISPLAYED`.
- `- `QUALITY_DASHBOARD_OPENED`` + folytatás -> ``BENCHMARK_TRIGGERED``
- ``BENCHMARK_TRIGGERED`` + folytatás -> ``SAMPLE_EVALUATED``
- ``SAMPLE_EVALUATED`` + folytatás -> ``METRICS_REPORT_DISPLAYED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-029-01: REQ-029-01 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Minőségért felelős adminisztrátorként szeretném az aktív felismerési profilt és küszöböket áttekinteni, hogy tudjam, milyen szabályok érvényesek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-02: REQ-029-02 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Minőségért felelős adminisztrátorként szeretnék címkézett mintákon értékelést futtatni, hogy mérjem a tévesen biztosnak jelölt mezők kockázatát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-03: REQ-029-03 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Minőségért felelős adminisztrátorként szeretném az értékelés eredményét és mintanagyságát látni, hogy megfelelő bizonyíték alapján döntsek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-04: REQ-029-04 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Minőségért felelős adminisztrátorként szeretném csak sikeres értékelés után közzétenni az új küszöböket, hogy ne romoljon észrevétlenül a felhasználói adatminőség.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-05: REQ-029-05 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-06: REQ-029-06 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-029-07: REQ-029-07 bizonyítása

Given a minőségért felelős adminisztrátor, aki címkézett mintákon ellenőrzi a felismerést a szükséges előfeltételekkel
When a REQ-029-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-029-01: `GET /api/v2/diagnostics/ocr-quality`
- Cél: Karakterhiba-arány, felismerési pontosság és fallback arány.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-029-02: `POST /api/v2/diagnostics/benchmark`
- Cél: Minőségi benchmark futtatása mintakészleten.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/quality.py`: Képminőség és kontraszt analízis.
- `app/quality_service.py`: Felismerési hibastatisztikák és összehasonlító benchmarkok.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-029-01 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-029-01.
- REQ-029-02 -> `tests/test_ocr_coverage.py` (Unit/contract); scenario: AC-029-02.
- REQ-029-03 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-029-03.
- REQ-029-04 -> `tests/test_ocr_coverage.py` (Unit/contract); scenario: AC-029-04.
- REQ-029-05 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-029-05.
- REQ-029-06 -> `tests/test_ocr_coverage.py` (Unit/contract); scenario: AC-029-06.
- REQ-029-07 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-029-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
