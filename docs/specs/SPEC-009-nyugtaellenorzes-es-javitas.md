---
id: FEAT-009
title: Nyugtaellenőrzés és javítás
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-009
---

# FEAT-009: Nyugtaellenőrzés és javítás

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A hibásan felismert mezők javítása nélkül a költési, adózási és exporteredmények megbízhatatlanok.

Kanonikus források:
- `briefs/BRIEF-009-nyugtaellenorzes-es-javitas.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/product-workflows.md`
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

- ACT-009-01: ellenőrzőként.
- ACT-009-02: csak megtekintési jogosultságú felhasználóként.

- PRE-009-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-009-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-009-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-009-01 [MUST]: Ellenőrzőként szeretném a bizonytalan mezőket egy munkafolyamatban végignézni, hogy ne maradjon rejtett hiba.
- REQ-009-02 [MUST]: Ellenőrzőként szeretném a kereskedőt, dátumot, összegeket, pénznemet, kategóriát és tételeket javítani, hogy a nyugta a valós vásárlást tükrözze.
- REQ-009-03 [MUST]: Ellenőrzőként szeretném mentés előtt látni az érvényességi hibákat, hogy például az összesítések vagy kötelező mezők eltéréseit kijavíthassam.
- REQ-009-04 [MUST]: Ellenőrzőként szeretném a javított nyugtát jóváhagyni, hogy az bekerülhessen az összesítésekbe és exportokba.
- REQ-009-05 [MUST]: Ellenőrzőként szeretnék sikertelen mentés után a bevitt módosítások elvesztése nélkül újrapróbálkozni, hogy ne kelljen megismételnem a munkát.
- REQ-009-06 [MUST]: Csak megtekintési jogosultságú felhasználóként szeretném látni, hogy miért nem szerkeszthetek, hogy ne tévesszem össze a jogosultsági korlátot rendszerhibával.
- REQ-009-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-009-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-009-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-009-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-009-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-009-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-009-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-009-01: `page`, Page; Ellenőrzésre váró nyugták munkaterülete; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-009-02: `WorkflowState`, Component; Munkafolyamat állapotjelző; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-009-03: `ConfidenceBadge`, Component; Bizonytalan mezők vizuális kiemelése; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Ellenőrzőként szeretném a bizonytalan mezőket egy munkafolyamatban végignézni, hogy ne maradjon rejtett hiba.
5. A szereplő végrehajtja a következő felhasználói célt: Ellenőrzőként szeretném a kereskedőt, dátumot, összegeket, pénznemet, kategóriát és tételeket javítani, hogy a nyugta a valós vásárlást tükrözze.
6. A szereplő végrehajtja a következő felhasználói célt: Ellenőrzőként szeretném mentés előtt látni az érvényességi hibákat, hogy például az összesítések vagy kötelező mezők eltéréseit kijavíthassam.
7. A szereplő végrehajtja a következő felhasználói célt: Ellenőrzőként szeretném a javított nyugtát jóváhagyni, hogy az bekerülhessen az összesítésekbe és exportokba.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `PENDING_REVIEW` -> `FIELD_MANUALLY_EDITED` -> `CONFIRMED_VERIFIED` vagy `REJECTED`.
- `- `PENDING_REVIEW`` + folytatás -> ``FIELD_MANUALLY_EDITED``
- ``FIELD_MANUALLY_EDITED`` + folytatás -> ``CONFIRMED_VERIFIED` vagy `REJECTED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-009-01: REQ-009-01 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ellenőrzőként szeretném a bizonytalan mezőket egy munkafolyamatban végignézni, hogy ne maradjon rejtett hiba.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-02: REQ-009-02 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ellenőrzőként szeretném a kereskedőt, dátumot, összegeket, pénznemet, kategóriát és tételeket javítani, hogy a nyugta a valós vásárlást tükrözze.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-03: REQ-009-03 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ellenőrzőként szeretném mentés előtt látni az érvényességi hibákat, hogy például az összesítések vagy kötelező mezők eltéréseit kijavíthassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-04: REQ-009-04 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ellenőrzőként szeretném a javított nyugtát jóváhagyni, hogy az bekerülhessen az összesítésekbe és exportokba.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-05: REQ-009-05 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ellenőrzőként szeretnék sikertelen mentés után a bevitt módosítások elvesztése nélkül újrapróbálkozni, hogy ne kelljen megismételnem a munkát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-06: REQ-009-06 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Csak megtekintési jogosultságú felhasználóként szeretném látni, hogy miért nem szerkeszthetek, hogy ne tévesszem össze a jogosultsági korlátot rendszerhibával.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-07: REQ-009-07 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-08: REQ-009-08 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-009-09: REQ-009-09 bizonyítása

Given a felhasználó vagy kijelölt ellenőrző, aki a bizonytalan nyugtákat véglegesíti a szükséges előfeltételekkel
When a REQ-009-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-009-01: `GET /api/v2/review/pending`
- Cél: Ellenőrzésre váró bizonytalan tételek listája.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-009-02: `PUT /api/v2/receipts/{id}/correct`
- Cél: Felhasználói adatjavítás rögzítése.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-009-03: `POST /api/v2/receipts/{id}/confirm`
- Cél: Nyugta jóváhagyása és lezárása.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-009-04: `POST /api/v2/receipts/{id}/reject`
- Cél: Érvénytelenített elutasítás.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/quality_service.py`: Alacsony megbízhatóságú tételek válogatása.
- `app/product_service.py`: Kézi mezőfelülbírálás, könyvelési lezárás.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-009-01 -> `tests/test_review_workflow.py` (Unit/contract); scenario: AC-009-01.
- REQ-009-02 -> `tests/test_us_022_ocr_confidence_contract.py` (Unit/contract); scenario: AC-009-02.
- REQ-009-03 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-009-03.
- REQ-009-04 -> `tests/test_review_workflow.py` (Unit/contract); scenario: AC-009-04.
- REQ-009-05 -> `tests/test_us_022_ocr_confidence_contract.py` (Unit/contract); scenario: AC-009-05.
- REQ-009-06 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-009-06.
- REQ-009-07 -> `tests/test_review_workflow.py` (Unit/contract); scenario: AC-009-07.
- REQ-009-08 -> `tests/test_us_022_ocr_confidence_contract.py` (Unit/contract); scenario: AC-009-08.
- REQ-009-09 -> `tests/test_quality_service.py` (Unit/contract); scenario: AC-009-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
