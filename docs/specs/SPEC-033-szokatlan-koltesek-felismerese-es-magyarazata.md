---
id: FEAT-033
title: Szokatlan költések felismerése és magyarázata
status: ready_for_dev
version: 1
risk: low
owner: system-architect
related_brief: BRIEF-033
---

# FEAT-033: Szokatlan költések felismerése és magyarázata

## 1. Cél és felhasználói eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználó nehezen veszi észre azokat a vásárlásokat, amelyek jelentősen eltérnek a megszokott mintától.

Kanonikus források:
- `briefs/BRIEF-033-szokatlan-koltesek-felismerese-es-magyarazata.md`
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

- ACT-033-01: felhasználóként.

- PRE-033-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-033-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-033-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-033-01 [MUST]: Felhasználóként szeretném látni a szokatlannak jelölt költéseket, hogy gyorsan ellenőrizhessem a váratlan eltéréseket.
- REQ-033-02 [MUST]: Felhasználóként szeretném érteni, milyen korábbi mintához képest számít egy költés szokatlannak, hogy ne kezeljem indokolatlan riasztásként.
- REQ-033-03 [MUST]: Felhasználóként szeretném a jelzésből megnyitni az érintett nyugtát, hogy ellenőrizhessem vagy javíthassam az alapadatot.
- REQ-033-04 [MUST]: Felhasználóként szeretném tudni, ha kevés adat miatt nem állapítható meg megbízható eltérés, hogy ne kapjak hamis bizonyosságot.
- REQ-033-05 [MUST]: Felhasználóként szeretném a téves jelzést visszajelzéssel ellátni, hogy a későbbi értelmezés pontosabb lehessen.
- REQ-033-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-033-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-033-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-033-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-033-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-033-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-033-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-033-01: `service-feedback`, állapotjelző felület; a külső művelet eredményét közli; folyamatban loading, hibánál újrapróbálható állapotot mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném látni a szokatlannak jelölt költéseket, hogy gyorsan ellenőrizhessem a váratlan eltéréseket.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném érteni, milyen korábbi mintához képest számít egy költés szokatlannak, hogy ne kezeljem indokolatlan riasztásként.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a jelzésből megnyitni az érintett nyugtát, hogy ellenőrizhessem vagy javíthassam az alapadatot.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném tudni, ha kevés adat miatt nem állapítható meg megbízható eltérés, hogy ne kapjak hamis bizonyosságot.
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

### AC-033-01: REQ-033-01 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném látni a szokatlannak jelölt költéseket, hogy gyorsan ellenőrizhessem a váratlan eltéréseket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-02: REQ-033-02 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném érteni, milyen korábbi mintához képest számít egy költés szokatlannak, hogy ne kezeljem indokolatlan riasztásként.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-03: REQ-033-03 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a jelzésből megnyitni az érintett nyugtát, hogy ellenőrizhessem vagy javíthassam az alapadatot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-04: REQ-033-04 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném tudni, ha kevés adat miatt nem állapítható meg megbízható eltérés, hogy ne kapjak hamis bizonyosságot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-05: REQ-033-05 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a téves jelzést visszajelzéssel ellátni, hogy a későbbi értelmezés pontosabb lehessen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-06: REQ-033-06 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-07: REQ-033-07 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-033-08: REQ-033-08 bizonyítása

Given a háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál a szükséges előfeltételekkel
When a REQ-033-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-033-01: `GET /forecasts/anomalies`
- Request: a handler szerinti útvonal- és lekérdezési paraméterek.
- Response: a meglévő szervermodell és kliensinterfész szerinti típusos eredmény.
- Hibák: a handler által ténylegesen alkalmazott 400, 401, 403, 404, 409, 422, 429 vagy 5xx részhalmaz; hiba nem jelenthet sikert.

## 12. Adatmodell és perzisztencia

- `app/forecast.py`: a feature meglévő domain-, validációs és perzisztencia-szerződésének forrása.
- Migráció: nincs; a specifikáció a jelenlegi viselkedést rögzíti.
- Sikertelen írás nem hagyhat részleges perzisztált állapotot.

## 13. Tesztterv és lefedettségi leképezés

- REQ-033-01 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-01.
- REQ-033-02 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-02.
- REQ-033-03 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-03.
- REQ-033-04 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-04.
- REQ-033-05 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-05.
- REQ-033-06 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-06.
- REQ-033-07 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-07.
- REQ-033-08 -> `tests/test_forecast.py` (Integration/contract); scenario: AC-033-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
