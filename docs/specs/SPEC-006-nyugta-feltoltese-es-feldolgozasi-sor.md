---
id: FEAT-006
title: Nyugta feltöltése és feldolgozási sor
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-006
---

# FEAT-006: Nyugta feltöltése és feldolgozási sor

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

A papír- és digitális nyugták rögzítése lassú, a több fájlból álló feldolgozás állapota pedig könnyen követhetetlenné válik.

Kanonikus források:
- `briefs/BRIEF-006-nyugta-feltoltese-es-feldolgozasi-sor.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `docs/ocr-pipeline.md`
- `specs/batch_processing_v0.3.md`

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

- ACT-006-01: felhasználóként.
- ACT-006-02: mobilos felhasználóként.

- PRE-006-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-006-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-006-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-006-01 [MUST]: Felhasználóként szeretnék egy vagy több támogatott nyugtaképet kijelölni vagy behúzni, hogy gyorsan elindíthassam a rögzítést.
- REQ-006-02 [MUST]: Mobilos felhasználóként szeretném a kamerával közvetlenül lefényképezni a nyugtát, hogy ne kelljen előbb külön fájlt készítenem.
- REQ-006-03 [MUST]: Felhasználóként szeretném feltöltés előtt látni a kiválasztott fájlokat és eltávolítani a tévesen kiválasztott elemeket, hogy csak a szükséges nyugták kerüljenek sorba.
- REQ-006-04 [MUST]: Felhasználóként szeretném fájlonként látni a feltöltés és feldolgozás állapotát, hogy tudjam, mi készült el és mi várakozik.
- REQ-006-05 [MUST]: Felhasználóként szeretnék egy sikertelen elemnél újrapróbálási lehetőséget kapni anélkül, hogy a sikeres elemeket újra fel kellene töltenem.
- REQ-006-06 [MUST]: Felhasználóként szeretnék egyértelmű visszajelzést kapni nem támogatott vagy túl nagy fájlról, hogy megfelelő bemenettel folytathassam.
- REQ-006-07 [MUST]: Felhasználóként szeretném megszakítás után is megtalálni a még feldolgozás alatt álló feladatokat, hogy később ellenőrizhessem az eredményüket.
- REQ-006-08 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-006-09 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-006-10 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-006-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-006-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-006-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-006-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-006-01: `page`, Page; Nyugtafeltöltési oldal; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-006-02: `DropZone`, Component; Drag-and-drop és kamera feltöltési zóna; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-006-03: `UploadQueue`, Component; Feltöltési tétellista és folyamatjelzők; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-006-04: `AiScanToggle`, Component; AI Vision OCR mód kapcsoló; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretnék egy vagy több támogatott nyugtaképet kijelölni vagy behúzni, hogy gyorsan elindíthassam a rögzítést.
5. A szereplő végrehajtja a következő felhasználói célt: Mobilos felhasználóként szeretném a kamerával közvetlenül lefényképezni a nyugtát, hogy ne kelljen előbb külön fájlt készítenem.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném feltöltés előtt látni a kiválasztott fájlokat és eltávolítani a tévesen kiválasztott elemeket, hogy csak a szükséges nyugták kerüljenek sorba.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném fájlonként látni a feltöltés és feldolgozás állapotát, hogy tudjam, mi készült el és mi várakozik.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `FILES_SELECTED` -> `VALIDATING_MAGIC_BYTES` -> `UPLOADING` -> `QUEUED_IN_BATCH` -> `OCR_PROCESSING` -> `COMPLETED` / `FAILED_ITEM_RETRYABLE`.
- `- `FILES_SELECTED`` + folytatás -> ``VALIDATING_MAGIC_BYTES``
- ``VALIDATING_MAGIC_BYTES`` + folytatás -> ``UPLOADING``
- ``UPLOADING`` + folytatás -> ``QUEUED_IN_BATCH``
- ``QUEUED_IN_BATCH`` + folytatás -> ``OCR_PROCESSING``
- ``OCR_PROCESSING`` + folytatás -> ``COMPLETED` / `FAILED_ITEM_RETRYABLE`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-006-01: REQ-006-01 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék egy vagy több támogatott nyugtaképet kijelölni vagy behúzni, hogy gyorsan elindíthassam a rögzítést.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-02: REQ-006-02 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Mobilos felhasználóként szeretném a kamerával közvetlenül lefényképezni a nyugtát, hogy ne kelljen előbb külön fájlt készítenem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-03: REQ-006-03 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném feltöltés előtt látni a kiválasztott fájlokat és eltávolítani a tévesen kiválasztott elemeket, hogy csak a szükséges nyugták kerüljenek sorba.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-04: REQ-006-04 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném fájlonként látni a feltöltés és feldolgozás állapotát, hogy tudjam, mi készült el és mi várakozik.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-05: REQ-006-05 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék egy sikertelen elemnél újrapróbálási lehetőséget kapni anélkül, hogy a sikeres elemeket újra fel kellene töltenem.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-06: REQ-006-06 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretnék egyértelmű visszajelzést kapni nem támogatott vagy túl nagy fájlról, hogy megfelelő bemenettel folytathassam.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-07: REQ-006-07 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném megszakítás után is megtalálni a még feldolgozás alatt álló feladatokat, hogy később ellenőrizhessem az eredményüket.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-08: REQ-006-08 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-09: REQ-006-09 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-09 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-006-10: REQ-006-10 bizonyítása

Given a felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá a szükséges előfeltételekkel
When a REQ-006-10 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-006-01: `POST /api/v1/receipts/upload`
- Cél: Egyedi képfeltöltés és azonnali feldolgozás.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-006-02: `POST /api/v1/receipts/upload-url`
- Cél: Kép letöltése URL-ről SSRF védelemmel.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-006-03: `POST /api/v1/batch/upload`
- Cél: Kötegelt feltöltés.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-006-04: `GET /api/v1/batch/{batch_id}/status`
- Cél: Köteg feldolgozási állapot lekérdezése.
- Request: útvonalparaméter `batch_id`.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/preprocessing.py`: Képformátum ellenőrzés, magic bytes vizsgálat, normalizálás.
- `app/batch.py`: Kötegelt feladatok aszinkron koordinációja.
- `app/ssrf_guard.py`: Hálózati egress és privát IP védelem URL feltöltésnél.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-006-01 -> `tests/test_us_003_upload.py` (Unit/contract); scenario: AC-006-01.
- REQ-006-02 -> `tests/test_batch_processing.py` (Unit/contract); scenario: AC-006-02.
- REQ-006-03 -> `tests/test_batch_processor.py` (Unit/contract); scenario: AC-006-03.
- REQ-006-04 -> `tests/test_magic_bytes.py` (Unit/contract); scenario: AC-006-04.
- REQ-006-05 -> `tests/test_ssrf_guard.py` (Unit/contract); scenario: AC-006-05.
- REQ-006-06 -> `tests/test_async_nonblocking_fetch.py` (Unit/contract); scenario: AC-006-06.
- REQ-006-07 -> `tests/test_us_003_upload.py` (Unit/contract); scenario: AC-006-07.
- REQ-006-08 -> `tests/test_batch_processing.py` (Unit/contract); scenario: AC-006-08.
- REQ-006-09 -> `tests/test_batch_processor.py` (Unit/contract); scenario: AC-006-09.
- REQ-006-10 -> `tests/test_magic_bytes.py` (Unit/contract); scenario: AC-006-10.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
