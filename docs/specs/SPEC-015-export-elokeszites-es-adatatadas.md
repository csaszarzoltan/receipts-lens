---
id: FEAT-015
title: Export-előkészítés és adatátadás
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-015
---

# FEAT-015: Export-előkészítés és adatátadás

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Hibás vagy hiányos nyugtákat nem szabad észrevétlenül külső feldolgozásra átadni.

Kanonikus források:
- `briefs/BRIEF-015-export-elokeszites-es-adatatadas.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/accounting-export-guide.md`

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

- ACT-015-01: könyvelőként.
- ACT-015-02: felhasználóként.

- PRE-015-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-015-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-015-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-015-01 [MUST]: Könyvelőként szeretném export előtt látni, mely nyugták készek és melyek blokkoltak, hogy csak ellenőrzött adatot adjak át.
- REQ-015-02 [MUST]: Könyvelőként szeretném megérteni minden blokkolás okát, hogy célzottan javíthassam a hiányosságokat.
- REQ-015-03 [MUST]: Könyvelőként szeretnék előnézetet kapni az export tartalmáról és formátumáról, hogy megerősítés előtt ellenőrizhessem.
- REQ-015-04 [MUST]: Könyvelőként szeretném a megfelelő profilban létrehozni és letölteni az exportot, hogy az illeszkedjen a célrendszerhez.
- REQ-015-05 [MUST]: Könyvelőként szeretném a korábbi exportok állapotát és eredményét visszakeresni, hogy auditálható legyen az adatátadás.
- REQ-015-06 [MUST]: Felhasználóként szeretném, hogy képletnek tűnő szöveg se válhasson veszélyes táblázatutasítássá, hogy a letöltött állomány biztonságosan megnyitható legyen.
- REQ-015-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-015-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-015-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-015-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-015-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-015-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-015-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-015-01: `page`, Page; Exportkezelő főoldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-015-02: `page`, Page; Export előkészítő varázsló; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-015-03: `page`, Page; Export futtatás auditnaplója és letöltése; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném export előtt látni, mely nyugták készek és melyek blokkoltak, hogy csak ellenőrzött adatot adjak át.
5. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném megérteni minden blokkolás okát, hogy célzottan javíthassam a hiányosságokat.
6. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretnék előnézetet kapni az export tartalmáról és formátumáról, hogy megerősítés előtt ellenőrizhessem.
7. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném a megfelelő profilban létrehozni és letölteni az exportot, hogy az illeszkedjen a célrendszerhez.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `EXPORT_INITIATED` -> `PROFILE_SELECTED` -> `READINESS_VALIDATED` -> `GENERATING_PACKAGE` -> `EXPORT_READY_FOR_DOWNLOAD`.
- `- `EXPORT_INITIATED`` + folytatás -> ``PROFILE_SELECTED``
- ``PROFILE_SELECTED`` + folytatás -> ``READINESS_VALIDATED``
- ``READINESS_VALIDATED`` + folytatás -> ``GENERATING_PACKAGE``
- ``GENERATING_PACKAGE`` + folytatás -> ``EXPORT_READY_FOR_DOWNLOAD`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-015-01: REQ-015-01 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném export előtt látni, mely nyugták készek és melyek blokkoltak, hogy csak ellenőrzött adatot adjak át.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-02: REQ-015-02 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném megérteni minden blokkolás okát, hogy célzottan javíthassam a hiányosságokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-03: REQ-015-03 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretnék előnézetet kapni az export tartalmáról és formátumáról, hogy megerősítés előtt ellenőrizhessem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-04: REQ-015-04 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a megfelelő profilban létrehozni és letölteni az exportot, hogy az illeszkedjen a célrendszerhez.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-05: REQ-015-05 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a korábbi exportok állapotát és eredményét visszakeresni, hogy auditálható legyen az adatátadás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-06: REQ-015-06 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy képletnek tűnő szöveg se válhasson veszélyes táblázatutasítássá, hogy a letöltött állomány biztonságosan megnyitható legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-07: REQ-015-07 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-08: REQ-015-08 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-015-09: REQ-015-09 bizonyítása

Given a könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít a szükséges előfeltételekkel
When a REQ-015-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-015-01: `GET /api/v2/exports/profiles`
- Cél: Támogatott exportsémák: CSV, JSON, Könyvelői ZIP.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-015-02: `POST /api/v2/exports/prepare`
- Cél: Export felkészültség validáció és hiánylista.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-015-03: `POST /api/v2/exports/execute`
- Cél: Export generálás futtatása és csomagolás.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-015-04: `GET /api/v2/exports/runs/{id}`
- Cél: Export állapot és csomag letöltése.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/export.py`: CSV / JSON struktúrázás.
- `app/export_workflow.py`: Többlépcsős export előkészítés, hiányzó mezők ellenőrzése.
- `app/provider_export_service.py`: Könyvelői formátumok és csomagolt képek generálása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-015-01 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-015-01.
- REQ-015-02 -> `tests/test_export_readiness_workflow.py` (Unit/contract); scenario: AC-015-02.
- REQ-015-03 -> `tests/test_export_service.py` (Unit/contract); scenario: AC-015-03.
- REQ-015-04 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-015-04.
- REQ-015-05 -> `tests/test_export_readiness_workflow.py` (Unit/contract); scenario: AC-015-05.
- REQ-015-06 -> `tests/test_export_service.py` (Unit/contract); scenario: AC-015-06.
- REQ-015-07 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-015-07.
- REQ-015-08 -> `tests/test_export_readiness_workflow.py` (Unit/contract); scenario: AC-015-08.
- REQ-015-09 -> `tests/test_export_service.py` (Unit/contract); scenario: AC-015-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
