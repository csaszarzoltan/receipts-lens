---
id: FEAT-004
title: Kezdeti beállítás és első nyugta
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-004
---

# FEAT-004: Kezdeti beállítás és első nyugta

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Az első használatkor túl sok ismeretlen lehetőség akadályozhatja a gyors értékteremtést.

Kanonikus források:
- `briefs/BRIEF-004-kezdeti-beallitas-es-elso-nyugta.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/stories/US-003-nyugta-feltoltes.md`
- `docs/plans/consumer-pivot-2026-08-13.md`

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

- ACT-004-01: új felhasználóként.

- PRE-004-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-004-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-004-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-004-01 [MUST]: Új felhasználóként szeretném lépésekben megadni az alapbeállításaimat, hogy személyre szabott munkaterülettel induljak.
- REQ-004-02 [MUST]: Új felhasználóként szeretném kiválasztani a nyelvet és az alap pénznemet, hogy az összegek és feliratok számomra érthetően jelenjenek meg.
- REQ-004-03 [MUST]: Új felhasználóként szeretném meghívni a háztartásom tagjait vagy ezt a lépést későbbre hagyni, hogy a saját tempómban haladhassak.
- REQ-004-04 [MUST]: Új felhasználóként szeretném már a beállítás közben feltölteni az első nyugtát, hogy azonnal lássam a szolgáltatás eredményét.
- REQ-004-05 [MUST]: Új felhasználóként szeretném egy megszakított beállítást folytatni, hogy ne kelljen elölről kezdenem.
- REQ-004-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-004-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-004-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-004-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-004-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-004-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-004-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-004-01: `page`, Page; 3 lépéses onboarding varázsló; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-004-02: `Onboarding`, Component; Onboarding lépéskezelő komponens; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Új felhasználóként szeretném lépésekben megadni az alapbeállításaimat, hogy személyre szabott munkaterülettel induljak.
5. A szereplő végrehajtja a következő felhasználói célt: Új felhasználóként szeretném kiválasztani a nyelvet és az alap pénznemet, hogy az összegek és feliratok számomra érthetően jelenjenek meg.
6. A szereplő végrehajtja a következő felhasználói célt: Új felhasználóként szeretném meghívni a háztartásom tagjait vagy ezt a lépést későbbre hagyni, hogy a saját tempómban haladhassak.
7. A szereplő végrehajtja a következő felhasználói célt: Új felhasználóként szeretném már a beállítás közben feltölteni az első nyugtát, hogy azonnal lássam a szolgáltatás eredményét.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `NEW_USER` -> `STEP_1_WELCOME` -> `STEP_2_CAPTURE_FIRST` -> `STEP_3_FIRST_RESULT` -> `WORKSPACE_READY`.
- `- `NEW_USER`` + folytatás -> ``STEP_1_WELCOME``
- ``STEP_1_WELCOME`` + folytatás -> ``STEP_2_CAPTURE_FIRST``
- ``STEP_2_CAPTURE_FIRST`` + folytatás -> ``STEP_3_FIRST_RESULT``
- ``STEP_3_FIRST_RESULT`` + folytatás -> ``WORKSPACE_READY`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-004-01: REQ-004-01 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretném lépésekben megadni az alapbeállításaimat, hogy személyre szabott munkaterülettel induljak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-02: REQ-004-02 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretném kiválasztani a nyelvet és az alap pénznemet, hogy az összegek és feliratok számomra érthetően jelenjenek meg.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-03: REQ-004-03 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretném meghívni a háztartásom tagjait vagy ezt a lépést későbbre hagyni, hogy a saját tempómban haladhassak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-04: REQ-004-04 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretném már a beállítás közben feltölteni az első nyugtát, hogy azonnal lássam a szolgáltatás eredményét.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-05: REQ-004-05 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Új felhasználóként szeretném egy megszakított beállítást folytatni, hogy ne kelljen elölről kezdenem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-06: REQ-004-06 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-07: REQ-004-07 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-004-08: REQ-004-08 bizonyítása

Given a frissen regisztrált felhasználó, aki először állítja be a háztartását és tölti fel az első nyugtát a szükséges előfeltételekkel
When a REQ-004-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-004-01: `GET /api/v2/onboarding/status`
- Cél: Onboarding állapot lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-004-02: `POST /api/v2/onboarding/complete`
- Cél: Onboarding befejezése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-004-03: `POST /api/v2/onboarding/first-receipt`
- Cél: Első mintanyugta rögzítése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/product_service.py`: Kezdő konfiguráció, alapértelmezett kategóriák.
- `app/consumer_dashboard.py`: Onboarding előrehaladás nyilvántartása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-004-01 -> `tests/test_us_onboarding_f15.py` (Unit/contract); scenario: AC-004-01.
- REQ-004-02 -> `tests/test_stories.py` (Unit/contract); scenario: AC-004-02.
- REQ-004-03 -> `tests/test_development_stories.py` (Unit/contract); scenario: AC-004-03.
- REQ-004-04 -> `tests/test_us_onboarding_f15.py` (Unit/contract); scenario: AC-004-04.
- REQ-004-05 -> `tests/test_stories.py` (Unit/contract); scenario: AC-004-05.
- REQ-004-06 -> `tests/test_development_stories.py` (Unit/contract); scenario: AC-004-06.
- REQ-004-07 -> `tests/test_us_onboarding_f15.py` (Unit/contract); scenario: AC-004-07.
- REQ-004-08 -> `tests/test_stories.py` (Unit/contract); scenario: AC-004-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
