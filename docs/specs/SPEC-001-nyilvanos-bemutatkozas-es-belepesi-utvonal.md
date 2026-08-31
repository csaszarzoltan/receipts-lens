---
id: FEAT-001
title: Nyilvános bemutatkozás és belépési útvonal
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-001
---

# FEAT-001: Nyilvános bemutatkozás és belépési útvonal

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Látogatóként nehezen tudnám felmérni, mire használható a szolgáltatás, és hogyan kezdhetem el biztonságosan.

Kanonikus források:
- `briefs/BRIEF-001-nyilvanos-bemutatkozas-es-belepesi-utvonal.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/WINDOWS_GUIDE_HU.md`
- `docs/decisions/ADR-001-pre-login-language-switcher.md`
- `docs/decisions/ADR-002-pre-login-dark-mode.md`
- `README.md`

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

- ACT-001-01: látogatóként.
- ACT-001-02: mobilos látogatóként.
- ACT-001-03: visszatérő felhasználóként.

- PRE-001-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-001-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-001-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-001-01 [MUST]: Látogatóként szeretném áttekinteni a szolgáltatás fő előnyeit, hogy eldönthessem, alkalmas-e a nyugtáim kezelésére.
- REQ-001-02 [MUST]: Látogatóként szeretnék egyértelműen eljutni a regisztrációhoz vagy a bejelentkezéshez, hogy ne kelljen a következő lépést keresnem.
- REQ-001-03 [MUST]: Mobilos látogatóként szeretném a bemutatkozó oldalt kis képernyőn is használni, hogy útközben is el tudjam kezdeni a folyamatot.
- REQ-001-04 [MUST]: Visszatérő felhasználóként szeretném a munkaterületet közvetlenül megnyitni, hogy ne kelljen újra végignéznem a bemutatkozást.
- REQ-001-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-001-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-001-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-001-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-001-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-001-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-001-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-001-01: `page`, Page; Főoldali bemutatkozó landing oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-001-02: `Topbar`, Component; Navigációs sáv bejelentkezési és regisztrációs hivatkozásokkal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-001-03: `ThemeToggle`, Component; Téma váltó gomb a fejlécben; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-001-04: `LanguageSwitcher`, Component; Nyelvválasztó komponens; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-001-05: `MobileNav`, Component; Reszponzív mobilos menü; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Látogatóként szeretném áttekinteni a szolgáltatás fő előnyeit, hogy eldönthessem, alkalmas-e a nyugtáim kezelésére.
5. A szereplő végrehajtja a következő felhasználói célt: Látogatóként szeretnék egyértelműen eljutni a regisztrációhoz vagy a bejelentkezéshez, hogy ne kelljen a következő lépést keresnem.
6. A szereplő végrehajtja a következő felhasználói célt: Mobilos látogatóként szeretném a bemutatkozó oldalt kis képernyőn is használni, hogy útközben is el tudjam kezdeni a folyamatot.
7. A szereplő végrehajtja a következő felhasználói célt: Visszatérő felhasználóként szeretném a munkaterületet közvetlenül megnyitni, hogy ne kelljen újra végignéznem a bemutatkozást.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `ANONYMOUS_VISITOR` -> `EXPLORING_LANDING` -> `NAVIGATE_TO_AUTH` (Login / Register) vagy `DIRECT_WORKSPACE_ACCESS`.
- `- `ANONYMOUS_VISITOR`` + folytatás -> ``EXPLORING_LANDING``
- ``EXPLORING_LANDING`` + folytatás -> ``NAVIGATE_TO_AUTH` (Login / Register) vagy `DIRECT_WORKSPACE_ACCESS`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-001-01: REQ-001-01 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Látogatóként szeretném áttekinteni a szolgáltatás fő előnyeit, hogy eldönthessem, alkalmas-e a nyugtáim kezelésére.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-02: REQ-001-02 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Látogatóként szeretnék egyértelműen eljutni a regisztrációhoz vagy a bejelentkezéshez, hogy ne kelljen a következő lépést keresnem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-03: REQ-001-03 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Mobilos látogatóként szeretném a bemutatkozó oldalt kis képernyőn is használni, hogy útközben is el tudjam kezdeni a folyamatot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-04: REQ-001-04 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Visszatérő felhasználóként szeretném a munkaterületet közvetlenül megnyitni, hogy ne kelljen újra végignéznem a bemutatkozást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-05: REQ-001-05 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-06: REQ-001-06 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-001-07: REQ-001-07 bizonyítása

Given a új vagy visszatérő látogató, aki még nincs bejelentkezve a szükséges előfeltételekkel
When a REQ-001-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-001-01: `GET /`
- Cél: Nyilvános kezdőlap HTML / JSON válasz.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-001-02: `GET /health`
- Cél: Rendszer elérhetőségi állapot.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/homepage.py`: Önálló kezdőlap renderelés és funkcionalitás ismertető.
- `app/main.py`: Alkalmazás belépési pont és root routerek.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-001-01 -> `tests/test_homepage.py` (Unit/contract); scenario: AC-001-01.
- REQ-001-02 -> `tests/test_frontend.py` (E2E); scenario: AC-001-02.
- REQ-001-03 -> `tests/test_windows_guide.py` (Unit/contract); scenario: AC-001-03.
- REQ-001-04 -> `tests/test_homepage.py` (Unit/contract); scenario: AC-001-04.
- REQ-001-05 -> `tests/test_frontend.py` (E2E); scenario: AC-001-05.
- REQ-001-06 -> `tests/test_windows_guide.py` (Unit/contract); scenario: AC-001-06.
- REQ-001-07 -> `tests/test_homepage.py` (Unit/contract); scenario: AC-001-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
