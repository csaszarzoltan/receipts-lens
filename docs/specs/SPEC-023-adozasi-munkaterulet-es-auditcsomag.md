---
id: FEAT-023
title: Adózási munkaterület és auditcsomag
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-023
---

# FEAT-023: Adózási munkaterület és auditcsomag

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Az adózási célú összesítéshez bizonyítható forráskapcsolat, hiányosságjelzés és letölthető dokumentáció szükséges.

Kanonikus források:
- `briefs/BRIEF-023-adozasi-munkaterulet-es-auditcsomag.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/decisions/ADR-004-tax-pro-pack.md`
- `.agent-pipeline/02_specs/done/SPEC-ADR-004.md`

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

- ACT-023-01: könyvelőként.
- ACT-023-02: felhasználóként.

- PRE-023-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-023-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-023-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-023-01 [MUST]: Könyvelőként szeretném az adózási szempontból releváns nyugtákat és összegeket egy munkaterületen áttekinteni, hogy előkészítsem a bevallási munkát.
- REQ-023-02 [MUST]: Könyvelőként szeretném látni a hiányzó vagy kockázatos bizonyítékokat, hogy még időben pótolhassam őket.
- REQ-023-03 [MUST]: Könyvelőként szeretném a levonhatósági vagy adóbesorolási javaslat bizonyosságát és indokát látni, hogy ne kezeljem automatikus döntésként.
- REQ-023-04 [MUST]: Könyvelőként szeretnék auditálható összesítést és dokumentumcsomagot letölteni, hogy a számítások visszakövethetők legyenek.
- REQ-023-05 [MUST]: Felhasználóként szeretném, hogy adózási művelet hibájánál a forrásadat változatlan maradjon, hogy a javítás biztonságosan újrapróbálható legyen.
- REQ-023-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-023-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-023-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-023-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-023-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-023-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-023-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-023-01: `page`, Page; Adózási összesítő munkaterület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-023-02: `TaxBadge`, Component; Adólevonható tétel jelvény; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném az adózási szempontból releváns nyugtákat és összegeket egy munkaterületen áttekinteni, hogy előkészítsem a bevallási munkát.
5. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném látni a hiányzó vagy kockázatos bizonyítékokat, hogy még időben pótolhassam őket.
6. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném a levonhatósági vagy adóbesorolási javaslat bizonyosságát és indokát látni, hogy ne kezeljem automatikus döntésként.
7. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretnék auditálható összesítést és dokumentumcsomagot letölteni, hogy a számítások visszakövethetők legyenek.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `TAX_YEAR_SELECTED` -> `DEDUCTIONS_COMPILED` -> `MISSING_PROOFS_HIGHLIGHTED` -> `AUDIT_PACK_ZIP_BUILT`.
- `- `TAX_YEAR_SELECTED`` + folytatás -> ``DEDUCTIONS_COMPILED``
- ``DEDUCTIONS_COMPILED`` + folytatás -> ``MISSING_PROOFS_HIGHLIGHTED``
- ``MISSING_PROOFS_HIGHLIGHTED`` + folytatás -> ``AUDIT_PACK_ZIP_BUILT`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-023-01: REQ-023-01 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném az adózási szempontból releváns nyugtákat és összegeket egy munkaterületen áttekinteni, hogy előkészítsem a bevallási munkát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-02: REQ-023-02 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném látni a hiányzó vagy kockázatos bizonyítékokat, hogy még időben pótolhassam őket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-03: REQ-023-03 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a levonhatósági vagy adóbesorolási javaslat bizonyosságát és indokát látni, hogy ne kezeljem automatikus döntésként.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-04: REQ-023-04 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretnék auditálható összesítést és dokumentumcsomagot letölteni, hogy a számítások visszakövethetők legyenek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-05: REQ-023-05 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy adózási művelet hibájánál a forrásadat változatlan maradjon, hogy a javítás biztonságosan újrapróbálható legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-06: REQ-023-06 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-07: REQ-023-07 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-023-08: REQ-023-08 bizonyítása

Given a adózási feladatot végző tulajdonos vagy könyvelő a szükséges előfeltételekkel
When a REQ-023-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-023-01: `GET /api/v2/tax/summary`
- Cél: Adóévi levonások és kategóriaösszesítések.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-023-02: `GET /api/v2/tax/deductions`
- Cél: Levonható nyugták tételes kimutatása.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-023-03: `POST /api/v2/tax/audit-pack`
- Cél: Adóhatósági auditcsomag generálása képekkel és metaadatokkal.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/tax_service.py`: Adóalap-csökkentő tételek számítása és szabályai.
- `app/tax_audit.py`: Auditcsomag összeállítása ZIP formátumban hitelesítési ujjlenyomatokkal.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-023-01 -> `tests/test_tax_service.py` (Unit/contract); scenario: AC-023-01.
- REQ-023-02 -> `tests/test_tax_audit.py` (Unit/contract); scenario: AC-023-02.
- REQ-023-03 -> `.agent-pipeline/03_e2e_suites/test_e2e_adr_004.py` (E2E); scenario: AC-023-03.
- REQ-023-04 -> `tests/test_tax_service.py` (Unit/contract); scenario: AC-023-04.
- REQ-023-05 -> `tests/test_tax_audit.py` (Unit/contract); scenario: AC-023-05.
- REQ-023-06 -> `.agent-pipeline/03_e2e_suites/test_e2e_adr_004.py` (E2E); scenario: AC-023-06.
- REQ-023-07 -> `tests/test_tax_service.py` (Unit/contract); scenario: AC-023-07.
- REQ-023-08 -> `tests/test_tax_audit.py` (Unit/contract); scenario: AC-023-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
