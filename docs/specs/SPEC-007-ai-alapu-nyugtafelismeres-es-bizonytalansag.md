---
id: FEAT-007
title: AI-alapú nyugtafelismerés és bizonytalanság
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-007
---

# FEAT-007: AI-alapú nyugtafelismerés és bizonytalanság

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A felismert nyugtaadatok nem mindig pontosak, ezért a felhasználónak látnia kell, miben bízhat és mit kell ellenőriznie.

Kanonikus források:
- `briefs/BRIEF-007-ai-alapu-nyugtafelismeres-es-bizonytalansag.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/ai-vision-ocr.md`
- `docs/ocr.md`
- `docs/decisions/ADR-005-vision-pro-ocr.md`
- `specs/async_confidence_v0.2.md`

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

- ACT-007-01: felhasználóként.
- ACT-007-02: többnyelvű nyugta feldolgozásakor.

- PRE-007-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-007-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-007-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-007-01 [MUST]: Felhasználóként szeretném, hogy a rendszer azonosítsa a kereskedőt, dátumot, pénznemet, végösszeget és tételeket, hogy ne kelljen mindent kézzel begépelnem.
- REQ-007-02 [MUST]: Felhasználóként szeretném mezőnként látni a felismerés bizonyosságát, hogy a kockázatos adatokat célzottan ellenőrizhessem.
- REQ-007-03 [MUST]: Felhasználóként szeretném a nyugta eredeti képét a felismert adatok mellett megtekinteni, hogy össze tudjam hasonlítani őket.
- REQ-007-04 [MUST]: Többnyelvű nyugta feldolgozásakor szeretném, hogy az eredeti tartalom értelmezhetően kerüljön rögzítésre, hogy külföldi vásárlásaimat is kezelhessem.
- REQ-007-05 [MUST]: Felhasználóként szeretném, hogy bizonytalan eredmény ne váljon észrevétlenül végleges adattá, hogy elkerüljem a hibás kimutatásokat.
- REQ-007-06 [MUST]: Felhasználóként szeretnék érthető állapotot kapni, ha a felismerő szolgáltatás nem érhető el, hogy később újrapróbálhassam vagy kézzel folytathassam.
- REQ-007-07 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-007-08 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-007-09 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-007-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-007-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-007-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-007-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-007-01: `AiResultPanel`, Dialog/Panel; Felismerési mezők és megbízhatósági pontszámok panelje; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-007-02: `ConfidenceBadge`, Component; Magas, közepes, bizonytalan színjelvény; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-007-03: `AiScanToggle`, Component; Vision Pro vs Standard Tesseract választó; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy a rendszer azonosítsa a kereskedőt, dátumot, pénznemet, végösszeget és tételeket, hogy ne kelljen mindent kézzel begépelnem.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném mezőnként látni a felismerés bizonyosságát, hogy a kockázatos adatokat célzottan ellenőrizhessem.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném a nyugta eredeti képét a felismert adatok mellett megtekinteni, hogy össze tudjam hasonlítani őket.
7. A szereplő végrehajtja a következő felhasználói célt: Többnyelvű nyugta feldolgozásakor szeretném, hogy az eredeti tartalom értelmezhetően kerüljön rögzítésre, hogy külföldi vásárlásaimat is kezelhessem.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `RAW_IMAGE` -> `TEXT_EXTRACTION` -> `KEY_VALUE_PARSING` -> `FIELD_CONFIDENCE_SCORED` -> `UNCERTAINTY_FLAGGED` -> `NORMALIZED`.
- `- `RAW_IMAGE`` + folytatás -> ``TEXT_EXTRACTION``
- ``TEXT_EXTRACTION`` + folytatás -> ``KEY_VALUE_PARSING``
- ``KEY_VALUE_PARSING`` + folytatás -> ``FIELD_CONFIDENCE_SCORED``
- ``FIELD_CONFIDENCE_SCORED`` + folytatás -> ``UNCERTAINTY_FLAGGED``
- ``UNCERTAINTY_FLAGGED`` + folytatás -> ``NORMALIZED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-007-01: REQ-007-01 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy a rendszer azonosítsa a kereskedőt, dátumot, pénznemet, végösszeget és tételeket, hogy ne kelljen mindent kézzel begépelnem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-02: REQ-007-02 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném mezőnként látni a felismerés bizonyosságát, hogy a kockázatos adatokat célzottan ellenőrizhessem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-03: REQ-007-03 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném a nyugta eredeti képét a felismert adatok mellett megtekinteni, hogy össze tudjam hasonlítani őket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-04: REQ-007-04 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Többnyelvű nyugta feldolgozásakor szeretném, hogy az eredeti tartalom értelmezhetően kerüljön rögzítésre, hogy külföldi vásárlásaimat is kezelhessem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-05: REQ-007-05 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy bizonytalan eredmény ne váljon észrevétlenül végleges adattá, hogy elkerüljem a hibás kimutatásokat.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-06: REQ-007-06 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék érthető állapotot kapni, ha a felismerő szolgáltatás nem érhető el, hogy később újrapróbálhassam vagy kézzel folytathassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-07: REQ-007-07 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-08: REQ-007-08 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-007-09: REQ-007-09 bizonyítása

Given a nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén a szükséges előfeltételekkel
When a REQ-007-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-007-01: `POST /api/v1/receipts/parse`
- Cél: OCR szövegkivonatolás és mezőfelismerés.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-007-02: `POST /api/v1/receipts/vision-parse`
- Cél: Multimodális AI Vision struktúrált kinyerés.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-007-03: `GET /api/v1/receipts/{id}/ocr-result`
- Cél: Mezőszintű konfidencia pontszámok.
- Request: útvonalparaméter `id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/ocr.py`: Tesseract motor, mintaillesztés és bizonytalanság számítás.
- `app/vision_ocr.py`: Vision Pro integráció struktúrált kinyeréssel és fallback mechanizmussal.
- `app/normalization.py`: Dátum, összeg, pénznem és kereskedő normalizálás.
- `app/taxonomy.py`: Kereskedő és tételszintű entitásfelismerés.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-007-01 -> `tests/test_vision_ocr.py` (Unit/contract); scenario: AC-007-01.
- REQ-007-02 -> `tests/test_api_vision.py` (Integration); scenario: AC-007-02.
- REQ-007-03 -> `tests/test_async_confidence.py` (Unit/contract); scenario: AC-007-03.
- REQ-007-04 -> `tests/test_bug001_confidence.py` (Unit/contract); scenario: AC-007-04.
- REQ-007-05 -> `tests/test_us_022_ocr_confidence_contract.py` (Unit/contract); scenario: AC-007-05.
- REQ-007-06 -> `tests/test_multilang_ocr.py` (Unit/contract); scenario: AC-007-06.
- REQ-007-07 -> `tests/test_vision_ocr.py` (Unit/contract); scenario: AC-007-07.
- REQ-007-08 -> `tests/test_api_vision.py` (Integration); scenario: AC-007-08.
- REQ-007-09 -> `tests/test_async_confidence.py` (Unit/contract); scenario: AC-007-09.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
