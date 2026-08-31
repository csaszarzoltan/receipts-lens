---
id: FEAT-030
title: Jelszó nélküli belépés e-mailes hivatkozással
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-030
---

# FEAT-030: Jelszó nélküli belépés e-mailes hivatkozással

## 1. Cél és felhasználói eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználó jelszó megadása nélkül is biztonságosan szeretne hozzáférni a saját háztartási munkaterületéhez.

Kanonikus források:
- `briefs/BRIEF-030-jelszo-nelkuli-belepes-e-mailes-hivatkozassal.md`
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

- ACT-030-01: felhasználóként.

- PRE-030-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-030-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-030-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-030-01 [MUST]: Felhasználóként szeretnék e-mailes belépési hivatkozást kérni, hogy elfelejtett jelszó nélkül is hozzáférhessek a fiókomhoz.
- REQ-030-02 [MUST]: Felhasználóként szeretném ugyanazt a semleges visszajelzést kapni attól függetlenül, hogy az e-mail-cím ismert-e, hogy a rendszer ne árulja el mások fiókjának létezését.
- REQ-030-03 [MUST]: Felhasználóként szeretném az érvényes belépési hivatkozással megnyitni a saját munkaterületemet, hogy folytathassam a feladataimat.
- REQ-030-04 [MUST]: Felhasználóként szeretnék lejárt, hibás vagy már felhasznált hivatkozásnál egyértelmű tájékoztatást és új igénylési lehetőséget kapni, hogy biztonságosan újrapróbálhassam.
- REQ-030-05 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-030-06 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-030-07 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-030-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-030-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-030-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-030-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-030-01: `service-feedback`, állapotjelző felület; a külső művelet eredményét közli; folyamatban loading, hibánál újrapróbálható állapotot mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék e-mailes belépési hivatkozást kérni, hogy elfelejtett jelszó nélkül is hozzáférhessek a fiókomhoz.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném ugyanazt a semleges visszajelzést kapni attól függetlenül, hogy az e-mail-cím ismert-e, hogy a rendszer ne árulja el mások fiókjának létezését.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném az érvényes belépési hivatkozással megnyitni a saját munkaterületemet, hogy folytathassam a feladataimat.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék lejárt, hibás vagy már felhasznált hivatkozásnál egyértelmű tájékoztatást és új igénylési lehetőséget kapni, hogy biztonságosan újrapróbálhassam.
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

### AC-030-01: REQ-030-01 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék e-mailes belépési hivatkozást kérni, hogy elfelejtett jelszó nélkül is hozzáférhessek a fiókomhoz.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-02: REQ-030-02 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném ugyanazt a semleges visszajelzést kapni attól függetlenül, hogy az e-mail-cím ismert-e, hogy a rendszer ne árulja el mások fiókjának létezését.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-03: REQ-030-03 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném az érvényes belépési hivatkozással megnyitni a saját munkaterületemet, hogy folytathassam a feladataimat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-04: REQ-030-04 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék lejárt, hibás vagy már felhasznált hivatkozásnál egyértelmű tájékoztatást és új igénylési lehetőséget kapni, hogy biztonságosan újrapróbálhassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-05: REQ-030-05 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-06: REQ-030-06 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-030-07: REQ-030-07 bizonyítása

Given a visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ a szükséges előfeltételekkel
When a REQ-030-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-030-01: `POST /auth/magic-link-request`
- Request: validált kérési törzs a meglévő Pydantic és TypeScript szerződés szerint.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

### API-030-02: `POST /auth/magic-link-verify`
- Request: validált kérési törzs a meglévő Pydantic és TypeScript szerződés szerint.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

## 12. Adatmodell és perzisztencia

- `app/auth_api.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- Migráció: nincs; a specifikáció a jelenlegi viselkedést rögzíti.
- Sikertelen írás nem hagyhat részleges perzisztált állapotot.

## 13. Tesztterv és lefedettségi leképezés

- REQ-030-01 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-01.
- REQ-030-02 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-02.
- REQ-030-03 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-03.
- REQ-030-04 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-04.
- REQ-030-05 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-05.
- REQ-030-06 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-06.
- REQ-030-07 -> `tests/test_us_024_auth_contract.py` (Integration/contract); scenario: AC-030-07.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
