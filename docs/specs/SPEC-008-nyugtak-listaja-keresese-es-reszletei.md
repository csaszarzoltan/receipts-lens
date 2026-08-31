---
id: FEAT-008
title: Nyugták listája, keresése és részletei
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-008
---

# FEAT-008: Nyugták listája, keresése és részletei

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Sok rögzített nyugta között nehéz megtalálni egy konkrét vásárlást és ellenőrizni annak részleteit.

Kanonikus források:
- `briefs/BRIEF-008-nyugtak-listaja-keresese-es-reszletei.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/gui-workspace.md`
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

- ACT-008-01: felhasználóként.

- PRE-008-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-008-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-008-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-008-01 [MUST]: Felhasználóként szeretném a nyugtáimat rendezett listában látni, hogy áttekintsem a korábbi vásárlásaimat.
- REQ-008-02 [MUST]: Felhasználóként szeretnék kereskedő, dátum vagy állapot alapján keresni és szűrni, hogy gyorsan megtaláljam a szükséges nyugtát.
- REQ-008-03 [MUST]: Felhasználóként szeretnék lapozni a nagy eredményhalmazban, hogy a lista kezelhető maradjon.
- REQ-008-04 [MUST]: Felhasználóként szeretném megnyitni egy nyugta teljes részleteit, tételeit és eredeti képét, hogy ellenőrizhessem a rögzített vásárlást.
- REQ-008-05 [MUST]: Felhasználóként szeretnék hasznos üres találati állapotot kapni, hogy módosíthassam a keresést vagy új nyugtát adhassak hozzá.
- REQ-008-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-008-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-008-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-008-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-008-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-008-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-008-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-008-01: `page`, Page; Nyugták listanézete; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-008-02: `page`, Page; Egyedi nyugta részletes nézete; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-008-03: `FilterBar`, Component; Kereső, szűrő és rendező sáv; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-008-04: `ReceiptCard`, Component; Nyugta kártya előnézettel és státusszal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-008-05: `Pagination`, Component; Lapozó komponens; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a nyugtáimat rendezett listában látni, hogy áttekintsem a korábbi vásárlásaimat.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék kereskedő, dátum vagy állapot alapján keresni és szűrni, hogy gyorsan megtaláljam a szükséges nyugtát.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék lapozni a nagy eredményhalmazban, hogy a lista kezelhető maradjon.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném megnyitni egy nyugta teljes részleteit, tételeit és eredeti képét, hogy ellenőrizhessem a rögzített vásárlást.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `RECEIPTS_LISTED` -> `FILTER_APPLIED` -> `RECEIPT_SELECTED` -> `DETAIL_INSPECTED` -> `RECEIPT_DELETED`.
- `- `RECEIPTS_LISTED`` + folytatás -> ``FILTER_APPLIED``
- ``FILTER_APPLIED`` + folytatás -> ``RECEIPT_SELECTED``
- ``RECEIPT_SELECTED`` + folytatás -> ``DETAIL_INSPECTED``
- ``DETAIL_INSPECTED`` + folytatás -> ``RECEIPT_DELETED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-008-01: REQ-008-01 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a nyugtáimat rendezett listában látni, hogy áttekintsem a korábbi vásárlásaimat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-02: REQ-008-02 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék kereskedő, dátum vagy állapot alapján keresni és szűrni, hogy gyorsan megtaláljam a szükséges nyugtát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-03: REQ-008-03 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék lapozni a nagy eredményhalmazban, hogy a lista kezelhető maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-04: REQ-008-04 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném megnyitni egy nyugta teljes részleteit, tételeit és eredeti képét, hogy ellenőrizhessem a rögzített vásárlást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-05: REQ-008-05 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék hasznos üres találati állapotot kapni, hogy módosíthassam a keresést vagy új nyugtát adhassak hozzá.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-06: REQ-008-06 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-07: REQ-008-07 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-008-08: REQ-008-08 bizonyítása

Given a felhasználó, aki korábbi vásárlásokat keres vagy tekint át a szükséges előfeltételekkel
When a REQ-008-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-008-01: `GET /api/v2/receipts`
- Cél: Szűrt, rendezett és lapozott nyugtalista.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-008-02: `GET /api/v2/receipts/{id}`
- Cél: Egyedi nyugta tételei és képadatai.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-008-03: `DELETE /api/v2/receipts/{id}`
- Cél: Nyugta törlése.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/product_service.py`: Keresési szűrők, lapozás, aggregációk.
- `app/receipt_parsing.py`: Nyugta tételek és metaadatok kezelése.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-008-01 -> `tests/test_receipt_detail_api.py` (Integration); scenario: AC-008-01.
- REQ-008-02 -> `tests/test_receipt_crud_runtime.py` (Integration); scenario: AC-008-02.
- REQ-008-03 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-008-03.
- REQ-008-04 -> `tests/test_receipt_detail_api.py` (Integration); scenario: AC-008-04.
- REQ-008-05 -> `tests/test_receipt_crud_runtime.py` (Integration); scenario: AC-008-05.
- REQ-008-06 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-008-06.
- REQ-008-07 -> `tests/test_receipt_detail_api.py` (Integration); scenario: AC-008-07.
- REQ-008-08 -> `tests/test_receipt_crud_runtime.py` (Integration); scenario: AC-008-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
