---
id: FEAT-003
title: Google-belépés és fiók-összekapcsolás
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-003
---

# FEAT-003: Google-belépés és fiók-összekapcsolás

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználó gyorsabb belépést szeretne úgy, hogy közben ne keletkezzen véletlenül több fiókja.

Kanonikus források:
- `briefs/BRIEF-003-google-belepes-es-fiok-osszekapcsolas.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/stories/US-002-google-sso.md`
- `docs/plans/google-sso-2026-08-26.md`

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

- ACT-003-01: felhasználóként.
- ACT-003-02: meglévő felhasználóként.

- PRE-003-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-003-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-003-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-003-01 [MUST]: Felhasználóként szeretnék Google-fiókkal belépni, hogy ne kelljen új jelszót kezelnem.
- REQ-003-02 [MUST]: Meglévő felhasználóként szeretném a Google-belépést a jelenlegi fiókomhoz kapcsolni, hogy ugyanazokat az adatokat érjem el mindkét belépési móddal.
- REQ-003-03 [MUST]: Felhasználóként szeretnék biztonságosan visszatérni arra az oldalra, ahonnan a belépést indítottam, hogy folytathassam a megkezdett feladatot.
- REQ-003-04 [MUST]: Felhasználóként szeretnék érthető hibaüzenetet kapni megszakított vagy elutasított Google-belépésnél, hogy más módon beléphessek vagy újrapróbálhassam.
- REQ-003-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-003-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-003-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-003-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-003-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-003-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-003-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-003-01: `page`, Page; Google belépési gomb; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-003-02: `page`, Page; OAuth visszahívási oldal és állapotjelző; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék Google-fiókkal belépni, hogy ne kelljen új jelszót kezelnem.
5. A szereplő végrehajtja a következő felhasználói célt: Meglévő felhasználóként szeretném a Google-belépést a jelenlegi fiókomhoz kapcsolni, hogy ugyanazokat az adatokat érjem el mindkét belépési móddal.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék biztonságosan visszatérni arra az oldalra, ahonnan a belépést indítottam, hogy folytathassam a megkezdett feladatot.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék érthető hibaüzenetet kapni megszakított vagy elutasított Google-belépésnél, hogy más módon beléphessek vagy újrapróbálhassam.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `ANONYMOUS` -> `OAUTH_REDIRECT` -> `OIDC_EXCHANGE` -> `ACCOUNT_LINKED` -> `AUTHENTICATED`.
- `- `ANONYMOUS`` + folytatás -> ``OAUTH_REDIRECT``
- ``OAUTH_REDIRECT`` + folytatás -> ``OIDC_EXCHANGE``
- ``OIDC_EXCHANGE`` + folytatás -> ``ACCOUNT_LINKED``
- ``ACCOUNT_LINKED`` + folytatás -> ``AUTHENTICATED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-003-01: REQ-003-01 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék Google-fiókkal belépni, hogy ne kelljen új jelszót kezelnem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-02: REQ-003-02 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Meglévő felhasználóként szeretném a Google-belépést a jelenlegi fiókomhoz kapcsolni, hogy ugyanazokat az adatokat érjem el mindkét belépési móddal.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-03: REQ-003-03 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék biztonságosan visszatérni arra az oldalra, ahonnan a belépést indítottam, hogy folytathassam a megkezdett feladatot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-04: REQ-003-04 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék érthető hibaüzenetet kapni megszakított vagy elutasított Google-belépésnél, hogy más módon beléphessek vagy újrapróbálhassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-05: REQ-003-05 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-06: REQ-003-06 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-003-07: REQ-003-07 bizonyítása

Given a google-fiókkal rendelkező új vagy meglévő felhasználó a szükséges előfeltételekkel
When a REQ-003-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-003-01: `GET /api/v2/auth/google/login`
- Cél: Google OAuth átirányítás kezdeményezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-003-02: `GET /api/v2/auth/google/callback`
- Cél: Google OIDC token csere és ellenőrzés.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-003-03: `POST /api/v2/auth/google/exchange`
- Cél: Frontend token érvényesítés.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/google_oidc.py`: OIDC állapot, PKCE, Google ID token hitelesítés és fiók-összerendelés.
- `app/auth_api.py`: Munkamenet generálás Google SSO után.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-003-01 -> `tests/test_us_002_google_sso.py` (Unit/contract); scenario: AC-003-01.
- REQ-003-02 -> `tests/test_google_oidc.py` (Unit/contract); scenario: AC-003-02.
- REQ-003-03 -> `tests/test_google_auth_routes.py` (Unit/contract); scenario: AC-003-03.
- REQ-003-04 -> `frontend/e2e/us_002_google_sso.spec.ts` (E2E); scenario: AC-003-04.
- REQ-003-05 -> `tests/test_us_002_google_sso.py` (Unit/contract); scenario: AC-003-05.
- REQ-003-06 -> `tests/test_google_oidc.py` (Unit/contract); scenario: AC-003-06.
- REQ-003-07 -> `tests/test_google_auth_routes.py` (Unit/contract); scenario: AC-003-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
