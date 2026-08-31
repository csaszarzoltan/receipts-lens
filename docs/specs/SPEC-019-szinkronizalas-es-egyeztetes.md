---
id: FEAT-019
title: Szinkronizálás és egyeztetés
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-019
---

# FEAT-019: Szinkronizálás és egyeztetés

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A külső rendszer és a helyi nyilvántartás eltérései csendes adatvesztést vagy kettős rögzítést okozhatnak.

Kanonikus források:
- `briefs/BRIEF-019-szinkronizalas-es-egyeztetes.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/decisions/ADR-006-qbo-xero-sync-accountant-invite.md`

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

- ACT-019-01: könyvelőként.

- PRE-019-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-019-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-019-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-019-01 [MUST]: Könyvelőként szeretném előnézetben látni, milyen adatok kerülnének szinkronizálásra, hogy a változtatás előtt ellenőrizhessem a hatást.
- REQ-019-02 [MUST]: Könyvelőként szeretném megerősíteni a szinkronizálást, hogy csak tudatos döntés után történjen külső módosítás.
- REQ-019-03 [MUST]: Könyvelőként szeretném tételesen látni a sikeres, kihagyott és hibás eredményeket, hogy a részleges végrehajtást kezelhessem.
- REQ-019-04 [MUST]: Könyvelőként szeretném ismételt kérés esetén elkerülni a duplikált külső bejegyzéseket, hogy biztonságosan újrapróbálhassak.
- REQ-019-05 [MUST]: Könyvelőként szeretném a helyi és külső eltéréseket egyeztetni, hogy a két rendszer közötti állapot tisztázható legyen.
- REQ-019-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-019-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-019-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-019-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-019-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-019-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-019-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-019-01: `page`, Page; Könyvelési szinkronizációs és egyeztetési munkaterület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném előnézetben látni, milyen adatok kerülnének szinkronizálásra, hogy a változtatás előtt ellenőrizhessem a hatást.
5. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném megerősíteni a szinkronizálást, hogy csak tudatos döntés után történjen külső módosítás.
6. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném tételesen látni a sikeres, kihagyott és hibás eredményeket, hogy a részleges végrehajtást kezelhessem.
7. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném ismételt kérés esetén elkerülni a duplikált külső bejegyzéseket, hogy biztonságosan újrapróbálhassak.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `SYNC_IDLE` -> `SYNC_IN_PROGRESS` -> `DISCREPANCY_DETECTED` -> `MANUAL_RECONCILIATION` -> `FULLY_SYNCED`.
- `- `SYNC_IDLE`` + folytatás -> ``SYNC_IN_PROGRESS``
- ``SYNC_IN_PROGRESS`` + folytatás -> ``DISCREPANCY_DETECTED``
- ``DISCREPANCY_DETECTED`` + folytatás -> ``MANUAL_RECONCILIATION``
- ``MANUAL_RECONCILIATION`` + folytatás -> ``FULLY_SYNCED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-019-01: REQ-019-01 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném előnézetben látni, milyen adatok kerülnének szinkronizálásra, hogy a változtatás előtt ellenőrizhessem a hatást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-02: REQ-019-02 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném megerősíteni a szinkronizálást, hogy csak tudatos döntés után történjen külső módosítás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-03: REQ-019-03 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném tételesen látni a sikeres, kihagyott és hibás eredményeket, hogy a részleges végrehajtást kezelhessem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-04: REQ-019-04 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném ismételt kérés esetén elkerülni a duplikált külső bejegyzéseket, hogy biztonságosan újrapróbálhassak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-05: REQ-019-05 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a helyi és külső eltéréseket egyeztetni, hogy a két rendszer közötti állapot tisztázható legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-06: REQ-019-06 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-07: REQ-019-07 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-019-08: REQ-019-08 bizonyítása

Given a könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál a szükséges előfeltételekkel
When a REQ-019-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-019-01: `POST /api/v2/sync/trigger`
- Cél: Szinkronizáció indítása külső főkönyvbe.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-019-02: `GET /api/v2/sync/status`
- Cél: Szinkronizációs folyamat állapota.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-019-03: `POST /api/v2/reconciliation/run`
- Cél: Tranzakcióegyeztetési vizsgálat futtatása.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/sync_service.py`: Kétirányú adatmozgás, hibaújrapróbálás.
- `app/reconciliation_service.py`: Főkönyvi tételek és nyugták automatikus párosítása.
- `app/accounting_projection.py`: Könyvelési kontírozási vetület előállítása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-019-01 -> `tests/test_sync_service.py` (Unit/contract); scenario: AC-019-01.
- REQ-019-02 -> `tests/test_reconciliation_service.py` (Unit/contract); scenario: AC-019-02.
- REQ-019-03 -> `tests/test_us_010_018_api_completion.py` (Integration); scenario: AC-019-03.
- REQ-019-04 -> `tests/test_sync_service.py` (Unit/contract); scenario: AC-019-04.
- REQ-019-05 -> `tests/test_reconciliation_service.py` (Unit/contract); scenario: AC-019-05.
- REQ-019-06 -> `tests/test_us_010_018_api_completion.py` (Integration); scenario: AC-019-06.
- REQ-019-07 -> `tests/test_sync_service.py` (Unit/contract); scenario: AC-019-07.
- REQ-019-08 -> `tests/test_reconciliation_service.py` (Unit/contract); scenario: AC-019-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
