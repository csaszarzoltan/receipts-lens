---
id: FEAT-011
title: Kategorizálás és háztartási könyvelési besorolás
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-011
---

# FEAT-011: Kategorizálás és háztartási könyvelési besorolás

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A vásárlások egységes besorolása nélkül nehéz megérteni, mire megy el a pénz.

Kanonikus források:
- `briefs/BRIEF-011-kategorizalas-es-haztartasi-konyvelesi-besorolas.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/categorization.md`

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

- ACT-011-01: felhasználóként.
- ACT-011-02: könyvelőként.

- PRE-011-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-011-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-011-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-011-01 [MUST]: Felhasználóként szeretném, hogy a rendszer kategóriát javasoljon a vásárláshoz, hogy gyorsabban rendszerezzem a kiadásaimat.
- REQ-011-02 [MUST]: Felhasználóként szeretném a javasolt kategóriát felülbírálni, hogy a saját háztartási logikám szerint tarthassam nyilván a költést.
- REQ-011-03 [MUST]: Felhasználóként szeretném látni, ha egy besorolás bizonytalan, hogy ellenőrizhessem a kimutatások előtt.
- REQ-011-04 [MUST]: Könyvelőként szeretném az aktuális besorolási szabályokat áttekinteni és verziózottan módosítani, hogy a későbbi exportok következetesek legyenek.
- REQ-011-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-011-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-011-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-011-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-011-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-011-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-011-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-011-01: `page`, Page; Kategória választó lenyíló menü; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-011-02: `page`, Page; Kategória és adólevonási címke módosító; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy a rendszer kategóriát javasoljon a vásárláshoz, hogy gyorsabban rendszerezzem a kiadásaimat.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a javasolt kategóriát felülbírálni, hogy a saját háztartási logikám szerint tarthassam nyilván a költést.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném látni, ha egy besorolás bizonytalan, hogy ellenőrizhessem a kimutatások előtt.
7. A szereplő végrehajtja a következő felhasználói célt: Könyvelőként szeretném az aktuális besorolási szabályokat áttekinteni és verziózottan módosítani, hogy a későbbi exportok következetesek legyenek.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `UNCATEGORIZED` -> `AUTO_CATEGORIZED_BY_RULE` -> `USER_RECLASSIFIED` -> `CATEGORY_PERSISTED`.
- `- `UNCATEGORIZED`` + folytatás -> ``AUTO_CATEGORIZED_BY_RULE``
- ``AUTO_CATEGORIZED_BY_RULE`` + folytatás -> ``USER_RECLASSIFIED``
- ``USER_RECLASSIFIED`` + folytatás -> ``CATEGORY_PERSISTED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-011-01: REQ-011-01 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy a rendszer kategóriát javasoljon a vásárláshoz, hogy gyorsabban rendszerezzem a kiadásaimat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-02: REQ-011-02 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a javasolt kategóriát felülbírálni, hogy a saját háztartási logikám szerint tarthassam nyilván a költést.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-03: REQ-011-03 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném látni, ha egy besorolás bizonytalan, hogy ellenőrizhessem a kimutatások előtt.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-04: REQ-011-04 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Könyvelőként szeretném az aktuális besorolási szabályokat áttekinteni és verziózottan módosítani, hogy a későbbi exportok következetesek legyenek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-05: REQ-011-05 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-06: REQ-011-06 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-011-07: REQ-011-07 bizonyítása

Given a háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál a szükséges előfeltételekkel
When a REQ-011-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-011-01: `POST /api/v1/categorize`
- Cél: Kulcsszavas és kereskedői kategória javaslat.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-011-02: `GET /api/v2/categories`
- Cél: Háztartási kategóriafa lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-011-03: `PUT /api/v2/receipts/{id}/category`
- Cél: Kézi kategória és címke felülírás.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/categorizer.py`: Szabály- és kulcsszóalapú kategóriabesorolás.
- `app/taxonomy.py`: Szabványos háztartási és adózási taxonómia struktúra.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-011-01 -> `tests/test_categorize.py` (Unit/contract); scenario: AC-011-01.
- REQ-011-02 -> `tests/test_taxonomy.py` (Unit/contract); scenario: AC-011-02.
- REQ-011-03 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-011-03.
- REQ-011-04 -> `tests/test_categorize.py` (Unit/contract); scenario: AC-011-04.
- REQ-011-05 -> `tests/test_taxonomy.py` (Unit/contract); scenario: AC-011-05.
- REQ-011-06 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-011-06.
- REQ-011-07 -> `tests/test_categorize.py` (Unit/contract); scenario: AC-011-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
