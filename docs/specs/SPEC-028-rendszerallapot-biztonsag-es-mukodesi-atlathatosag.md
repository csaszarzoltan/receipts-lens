---
id: FEAT-028
title: Rendszerállapot, biztonság és működési átláthatóság
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-028
---

# FEAT-028: Rendszerállapot, biztonság és működési átláthatóság

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználó nem kaphat félrevezető sikert, ha a szolgáltatás vagy valamely szükséges függőség nem működik megfelelően.

Kanonikus források:
- `briefs/BRIEF-028-rendszerallapot-biztonsag-es-mukodesi-atlathatosag.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/engineering-standards.md`
- `docs/api.md`

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

- ACT-028-01: felhasználóként.
- ACT-028-02: üzemeltetőként.

- PRE-028-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-028-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-028-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-028-01 [MUST]: Felhasználóként szeretnék egyértelmű, nem technikai hibaállapotot kapni szolgáltatáskiesésnél, hogy tudjam, mikor és hogyan próbálkozhatok újra.
- REQ-028-02 [MUST]: Felhasználóként szeretném, hogy részleges háttérhiba esetén csak a valóban elkészült műveletek jelenjenek meg sikeresként, hogy ne legyen megtévesztő az állapot.
- REQ-028-03 [MUST]: Üzemeltetőként szeretném külön ellenőrizni az alap elérhetőséget és a tényleges használatra való készséget, hogy hibás rendszert ne engedjek forgalomba.
- REQ-028-04 [MUST]: Felhasználóként szeretném, hogy a szolgáltatás védjen a jogosulatlan hozzáféréstől, veszélyes külső címektől és túlzott kérésszámtól, hogy pénzügyi adataim biztonságban legyenek.
- REQ-028-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-028-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-028-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-028-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-028-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-028-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-028-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-028-01: `page`, Page; Rendszerdiagnosztikai és biztonsági áttekintő; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék egyértelmű, nem technikai hibaállapotot kapni szolgáltatáskiesésnél, hogy tudjam, mikor és hogyan próbálkozhatok újra.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy részleges háttérhiba esetén csak a valóban elkészült műveletek jelenjenek meg sikeresként, hogy ne legyen megtévesztő az állapot.
6. A szereplő végrehajtja a következő felhasználói célt: Üzemeltetőként szeretném külön ellenőrizni az alap elérhetőséget és a tényleges használatra való készséget, hogy hibás rendszert ne engedjek forgalomba.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy a szolgáltatás védjen a jogosulatlan hozzáféréstől, veszélyes külső címektől és túlzott kérésszámtól, hogy pénzügyi adataim biztonságban legyenek.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `HEALTH_CHECK_PINGED` -> `SUBSYSTEMS_EVALUATED` -> `STATUS_METRICS_RENDERED` -> `AUDIT_TRAIL_INSPECTED`.
- `- `HEALTH_CHECK_PINGED`` + folytatás -> ``SUBSYSTEMS_EVALUATED``
- ``SUBSYSTEMS_EVALUATED`` + folytatás -> ``STATUS_METRICS_RENDERED``
- ``STATUS_METRICS_RENDERED`` + folytatás -> ``AUDIT_TRAIL_INSPECTED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-028-01: REQ-028-01 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék egyértelmű, nem technikai hibaállapotot kapni szolgáltatáskiesésnél, hogy tudjam, mikor és hogyan próbálkozhatok újra.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-02: REQ-028-02 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy részleges háttérhiba esetén csak a valóban elkészült műveletek jelenjenek meg sikeresként, hogy ne legyen megtévesztő az állapot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-03: REQ-028-03 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Üzemeltetőként szeretném külön ellenőrizni az alap elérhetőséget és a tényleges használatra való készséget, hogy hibás rendszert ne engedjek forgalomba.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-04: REQ-028-04 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy a szolgáltatás védjen a jogosulatlan hozzáféréstől, veszélyes külső címektől és túlzott kérésszámtól, hogy pénzügyi adataim biztonságban legyenek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-05: REQ-028-05 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-06: REQ-028-06 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-028-07: REQ-028-07 bizonyítása

Given a felhasználó és üzemeltető, aki a szolgáltatás elérhetőségét és biztonságos működését ellenőrzi a szükséges előfeltételekkel
When a REQ-028-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-028-01: `GET /health`
- Cél: Alapvető üzemképesség.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-028-02: `GET /api/v2/system/status`
- Cél: Adatbázis, OCR munkaszálak és háttérfolyamatok állapota.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-028-03: `GET /api/v2/security/audit-log`
- Cél: Biztonsági események és bejelentkezési auditnapló.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/main.py`: Egészség-ellenőrzési logika.
- `app/security.py`: Biztonsági fejlécek, CSP szabályok, audit logolás.
- `app/ssrf_guard.py`: Kimenő hálózati kérések felügyelete és tiltása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-028-01 -> `tests/test_security.py` (Unit/contract); scenario: AC-028-01.
- REQ-028-02 -> `tests/test_security_headers.py` (Unit/contract); scenario: AC-028-02.
- REQ-028-03 -> `tests/test_security_egress_allowlist.py` (Unit/contract); scenario: AC-028-03.
- REQ-028-04 -> `tests/test_ssrf_guard.py` (Unit/contract); scenario: AC-028-04.
- REQ-028-05 -> `tests/test_security.py` (Unit/contract); scenario: AC-028-05.
- REQ-028-06 -> `tests/test_security_headers.py` (Unit/contract); scenario: AC-028-06.
- REQ-028-07 -> `tests/test_security_egress_allowlist.py` (Unit/contract); scenario: AC-028-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
