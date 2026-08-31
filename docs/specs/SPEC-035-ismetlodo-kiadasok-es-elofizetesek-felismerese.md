---
id: FEAT-035
title: Ismétlődő kiadások és előfizetések felismerése
status: ready_for_dev
version: 1
risk: low
owner: system-architect
related_brief: BRIEF-035
---

# FEAT-035: Ismétlődő kiadások és előfizetések felismerése

## 1. Cél és felhasználói eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A rendszeresen ismétlődő terhelések és árváltozások észrevétlenül növelhetik a háztartás költségeit.

Kanonikus források:
- `briefs/BRIEF-035-ismetlodo-kiadasok-es-elofizetesek-felismerese.md`
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

- ACT-035-01: felhasználóként.

- PRE-035-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-035-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-035-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-035-01 [MUST]: Felhasználóként szeretném az azonosított ismétlődő kiadásokat és előfizetéseket listában látni, hogy áttekintsem a rendszeres terheket.
- REQ-035-02 [MUST]: Felhasználóként szeretném látni a várható következő terhelést és a korábbi összegek trendjét, hogy előre tervezzek.
- REQ-035-03 [MUST]: Felhasználóként szeretnék áremelkedésre vagy közelgő megújulásra figyelmeztetést kapni, hogy időben dönthessek a folytatásról.
- REQ-035-04 [MUST]: Felhasználóként szeretném egy tévesen ismétlődőnek jelölt kiadás besorolását javítani, hogy az összesítés ne legyen félrevezető.
- REQ-035-05 [MUST]: Felhasználóként szeretnék egy lemondási útmutatót megtekinteni, ha az adott előfizetéshez rendelkezésre áll, hogy csökkenthessem a felesleges költséget.
- REQ-035-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-035-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-035-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-035-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-035-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-035-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-035-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-035-01: `service-feedback`, állapotjelző felület; a külső művelet eredményét közli; folyamatban loading, hibánál újrapróbálható állapotot mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném az azonosított ismétlődő kiadásokat és előfizetéseket listában látni, hogy áttekintsem a rendszeres terheket.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném látni a várható következő terhelést és a korábbi összegek trendjét, hogy előre tervezzek.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék áremelkedésre vagy közelgő megújulásra figyelmeztetést kapni, hogy időben dönthessek a folytatásról.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném egy tévesen ismétlődőnek jelölt kiadás besorolását javítani, hogy az összesítés ne legyen félrevezető.
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

### AC-035-01: REQ-035-01 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném az azonosított ismétlődő kiadásokat és előfizetéseket listában látni, hogy áttekintsem a rendszeres terheket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-02: REQ-035-02 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném látni a várható következő terhelést és a korábbi összegek trendjét, hogy előre tervezzek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-03: REQ-035-03 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék áremelkedésre vagy közelgő megújulásra figyelmeztetést kapni, hogy időben dönthessek a folytatásról.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-04: REQ-035-04 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném egy tévesen ismétlődőnek jelölt kiadás besorolását javítani, hogy az összesítés ne legyen félrevezető.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-05: REQ-035-05 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék egy lemondási útmutatót megtekinteni, ha az adott előfizetéshez rendelkezésre áll, hogy csökkenthessem a felesleges költséget.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-06: REQ-035-06 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-07: REQ-035-07 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-035-08: REQ-035-08 bizonyítása

Given a felhasználó, aki korábbi nyugtákból és terhelésekből ismétlődő kiadásokat követ a szükséges előfeltételekkel
When a REQ-035-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-035-01: `GET /product/recurring-expenses`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-035-02: `POST /product/recurring-expenses/feedback`
- Request: validált kérési törzs a meglévő Pydantic és TypeScript szerződés szerint.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-035-03: `GET /subscriptions`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-035-04: `GET /subscriptions/{subscription_id}/cancel-guide`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

## 12. Adatmodell és perzisztencia

- `app/product_api.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- `app/subscriptions_api.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- Migráció: nincs; a specifikáció a jelenlegi viselkedést rögzíti.
- Sikertelen írás nem hagyhat részleges perzisztált állapotot.

## 13. Tesztterv és lefedettségi leképezés

- REQ-035-01 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-01.
- REQ-035-02 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-02.
- REQ-035-03 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-03.
- REQ-035-04 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-04.
- REQ-035-05 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-05.
- REQ-035-06 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-06.
- REQ-035-07 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-07.
- REQ-035-08 -> `tests/test_subscription_dashboard.py` (Integration/contract); scenario: AC-035-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
