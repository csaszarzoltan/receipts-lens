---
id: FEAT-002
title: Fiók létrehozása és munkamenet
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-002
---

# FEAT-002: Fiók létrehozása és munkamenet

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználónak védett fiókra és kiszámítható belépési folyamatra van szüksége a személyes pénzügyi adataihoz.

Kanonikus források:
- `briefs/BRIEF-002-fiok-letrehozasa-es-munkamenet.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/engineering-standards.md`
- `docs/plans/user-stories-consumer-pivot.md`

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

- ACT-002-01: új felhasználóként.
- ACT-002-02: felhasználóként.
- ACT-002-03: visszatérő felhasználóként.
- ACT-002-04: bejelentkezett felhasználóként.
- ACT-002-05: túl sok sikertelen próbálkozás után.

- PRE-002-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-002-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-002-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-002-01 [MUST]: A bejelentkezés egyetlen kapun, kézi szerepkör- vagy háztartásválasztás nélkül történik; hitelesítés után a rendszer automatikusan tölti be az aktív háztartást és az összes jogosultságot.
- REQ-002-02 [MUST]: Felhasználóként szeretném, hogy hibás vagy hiányos regisztrációs adatoknál érthető javítási útmutatást kapjak, hogy be tudjam fejezni a regisztrációt.
- REQ-002-03 [MUST]: Visszatérő felhasználóként szeretnék a hitelesítő adataimmal belépni, hogy hozzáférjek a saját nyugtáimhoz.
- REQ-002-04 [MUST]: Bejelentkezett felhasználóként szeretném, hogy aktív használat közben a munkamenetem megmaradjon, hogy ne veszítsem el a folyamatban lévő munkámat.
- REQ-002-05 [MUST]: Bejelentkezett felhasználóként szeretnék kijelentkezni minden aktuális eszközről, hogy elveszett vagy közös eszköz esetén megvédhessem az adataimat.
- REQ-002-06 [MUST]: Túl sok sikertelen próbálkozás után szeretnék egyértelmű visszajelzést kapni az ideiglenes korlátozásról, hogy tudjam, mikor próbálkozhatok újra.
- REQ-002-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-002-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-002-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-002-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-002-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-002-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-002-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-002-01: `page`, Page; Regisztrációs űrlap; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-002-02: `page`, Page; Bejelentkező űrlap; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-002-03: `page`, Page; Varázslink belépési oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Új felhasználóként szeretnék e-mail-címmel és jelszóval fiókot létrehozni, hogy saját védett munkaterületem legyen.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy hibás vagy hiányos regisztrációs adatoknál érthető javítási útmutatást kapjak, hogy be tudjam fejezni a regisztrációt.
6. A szereplő végrehajtja a következő felhasználói célt: Visszatérő felhasználóként szeretnék a hitelesítő adataimmal belépni, hogy hozzáférjek a saját nyugtáimhoz.
7. A szereplő végrehajtja a következő felhasználói célt: Bejelentkezett felhasználóként szeretném, hogy aktív használat közben a munkamenetem megmaradjon, hogy ne veszítsem el a folyamatban lévő munkámat.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `UNAUTHENTICATED` -> `REGISTERED` -> `AUTHENTICATED_SESSION` -> `SESSION_REFRESHED` -> `LOGGED_OUT`.
- `- `UNAUTHENTICATED`` + folytatás -> ``REGISTERED``
- ``REGISTERED`` + folytatás -> ``AUTHENTICATED_SESSION``
- ``AUTHENTICATED_SESSION`` + folytatás -> ``SESSION_REFRESHED``
- ``SESSION_REFRESHED`` + folytatás -> ``LOGGED_OUT`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-002-01: REQ-002-01 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretnék e-mail-címmel és jelszóval fiókot létrehozni, hogy saját védett munkaterületem legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-02: REQ-002-02 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy hibás vagy hiányos regisztrációs adatoknál érthető javítási útmutatást kapjak, hogy be tudjam fejezni a regisztrációt.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-03: REQ-002-03 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Visszatérő felhasználóként szeretnék a hitelesítő adataimmal belépni, hogy hozzáférjek a saját nyugtáimhoz.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-04: REQ-002-04 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Bejelentkezett felhasználóként szeretném, hogy aktív használat közben a munkamenetem megmaradjon, hogy ne veszítsem el a folyamatban lévő munkámat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-05: REQ-002-05 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Bejelentkezett felhasználóként szeretnék kijelentkezni minden aktuális eszközről, hogy elveszett vagy közös eszköz esetén megvédhessem az adataimat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-06: REQ-002-06 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Túl sok sikertelen próbálkozás után szeretnék egyértelmű visszajelzést kapni az ideiglenes korlátozásról, hogy tudjam, mikor próbálkozhatok újra.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-07: REQ-002-07 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-08: REQ-002-08 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-002-09: REQ-002-09 bizonyítása

Given a magánfelhasználó vagy meghívott közreműködő, aki fiókot hoz létre vagy visszatér a szükséges előfeltételekkel
When a REQ-002-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-002-01: `POST /api/v2/auth/register`
- Cél: Új fiók létrehozása jelszó hash-sel.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-002-02: `POST /api/v2/auth/login`
- Cél: Hitelesítés és JWT token kiadás.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-002-03: `POST /api/v2/auth/magic-link`
- Cél: Jelszó nélküli belépési kérelem.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-002-04: `POST /api/v2/auth/refresh`
- Cél: Munkamenet frissítés sliding sessionnel.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-002-05: `POST /api/v2/auth/logout`
- Cél: Munkamenet érvénytelenítése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-002-06: `GET /api/v2/auth/me`
- Cél: Aktuális bejelentkezett felhasználó lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/auth_api.py`: Hitelesítési végpontok, token ellenőrzés.
- `app/security.py`: Jelszó hashing, JWT generálás, rate limiting.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-002-01 -> `tests/test_auth_flow.py` (Unit/contract); scenario: AC-002-01.
- REQ-002-02 -> `tests/test_session_sliding.py` (Unit/contract); scenario: AC-002-02.
- REQ-002-03 -> `tests/test_bug003_006_store_split_auth.py` (Unit/contract); scenario: AC-002-03.
- REQ-002-04 -> `tests/test_security_headers.py` (Unit/contract); scenario: AC-002-04.
- REQ-002-05 -> `tests/test_rate_limiting.py` (Unit/contract); scenario: AC-002-05.
- REQ-002-06 -> `tests/test_auth_flow.py` (Unit/contract); scenario: AC-002-06.
- REQ-002-07 -> `tests/test_session_sliding.py` (Unit/contract); scenario: AC-002-07.
- REQ-002-08 -> `tests/test_bug003_006_store_split_auth.py` (Unit/contract); scenario: AC-002-08.
- REQ-002-09 -> `tests/test_security_headers.py` (Unit/contract); scenario: AC-002-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
