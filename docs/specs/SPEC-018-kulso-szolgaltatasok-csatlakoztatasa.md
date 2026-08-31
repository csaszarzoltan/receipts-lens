---
id: FEAT-018
title: Külső szolgáltatások csatlakoztatása
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-018
---

# FEAT-018: Külső szolgáltatások csatlakoztatása

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A könyvelési és nyugtaforrások kézi mozgatása időigényes, a kapcsolatok állapota pedig átláthatóságot igényel.

Kanonikus források:
- `briefs/BRIEF-018-kulso-szolgaltatasok-csatlakoztatasa.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/quickbooks-online.md`
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

- ACT-018-01: jogosult felhasználóként.
- ACT-018-02: felhasználóként.

- PRE-018-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-018-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-018-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-018-01 [MUST]: Jogosult felhasználóként szeretném látni az elérhető és már csatlakoztatott szolgáltatásokat, hogy kezelhessem az adatkapcsolatokat.
- REQ-018-02 [MUST]: Jogosult felhasználóként szeretném biztonságos jóváhagyási folyamattal összekapcsolni a szolgáltatást, hogy ne kelljen hozzáférési adatot másolnom.
- REQ-018-03 [MUST]: Jogosult felhasználóként szeretném a kapcsolat állapotát, utolsó szinkronját és esetleges hibáját látni, hogy eldönthessem, szükséges-e beavatkozás.
- REQ-018-04 [MUST]: Jogosult felhasználóként szeretném a kapcsolatot megszüntetni, hogy a külső hozzáférés és tárolt jogosultság eltávolítható legyen.
- REQ-018-05 [MUST]: Felhasználóként szeretném, hogy hibás vagy manipulált visszatérési cím ne téríthesse el a csatlakoztatási folyamatot, hogy a fiókom biztonságban maradjon.
- REQ-018-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-018-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-018-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-018-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-018-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-018-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-018-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-018-01: `page`, Page; Integrációk áttekintő oldala; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-018-02: `page`, Page; Egyedi integrációs beállító és OAuth indító oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném látni az elérhető és már csatlakoztatott szolgáltatásokat, hogy kezelhessem az adatkapcsolatokat.
5. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném biztonságos jóváhagyási folyamattal összekapcsolni a szolgáltatást, hogy ne kelljen hozzáférési adatot másolnom.
6. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném a kapcsolat állapotát, utolsó szinkronját és esetleges hibáját látni, hogy eldönthessem, szükséges-e beavatkozás.
7. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném a kapcsolatot megszüntetni, hogy a külső hozzáférés és tárolt jogosultság eltávolítható legyen.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `DISCONNECTED` -> `OAUTH_INITIATED` -> `CALLBACK_VERIFIED` -> `CONNECTED_AND_ACTIVE` -> `DISCONNECTED`.
- `- `DISCONNECTED`` + folytatás -> ``OAUTH_INITIATED``
- ``OAUTH_INITIATED`` + folytatás -> ``CALLBACK_VERIFIED``
- ``CALLBACK_VERIFIED`` + folytatás -> ``CONNECTED_AND_ACTIVE``
- ``CONNECTED_AND_ACTIVE`` + folytatás -> ``DISCONNECTED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-018-01: REQ-018-01 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném látni az elérhető és már csatlakoztatott szolgáltatásokat, hogy kezelhessem az adatkapcsolatokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-02: REQ-018-02 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném biztonságos jóváhagyási folyamattal összekapcsolni a szolgáltatást, hogy ne kelljen hozzáférési adatot másolnom.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-03: REQ-018-03 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném a kapcsolat állapotát, utolsó szinkronját és esetleges hibáját látni, hogy eldönthessem, szükséges-e beavatkozás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-04: REQ-018-04 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném a kapcsolatot megszüntetni, hogy a külső hozzáférés és tárolt jogosultság eltávolítható legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-05: REQ-018-05 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy hibás vagy manipulált visszatérési cím ne téríthesse el a csatlakoztatási folyamatot, hogy a fiókom biztonságban maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-06: REQ-018-06 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-07: REQ-018-07 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-018-08: REQ-018-08 bizonyítása

Given a üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol a szükséges előfeltételekkel
When a REQ-018-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-018-01: `GET /api/v2/integrations`
- Cél: Elérhető és csatlakoztatott integrációk listája.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-018-02: `POST /api/v2/integrations/{id}/connect`
- Cél: OAuth2 kapcsolat kezdeményezése.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-018-03: `GET /api/v2/integrations/{id}/callback`
- Cél: OAuth visszahívás és token tárolás.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-018-04: `DELETE /api/v2/integrations/{id}/disconnect`
- Cél: Kapcsolat bontása és token törlése.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/integrations.py`: Integrációs katalógus és állapotok.
- `app/connection_service.py`: Kapcsolat életciklus kezelése.
- `app/credential_store.py`: Titkosított token tárolás.
- `app/intuit_oauth.py`: kapcsolódó domain- vagy szolgáltatási állapot.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-018-01 -> `tests/test_qbo_oauth_config.py` (Unit/contract); scenario: AC-018-01.
- REQ-018-02 -> `tests/test_qbo_live_callback.py` (Unit/contract); scenario: AC-018-02.
- REQ-018-03 -> `tests/test_connection_service.py` (Unit/contract); scenario: AC-018-03.
- REQ-018-04 -> `tests/test_us_010_012_connection_completion.py` (Unit/contract); scenario: AC-018-04.
- REQ-018-05 -> `tests/test_qbo_oauth_config.py` (Unit/contract); scenario: AC-018-05.
- REQ-018-06 -> `tests/test_qbo_live_callback.py` (Unit/contract); scenario: AC-018-06.
- REQ-018-07 -> `tests/test_connection_service.py` (Unit/contract); scenario: AC-018-07.
- REQ-018-08 -> `tests/test_us_010_012_connection_completion.py` (Unit/contract); scenario: AC-018-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
