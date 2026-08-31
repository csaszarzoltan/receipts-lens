---
id: FEAT-037
title: Diagnosztikai csomag és támogatási hibaelemzés
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-037
---

# FEAT-037: Diagnosztikai csomag és támogatási hibaelemzés

## 1. Cél és felhasználói eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Összetett hiba esetén a felhasználónak úgy kell támogatási adatot átadnia, hogy érzékeny nyugtatartalom vagy hitelesítő adat ne szivárogjon ki.

Kanonikus források:
- `briefs/BRIEF-037-diagnosztikai-csomag-es-tamogatasi-hibaelemzes.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`

Kapcsolódó domain-invariánsok: szerveroldali jogosultság, háztartási adatelkülönítés, explicit megerősítés, hibánál részleges állapot tilalma és ismételt kérés biztonsága.

## 3. Scope (Benne van / Nincs benne)

### Benne van

- A felsorolt jelenlegi felhasználói folyamatok és megfigyelhető állapotok.
- A javítás, megszakítás, újrapróbálás és jogosultsági korlát, ahol a folyamatban releváns.

### Nincs benne

- A forrásban vagy tesztekben nem igazolt jövőbeli működés.
- A technikai megvalósítás részletei és belső szerződései.

## 4. Szereplők és előfeltételek

- ACT-037-01: felhasználóként.
- ACT-037-02: üzemeltetőként.

- PRE-037-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-037-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-037-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-037-01 [MUST]: Felhasználóként szeretném a rendszer diagnosztikai állapotát áttekinteni, hogy megértsem, mely szolgáltatás működik vagy hibás.
- REQ-037-02 [MUST]: Felhasználóként szeretnék letölthető diagnosztikai csomagot készíteni, hogy a támogatás reprodukálni tudja a hibát.
- REQ-037-03 [MUST]: Felhasználóként szeretném a letöltés előtt tudni, milyen adat kerül a csomagba, hogy ellenőrizhessem az adatvédelmi hatást.
- REQ-037-04 [MUST]: Felhasználóként szeretném, hogy a diagnosztikai csomag ne tartalmazzon jelszót, hozzáférési kulcsot vagy teljes nyugtatartalmat, hogy biztonságosan megoszthassam.
- REQ-037-05 [MUST]: Üzemeltetőként szeretném a környezeti és függőségi állapotot időbélyeggel látni, hogy a hibát a megfelelő rendszerállapothoz kapcsolhassam.
- REQ-037-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-037-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-037-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-037-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-037-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-037-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-037-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-037-01: `service-feedback`, állapotjelző felület; a külső művelet eredményét közli; folyamatban loading, hibánál újrapróbálható állapotot mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a rendszer diagnosztikai állapotát áttekinteni, hogy megértsem, mely szolgáltatás működik vagy hibás.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék letölthető diagnosztikai csomagot készíteni, hogy a támogatás reprodukálni tudja a hibát.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a letöltés előtt tudni, milyen adat kerül a csomagba, hogy ellenőrizhessem az adatvédelmi hatást.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy a diagnosztikai csomag ne tartalmazzon jelszót, hozzáférési kulcsot vagy teljes nyugtatartalmat, hogy biztonságosan megoszthassam.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- `IDLE` + megnyitás -> `LOADING`
- `LOADING` + siker -> `READY`
- `LOADING` + üres eredmény -> `EMPTY`
- `LOADING` + hiba -> `ERROR`
- `READY` + módosítás -> `SUBMITTING`
- `SUBMITTING` + siker -> `SUCCESS`
- `SUBMITTING` + validációs hiba -> `READY`
- `SUBMITTING` + rendszerhiba -> `ERROR`
- `ERROR` + újrapróbálás -> `LOADING`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-037-01: REQ-037-01 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a rendszer diagnosztikai állapotát áttekinteni, hogy megértsem, mely szolgáltatás működik vagy hibás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-02: REQ-037-02 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék letölthető diagnosztikai csomagot készíteni, hogy a támogatás reprodukálni tudja a hibát.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-03: REQ-037-03 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a letöltés előtt tudni, milyen adat kerül a csomagba, hogy ellenőrizhessem az adatvédelmi hatást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-04: REQ-037-04 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy a diagnosztikai csomag ne tartalmazzon jelszót, hozzáférési kulcsot vagy teljes nyugtatartalmat, hogy biztonságosan megoszthassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-05: REQ-037-05 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Üzemeltetőként szeretném a környezeti és függőségi állapotot időbélyeggel látni, hogy a hibát a megfelelő rendszerállapothoz kapcsolhassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-06: REQ-037-06 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-07: REQ-037-07 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-037-08: REQ-037-08 bizonyítása

Given a hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető a szükséges előfeltételekkel
When a REQ-037-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-037-01: `GET /product/diagnostics`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-037-02: `GET /product/diagnostics/bundle`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

## 12. Adatmodell és perzisztencia

- `app/product_api.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- `app/accounting_workspace.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- Migráció: nincs; a specifikáció a jelenlegi viselkedést rögzíti.
- Sikertelen írás nem hagyhat részleges perzisztált állapotot.

## 13. Tesztterv és lefedettségi leképezés

- REQ-037-01 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-01.
- REQ-037-02 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-02.
- REQ-037-03 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-03.
- REQ-037-04 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-04.
- REQ-037-05 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-05.
- REQ-037-06 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-06.
- REQ-037-07 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-07.
- REQ-037-08 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-037-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
