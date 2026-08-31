---
id: FEAT-025
title: Adatvédelem, megőrzés és törlés
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-025
---

# FEAT-025: Adatvédelem, megőrzés és törlés

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A pénzügyi képek és adatok érzékenyek, ezért a felhasználónak átlátható megőrzési és törlési kontrollra van szüksége.

Kanonikus források:
- `briefs/BRIEF-025-adatvedelem-megorzes-es-torles.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/engineering-standards.md`

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

- ACT-025-01: felhasználóként.
- ACT-025-02: háztartási tulajdonosként.

- PRE-025-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-025-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-025-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-025-01 [MUST]: Felhasználóként szeretném látni, milyen adatokat őriz a szolgáltatás rólam és a nyugtáimról, hogy tudatosan használhassam.
- REQ-025-02 [MUST]: Háztartási tulajdonosként szeretném beállítani a megőrzési időt, hogy az adatok csak a szükséges ideig maradjanak meg.
- REQ-025-03 [MUST]: Felhasználóként szeretnék adateltávolítás előtt előnézetet kapni a következményekről, hogy elkerüljem a véletlen veszteséget.
- REQ-025-04 [MUST]: Felhasználóként szeretném külön megerősítéssel végrehajtani a végleges törlést, hogy a visszafordíthatatlan művelet tudatos legyen.
- REQ-025-05 [MUST]: Felhasználóként szeretném, hogy sikertelen törlés ne jelenjen meg sikeresként, és az érintett adatok állapota egyértelmű maradjon.
- REQ-025-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-025-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-025-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-025-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-025-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-025-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-025-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-025-01: `page`, Page; Adatvédelmi és megőrzési beállítások képernyője; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném látni, milyen adatokat őriz a szolgáltatás rólam és a nyugtáimról, hogy tudatosan használhassam.
5. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném beállítani a megőrzési időt, hogy az adatok csak a szükséges ideig maradjanak meg.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék adateltávolítás előtt előnézetet kapni a következményekről, hogy elkerüljem a véletlen veszteséget.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném külön megerősítéssel végrehajtani a végleges törlést, hogy a visszafordíthatatlan művelet tudatos legyen.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `PRIVACY_PANEL_VIEWED` -> `DATA_EXPORT_REQUESTED` -> `DELETION_INITIATED` -> `CONFIRMATION_BARRIER_PASSED` -> `ACCOUNT_PURGED`.
- `- `PRIVACY_PANEL_VIEWED`` + folytatás -> ``DATA_EXPORT_REQUESTED``
- ``DATA_EXPORT_REQUESTED`` + folytatás -> ``DELETION_INITIATED``
- ``DELETION_INITIATED`` + folytatás -> ``CONFIRMATION_BARRIER_PASSED``
- ``CONFIRMATION_BARRIER_PASSED`` + folytatás -> ``ACCOUNT_PURGED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-025-01: REQ-025-01 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném látni, milyen adatokat őriz a szolgáltatás rólam és a nyugtáimról, hogy tudatosan használhassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-02: REQ-025-02 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném beállítani a megőrzési időt, hogy az adatok csak a szükséges ideig maradjanak meg.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-03: REQ-025-03 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék adateltávolítás előtt előnézetet kapni a következményekről, hogy elkerüljem a véletlen veszteséget.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-04: REQ-025-04 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném külön megerősítéssel végrehajtani a végleges törlést, hogy a visszafordíthatatlan művelet tudatos legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-05: REQ-025-05 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy sikertelen törlés ne jelenjen meg sikeresként, és az érintett adatok állapota egyértelmű maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-06: REQ-025-06 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-07: REQ-025-07 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-025-08: REQ-025-08 bizonyítása

Given a saját adataiért felelős felhasználó vagy háztartási tulajdonos a szükséges előfeltételekkel
When a REQ-025-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-025-01: `GET /api/v2/privacy/data-export`
- Cél: Teljes személyes adatexport letöltése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-025-02: `DELETE /api/v2/privacy/account`
- Cél: Fiók és kapcsolódó adatok végleges törlése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-025-03: `POST /api/v2/privacy/retention`
- Cél: Automatikus adatmegőrzési időkorlát beállítása.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/governance.py`: GDPR adatexport összeállítása és törlési kaszkádok.
- `app/security.py`: Képadatok biztonságos felülírása és anonimizálás.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-025-01 -> `tests/test_security.py` (Unit/contract); scenario: AC-025-01.
- REQ-025-02 -> `tests/test_security_integration.py` (Integration); scenario: AC-025-02.
- REQ-025-03 -> `tests/test_security.py` (Unit/contract); scenario: AC-025-03.
- REQ-025-04 -> `tests/test_security_integration.py` (Integration); scenario: AC-025-04.
- REQ-025-05 -> `tests/test_security.py` (Unit/contract); scenario: AC-025-05.
- REQ-025-06 -> `tests/test_security_integration.py` (Integration); scenario: AC-025-06.
- REQ-025-07 -> `tests/test_security.py` (Unit/contract); scenario: AC-025-07.
- REQ-025-08 -> `tests/test_security_integration.py` (Integration); scenario: AC-025-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
