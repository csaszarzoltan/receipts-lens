---
id: FEAT-026
title: Értesítések és állapotüzenetek
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-026
---

# FEAT-026: Értesítések és állapotüzenetek

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A háttérben befejeződő vagy beavatkozást igénylő műveletek könnyen észrevétlenek maradnak.

Kanonikus források:
- `briefs/BRIEF-026-ertesitesek-es-allapotuzenetek.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/alerts.md`

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

- ACT-026-01: felhasználóként.

- PRE-026-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-026-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-026-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-026-01 [MUST]: Felhasználóként szeretném egy értesítési panelen látni az új eseményeket, hogy ne maradjak le a fontos változásokról.
- REQ-026-02 [MUST]: Felhasználóként szeretném külön felismerni az olvasatlan és intézkedést igénylő értesítéseket, hogy megfelelő sorrendben reagáljak.
- REQ-026-03 [MUST]: Felhasználóként szeretnék az értesítésből a kapcsolódó feladathoz jutni, hogy gyorsan intézkedhessek.
- REQ-026-04 [MUST]: Felhasználóként szeretném az értesítést elolvasottnak jelölni vagy elvetni, hogy a lista kezelhető maradjon.
- REQ-026-05 [MUST]: Felhasználóként szeretném beállítani az előfizetéssel kapcsolatos e-mailes figyelmeztetéseket, hogy a kívánt csatornán kapjak jelzést.
- REQ-026-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-026-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-026-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-026-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-026-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-026-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-026-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-026-01: `NotificationPanel`, Dialog/Panel; Gördülő értesítési központ; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-026-02: `Toast`, Component; Globális toast értesítő komponens; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném egy értesítési panelen látni az új eseményeket, hogy ne maradjak le a fontos változásokról.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném külön felismerni az olvasatlan és intézkedést igénylő értesítéseket, hogy megfelelő sorrendben reagáljak.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék az értesítésből a kapcsolódó feladathoz jutni, hogy gyorsan intézkedhessek.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném az értesítést elolvasottnak jelölni vagy elvetni, hogy a lista kezelhető maradjon.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `EVENT_TRIGGERED` -> `TOAST_DISPLAYED` -> `NOTIFICATION_BADGE_INCREMENTED` -> `PANEL_OPENED` -> `MARKED_AS_READ`.
- `- `EVENT_TRIGGERED`` + folytatás -> ``TOAST_DISPLAYED``
- ``TOAST_DISPLAYED`` + folytatás -> ``NOTIFICATION_BADGE_INCREMENTED``
- ``NOTIFICATION_BADGE_INCREMENTED`` + folytatás -> ``PANEL_OPENED``
- ``PANEL_OPENED`` + folytatás -> ``MARKED_AS_READ`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-026-01: REQ-026-01 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném egy értesítési panelen látni az új eseményeket, hogy ne maradjak le a fontos változásokról.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-02: REQ-026-02 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném külön felismerni az olvasatlan és intézkedést igénylő értesítéseket, hogy megfelelő sorrendben reagáljak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-03: REQ-026-03 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék az értesítésből a kapcsolódó feladathoz jutni, hogy gyorsan intézkedhessek.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-04: REQ-026-04 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném az értesítést elolvasottnak jelölni vagy elvetni, hogy a lista kezelhető maradjon.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-05: REQ-026-05 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném beállítani az előfizetéssel kapcsolatos e-mailes figyelmeztetéseket, hogy a kívánt csatornán kapjak jelzést.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-06: REQ-026-06 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-07: REQ-026-07 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-026-08: REQ-026-08 bizonyítása

Given a aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül a szükséges előfeltételekkel
When a REQ-026-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-026-01: `GET /api/v2/notifications`
- Cél: Olvasatlan és korábbi értesítések lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-026-02: `PUT /api/v2/notifications/{id}/read`
- Cél: Értesítés olvasottnak jelölése.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-026-03: `POST /api/v2/notifications/mark-all-read`
- Cél: Összes értesítés együttes olvasottá tétele.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/alerts.py`: Alkalmazáson belüli események és riasztások kézbesítése.
- `app/subscription_alerts.py`: Rendszerszintű és előfizetési figyelmeztetések.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-026-01 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-026-01.
- REQ-026-02 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-026-02.
- REQ-026-03 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-026-03.
- REQ-026-04 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-026-04.
- REQ-026-05 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-026-05.
- REQ-026-06 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-026-06.
- REQ-026-07 -> `tests/test_alerts.py` (Unit/contract); scenario: AC-026-07.
- REQ-026-08 -> `tests/test_subscription_alerts.py` (Unit/contract); scenario: AC-026-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
