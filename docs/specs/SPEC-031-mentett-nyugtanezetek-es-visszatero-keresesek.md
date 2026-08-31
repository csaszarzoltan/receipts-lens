---
id: FEAT-031
title: Mentett nyugtanézetek és visszatérő keresések
status: ready_for_dev
version: 1
risk: low
owner: system-architect
related_brief: BRIEF-031
---

# FEAT-031: Mentett nyugtanézetek és visszatérő keresések

## 1. Cél és felhasználói eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Az ismételten használt szűrési feltételek kézi újraépítése lassítja a nyugták rendszeres ellenőrzését.

Kanonikus források:
- `briefs/BRIEF-031-mentett-nyugtanezetek-es-visszatero-keresesek.md`
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

- ACT-031-01: felhasználóként.

- PRE-031-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-031-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-031-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-031-01 [MUST]: Felhasználóként szeretném az aktuális keresési és szűrési feltételeket elnevezett nézetként elmenteni, hogy később egy lépésben visszatérhessek hozzájuk.
- REQ-031-02 [MUST]: Felhasználóként szeretném a saját mentett nézeteimet listában látni, hogy gyorsan kiválaszthassam a szükséges munkakörnyezetet.
- REQ-031-03 [MUST]: Felhasználóként szeretném egy mentett nézet alkalmazásakor az aktuális találatokat látni, hogy a nézet mindig a friss adatokon működjön.
- REQ-031-04 [MUST]: Felhasználóként szeretném a már nem szükséges mentett nézetet törölni, hogy a listám áttekinthető maradjon.
- REQ-031-05 [MUST]: Felhasználóként szeretnék hibás vagy hiányos nézetfeltételeknél javítható visszajelzést kapni, hogy ne keletkezzen használhatatlan nézet.
- REQ-031-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-031-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-031-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-031-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-031-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-031-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-031-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-031-01: `service-feedback`, állapotjelző felület; a külső művelet eredményét közli; folyamatban loading, hibánál újrapróbálható állapotot mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném az aktuális keresési és szűrési feltételeket elnevezett nézetként elmenteni, hogy később egy lépésben visszatérhessek hozzájuk.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a saját mentett nézeteimet listában látni, hogy gyorsan kiválaszthassam a szükséges munkakörnyezetet.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném egy mentett nézet alkalmazásakor az aktuális találatokat látni, hogy a nézet mindig a friss adatokon működjön.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a már nem szükséges mentett nézetet törölni, hogy a listám áttekinthető maradjon.
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

### AC-031-01: REQ-031-01 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném az aktuális keresési és szűrési feltételeket elnevezett nézetként elmenteni, hogy később egy lépésben visszatérhessek hozzájuk.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-02: REQ-031-02 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a saját mentett nézeteimet listában látni, hogy gyorsan kiválaszthassam a szükséges munkakörnyezetet.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-03: REQ-031-03 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném egy mentett nézet alkalmazásakor az aktuális találatokat látni, hogy a nézet mindig a friss adatokon működjön.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-04: REQ-031-04 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a már nem szükséges mentett nézetet törölni, hogy a listám áttekinthető maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-05: REQ-031-05 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék hibás vagy hiányos nézetfeltételeknél javítható visszajelzést kapni, hogy ne keletkezzen használhatatlan nézet.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-06: REQ-031-06 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-07: REQ-031-07 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-031-08: REQ-031-08 bizonyítása

Given a felhasználó, aki rendszeresen ugyanazon kereskedőkre, időszakokra vagy állapotokra keres a szükséges előfeltételekkel
When a REQ-031-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-031-01: `GET /product/saved-views`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-031-02: `POST /product/saved-views`
- Request: validált kérési törzs a meglévő Pydantic és TypeScript szerződés szerint.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-031-03: `DELETE /product/saved-views/{view_id}`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

## 12. Adatmodell és perzisztencia

- `app/product_api.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- `app/product_service.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- Migráció: nincs; a specifikáció a jelenlegi viselkedést rögzíti.
- Sikertelen írás nem hagyhat részleges perzisztált állapotot.

## 13. Tesztterv és lefedettségi leképezés

- REQ-031-01 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-01.
- REQ-031-02 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-02.
- REQ-031-03 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-03.
- REQ-031-04 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-04.
- REQ-031-05 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-05.
- REQ-031-06 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-06.
- REQ-031-07 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-07.
- REQ-031-08 -> `tests/test_product_features.py` (Integration/contract); scenario: AC-031-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
