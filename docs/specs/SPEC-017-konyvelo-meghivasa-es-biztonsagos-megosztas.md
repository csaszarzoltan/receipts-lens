---
id: FEAT-017
title: Könyvelő meghívása és biztonságos megosztás
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-017
---

# FEAT-017: Könyvelő meghívása és biztonságos megosztás

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A külső könyvelőnek ellenőrizhető, korlátozott és visszavonható hozzáférésre van szüksége.

Kanonikus források:
- `briefs/BRIEF-017-konyvelo-meghivasa-es-biztonsagos-megosztas.md`
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

- ACT-017-01: háztartási tulajdonosként.
- ACT-017-02: könyvelőként.
- ACT-017-03: meghívottként.

- PRE-017-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-017-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-017-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-017-01 [MUST]: Háztartási tulajdonosként szeretnék lejáró meghívást küldeni a könyvelőmnek, hogy biztonságosan bevonhassam.
- REQ-017-02 [MUST]: Könyvelőként szeretném a meghívás elfogadása előtt látni, mely háztartáshoz és milyen szerepkörrel csatlakozom, hogy tudatos döntést hozzak.
- REQ-017-03 [MUST]: Könyvelőként szeretném a számomra engedélyezett nyugtákat és exportfeladatokat elérni, hogy elvégezhessem a megbízást.
- REQ-017-04 [MUST]: Háztartási tulajdonosként szeretném a könyvelő hozzáférését visszavonni, hogy a megbízás megszűnése után ne lássa az adatokat.
- REQ-017-05 [MUST]: Meghívottként szeretnék lejárt vagy már felhasznált meghívásnál egyértelmű tájékoztatást kapni, hogy új meghívást kérhessek.
- REQ-017-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-017-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-017-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-017-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-017-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-017-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-017-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-017-01: `page`, Page; Könyvelői dedikált olvasási munkaterület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-017-02: `page`, Page; Könyvelői hozzáférések kezelése; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-017-03: `InviteAccountantModal`, Dialog/Panel; Könyvelő meghívása párbeszédablak; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretnék lejáró meghívást küldeni a könyvelőmnek, hogy biztonságosan bevonhassam.
5. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném a meghívás elfogadása előtt látni, mely háztartáshoz és milyen szerepkörrel csatlakozom, hogy tudatos döntést hozzak.
6. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném a számomra engedélyezett nyugtákat és exportfeladatokat elérni, hogy elvégezhessem a megbízást.
7. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném a könyvelő hozzáférését visszavonni, hogy a megbízás megszűnése után ne lássa az adatokat.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `INVITATION_CREATED` -> `TOKEN_DELIVERED` -> `ACCOUNTANT_ACCESSED` -> `ACCESS_EXPIRED_OR_REVOKED`.
- `- `INVITATION_CREATED`` + folytatás -> ``TOKEN_DELIVERED``
- ``TOKEN_DELIVERED`` + folytatás -> ``ACCOUNTANT_ACCESSED``
- ``ACCOUNTANT_ACCESSED`` + folytatás -> ``ACCESS_EXPIRED_OR_REVOKED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-017-01: REQ-017-01 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretnék lejáró meghívást küldeni a könyvelőmnek, hogy biztonságosan bevonhassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-02: REQ-017-02 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a meghívás elfogadása előtt látni, mely háztartáshoz és milyen szerepkörrel csatlakozom, hogy tudatos döntést hozzak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-03: REQ-017-03 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném a számomra engedélyezett nyugtákat és exportfeladatokat elérni, hogy elvégezhessem a megbízást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-04: REQ-017-04 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném a könyvelő hozzáférését visszavonni, hogy a megbízás megszűnése után ne lássa az adatokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-05: REQ-017-05 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Meghívottként szeretnék lejárt vagy már felhasznált meghívásnál egyértelmű tájékoztatást kapni, hogy új meghívást kérhessek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-06: REQ-017-06 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-07: REQ-017-07 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-017-08: REQ-017-08 bizonyítása

Given a háztartási tulajdonos és külső könyvelő vagy tanácsadó a szükséges előfeltételekkel
When a REQ-017-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-017-01: `POST /api/v2/accountant/invite`
- Cél: Időkorlátos meghívó token generálása.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-017-02: `GET /api/v2/accountant/access/{token}`
- Cél: Könyvelői hozzáférés érvényesítése és adatok betöltése.
- Request: útvonalparaméter `token`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-017-03: `DELETE /api/v2/accountant/access/{id}`
- Cél: Könyvelői jogosultság azonnali visszavonása.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/accountant_invite.py`: Biztonságos tokenkezelés, olvasási jogosultság delegálás.
- `app/security.py`: Izolált könyvelői munkamenet biztosítása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-017-01 -> `tests/test_accountant_invite.py` (Unit/contract); scenario: AC-017-01.
- REQ-017-02 -> `tests/test_us_024_auth_contract.py` (Unit/contract); scenario: AC-017-02.
- REQ-017-03 -> `tests/test_us_024b_role_gate_gaps.py` (Unit/contract); scenario: AC-017-03.
- REQ-017-04 -> `tests/test_accountant_invite.py` (Unit/contract); scenario: AC-017-04.
- REQ-017-05 -> `tests/test_us_024_auth_contract.py` (Unit/contract); scenario: AC-017-05.
- REQ-017-06 -> `tests/test_us_024b_role_gate_gaps.py` (Unit/contract); scenario: AC-017-06.
- REQ-017-07 -> `tests/test_accountant_invite.py` (Unit/contract); scenario: AC-017-07.
- REQ-017-08 -> `tests/test_us_024_auth_contract.py` (Unit/contract); scenario: AC-017-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
