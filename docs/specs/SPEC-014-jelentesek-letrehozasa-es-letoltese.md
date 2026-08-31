---
id: FEAT-014
title: Jelentések létrehozása és letöltése
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-014
---

# FEAT-014: Jelentések létrehozása és letöltése

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználónak megosztható, újra előállítható összesítésre van szüksége a kiválasztott időszakról.

Kanonikus források:
- `briefs/BRIEF-014-jelentesek-letrehozasa-es-letoltese.md`
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

- ACT-014-01: felhasználóként.

- PRE-014-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-014-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-014-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-014-01 [MUST]: Felhasználóként szeretném kiválasztani a jelentés időszakát és tartalmát, hogy a célomhoz illeszkedő összesítést kapjak.
- REQ-014-02 [MUST]: Felhasználóként szeretném a létrehozás állapotát követni, hogy hosszabb feldolgozásnál is tudjam, mi történik.
- REQ-014-03 [MUST]: Felhasználóként szeretném a kész jelentést megtekinteni és letölteni, hogy archiválhassam vagy megoszthassam.
- REQ-014-04 [MUST]: Felhasználóként szeretnék részleges vagy sikertelen jelentéskészítésnél érthető hibát és újrapróbálást kapni, hogy ne kelljen a beállításokat újra megadnom.
- REQ-014-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-014-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-014-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-014-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-014-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-014-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-014-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-014-01: `page`, Page; Pénzügyi jelentéskészítő munkaterület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-014-02: `Charts`, Component; Jelentés előnézeti diagramok; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném kiválasztani a jelentés időszakát és tartalmát, hogy a célomhoz illeszkedő összesítést kapjak.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a létrehozás állapotát követni, hogy hosszabb feldolgozásnál is tudjam, mi történik.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a kész jelentést megtekinteni és letölteni, hogy archiválhassam vagy megoszthassam.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék részleges vagy sikertelen jelentéskészítésnél érthető hibát és újrapróbálást kapni, hogy ne kelljen a beállításokat újra megadnom.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `REPORT_CRITERIA_SELECTED` -> `SUMMARY_AGGREGATED` -> `PDF_COMPILED` -> `DOWNLOAD_READY`.
- `- `REPORT_CRITERIA_SELECTED`` + folytatás -> ``SUMMARY_AGGREGATED``
- ``SUMMARY_AGGREGATED`` + folytatás -> ``PDF_COMPILED``
- ``PDF_COMPILED`` + folytatás -> ``DOWNLOAD_READY`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-014-01: REQ-014-01 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném kiválasztani a jelentés időszakát és tartalmát, hogy a célomhoz illeszkedő összesítést kapjak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-02: REQ-014-02 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a létrehozás állapotát követni, hogy hosszabb feldolgozásnál is tudjam, mi történik.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-03: REQ-014-03 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a kész jelentést megtekinteni és letölteni, hogy archiválhassam vagy megoszthassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-04: REQ-014-04 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék részleges vagy sikertelen jelentéskészítésnél érthető hibát és újrapróbálást kapni, hogy ne kelljen a beállításokat újra megadnom.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-05: REQ-014-05 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-06: REQ-014-06 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-014-07: REQ-014-07 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki jelentést készít a szükséges előfeltételekkel
When a REQ-014-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-014-01: `GET /api/v1/reports/summary`
- Cél: Összesített kimutatás adott időszakra.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-014-02: `POST /api/v1/reports/generate-pdf`
- Cél: Formázott PDF jelentés generálása.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-014-03: `GET /api/v1/reports/download/{id}`
- Cél: Elkészült jelentés letöltése.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/reports.py`: Jelentés adathalmaz összeállítása.
- `app/report_generator.py`: ReportLab alapú PDF formázás és táblázatépítés.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-014-01 -> `tests/test_reports.py` (Unit/contract); scenario: AC-014-01.
- REQ-014-02 -> `tests/test_report_generator.py` (Unit/contract); scenario: AC-014-02.
- REQ-014-03 -> `tests/test_reports.py` (Unit/contract); scenario: AC-014-03.
- REQ-014-04 -> `tests/test_report_generator.py` (Unit/contract); scenario: AC-014-04.
- REQ-014-05 -> `tests/test_reports.py` (Unit/contract); scenario: AC-014-05.
- REQ-014-06 -> `tests/test_report_generator.py` (Unit/contract); scenario: AC-014-06.
- REQ-014-07 -> `tests/test_reports.py` (Unit/contract); scenario: AC-014-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
