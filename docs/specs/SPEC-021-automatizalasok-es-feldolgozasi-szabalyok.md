---
id: FEAT-021
title: Automatizálások és feldolgozási szabályok
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-021
---

# FEAT-021: Automatizálások és feldolgozási szabályok

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Az ismétlődő feldolgozási lépések kézi végrehajtása időigényes, de az automatizmusoknak átláthatónak és szabályozhatónak kell maradniuk.

Kanonikus források:
- `briefs/BRIEF-021-automatizalasok-es-feldolgozasi-szabalyok.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/product-workflows.md`

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

- ACT-021-01: jogosult felhasználóként.

- PRE-021-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-021-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-021-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-021-01 [MUST]: Jogosult felhasználóként szeretnék automatizálási szabályt létrehozni, hogy az ismétlődő feladatok kevesebb kézi munkát igényeljenek.
- REQ-021-02 [MUST]: Jogosult felhasználóként szeretném a szabály feltételeit és várható hatását ellenőrizni, hogy ne induljon túl tág automatizmus.
- REQ-021-03 [MUST]: Jogosult felhasználóként szeretném a szabályt szüneteltetni, módosítani vagy törölni, hogy mindig nálam maradjon a kontroll.
- REQ-021-04 [MUST]: Jogosult felhasználóként szeretném látni a futások eredményét és hibáját, hogy az automatizmus működése auditálható legyen.
- REQ-021-05 [MUST]: Jogosult felhasználóként szeretném a sikertelen futást biztonságosan újrapróbálni, hogy ne keletkezzen duplikált eredmény.
- REQ-021-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-021-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-021-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-021-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-021-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-021-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-021-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-021-01: `page`, Page; Szabálykezelő központ; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-021-02: `page`, Page; Feltétel- és akciószerkesztő oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-021-03: `page`, Page; Szabálylefutási előzmények; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretnék automatizálási szabályt létrehozni, hogy az ismétlődő feladatok kevesebb kézi munkát igényeljenek.
5. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném a szabály feltételeit és várható hatását ellenőrizni, hogy ne induljon túl tág automatizmus.
6. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném a szabályt szüneteltetni, módosítani vagy törölni, hogy mindig nálam maradjon a kontroll.
7. A szereplő végrehajtja a következő felhasználói célt: Jogosult felhasználóként szeretném látni a futások eredményét és hibáját, hogy az automatizmus működése auditálható legyen.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `RULE_DEFINED` -> `RECEIPT_ARRIVED` -> `CONDITION_EVALUATED` -> `ACTION_EXECUTED` -> `RUN_AUDIT_LOGGED`.
- `- `RULE_DEFINED`` + folytatás -> ``RECEIPT_ARRIVED``
- ``RECEIPT_ARRIVED`` + folytatás -> ``CONDITION_EVALUATED``
- ``CONDITION_EVALUATED`` + folytatás -> ``ACTION_EXECUTED``
- ``ACTION_EXECUTED`` + folytatás -> ``RUN_AUDIT_LOGGED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-021-01: REQ-021-01 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretnék automatizálási szabályt létrehozni, hogy az ismétlődő feladatok kevesebb kézi munkát igényeljenek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-02: REQ-021-02 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném a szabály feltételeit és várható hatását ellenőrizni, hogy ne induljon túl tág automatizmus.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-03: REQ-021-03 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném a szabályt szüneteltetni, módosítani vagy törölni, hogy mindig nálam maradjon a kontroll.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-04: REQ-021-04 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném látni a futások eredményét és hibáját, hogy az automatizmus működése auditálható legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-05: REQ-021-05 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jogosult felhasználóként szeretném a sikertelen futást biztonságosan újrapróbálni, hogy ne keletkezzen duplikált eredmény.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-06: REQ-021-06 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-07: REQ-021-07 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-021-08: REQ-021-08 bizonyítása

Given a jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be a szükséges előfeltételekkel
When a REQ-021-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-021-01: `GET /api/v2/automations`
- Cél: Konfigurált szabályok listája.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-021-02: `POST /api/v2/automations`
- Cél: Új if-then feldolgozási szabály mentése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-021-03: `PUT /api/v2/automations/{id}`
- Cél: Szabályfeltételek és akciók frissítése.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-021-04: `GET /api/v2/automations/{id}/runs`
- Cél: Végrehajtási napló lekérdezése.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/automation_service.py`: Feltételkiértékelő motor: kereskedő egyezés, értékhatár, automatikus címkézés és áthelyezés.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-021-01 -> `tests/test_automation_service.py` (Unit/contract); scenario: AC-021-01.
- REQ-021-02 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-021-02.
- REQ-021-03 -> `tests/test_automation_service.py` (Unit/contract); scenario: AC-021-03.
- REQ-021-04 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-021-04.
- REQ-021-05 -> `tests/test_automation_service.py` (Unit/contract); scenario: AC-021-05.
- REQ-021-06 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-021-06.
- REQ-021-07 -> `tests/test_automation_service.py` (Unit/contract); scenario: AC-021-07.
- REQ-021-08 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-021-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
