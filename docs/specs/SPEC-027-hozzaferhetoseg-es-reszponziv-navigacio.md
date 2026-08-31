---
id: FEAT-027
title: Hozzáférhetőség és reszponzív navigáció
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-027
---

# FEAT-027: Hozzáférhetőség és reszponzív navigáció

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A pénzügyi munkafolyamatoknak egér nélkül, segítő technológiával és különböző képernyőméreteken is elvégezhetőnek kell lenniük.

Kanonikus források:
- `briefs/BRIEF-027-hozzaferhetoseg-es-reszponziv-navigacio.md`
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

- ACT-027-01: billentyűzetet használó felhasználóként.
- ACT-027-02: képernyőolvasót használó felhasználóként.
- ACT-027-03: mobilos felhasználóként.
- ACT-027-04: felhasználóként.

- PRE-027-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-027-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-027-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-027-01 [MUST]: Billentyűzetet használó felhasználóként szeretném logikus sorrendben elérni az összes interaktív elemet, hogy egér nélkül is befejezhessem a feladataimat.
- REQ-027-02 [MUST]: Képernyőolvasót használó felhasználóként szeretném érthető nevekkel és állapotokkal elérni a navigációt, űrlapokat és párbeszédablakokat, hogy önállóan használjam a szolgáltatást.
- REQ-027-03 [MUST]: Mobilos felhasználóként szeretném a fő területeket alsó navigációból vagy összecsukható menüből elérni, hogy kis képernyőn se vesszek el.
- REQ-027-04 [MUST]: Felhasználóként szeretném, hogy betöltés, siker és hiba állapota vizuálisan és segítő technológiával is érzékelhető legyen, hogy mindig tudjam, mi történt.
- REQ-027-05 [MUST]: Felhasználóként szeretném a párbeszédablakot megszakítani és a fókuszt a kiinduló elemre visszakapni, hogy a munkafolyamat kiszámítható maradjon.
- REQ-027-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-027-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-027-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-027-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-027-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-027-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-027-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-027-01: `AppShell`, Component; Alkalmazáskeret ARIA attribútumokkal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-027-02: `Sidebar`, Component; Összecsukható és billentyűzettel vezérelhető oldalsáv; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-027-03: `MobileNav`, Component; Alsó vagy lenyíló mobilnavigáció; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-027-04: `Modal`, Dialog/Panel; Fókuszcsapdával ellátott modális ablak; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Billentyűzetet használó felhasználóként szeretném logikus sorrendben elérni az összes interaktív elemet, hogy egér nélkül is befejezhessem a feladataimat.
5. A szereplő végrehajtja a következő felhasználói célt: Képernyőolvasót használó felhasználóként szeretném érthető nevekkel és állapotokkal elérni a navigációt, űrlapokat és párbeszédablakokat, hogy önállóan használjam a szolgáltatást.
6. A szereplő végrehajtja a következő felhasználói célt: Mobilos felhasználóként szeretném a fő területeket alsó navigációból vagy összecsukható menüből elérni, hogy kis képernyőn se vesszek el.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy betöltés, siker és hiba állapota vizuálisan és segítő technológiával is érzékelhető legyen, hogy mindig tudjam, mi történt.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `KEYBOARD_TAB_FOCUS` -> `MODAL_FOCUS_TRAPPED` -> `ESCAPE_KEY_PRESSED` -> `FOCUS_RESTORED`.
- `- `KEYBOARD_TAB_FOCUS`` + folytatás -> ``MODAL_FOCUS_TRAPPED``
- ``MODAL_FOCUS_TRAPPED`` + folytatás -> ``ESCAPE_KEY_PRESSED``
- ``ESCAPE_KEY_PRESSED`` + folytatás -> ``FOCUS_RESTORED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-027-01: REQ-027-01 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Billentyűzetet használó felhasználóként szeretném logikus sorrendben elérni az összes interaktív elemet, hogy egér nélkül is befejezhessem a feladataimat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-02: REQ-027-02 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Képernyőolvasót használó felhasználóként szeretném érthető nevekkel és állapotokkal elérni a navigációt, űrlapokat és párbeszédablakokat, hogy önállóan használjam a szolgáltatást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-03: REQ-027-03 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Mobilos felhasználóként szeretném a fő területeket alsó navigációból vagy összecsukható menüből elérni, hogy kis képernyőn se vesszek el.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-04: REQ-027-04 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy betöltés, siker és hiba állapota vizuálisan és segítő technológiával is érzékelhető legyen, hogy mindig tudjam, mi történt.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-05: REQ-027-05 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a párbeszédablakot megszakítani és a fókuszt a kiinduló elemre visszakapni, hogy a munkafolyamat kiszámítható maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-06: REQ-027-06 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-07: REQ-027-07 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-027-08: REQ-027-08 bizonyítása

Given a billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó a szükséges előfeltételekkel
When a REQ-027-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

A feature közvetlen felületi vagy belső munkafolyamatként működik; új publikus API nem része ennek a specifikációnak. A meglévő alkalmazási szerződések változatlanok.

## 12. Adatmodell és perzisztencia

- `frontend/components/AppShell.tsx`: WCAG 2.1 AA megfelelőség, fókuszkezelés, képernyőolvasó címkék.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-027-01 -> `tests/test_accessible_actions_and_deep_links.py` (Unit/contract); scenario: AC-027-01.
- REQ-027-02 -> `tests/test_frontend.py` (E2E); scenario: AC-027-02.
- REQ-027-03 -> `tests/test_accessible_actions_and_deep_links.py` (Unit/contract); scenario: AC-027-03.
- REQ-027-04 -> `tests/test_frontend.py` (E2E); scenario: AC-027-04.
- REQ-027-05 -> `tests/test_accessible_actions_and_deep_links.py` (Unit/contract); scenario: AC-027-05.
- REQ-027-06 -> `tests/test_frontend.py` (E2E); scenario: AC-027-06.
- REQ-027-07 -> `tests/test_accessible_actions_and_deep_links.py` (Unit/contract); scenario: AC-027-07.
- REQ-027-08 -> `tests/test_frontend.py` (E2E); scenario: AC-027-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
