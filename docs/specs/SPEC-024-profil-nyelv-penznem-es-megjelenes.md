---
id: FEAT-024
title: Profil, nyelv, pénznem és megjelenés
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-024
---

# FEAT-024: Profil, nyelv, pénznem és megjelenés

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A különböző háztartások eltérő nyelvi, pénznemi és megjelenítési igényekkel használják a szolgáltatást.

Kanonikus források:
- `briefs/BRIEF-024-profil-nyelv-penznem-es-megjelenes.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/multi-language-guide.md`
- `docs/plans/dark-mode-2026-08-12.md`
- `docs/decisions/ADR-001-pre-login-language-switcher.md`
- `docs/decisions/ADR-002-pre-login-dark-mode.md`
- `docs/decisions/ADR-003-full-translation.md`

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

- ACT-024-01: felhasználóként.
- ACT-024-02: látogatóként.

- PRE-024-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-024-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-024-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-024-01 [MUST]: Felhasználóként szeretném a megjelenített nevemet és alapbeállításaimat módosítani, hogy a munkaterület engem tükrözzön.
- REQ-024-02 [MUST]: Felhasználóként szeretnék a támogatott nyelvek között váltani, hogy a teljes felületet az általam értett nyelven használjam.
- REQ-024-03 [MUST]: Felhasználóként szeretném az alap pénznemet beállítani, hogy az összegek következetesen jelenjenek meg.
- REQ-024-04 [MUST]: Felhasználóként szeretnék világos, sötét vagy rendszerhez igazodó témát választani, hogy kényelmesen használjam a felületet.
- REQ-024-05 [MUST]: Látogatóként szeretném már bejelentkezés előtt nyelvet és témát váltani, hogy a belépési folyamat is megfelelő legyen.
- REQ-024-06 [MUST]: Felhasználóként szeretném, hogy választásaim újranyitáskor is megmaradjanak, hogy ne kelljen minden alkalommal újra beállítanom őket.
- REQ-024-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-024-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-024-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-024-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-024-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-024-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-024-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-024-01: `page`, Page; Profilbeállítások képernyő; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-024-02: `ProfileMenu`, Component; Felhasználói profilmenü; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-024-03: `LanguageSwitcher`, Component; Nyelvválasztó felület; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-024-04: `ThemeToggle`, Component; Sötét / világos mód kapcsoló; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a megjelenített nevemet és alapbeállításaimat módosítani, hogy a munkaterület engem tükrözzön.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék a támogatott nyelvek között váltani, hogy a teljes felületet az általam értett nyelven használjam.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném az alap pénznemet beállítani, hogy az összegek következetesen jelenjenek meg.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék világos, sötét vagy rendszerhez igazodó témát választani, hogy kényelmesen használjam a felületet.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `PREFERENCES_OPENED` -> `LOCALE_THEME_CHANGED` -> `UI_RERENDERED_IMMEDIATELY` -> `SETTINGS_SAVED`.
- `- `PREFERENCES_OPENED`` + folytatás -> ``LOCALE_THEME_CHANGED``
- ``LOCALE_THEME_CHANGED`` + folytatás -> ``UI_RERENDERED_IMMEDIATELY``
- ``UI_RERENDERED_IMMEDIATELY`` + folytatás -> ``SETTINGS_SAVED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-024-01: REQ-024-01 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a megjelenített nevemet és alapbeállításaimat módosítani, hogy a munkaterület engem tükrözzön.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-02: REQ-024-02 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék a támogatott nyelvek között váltani, hogy a teljes felületet az általam értett nyelven használjam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-03: REQ-024-03 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném az alap pénznemet beállítani, hogy az összegek következetesen jelenjenek meg.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-04: REQ-024-04 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék világos, sötét vagy rendszerhez igazodó témát választani, hogy kényelmesen használjam a felületet.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-05: REQ-024-05 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Látogatóként szeretném már bejelentkezés előtt nyelvet és témát váltani, hogy a belépési folyamat is megfelelő legyen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-06: REQ-024-06 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy választásaim újranyitáskor is megmaradjanak, hogy ne kelljen minden alkalommal újra beállítanom őket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-07: REQ-024-07 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-08: REQ-024-08 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-024-09: REQ-024-09 bizonyítása

Given a bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén a szükséges előfeltételekkel
When a REQ-024-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-024-01: `GET /api/v2/settings/profile`
- Cél: Profiladatok, nyelv és preferenciák lekérése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-024-02: `PUT /api/v2/settings/profile`
- Cél: Profil, alapértelmezett pénznem és felületi nyelv mentése.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/product_service.py`: Felhasználói profil preferenciák perzisztálása.
- `app/normalization.py`: Pénznem- és számformázási lokalizációs szabályok.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-024-01 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-024-01.
- REQ-024-02 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-024-02.
- REQ-024-03 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-024-03.
- REQ-024-04 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-024-04.
- REQ-024-05 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-024-05.
- REQ-024-06 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-024-06.
- REQ-024-07 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-024-07.
- REQ-024-08 -> `tests/test_export_profiles.py` (Unit/contract); scenario: AC-024-08.
- REQ-024-09 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-024-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
