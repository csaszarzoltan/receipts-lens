---
id: FEAT-020
title: Jóváhagyások és kontrollált változtatások
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-020
---

# FEAT-020: Jóváhagyások és kontrollált változtatások

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A pénzügyi hatású műveletekhez a végrehajtás előtt megfelelő szerepkörű jóváhagyás szükséges.

Kanonikus források:
- `briefs/BRIEF-020-jovahagyasok-es-kontrollalt-valtoztatasok.md`
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

- ACT-020-01: kérelmezőként.
- ACT-020-02: jóváhagyóként.

- PRE-020-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-020-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-020-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-020-01 [MUST]: Kérelmezőként szeretném jóváhagyásra elküldeni a pénzügyi műveletet, hogy az ne történjen meg jogosulatlanul.
- REQ-020-02 [MUST]: Jóváhagyóként szeretném egy helyen látni a várakozó kérelmeket és azok lényeges hatását, hogy felelős döntést hozzak.
- REQ-020-03 [MUST]: Jóváhagyóként szeretném elfogadni vagy indoklással elutasítani a kérelmet, hogy a döntés érthető és visszakereshető legyen.
- REQ-020-04 [MUST]: Kérelmezőként szeretném látni a kérelem aktuális állapotát és döntését, hogy tudjam, mi a következő lépés.
- REQ-020-05 [MUST]: Jóváhagyóként szeretném, hogy már eldöntött vagy közben módosult kérelmet ne lehessen elavult állapotból újra jóváhagyni, hogy elkerüljük a konfliktust.
- REQ-020-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-020-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-020-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-020-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-020-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-020-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-020-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-020-01: `page`, Page; Jóváhagyási várólista oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-020-02: `WorkflowState`, Component; Munkafolyamat és jóváhagyási lépés jelző; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-020-03: `Modal`, Dialog/Panel; Indoklással ellátott jóváhagyási párbeszédablak; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Kérelmezőként szeretném jóváhagyásra elküldeni a pénzügyi műveletet, hogy az ne történjen meg jogosulatlanul.
5. A szereplő végrehajtja a következő felhasználói célt: Jóváhagyóként szeretném egy helyen látni a várakozó kérelmeket és azok lényeges hatását, hogy felelős döntést hozzak.
6. A szereplő végrehajtja a következő felhasználói célt: Jóváhagyóként szeretném elfogadni vagy indoklással elutasítani a kérelmet, hogy a döntés érthető és visszakereshető legyen.
7. A szereplő végrehajtja a következő felhasználói célt: Kérelmezőként szeretném látni a kérelem aktuális állapotát és döntését, hogy tudjam, mi a következő lépés.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `SUBMITTED_FOR_APPROVAL` -> `PENDING_REVIEW` -> `APPROVED_WITH_AUDIT` vagy `REJECTED_WITH_REASON`.
- `- `SUBMITTED_FOR_APPROVAL`` + folytatás -> ``PENDING_REVIEW``
- ``PENDING_REVIEW`` + folytatás -> ``APPROVED_WITH_AUDIT` vagy `REJECTED_WITH_REASON`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-020-01: REQ-020-01 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Kérelmezőként szeretném jóváhagyásra elküldeni a pénzügyi műveletet, hogy az ne történjen meg jogosulatlanul.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-02: REQ-020-02 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jóváhagyóként szeretném egy helyen látni a várakozó kérelmeket és azok lényeges hatását, hogy felelős döntést hozzak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-03: REQ-020-03 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jóváhagyóként szeretném elfogadni vagy indoklással elutasítani a kérelmet, hogy a döntés érthető és visszakereshető legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-04: REQ-020-04 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Kérelmezőként szeretném látni a kérelem aktuális állapotát és döntését, hogy tudjam, mi a következő lépés.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-05: REQ-020-05 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Jóváhagyóként szeretném, hogy már eldöntött vagy közben módosult kérelmet ne lehessen elavult állapotból újra jóváhagyni, hogy elkerüljük a konfliktust.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-06: REQ-020-06 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-07: REQ-020-07 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-020-08: REQ-020-08 bizonyítása

Given a jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata a szükséges előfeltételekkel
When a REQ-020-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-020-01: `GET /api/v2/approvals/pending`
- Cél: Jóváhagyásra váró tételek listája.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-020-02: `POST /api/v2/approvals/{id}/approve`
- Cél: Tétel jóváhagyása indoklással.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-020-03: `POST /api/v2/approvals/{id}/reject`
- Cél: Tétel visszautasítása javításra.
- Request: útvonalparaméter `id`, a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/governance.py`: Nagy összegű költések kétlépcsős jóváhagyási szabályai.
- `app/product_service.py`: Jóváhagyási auditnapló és státuszváltoztatás.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-020-01 -> `tests/test_governance.py` (Unit/contract); scenario: AC-020-01.
- REQ-020-02 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-020-02.
- REQ-020-03 -> `tests/test_governance.py` (Unit/contract); scenario: AC-020-03.
- REQ-020-04 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-020-04.
- REQ-020-05 -> `tests/test_governance.py` (Unit/contract); scenario: AC-020-05.
- REQ-020-06 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-020-06.
- REQ-020-07 -> `tests/test_governance.py` (Unit/contract); scenario: AC-020-07.
- REQ-020-08 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-020-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
