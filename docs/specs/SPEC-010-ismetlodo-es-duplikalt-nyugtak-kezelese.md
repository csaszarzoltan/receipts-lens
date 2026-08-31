---
id: FEAT-010
title: Ismétlődő és duplikált nyugták kezelése
status: ready_for_dev
version: 1
risk: medium
owner: system-architect
related_brief: BRIEF-010
---

# FEAT-010: Ismétlődő és duplikált nyugták kezelése

## 1. Cél és felhasználói eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

Mérhető készültségi feltétel: minden alábbi kötelező követelményhez sikeres acceptance scenario és végrehajtható tesztleképezés tartozik, a jogosulatlan és hibás ágak pedig nem okoznak nem szándékolt állapotváltozást.

## 2. Kontextus és források

Ugyanannak a vásárlásnak a többszöri rögzítése torzíthatja a költéseket és a könyvelési eredményeket.

Kanonikus források:
- `briefs/BRIEF-010-ismetlodo-es-duplikalt-nyugtak-kezelese.md`
- `METHODOLOGY.md`
- `05_docs/brief-evidence-matrix.md`
- `specs/duplicate_detection_v0.4.md`
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

- ACT-010-01: felhasználóként.

- PRE-010-01: A kapcsolódó felület vagy külső belépési pont elérhető.
- PRE-010-02: A művelethez szükséges azonosítási és jogosultsági állapot a bizonyítékmátrix szerint fennáll.
- PRE-010-03: A szükséges kiinduló adat érvényes vagy a felület javítható hibát jelez.

## 5. Funkcionális követelmények

- REQ-010-01 [MUST]: Felhasználóként szeretném, hogy a rendszer jelezze a lehetséges duplikátumokat, hogy ne számoljam el kétszer ugyanazt a vásárlást.
- REQ-010-02 [MUST]: Felhasználóként szeretném látni, milyen egyezések alapján merült fel a duplikáció gyanúja, hogy megalapozott döntést hozzak.
- REQ-010-03 [MUST]: Felhasználóként szeretném egymás mellett összehasonlítani a gyanús nyugtákat, hogy eldönthessem, valóban ugyanarról a vásárlásról van-e szó.
- REQ-010-04 [MUST]: Felhasználóként szeretném megtartani mindkét nyugtát, ha külön vásárlások, hogy a rendszer ne töröljön helyes adatot.
- REQ-010-05 [MUST]: Felhasználóként szeretném kizárni vagy összekapcsolni a valódi duplikátumot, hogy az összesítésekben csak egyszer szerepeljen.
- REQ-010-06 [MUST NOT]: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
- REQ-010-07 [ALWAYS]: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
- REQ-010-08 [CONCURRENCY]: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.

## 6. Nem funkcionális követelmények

- NFR-010-01 [PERFORMANCE]: A közvetlen UI-visszajelzés a művelet indításától 500 ms-on belül jelenjen meg; hosszabb feldolgozás folyamatos állapotjelzést adjon.
- NFR-010-02 [ACCESSIBILITY]: A fő folyamat billentyűzettel végigvihető, a fókusz sorrendje determinisztikus, az állapotváltozás segítő technológiával érzékelhető.
- NFR-010-03 [SECURITY]: A szerveroldali identitás és jogosultság az autoritatív; kliens által küldött szerepkör vagy tulajdonosazonosító önmagában nem fogadható el.
- NFR-010-04 [PRIVACY]: A válaszok, naplók és értesítések csak a feladat elvégzéséhez szükséges adatot tartalmazhatják; titok és teljes érzékeny tartalom nem naplózható.

## 7. UI-szerződés

- UI-010-01: `page`, Page; Duplikáció feloldó képernyő; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-010-02: `ReceiptCard`, Component; Egymás melletti összehasonlító kártyák; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.
- UI-010-03: `Modal`, Dialog/Panel; Összevonási megerősítő párbeszédablak; kérés közben loading vagy disabled állapotot, üres és hibás eredménynél érthető következő lépést mutat.

## 8. GUI-folyamat

1. A szereplő megnyitja a kapcsolódó belépési pontot.
2. A rendszer betölti a jogosultsága szerint elérhető aktuális állapotot.
3. Üres vagy hibás kiinduló állapot esetén a felület magyarázatot és végrehajtható következő lépést mutat.
4. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném, hogy a rendszer jelezze a lehetséges duplikátumokat, hogy ne számoljam el kétszer ugyanazt a vásárlást.
5. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném látni, milyen egyezések alapján merült fel a duplikáció gyanúja, hogy megalapozott döntést hozzak.
6. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném egymás mellett összehasonlítani a gyanús nyugtákat, hogy eldönthessem, valóban ugyanarról a vásárlásról van-e szó.
7. A szereplő végrehajtja a következő felhasználói célt: Felhasználóként szeretném megtartani mindkét nyugtát, ha külön vásárlások, hogy a rendszer ne töröljön helyes adatot.
8. Adatmódosítás előtt a rendszer validál, kockázatos vagy visszafordíthatatlan műveletnél megerősítést kér.
9. Siker esetén a felület a perzisztált eredményt mutatja, hiba esetén megőrzi a javítható bemenetet és újrapróbálást kínál.
10. A szereplő visszatérhet a kiinduló nézethez, ahol a friss állapot ismét betöltődik.

## 9. Állapotmodell

Állapotok és átmenetek:

- Bizonyítékmátrixból rekonstruált állapotsor: `- `DUPLICATE_SUSPECTED` -> `SIDE_BY_SIDE_COMPARISON` -> `RESOLUTION_CHOSEN` (Merge / Archive / Dismiss) -> `RESOLVED`.
- `- `DUPLICATE_SUSPECTED`` + folytatás -> ``SIDE_BY_SIDE_COMPARISON``
- ``SIDE_BY_SIDE_COMPARISON`` + folytatás -> ``RESOLUTION_CHOSEN` (Merge / Archive / Dismiss)`
- ``RESOLUTION_CHOSEN` (Merge / Archive / Dismiss)` + folytatás -> ``RESOLVED`

- Bármely módosító állapot + megszakítás -> az utolsó perzisztált stabil állapot.
- Bármely módosító állapot + nem helyreállítható hiba -> `ERROR`, dokumentálatlan részleges siker nélkül.

## 10. Acceptance scenario-k

### AC-010-01: REQ-010-01 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-01 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném, hogy a rendszer jelezze a lehetséges duplikátumokat, hogy ne számoljam el kétszer ugyanazt a vásárlást.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-02: REQ-010-02 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-02 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném látni, milyen egyezések alapján merült fel a duplikáció gyanúja, hogy megalapozott döntést hozzak.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-03: REQ-010-03 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-03 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném egymás mellett összehasonlítani a gyanús nyugtákat, hogy eldönthessem, valóban ugyanarról a vásárlásról van-e szó.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-04: REQ-010-04 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-04 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném megtartani mindkét nyugtát, ha külön vásárlások, hogy a rendszer ne töröljön helyes adatot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-05: REQ-010-05 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-05 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Felhasználóként szeretném kizárni vagy összekapcsolni a valódi duplikátumot, hogy az összesítésekben csak egyszer szerepeljen.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-06: REQ-010-06 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-06 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: A rendszer nem teheti elérhetővé más háztartás vagy más felhasználó védett adatait jogosultság nélkül.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-07: REQ-010-07 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-07 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Sikertelen vagy megszakított művelet nem jelenhet meg sikeresként, és nem hagyhat dokumentálatlan részleges állapotot.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

### AC-010-08: REQ-010-08 bizonyítása

Given a felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel a szükséges előfeltételekkel
When a REQ-010-08 követelményhez tartozó műveletet végrehajtja
Then a rendszer a követelmény szerinti megfigyelhető eredményt adja: Ismételt vagy párhuzamos kérés nem hozhat létre nem szándékolt duplikációt, és az ütközést determinisztikusan kell jelezni.
And jogosulatlan, érvénytelen, ismételt vagy hibás végrehajtás nem okoz rejtett adatváltozást.

## 11. API-szerződés

### API-010-01: `POST /api/v1/duplicates/detect`
- Cél: Duplikációk detektálása ujjlenyomat és összeg alapján.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-010-02: `GET /api/v2/duplicates`
- Cél: Gyanús párok és csoportok lekérdezése.
- Request: nincs kötelező törzs; opcionális szűrő- és lapozási paraméterek a handler szerint.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.

### API-010-03: `POST /api/v2/duplicates/resolve`
- Cél: Döntés érvényesítése: összevonás / megtartás / elvetés.
- Request: a kapcsolódó kliens- és szervermodell által validált JSON vagy fájltartalom.
- Response: a handler és a kapcsolódó kliensmodell szerinti típusos sikeres reprezentáció; lista esetén üres lista érvényes eredmény.
- Hibák: `400/422` érvénytelen bemenet, `401` nincs hitelesítés, `403` nincs jogosultság, `404` nem található vagy nem látható erőforrás, `409` állapot- vagy revízióütközés, `429` korlátozás, `5xx` függőségi vagy belső hiba; csak a tényleges handler által használt részhalmaz alkalmazandó.


## 12. Adatmodell és perzisztencia

- `app/duplicate_detection.py`: Kereskedő, dátum, végösszeg és képi ujjlenyomat illesztés.
- `app/product_service.py`: Duplikáció feloldási műveletek végrehajtása.
- Migráció: nincs, mert ez a dokumentum a meglévő viselkedést specifikálja és production kódot nem módosít.
- Tranzakciós szabály: sikertelen művelet nem hagyhat részleges írást; több írást érintő művelet atomikusan vagy kompenzáltan fejeződik be.

## 13. Tesztterv és lefedettségi leképezés

- REQ-010-01 -> `tests/test_duplicate_detection.py` (Unit/contract); scenario: AC-010-01.
- REQ-010-02 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-010-02.
- REQ-010-03 -> `tests/test_duplicate_detection.py` (Unit/contract); scenario: AC-010-03.
- REQ-010-04 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-010-04.
- REQ-010-05 -> `tests/test_duplicate_detection.py` (Unit/contract); scenario: AC-010-05.
- REQ-010-06 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-010-06.
- REQ-010-07 -> `tests/test_duplicate_detection.py` (Unit/contract); scenario: AC-010-07.
- REQ-010-08 -> `tests/test_product_features.py` (Unit/contract); scenario: AC-010-08.

Minőségi kapu: minden REQ-azonosító legalább egy AC-azonosítóhoz és legalább egy meglévő vagy célzott teszthez kapcsolódik. A teljes regresszió mellett a feature-hez rendelt teszteket célzottan is futtatni kell.

## 14. Kockázatok és biztonsági megfontolások

- Jogosultsági megkerülés: minden védett erőforrás szerveroldali tenant-, háztartás- vagy tulajdonosi szűrést igényel.
- Versenyhelyzet: módosító műveleteknél revízió, idempotenciakulcs vagy egyenértékű determinisztikus védelem szükséges, ahol a jelenlegi szerződés ezt támogatja.
- Külső függőség: időtúllépés vagy szolgáltatáshiba nem fordulhat csendes sikerbe; az újrapróbálás nem duplikálhat.
- Adatvédelem: napló, diagnosztika és értesítés nem tartalmazhat hitelesítő adatot vagy szükségtelen pénzügyi tartalmat.
- Visszafordíthatatlan művelet: explicit megerősítés és érthető következményleírás szükséges.
- Bizonytalanság: automatikus felismerés vagy javaslat nem jelenhet meg emberi döntésként, ha a rendszer bizonyossága korlátozott.
