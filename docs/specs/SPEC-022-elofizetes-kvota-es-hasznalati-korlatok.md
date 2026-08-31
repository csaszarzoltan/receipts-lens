---
id: FEAT-022
title: Előfizetés, kvóta és használati korlátok
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-022
---

# FEAT-022: Előfizetés, kvóta és használati korlátok

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felhasználónak előre értenie kell, milyen csomagot használ, mennyi feldolgozási lehetősége maradt, és mi történik a korlát elérésekor.

Kanonikus források:
- `briefs/BRIEF-022-elofizetes-kvota-es-hasznalati-korlatok.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/subscription-alerts.md`
- `docs/research/2026-08-27-receipt-lens-revenue-features.md`

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

- ACT-022-01: háztartási tulajdonosként.
- ACT-022-02: felhasználóként.

- PRE-022-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-022-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-022-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-022-01 [MUST]: Háztartási tulajdonosként szeretném látni az aktuális csomagot, annak korlátait és a felhasználást, hogy tervezni tudjam a további feldolgozást.
- REQ-022-02 [MUST]: Felhasználóként szeretnék időben figyelmeztetést kapni a kvóta közeledtéről, hogy ne érjen váratlan leállás.
- REQ-022-03 [MUST]: Háztartási tulajdonosként szeretném elindítani a csomagváltást, hogy nagyobb feldolgozási keretet kapjak.
- REQ-022-04 [MUST]: Háztartási tulajdonosként szeretném kezelni az előfizetési és számlázási beállításokat, hogy kontrolláljam a költségeket.
- REQ-022-05 [MUST]: Felhasználóként szeretném korlát elérésekor pontosan érteni, mely művelet nem végezhető el és mikor áll helyre, hogy megfelelően döntsek.
- REQ-022-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-022-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-022-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-022-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-022-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-022-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-022-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-022-01: `page`, Page; Csomagkezelő és előfizetési oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-022-02: `QuotaBar`, Component; Felhasznált havi szkennelési kvóta sáv; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném látni az aktuális csomagot, annak korlátait és a felhasználást, hogy tervezni tudjam a további feldolgozást.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék időben figyelmeztetést kapni a kvóta közeledtéről, hogy ne érjen váratlan leállás.
6. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném elindítani a csomagváltást, hogy nagyobb feldolgozási keretet kapjak.
7. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném kezelni az előfizetési és számlázási beállításokat, hogy kontrolláljam a költségeket.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `ACTIVE_PLAN` -> `QUOTA_CONSUMED` -> `WARNING_THRESHOLD_REACHED` -> `LIMIT_REACHED_GRACEFUL_BLOCK` -> `PLAN_UPGRADED`.
- `- `ACTIVE_PLAN`` + folytatás -> ``QUOTA_CONSUMED``
- ``QUOTA_CONSUMED`` + folytatás -> ``WARNING_THRESHOLD_REACHED``
- ``WARNING_THRESHOLD_REACHED`` + folytatás -> ``LIMIT_REACHED_GRACEFUL_BLOCK``
- ``LIMIT_REACHED_GRACEFUL_BLOCK`` + folytatás -> ``PLAN_UPGRADED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-022-01: REQ-022-01 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném látni az aktuális csomagot, annak korlátait és a felhasználást, hogy tervezni tudjam a további feldolgozást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-02: REQ-022-02 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék időben figyelmeztetést kapni a kvóta közeledtéről, hogy ne érjen váratlan leállás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-03: REQ-022-03 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném elindítani a csomagváltást, hogy nagyobb feldolgozási keretet kapjak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-04: REQ-022-04 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném kezelni az előfizetési és számlázási beállításokat, hogy kontrolláljam a költségeket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-05: REQ-022-05 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném korlát elérésekor pontosan érteni, mely művelet nem végezhető el és mikor áll helyre, hogy megfelelően döntsek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-06: REQ-022-06 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-07: REQ-022-07 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-022-08: REQ-022-08 bizonyítása

Given a ingyenes vagy fizetős csomagot használó háztartás tulajdonosa a szükséges előfeltételekkel
When a REQ-022-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-022-01: `GET /api/v2/subscriptions/me`
- Cél: Aktuális előfizetési csomag és érvényesség.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-022-02: `GET /api/v2/quota/usage`
- Cél: Havi OCR szkennelési kvótahasználat.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-022-03: `POST /api/v2/subscriptions/upgrade`
- Cél: Csomagváltás kezdeményezése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/quota.py`: Díjcsomag-limitek érvényesítése, túllépési korlátok.
- `app/subscription_alerts.py`: Kvóta fogyási és lejárati figyelmeztetések.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-022-01 -> `tests/test_quota.py` (Unit/contract); scenario: AC-022-01.
- REQ-022-02 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-022-02.
- REQ-022-03 -> `tests/test_configurable_limits.py` (Unit/contract); scenario: AC-022-03.
- REQ-022-04 -> `tests/test_quota.py` (Unit/contract); scenario: AC-022-04.
- REQ-022-05 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-022-05.
- REQ-022-06 -> `tests/test_configurable_limits.py` (Unit/contract); scenario: AC-022-06.
- REQ-022-07 -> `tests/test_quota.py` (Unit/contract); scenario: AC-022-07.
- REQ-022-08 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-022-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
