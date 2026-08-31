---
id: FEAT-016
title: Háztartási együttműködés és családi postafiók
status: ready_for_dev
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-016
---

# FEAT-016: Háztartási együttműködés és családi postafiók

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A közösen kezelt nyugtákhoz egyértelmű tagságra, szerepkörökre és feladatmegosztásra van szükség.

Kanonikus források:
- `briefs/BRIEF-016-haztartasi-egyuttmukodes-es-csaladi-postafiok.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
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

- ACT-016-01: háztartási tulajdonosként.
- ACT-016-02: meghívottként.
- ACT-016-03: háztartási tagként.
- ACT-016-04: felhasználóként.

- PRE-016-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-016-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-016-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-016-01 [MUST]: Háztartási tulajdonosként szeretnék tagot meghívni, hogy közösen kezelhessük a háztartás nyugtáit.
- REQ-016-02 [MUST]: Meghívottként szeretném a meghívás részleteit megtekinteni és elfogadni, hogy a megfelelő háztartáshoz csatlakozzak.
- REQ-016-03 [MUST]: Háztartási tulajdonosként szeretném a tagok szerepkörét és hozzáférését kezelni, hogy mindenki csak a szükséges műveleteket végezhesse.
- REQ-016-04 [MUST]: Háztartási tagként szeretném egy közös postafiókban látni a rám vagy a háztartásra váró feladatokat, hogy ne maradjon el ellenőrzés vagy jóváhagyás.
- REQ-016-05 [MUST]: Háztartási tagként szeretném a feladatok olvasott és elintézett állapotát kezelni, hogy követhető legyen az együttműködés.
- REQ-016-06 [MUST]: Felhasználóként szeretném, hogy más háztartás adatai sem kereséssel, sem közvetlen hivatkozással ne legyenek elérhetők, hogy a pénzügyi adatok elkülönüljenek.
- REQ-016-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-016-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-016-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-016-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-016-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-016-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-016-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-016-01: `page`, Page; Közös családi bejövő postafiók; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-016-02: `page`, Page; Háztartási tagok kezelése és szerepkörök; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretnék tagot meghívni, hogy közösen kezelhessük a háztartás nyugtáit.
5. A szereplő végrehajtja a következő felhasználói célt: Meghívottként szeretném a meghívás részleteit megtekinteni és elfogadni, hogy a megfelelő háztartáshoz csatlakozzak.
6. A szereplő végrehajtja a következő felhasználói célt: Háztartási tulajdonosként szeretném a tagok szerepkörét és hozzáférését kezelni, hogy mindenki csak a szükséges műveleteket végezhesse.
7. A szereplő végrehajtja a következő felhasználói célt: Háztartási tagként szeretném egy közös postafiókban látni a rám vagy a háztartásra váró feladatokat, hogy ne maradjon el ellenőrzés vagy jóváhagyás.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `ITEM_DROPPED_TO_INBOX` -> `ASSIGNED_TO_CONTRIBUTOR` -> `MOVED_TO_REVIEW` -> `CONSOLIDATED_IN_HOUSEHOLD`.
- `- `ITEM_DROPPED_TO_INBOX`` + folytatás -> ``ASSIGNED_TO_CONTRIBUTOR``
- ``ASSIGNED_TO_CONTRIBUTOR`` + folytatás -> ``MOVED_TO_REVIEW``
- ``MOVED_TO_REVIEW`` + folytatás -> ``CONSOLIDATED_IN_HOUSEHOLD`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-016-01: REQ-016-01 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretnék tagot meghívni, hogy közösen kezelhessük a háztartás nyugtáit.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-02: REQ-016-02 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Meghívottként szeretném a meghívás részleteit megtekinteni és elfogadni, hogy a megfelelő háztartáshoz csatlakozzak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-03: REQ-016-03 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tulajdonosként szeretném a tagok szerepkörét és hozzáférését kezelni, hogy mindenki csak a szükséges műveleteket végezhesse.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-04: REQ-016-04 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tagként szeretném egy közös postafiókban látni a rám vagy a háztartásra váró feladatokat, hogy ne maradjon el ellenőrzés vagy jóváhagyás.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-05: REQ-016-05 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Háztartási tagként szeretném a feladatok olvasott és elintézett állapotát kezelni, hogy követhető legyen az együttműködés.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-06: REQ-016-06 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy más háztartás adatai sem kereséssel, sem közvetlen hivatkozással ne legyenek elérhetők, hogy a pénzügyi adatok elkülönüljenek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-07: REQ-016-07 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-08: REQ-016-08 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-016-09: REQ-016-09 bizonyítása

Given a háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó a szükséges előfeltételekkel
When a REQ-016-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-016-01: `GET /api/v2/inbox`
- Cél: Közös beérkező nyugták listája.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-016-02: `POST /api/v2/inbox/upload`
- Cél: Nyugta beküldése a közös postafiókba.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-016-03: `GET /api/v2/household/members`
- Cél: Háztartás tagjainak lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-016-04: `POST /api/v2/household/invite`
- Cél: Új családtagsági meghívó küldése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/inbox_service.py`: Családi postafiók beérkezési logika és hozzárendelés.
- `app/consumer_dashboard.py`: Tagok aktivitásának és beküldéseinek követése.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-016-01 -> `tests/test_inbox_service.py` (Unit/contract); scenario: AC-016-01.
- REQ-016-02 -> `tests/test_us_019_consumer_navigation.py` (Unit/contract); scenario: AC-016-02.
- REQ-016-03 -> `tests/test_inbox_service.py` (Unit/contract); scenario: AC-016-03.
- REQ-016-04 -> `tests/test_us_019_consumer_navigation.py` (Unit/contract); scenario: AC-016-04.
- REQ-016-05 -> `tests/test_inbox_service.py` (Unit/contract); scenario: AC-016-05.
- REQ-016-06 -> `tests/test_us_019_consumer_navigation.py` (Unit/contract); scenario: AC-016-06.
- REQ-016-07 -> `tests/test_inbox_service.py` (Unit/contract); scenario: AC-016-07.
- REQ-016-08 -> `tests/test_us_019_consumer_navigation.py` (Unit/contract); scenario: AC-016-08.
- REQ-016-09 -> `tests/test_inbox_service.py` (Unit/contract); scenario: AC-016-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
