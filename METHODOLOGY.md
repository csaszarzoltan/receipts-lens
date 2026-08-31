# Követelményvezérelt, Bizonyított AI-fejlesztési Rendszer

**Rövid név:** RVAD, Requirements-driven Verified AI Development  
**Verzió:** 1.1  
**Státusz:** Összesített módszertani alapverzió  
**Dátum:** 2026-08-28  
**Változás:** A traceability kézi YAML-karbantartása helyett Runner által generált, determinisztikus bizonyítási gráf  

## 0. A dokumentum célja

Ez a módszertan olyan AI-támogatott szoftverfejlesztési rendszert határoz meg, amelyben:

- a kívánt működés elsődleges és autoritatív forrása a jóváhagyott specifikáció;
- minden fontos követelményhez futtatható teszt és ellenőrizhető bizonyíték tartozik;
- az implementáció kis, zárt és egyértelmű feladatokra bontható;
- egyszerűbb vagy olcsóbb LLM is képes a feladatok megbízható végrehajtására;
- az LLM állításai helyett determinisztikus eszközök döntenek a sikerességről;
- a kutatás, a termékdöntés, a specifikáció, a tesztelés, a fejlesztés és az üzemeltetési visszacsatolás egyetlen nyomon követhető láncot alkot.

A módszertan három rendszer erősségeit egyesíti:

1. **specifikációvezérelt fejlesztés:** invariánsok, UI-szerződés, állapotmodell, szerepkörök, jogosultságok, végrehajtási bizonyíték és auditálhatóság;
2. **behavior-first evolúciós megközelítés:** felhasználói viselkedés, GUI-folyamat, RED tesztek, prototípus és production visszacsatolás;
3. **projektspecifikus módszertani profil:** technológiai konvenciók, fájlszerkezet, parancsok, minőségi kapuk és integrációs szabályok.

A központi cél nem a lehető leghosszabb dokumentáció, hanem a **kellően pontos, tesztelhető és géppel ellenőrizhető fejlesztési szerződés**.

---

# 1. Alapelvek

## 1.1. A specifikáció az üzleti szándék autoritatív forrása

A forráskód a rendszer jelenlegi viselkedésének bizonyítéka, de nem írhatja felül automatikusan a jóváhagyott üzleti szándékot.

A források elsőbbségi sorrendje:

1. jóváhagyott domain-invariánsok;
2. jóváhagyott feature-specifikáció;
3. acceptance scenario-k és tesztleképezés;
4. futtatható tesztek;
5. implementáció;
6. generált dokumentáció és LLM-összefoglaló.

Ha a kód vagy a teszt eltér a jóváhagyott specifikációtól, nem a specifikációt kell automatikusan a kódhoz igazítani. A konfliktust osztályozni, majd szükség esetén emberhez kell eszkalálni.

## 1.2. A viselkedés megelőzi az implementációt

Először azt kell meghatározni, hogy a rendszer mit tegyen a felhasználó és a külső rendszerek szemszögéből. Csak ezután következhet annak eldöntése, hogy ezt milyen architektúrával és kóddal valósítjuk meg.

A fejlesztési lánc:

```text
igény vagy megfigyelt probléma
    -> feature brief
    -> követelmény-kontraktus
    -> acceptance scenario-k
    -> tesztterv és RED bizonyíték
    -> minimális implementáció
    -> célzott verifikáció
    -> teljes regresszió
    -> független review
    -> PR és release
    -> production visszacsatolás
    -> új vagy módosított követelményjavaslat
```

## 1.3. Követelményenként bizonyítható megfelelés

Minden kötelező követelményhez legalább egy futtatható tesztnek kell tartoznia. A release egyik legfontosabb mérőszáma a követelmény-lefedettség:

```text
requirement coverage = teszttel lefedett kötelező követelmények / összes kötelező követelmény
```

A célérték jóváhagyott feature esetén 100 százalék. Ez nem azonos a kódsor-lefedettséggel. A kód coverage hasznos kiegészítő mérőszám, de nem bizonyítja önmagában az üzleti követelmények teljesülését.

## 1.4. A legalacsonyabb megfelelő tesztszint elve

Nem kell minden követelményt böngészőből tesztelni. Minden viselkedést azon a legalacsonyabb tesztszinten kell bizonyítani, amely még hitelesen ellenőrzi a követelményt.

- tiszta üzleti logika: unit teszt;
- API-szerződés: contract vagy API teszt;
- adatbázis és komponensek együttműködése: integration teszt;
- kritikus felhasználói út és UI-szerződés: E2E teszt;
- éles szolgáltatás elérhetősége és külső integráció: production canary.

## 1.5. Az LLM generál, a runner dönt

Az LLM valószínűségi rendszer. Javasolhat specifikációt, tesztet, implementációt és diagnózist, de saját szöveges állítása nem minősül bizonyítéknak.

A sikerességet determinisztikus komponensek állapítják meg:

- sémavalidátor;
- linter;
- fordító vagy build rendszer;
- type checker;
- tesztfuttató;
- secret scanner;
- jogosultság- és diff-ellenőrző;
- automatikus traceability collector és validator;
- Git és CI exit kódok.

## 1.6. Kis scope, zárt bemenet, minimális diff

Egyszerűbb LLM esetén különösen fontos, hogy egy végrehajtási feladat:

- kevés követelményt tartalmazzon;
- pontos célállapotot adjon meg;
- felsorolja a módosítható fájlokat;
- felsorolja a tiltott fájlokat és műveleteket;
- megadja a futtatandó parancsokat;
- meghatározza a leállási feltételeket;
- minimális, célzott módosítást várjon el.

## 1.7. Az evolúció csak ellenőrzött specifikációváltozáson keresztül történhet

Production hiba, canary bukás, felhasználói visszajelzés vagy közvetlen kódmódosítás létrehozhat specifikációs javaslatot, de nem módosíthat automatikusan jóváhagyott üzleti szabályt.

A visszairányú folyamat:

```text
runtime jel vagy kódeltérés
    -> megfigyelés és bizonyíték
    -> PROPOSED specifikációváltozás
    -> hatáselemzés
    -> emberi vagy szabályalapú jóváhagyás
    -> új specifikációverzió
    -> új tesztek
    -> implementáció
```

---

# 2. A rendszer három fő fázisa

## 2.1. SPEC

A SPEC fázis eredménye egy jóváhagyott, tesztelhető és ellentmondásmentes követelmény-kontraktus.

Fő tevékenységei:

1. igény és probléma rögzítése;
2. szükség esetén kutatás és bizonyítékgyűjtés;
3. feature brief készítése;
4. scope és non-scope meghatározása;
5. követelmények és invariánsok azonosítása;
6. felhasználói és rendszerfolyamatok leírása;
7. UI- és API-szerződések rögzítése;
8. állapotmodell készítése, ha indokolt;
9. acceptance scenario-k megírása;
10. tesztleképezés és kockázati besorolás;
11. SPEC READY kapu futtatása;
12. szükséges emberi jóváhagyások megszerzése.

## 2.2. BUILD

A BUILD fázis a jóváhagyott specifikációból futtatható teszteket és minimális implementációt készít izolált környezetben.

Fő tevékenységei:

1. izolált Git worktree vagy egyenértékű munkakörnyezet létrehozása;
2. végrehajtási csomag összeállítása;
3. tesztek elkészítése;
4. tesztek statikus ellenőrzése;
5. RED futás és a bukási ok validálása;
6. minimális implementáció;
7. pre-test safety scan;
8. célzott tesztfuttatás;
9. triage és korlátozott javítási hurok;
10. teljes regresszió, lint, typecheck és build.

## 2.3. VERIFY

A VERIFY fázis igazolja, hogy a változtatás megfelel a jóváhagyott követelményeknek, a projekt szabályainak és a biztonsági korlátoknak.

Fő tevékenységei:

1. traceability ellenőrzése;
2. független reviewer vizsgálata;
3. final safety gate;
4. végrehajtási manifest készítése;
5. PR létrehozása;
6. emberi PR-döntés, ha szükséges;
7. release utáni smoke, nightly és canary ellenőrzések;
8. visszacsatolás a backlogba és a specifikációs folyamatba.

---

# 3. Követelmény-artefaktumok

## 3.1. Feature brief

A feature brief az ötlet és a fejleszthető specifikáció közötti rövid átmeneti dokumentum.

Kötelező tartalma:

```markdown
# Feature Brief

## Probléma
Mit nem tud most megtenni a felhasználó, vagy milyen hibát tapasztal?

## Célcsoport és kontextus
Ki, mikor és milyen helyzetben találkozik a problémával?

## Kívánt eredmény
Milyen megfigyelhető eredménnyel tekintjük megoldottnak?

## Scope
Mi tartozik bele?

## Non-scope
Mi nem tartozik bele?

## Érintett rendszerek
Mely UI, API, adatmodell vagy külső integráció érintett?

## Bizonytalanságok
Mely kérdésekre nincs még elfogadott válasz?
```

A brief státusza lehet:

- `DRAFT`;
- `NEEDS_RESEARCH`;
- `READY_FOR_SPEC`;
- `REJECTED`;
- `DUPLICATE`.

## 3.2. Domain-invariánsok

A több feature-re érvényes, hosszú életű üzleti korlátokat központi domain-dokumentumban kell tartani.

Jelölések:

- `[MUST]`: kötelező pozitív viselkedés;
- `[MUST NOT]`: tiltott viselkedés;
- `[ALWAYS]`: minden releváns helyzetben fennálló invariáns;
- `[CONCURRENCY]`: párhuzamossági vagy idempotenciaelvárás;
- `[SECURITY]`: biztonsági követelmény;
- `[PRIVACY]`: adatvédelmi követelmény;
- `[PERFORMANCE]`: mérhető teljesítményelvárás.

Minden invariánsnak rendelkeznie kell:

- egyedi azonosítóval;
- világos hatókörrel;
- ellenőrizhető megfogalmazással;
- legalább egy tesztleképezéssel;
- tulajdonossal vagy jóváhagyó szerepkörrel.

## 3.3. Feature-specifikáció

Egy feature alapértelmezetten egy központi feature-specifikációt kap. A happy path, edge case, error case, GUI-folyamat, hozzáférhetőség és concurrency nem kötelezően külön user story, hanem külön követelmény vagy scenario ugyanabban a lezárt kontextusban.

Nagy feature több önálló specifikációra bontható, ha:

- külön-külön szállítható részekből áll;
- a dokumentum túl nagy egy megbízható LLM-végrehajtáshoz;
- eltérő kockázati jóváhagyás vonatkozik a részekre;
- több, egymástól független felhasználói eredményt tartalmaz.

## 3.4. ADR

Az ADR azt rögzíti, hogy egy fontos műszaki vagy architekturális döntés miért és milyen alternatívák közül született.

Az ADR nem helyettesíti:

- a felhasználói követelményt;
- az acceptance criteria-t;
- a GUI-folyamatot;
- a teszttervet.

ADR szükséges például:

- új technológia vagy szolgáltatás bevezetésekor;
- tartós adatmodell-döntésnél;
- jelentős integrációs stratégiánál;
- biztonsági vagy skálázási architektúra módosításánál;
- több ésszerű alternatíva közötti hosszú távú döntésnél.

## 3.5. Kutatási dokumentum

Kutatás akkor szükséges, ha a specifikáció külső tényre, piacra, felhasználói fájdalomra, technológiai lehetőségre, szabványra vagy változó szolgáltatási információra támaszkodik.

Követelményei:

- forrás és dátum;
- ellenőrizhető idézet vagy pontos bizonyíték;
- opció-összehasonlítás, ha több megoldás lehetséges;
- bizonytalanságok és korlátok;
- kapcsolat a feature brieffel, ADR-rel vagy specifikációval;
- elkülönítés a jóváhagyott követelményektől.

A kutatási megállapítás önmagában nem válik üzleti követelménnyé. Ehhez specifikációs döntés szükséges.

---

# 4. Egységes feature-specifikációs sablon

```markdown
---
id: FEAT-023
title: Kosár ürítése
status: approved
version: 1
risk: medium
owner: product-owner
approvedBy: reviewer-id
approvedAt: 2026-08-28T09:00:00Z
baseCommit: abc1234
---

# FEAT-023: Kosár ürítése

## 1. Cél és felhasználói eredmény

A felhasználó egyetlen megerősített művelettel eltávolíthatja a kosár összes tételét.

## 2. Kontextus és források

- Kapcsolódó brief: BRIEF-023
- Kapcsolódó research: docs/research/...
- Kapcsolódó ADR: ADR-012
- Kapcsolódó domain-invariánsok: INV-CART-001, INV-API-003

## 3. Scope

### Benne van

- kosárürítés kezdeményezése;
- megerősítés és megszakítás;
- sikeres és hibás API-válasz kezelése;
- dupla kérés megakadályozása;
- állapot megjelenítése a felületen.

### Nincs benne

- egyedi tételek törlése;
- törölt kosár visszaállítása;
- fizetési tranzakció módosítása.

## 4. Szereplők és előfeltételek

- ACT-001: bejelentkezett vásárló;
- PRE-001: a kosár elérhető;
- PRE-002: a felhasználó jogosult a saját kosarának módosítására.

## 5. Funkcionális követelmények

- REQ-001 [MUST]: A rendszer törlés előtt megerősítő dialógust jelenít meg.
- REQ-002 [MUST NOT]: Üres kosár esetén az ürítés nem kezdeményezhető.
- REQ-003 [ALWAYS]: Sikertelen kérés után a kosár tartalma változatlan marad.
- REQ-004 [CONCURRENCY]: Egyidejűleg legfeljebb egy ürítési kérés futhat.
- REQ-005 [MUST]: Sikeres ürítés után a számláló értéke nulla és az üres állapot látható.

## 6. Nem funkcionális követelmények

- NFR-001 [PERFORMANCE]: A sikeres válasz után az UI 500 ms-on belül frissüljön.
- NFR-002 [ACCESSIBILITY]: A dialógus billentyűzettel kezelhető és fókuszcsapdával rendelkezik.
- NFR-003 [SECURITY]: A felhasználó csak a saját kosarát ürítheti.

## 7. UI-szerződés

- UI-001: `cart-clear-btn`, Button, üres kosárnál disabled, kérés alatt loading.
- UI-002: `cart-clear-modal`, Dialog, Esc és Mégse bezárhatja.
- UI-003: `cart-confirm-ok`, Button, egy ürítési műveletet indít.
- UI-004: `cart-confirm-cancel`, Button, mellékhatás nélkül bezár.
- UI-005: `cart-empty-view`, Container, üres kosárnál látható.
- UI-006: `cart-badge-count`, Badge, egész számot mutat.
- UI-007: `toast-error`, Alert, sikertelen kérésnél jelenik meg.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/cart` oldalt.
2. A `cart-clear-btn` gombra kattint.
3. Megjelenik a `cart-clear-modal`.
4. Mégse vagy Esc esetén a modal bezárul és nincs adatváltozás.
5. Jóváhagyás esetén a gomb loading állapotba kerül és elindul egy kérés.
6. Siker esetén a modal bezárul, a számláló nulla és megjelenik az üres nézet.
7. Hiba esetén a kosár megmarad, hibaüzenet jelenik meg, és a művelet újrapróbálható.

## 9. Állapotmodell

Állapotok:

- IDLE
- CONFIRMING
- CLEARING
- EMPTY

Átmenetek:

- IDLE + clear_click + item_count > 0 -> CONFIRMING
- CONFIRMING + cancel -> IDLE
- CONFIRMING + confirm + in_flight == false -> CLEARING
- CLEARING + success -> EMPTY
- CLEARING + failure -> CONFIRMING
- CLEARING + confirm -> CLEARING, új kérés nélkül

## 10. Acceptance scenario-k

### AC-001: Sikeres ürítés

Given a kosárban három termék van  
When a felhasználó megnyitja a megerősítő dialógust és jóváhagyja az ürítést  
Then pontosan egy ürítési kérés indul  
And megjelenik az üres állapot  
And a kosárszámláló értéke nulla lesz

### AC-002: Megszakítás

Given a kosárban termék van  
When a felhasználó megnyitja, majd megszakítja a dialógust  
Then a kosár tartalma változatlan marad  
And ürítési kérés nem indul

### AC-003: Üres kosár

Given a kosár üres  
When a felhasználó megnyitja a kosár oldalt  
Then az ürítés gomb disabled állapotú  
And ürítési kérés nem indítható

### AC-004: Hálózati hiba

Given a kosárban két termék van  
And az API hibával válaszol  
When a felhasználó jóváhagyja az ürítést  
Then a kosár továbbra is két terméket tartalmaz  
And hibaüzenet jelenik meg  
And a művelet újrapróbálható

### AC-005: Dupla kattintás

Given a megerősítő dialógus nyitva van  
When a felhasználó rövid időn belül kétszer aktiválja a jóváhagyást  
Then pontosan egy ürítési kérés indul

### AC-006: Billentyűzetes kezelés

Given a megerősítő dialógus nyitva van  
When a felhasználó az Escape billentyűt megnyomja  
Then a dialógus mellékhatás nélkül bezárul  
And a fókusz visszakerül az ürítés gombra

## 11. API-szerződés

- Endpoint: `DELETE /api/cart`
- Siker: HTTP 200, `{ "status": "ok", "data": { "itemCount": 0 } }`
- Jogosulatlan: HTTP 403, `{ "error": "forbidden" }`
- Hiba: szabványos hibaválasz, a kliens helyi állapota nem ürülhet ki.
- Idempotencia: párhuzamos kliensaktiválásból legfeljebb egy in-flight kérés.

## 12. Tesztleképezés

- REQ-001 -> AC-001, AC-002 -> E2E
- REQ-002 -> AC-003 -> component és API contract
- REQ-003 -> AC-004 -> integration és E2E
- REQ-004 -> AC-005 -> unit és E2E
- REQ-005 -> AC-001 -> E2E
- NFR-002 -> AC-006 -> accessibility E2E
- NFR-003 -> security contract test

## 13. Kockázatok és emberi döntések

- HR-001: A dialógus végleges szövegét Product Owner hagyja jóvá.
- HR-002: Jogosultsági változtatás esetén security review kötelező.

## 14. Nyitott kérdések

Nincs implementációt blokkoló nyitott kérdés.

## 15. Definition of Done

- minden kötelező requirement teszttel lefedett;
- a RED bizonyíték rögzített;
- a célzott tesztek zöldek;
- a teljes regresszió zöld;
- lint, typecheck és build zöld;
- a Runner által újragenerált traceability gate zöld;
- a reviewer jóváhagyta;
- a szükséges dokumentáció frissült;
- a final safety gate zöld;
- a PR létrejött.
```

---

# 5. A SPEC READY minőségi kapu

Fejlesztés csak `SPEC_READY` állapotú specifikációból indulhat.

## 5.1. Kötelező ellenőrzések

A gate ellenőrzi, hogy:

- a feature egyedi azonosítóval rendelkezik;
- a cél megfigyelhető eredményt ír le;
- a scope és non-scope rögzített;
- minden követelménynek stabil azonosítója van;
- a követelmények egyértelműek és tesztelhetők;
- nincs definiálatlan szubjektív kifejezés, például „gyors”, „egyszerű” vagy „megfelelő”;
- a happy path le van írva;
- a releváns edge case-ek le vannak írva;
- a hiba- és helyreállítási viselkedés le van írva;
- a jogosultsági, concurrency és adatkonzisztencia-kérdések értékelve vannak;
- minden invariánshoz tartozik acceptance scenario;
- minden kötelező requirementhez tervezett teszt tartozik;
- az UI-elemek stabil azonosítókkal rendelkeznek, ha van UI;
- az állapotátmenetek teljesek, ha a feature állapotos;
- az API-szerződés rögzített, ha van API-változás;
- nincs implementációt blokkoló nyitott kérdés;
- a kockázati besorolás elkészült;
- a kötelező emberi jóváhagyások megtörténtek.

## 5.2. Strukturált eredmény

```yaml
spec_id: FEAT-023
status: SPEC_READY
missing_sections: []
missing_requirements: []
untestable_statements: []
contradictions: []
uncovered_requirements: []
open_blocking_questions: []
human_gate_required: false
validated_at: 2026-08-28T09:15:00Z
```

Blokkoló lista esetén a státusz `NEEDS_CLARIFICATION`. Az implementer ilyen specifikációból nem indulhat el.

---

# 6. Kockázati besorolás és emberi kapuk

## 6.1. Kockázati szintek

### LOW

Példák:

- dokumentációs javítás;
- typo;
- belső refaktor változatlan viselkedéssel;
- meglévő teszt bővítése viselkedésváltozás nélkül;
- kis UI-hiba stabil szerződés mellett.

Jellemző folyamat:

- egyszerűsített specifikáció;
- automatikus teszt- és minőségi kapuk;
- normál PR-review.

### MEDIUM

Példák:

- új, jól körülhatárolt feature;
- új API-végpont;
- jelentősebb UI-folyamat;
- külső integráció módosítása;
- tartós üzleti viselkedés változása.

Jellemző folyamat:

- teljes feature-specifikáció;
- tesztleképezés;
- szükség esetén prototípus;
- független reviewer;
- emberi PR-jóváhagyás.

### HIGH

Példák:

- auth, RBAC, titkosítás vagy GDPR;
- pénzügyi logika vagy fizetési tranzakció;
- adatbázis-migráció adatvesztési kockázattal;
- publikus API breaking change;
- kritikus infrastruktúra;
- jóváhagyott domain-invariáns módosítása.

Jellemző folyamat:

- kötelező szakértői és emberi jóváhagyás;
- részletes kockázatelemzés;
- rollback terv;
- kibővített tesztelés;
- automatikus merge tiltása.

## 6.2. Kötelező emberi stop-gate események

A végrehajtás megáll, ha:

- `[MUST]`, `[MUST NOT]` vagy `[ALWAYS]` invariáns változik;
- hitelesítés, jogosultság vagy adatvédelem érintett;
- pénzügyi logika módosul;
- adatvesztési vagy irreverzibilis migrációs kockázat van;
- publikus interfész törő módosítása szükséges;
- két jóváhagyott követelmény ellentmond egymásnak;
- credential vagy secret kerül a diffbe;
- tiltott fájl módosítása történt;
- az iterációs vagy időkorlát elfogyott;
- jelentősen új GUI készül, de nincs jóváhagyott prototípus;
- az LLM-nek termékdöntést kellene saját hatáskörben meghoznia.

## 6.3. Kockázatalapú prototípus-gate

Prototípus kötelező, ha:

- új felhasználói út készül;
- jelentősen megváltozik az információs architektúra;
- több ésszerű UX-megoldás közül kell választani;
- kritikus vagy nehezen visszafordítható UI-művelet készül;
- a feature értéke nagyban függ a vizuális működéstől.

Prototípus általában nem szükséges:

- dokumentációs módosításhoz;
- belső refaktorhoz;
- backend-only változáshoz stabil szerződés mellett;
- kis, egyértelmű UI-hibajavításhoz;
- tesztbővítéshez viselkedésváltozás nélkül.

---

# 7. Tesztstratégia

## 7.1. Unit tesztek

Unit tesztet kell előnyben részesíteni:

- tiszta függvényekhez;
- üzleti számításokhoz;
- validációhoz;
- guard feltételekhez;
- állapotátmenetekhez;
- határértékekhez;
- concurrency vezérlés izolált logikájához.

## 7.2. Contract és API tesztek

Contract teszt szükséges:

- request és response sémához;
- HTTP státuszkódhoz;
- auth és jogosultsági viselkedéshez;
- publikus API-kompatibilitáshoz;
- idempotenciához;
- külső adapterek formátumához.

## 7.3. Integration tesztek

Integration teszt szükséges:

- repository és service együttműködéséhez;
- adatbázis-tranzakcióhoz;
- migrációhoz;
- cache és perzisztencia együttműködéséhez;
- kontrollált külső adapterhez;
- több komponensen áthaladó hibakezeléshez.

## 7.4. E2E tesztek

E2E teszt szükséges:

- kritikus felhasználói utakhoz;
- frontend és backend együttműködéséhez;
- UI-szerződéshez;
- route-okhoz és navigációhoz;
- fontos hozzáférhetőségi viselkedéshez;
- olyan acceptance scenario-hoz, amely alacsonyabb szinten nem bizonyítható hitelesen.

Az E2E teszt:

- stabil szelektorokat használjon;
- legyen izolált és idempotens;
- ne függjön szükségtelenül külső szolgáltatástól;
- ismételt futtatáskor is azonos eredményt adjon;
- bukáskor trace-t, screenshotot vagy megfelelő diagnosztikai artifactot készítsen.

## 7.5. Production canary

A production canary célja nem az összes funkció újratesztelése, hanem a kritikus éles útvonalak és külső függőségek rendszeres ellenőrzése.

A canary:

- ne használjon LLM-et a normál futáshoz;
- dedikált vagy biztonságos tesztadatot használjon;
- ne okozzon visszafordíthatatlan üzleti műveletet;
- zöld állapotban maradjon csendes;
- tartós bukáskor hozzon létre strukturált hibajelzést;
- a hibát új kutatási vagy specifikációs inputként továbbítsa.

## 7.6. RED bizonyíték

Az implementáció előtt igazolni kell, hogy az új teszt:

- szintaktikailag érvényes;
- elindul a tesztkörnyezetben;
- a hiányzó vagy hibás funkció miatt bukik;
- nem környezeti vagy teszthiba miatt piros;
- alkalmas arra, hogy a későbbi GREEN állapotot bizonyítsa.

A „tesztfájl létrejött” nem elegendő RED bizonyíték. A tesztet ténylegesen futtatni kell.

---

# 8. Automatikusan generált requirement-test traceability

## 8.1. Alapelv

A traceability nem kézzel karbantartott dokumentum, hanem a Runner által minden ellenőrzött végrehajtás során determinisztikusan előállított bizonyítási nézet.

A kézzel karbantartott feature-szintű `traceability.yaml` nem lehet autoritatív forrás, mert könnyen eltérhet:

- a jóváhagyott specifikációtól;
- a tényleges tesztmetaadatoktól;
- a tesztfuttató által felfedezett tesztektől;
- az aktuális commit tartalmától;
- a végrehajtási eredményektől.

A traceability gráfot ezért bármikor újra elő kell tudni állítani az elsődleges forrásokból. A generált artifact nem kézzel szerkesztendő.

## 8.2. Autoritatív és kiegészítő források

A Runner a kapcsolatokat az alábbi forrásokból építi fel.

### Elsődleges források

1. **Jóváhagyott specifikáció**
   - feature ID-k;
   - requirement ID-k;
   - nem funkcionális requirement ID-k;
   - acceptance scenario ID-k;
   - domain-invariánsok;
   - specifikációverzió és jóváhagyási állapot.

2. **Strukturált tesztmetaadatok**
   - a teszt által igazolt requirementek;
   - a kapcsolódó acceptance scenario;
   - a tesztszint;
   - a teszt stabil azonosítója;
   - a kötelező vagy opcionális státusz.

3. **Tesztfuttatók gépi riportjai**
   - a tesztet felfedezte-e a runner;
   - a teszt ténylegesen lefutott-e;
   - passed, failed, skipped, xfail, todo vagy disabled állapot;
   - futási idő és hibaartifactok;
   - az aktuális execution ID és commit.

4. **Execution packet és Runner manifest**
   - cél feature és requirementek;
   - specifikációverzió;
   - futtatandó tesztek és parancsok;
   - base és result commit;
   - minőségi kapuk eredménye.

### Másodlagos források

5. **Tesztfájl és tesztfüggvény neve**
   - egyszerű kezdeti integrációhoz vagy legacy fallbackként használható;
   - önmagában nem bizonyítja a requirement coverage-et, ha strukturált metaadat kötelező.

6. **Git diff, commit és PR-metaadat**
   - a megváltozott fájlok feature-höz rendelésére használható;
   - audit- és provenance-bizonyíték;
   - nem lehet egy requirement teljesítésének egyetlen bizonyítéka.

A commitüzenet szabad szöveg, squash során megváltozhat, és több feature-t is összefoghat. Emiatt csak kiegészítő bizonyíték.

## 8.3. Azonosítók

Ajánlott stabil azonosítók:

- `INV-*`: domain-invariáns;
- `FEAT-*`: feature;
- `REQ-*`: funkcionális requirement;
- `NFR-*`: nem funkcionális requirement;
- `UI-*`: UI-szerződés elem;
- `AC-*`: acceptance scenario;
- `TEST-*`: stabil teszteset-azonosító;
- `ADR-*`: architekturális döntés;
- `RUN-*`: végrehajtási futás.

Az azonosítók átnevezése kontrollált specifikációmódosítás. A Runnernek észlelnie kell az ismeretlen, duplikált és árva hivatkozásokat.

## 8.4. Strukturált tesztmetaadatok

A teszt és requirement kapcsolatát lehetőleg a teszt framework natív vagy jól definiált metaadat-mechanizmusával kell deklarálni.

### Pytest példa

```python
@pytest.mark.test_id("TEST-INT-023-01")
@pytest.mark.requirements("REQ-003", "REQ-004")
@pytest.mark.scenario("AC-004")
def test_cart_state_is_preserved_after_api_failure():
    ...
```

### Playwright példa

```typescript
test(
  "AC-004: hálózati hiba után a kosár megmarad",
  {
    annotation: [
      { type: "test-id", description: "TEST-E2E-023-04" },
      { type: "requirement", description: "REQ-003" },
      { type: "scenario", description: "AC-004" },
    ],
  },
  async ({ page }) => {
    // A teszt implementációja.
  },
);
```

### Gherkin példa

```gherkin
@feature:FEAT-023
@requirement:REQ-003
@scenario:AC-004
@test:TEST-E2E-023-04
Scenario: Hálózati hiba esetén a kosár tartalma megmarad
  Given a kosárban két termék van
  And az API hibával válaszol
  When a felhasználó jóváhagyja az ürítést
  Then a kosár továbbra is két terméket tartalmaz
```

A parser adapter feladata a framework-specifikus metaadatok normalizálása egy közös belső modellre.

## 8.5. Felismerési prioritás

A Runner a kapcsolatokat az alábbi prioritással állapítja meg:

```text
1. Strukturált tesztmetaadat vagy Gherkin tag
2. Framework-specifikus annotation, marker vagy decorator
3. Szabványosított teszt docstring vagy közvetlen meta-komment
4. Tesztfájl és tesztfüggvény neve
5. Execution packet deklarált kapcsolata
6. Commit- vagy PR-hivatkozás, kizárólag kiegészítő bizonyítékként
```

Ha magasabb prioritású és alacsonyabb prioritású forrás ellentmond egymásnak, a Runner blokkoló konfliktust jelez. Nem választhat csendben egy kapcsolatot.

## 8.6. Parser- és collector-architektúra

A Runner technológiaspecifikus adaptereket használhat:

```text
TraceabilityCollector
├── SpecificationParser
├── PytestMetadataCollector
├── PlaywrightMetadataCollector
├── GherkinTagCollector
├── VitestMetadataCollector
├── TestResultCollector
├── ExecutionPacketCollector
└── GitEvidenceCollector
```

A statikus parser vagy AST-elemzés azt állapítja meg, hogy a teszt deklaráltan mit igazol. A tesztfuttató riportja azt bizonyítja, hogy a teszt valóban fel lett fedezve és lefutott.

```text
statikus metaadat = mit állít a teszt, hogy ellenőriz
tesztriport        = mi futott le ténylegesen
specifikáció       = mit kötelező ellenőrizni
Runner-gráf        = a három forrás ellenőrzött összekapcsolása
```

AST-parser használata javasolt, ha a framework és a nyelv ezt indokolja. Egyszerű regex csak kontrollált, egyértelmű szintaxisnál használható, és nem írhatja felül az AST-ből vagy framework-riportból származó adatot.

## 8.7. Kötelező gráfkapcsolatok

A generált traceability gráf legalább az alábbi kapcsolatokat tartalmazza:

```text
igény -> feature
feature -> specifikációverzió
feature -> requirement
requirement -> acceptance scenario
requirement -> deklarált teszt
deklarált teszt -> felfedezett teszt
felfedezett teszt -> futtatási eredmény
futtatási eredmény -> execution ID és commit
feature -> módosított fájl
módosított fájl -> jogosult szerepkör
feature -> reviewer jelentés
feature -> PR és release
runtime hiba -> érintett feature vagy requirement
```

## 8.8. Generálás időpontjai

A Runner a traceability gráfot legalább három ponton építi újra:

1. **SPEC READY gate:** ellenőrzi, hogy minden requirementhez tervezett scenario és tesztszint tartozik;
2. **célzott és teljes tesztfuttatás után:** összekapcsolja a deklarált teszteket a tényleges teszteredményekkel;
3. **Final Safety Gate:** az aktuális commitból és lezárt futási bizonyítékokból újragenerálja a végleges gráfot.

A Final Safety Gate mindig tiszta újragenerálást végez. Nem bízhat meg egy korábbi, kézzel vagy más futásban előállított traceability artifactban.

## 8.9. Generált artifactok

Ajánlott kimenet:

```text
.ai-execution/
└── evidence/
    └── RUN-FEAT-023-20260828-01/
        ├── traceability.json
        ├── traceability.md
        ├── test-results.json
        ├── source-map.json
        └── validation-report.json
```

- `traceability.json`: gépi autoritás, sémavalidált gráf és összegzés;
- `traceability.md`: ugyanabból a JSON-ból generált emberbarát riport;
- `test-results.json`: normalizált tesztfuttatási eredmények;
- `source-map.json`: az egyes kapcsolatok forrása és felismerési módja;
- `validation-report.json`: konfliktusok, hiányok, fallbackek és gate-döntés.

A Markdown riport nem önálló forrás. Mindig a lezárt JSON artifactból generálódik.

## 8.10. Generált JSON példa

```json
{
  "schemaVersion": "1.0",
  "generated": true,
  "feature": "FEAT-023",
  "specVersion": 1,
  "specCommit": "abc1234",
  "executionId": "RUN-FEAT-023-20260828-01",
  "requirements": {
    "REQ-003": {
      "scenarios": ["AC-004"],
      "tests": [
        {
          "id": "TEST-INT-023-01",
          "level": "integration",
          "source": "tests/integration/test_cart_clear.py",
          "relationshipSource": "pytest-marker",
          "discovered": true,
          "executed": true,
          "result": "passed"
        },
        {
          "id": "TEST-E2E-023-04",
          "level": "e2e",
          "source": "frontend/e2e/cart-clear.spec.ts",
          "relationshipSource": "playwright-annotation",
          "discovered": true,
          "executed": true,
          "result": "passed"
        }
      ],
      "coverageStatus": "covered",
      "verificationStatus": "passed"
    }
  },
  "summary": {
    "requirementsTotal": 7,
    "requirementsCovered": 7,
    "requirementsPassed": 7,
    "requirementsFailed": 0,
    "requirementsUncovered": 0,
    "orphanTests": 0,
    "fallbackRelationships": 0,
    "status": "PASS"
  }
}
```

## 8.11. Final Safety Gate blokkolási szabályok

A gate blokkol, ha:

- jóváhagyott kötelező requirementhez nincs tesztkapcsolat;
- hivatkozott requirement vagy acceptance scenario nem létezik;
- egy stabil tesztazonosító több helyen szerepel;
- egy deklarált tesztet a tesztfuttató nem fedezett fel;
- kötelező requirementet csak skipped, disabled, todo vagy nem elfogadott xfail teszt fed;
- a kötelező teszt nem futott le az aktuális execution során;
- a teszteredmény nem köthető az aktuális commithez és specifikációverzióhoz;
- strukturált metaadatot követelő projektben a kapcsolat csak fájlnévből vagy commitüzenetből származik;
- két adatforrás egymásnak ellentmondó kapcsolatot ad;
- a generált artifact sémahibás;
- a generált artifactot előállítás után módosították;
- a specifikáció commitja eltér a végrehajtásban jóváhagyott verziótól;
- a requirement coverage vagy verification coverage a projekt által elvárt szint alatt van.

## 8.12. Fallback és migrációs mód

Legacy projektben fokozatos bevezetés engedélyezhető:

```yaml
traceability_policy:
  mode: migration
  structured_metadata_required_for_new_tests: true
  filename_fallback_allowed_for_legacy_tests: true
  commit_message_only_allowed: false
  fallback_relationships_block_release: false
  fallback_relationships_emit_warning: true
```

Szigorú módban:

```yaml
traceability_policy:
  mode: strict
  structured_metadata_required_for_new_tests: true
  filename_fallback_allowed_for_legacy_tests: false
  commit_message_only_allowed: false
  fallback_relationships_block_release: true
```

A migrációs mód célja a strukturált metaadatokra való átállás. Nem válhat tartós kivétellé.

## 8.13. Kézi kivételek

Egyes nem funkcionális követelmények külön környezetben vagy manuális jóváhagyással bizonyíthatók. Ehhez szűk, sémavalidált exception fájl használható, de ez nem általános traceability mátrix.

```yaml
schemaVersion: "1.0"
feature: FEAT-023
exceptions:
  - requirement: NFR-001
    verification: external-performance-run
    evidenceRequired: performance-report.json
    approvedBy: performance-owner
    expiresAt: 2026-09-30
    reason: A követelmény külön terhelési környezetben ellenőrizhető.
```

A kivételnek:

- meg kell neveznie a requirementet;
- ellenőrizhető artifactot kell követelnie;
- jóváhagyóval kell rendelkeznie;
- indoklást kell tartalmaznia;
- lehetőség szerint lejárati idővel kell rendelkeznie;
- meg kell jelennie a generált traceability riportban.

## 8.14. Release előtti összegzés

```yaml
feature: FEAT-023
spec_version: 1
execution_id: RUN-FEAT-023-20260828-01
requirements_total: 7
requirements_covered: 7
requirements_executed: 7
requirements_passed: 7
uncovered_requirements: []
failed_requirements: []
unexecuted_requirements: []
orphan_tests: []
fallback_relationships: []
conflicts: []
status: PASS
```

A release blokkol, ha jóváhagyott kötelező requirement nincs strukturáltan teszthez kötve, a teszt nem futott le, vagy a bizonyítás nem kapcsolható az aktuális specifikációverzióhoz és commithez.

---

# 9. LLM-szerepkörök és jogosultságok

Egy szerepet több LLM is elláthat, és ugyanaz az LLM is használható több külön futásban. A szerepek logikai elkülönítése azonban kötelező.

## 9.1. Researcher

Feladata:

- külső és belső bizonyíték gyűjtése;
- opciók összehasonlítása;
- bizonytalanságok jelölése;
- források rögzítése.

Nem jogosult:

- követelmény jóváhagyására;
- implementáció módosítására;
- bizonyíték nélküli üzleti szabály létrehozására.

## 9.2. Spec Author vagy Behavior Analyst

Feladata:

- briefből tesztelhető specifikáció készítése;
- követelmények, invariánsok és scenario-k azonosítása;
- UI-, API- és állapotszerződés rögzítése;
- ambiguity és conflict elemzés;
- traceability terv készítése.

Nem jogosult:

- jóváhagyás nélküli kritikus üzleti döntésre;
- forráskód vagy teszt módosítására a specifikációs futásban.

## 9.3. Test Author

Feladata:

- jóváhagyott requirementből teszt készítése;
- happy, edge, error, security és concurrency esetek megfelelő lefedése;
- RED futás végrehajtása;
- teszt és requirement kapcsolatának rögzítése.

Nem jogosult:

- alkalmazáskód módosítására;
- követelmény lazítására;
- teszt olyan megváltoztatására, amely csak a hibás kódot teszi zölddé.

## 9.4. Implementer

Feladata:

- a jóváhagyott specifikáció és RED tesztek alapján minimális kód készítése;
- célzott tesztek futtatása;
- bukás esetén implementációs hiba javítása;
- projektkonvenciók betartása.

Nem jogosult:

- tesztek vagy specifikációk módosítására;
- scope önálló bővítésére;
- új dependency indokolás nélküli hozzáadására;
- tiltott fájl módosítására;
- tesztfuttatás kihagyására.

## 9.5. Reviewer

Feladata:

- specifikáció, teszt és implementáció megfelelésének ellenőrzése;
- hiányzó requirement-lefedettség keresése;
- nem tervezett scope és biztonsági probléma keresése;
- strukturált döntés készítése.

A reviewer alapértelmezetten read-only a termékfájlokra nézve. Saját jelentését írhatja, de a vizsgált kódot nem javíthatja ugyanabban a review-lépésben.

## 9.6. Runner

A runner determinisztikus végrehajtó, nem LLM-szerep.

Feladata:

- izolált környezet létrehozása;
- jogosultságok betartatása;
- parancsok futtatása;
- exit kód és strukturált eredmény rögzítése;
- diff, secret és provenance ellenőrzés;
- iterációs limitek kezelése;
- manifest generálása;
- PR létrehozása a policy szerint.

---

# 10. Egyszerű LLM-re optimalizált végrehajtási csomag

Az implementer ne kapja meg szükségtelenül a teljes projekt minden dokumentumát. A runner állítson össze szűk, célzott execution packetet.

```yaml
task_id: TASK-FEAT-023-02
feature_id: FEAT-023
objective:
  - REQ-003 megvalósítása
  - REQ-004 megvalósítása

acceptance_scenarios:
  - AC-004
  - AC-005

authoritative_inputs:
  - .specs/features/FEAT-023-cart-clear/specification.md
  - .specs/domain/invariants.md
  - .ai/project-profile.yaml

allowed_files:
  - src/cart/cart-service.ts
  - src/cart/cart-controller.ts

forbidden_files:
  - tests/**
  - .specs/**
  - migrations/**
  - .ai-execution/**

tests_to_satisfy:
  - TEST-INT-023-01
  - TEST-UNIT-023-01
  - TEST-E2E-023-04
  - TEST-E2E-023-05

commands:
  syntax:
    - npm run typecheck
  targeted:
    - npm test -- cart-clear
    - npx playwright test e2e/cart-clear.spec.ts
  regression:
    - npm test
    - npx playwright test
    - npm run lint
    - npm run typecheck
    - npm run build

constraints:
  - Ne módosíts tesztet vagy specifikációt.
  - Ne változtasd meg a publikus API-t.
  - Ne adj hozzá új dependencyt.
  - A diff legyen minimális.
  - Minden módosítás után futtasd a célzott teszteket.
  - Célzott siker után futtasd a teljes regressziót.

stop_conditions:
  - Specifikációs ellentmondás észlelése.
  - Tiltott fájl módosítása válna szükségessé.
  - Adatbázis-migráció válna szükségessé.
  - Biztonsági vagy jogosultsági döntés válna szükségessé.
  - Három sikertelen kódjavítási iteráció.
```

## 10.1. A végrehajtási csomag tervezési szabályai

Egy csomag alapértelmezetten:

- legfeljebb 1 és 3 közötti requirementet tartalmaz;
- egy koherens viselkedési részt fed le;
- kevés, előre felsorolt fájlt enged módosítani;
- egyértelmű targeted és regression parancsokat tartalmaz;
- nem igényel új termékdöntést;
- egy modell kontextusában átlátható marad.

A „legfeljebb három fájl” lehet hasznos alapértelmezett figyelmeztetési küszöb, de ne legyen univerzális merev szabály. Generált fájloknál, jól szervezett cross-cutting változásnál vagy szükséges adaptermódosításnál indokoltan túlléphető, kockázati review mellett.

---

# 11. A teljes végrehajtási ciklus

## 11.1. Előkészítés

1. Az igény vagy hiba rögzítése.
2. Feature brief és szükség esetén kutatás elkészítése.
3. Feature-specifikáció létrehozása.
4. Kockázati besorolás.
5. SPEC READY gate.
6. Kötelező emberi jóváhagyás.
7. Izolált Git worktree létrehozása.
8. Execution packet összeállítása.

## 11.2. Tesztírás és RED

9. A Test Author elkészíti a specifikációból következő teszteket.
10. A runner ellenőrzi a módosított fájlok jogosultságát.
11. Secret és policy scan fut.
12. A tesztek szintaktikai és gyűjthetőségi ellenőrzése fut.
13. A célzott tesztek ténylegesen lefutnak.
14. A runner vagy triage logika ellenőrzi, hogy a bukás a hiányzó funkció miatt történt.
15. A RED eredmény és a requirement-test kapcsolat rögzítésre kerül.

## 11.3. Implementáció és GREEN

16. Az Implementer minimális alkalmazáskódot készít.
17. Pre-test safety scan fut.
18. A célzott tesztek lefutnak.
19. Bukás esetén osztályozott triage történik.
20. Javítható implementációs hiba esetén kódjavítás készül.
21. A célzott tesztek minden javítás után újra lefutnak.
22. Célzott GREEN után lefut a teljes regresszió.
23. Lint, typecheck, build és további projektkapuk futnak.

## 11.4. Review és lezárás

24. A Runner az aktuális forrásokból újragenerálja a traceability gráfot, majd a traceability gate lefut.
25. Független reviewer megvizsgálja a specifikációt, teszteket, diffet és bizonyítékokat.
26. Reviewer elutasítás esetén a feladat triage-ba vagy emberi eszkalációba kerül.
27. Jóváhagyás után final safety gate fut.
28. A runner strukturált, sémavalidált manifestet készít.
29. A manifest lezárásra kerül.
30. PR nyílik, automatikus merge nélkül, ha a projektprofil másként nem rendelkezik.
31. Az emberi PR-döntés külön eseményként kerül naplózásra.

## 11.5. Release és evolúció

32. Push vagy PR smoke teszt fut.
33. Ütemezett teljes E2E futás működik.
34. Production canary ellenőrzi a kritikus útvonalakat.
35. Tartós hiba strukturált backlog- vagy hibabejegyzést hoz létre.
36. A javítás új vagy módosított specifikáción keresztül indul.

---

# 12. Triage és javítási hurok

## 12.1. Hibakategóriák

### IMPLEMENTATION_ERROR

A kód eltér a jóváhagyott specifikációtól vagy nem teljesíti a helyes tesztet.

Művelet:

- Implementer javítja az engedélyezett forrásfájlokat;
- `patch_iterations` értéke eggyel nő;
- safety scan és célzott teszt újra lefut.

### TEST_ERROR

A teszt hibás, szintaktikailag érvénytelen, instabil vagy eltér a specifikációtól.

Művelet:

- Test Author javítja a tesztet;
- `patch_iterations` értéke eggyel nő;
- RED validációt újra végre kell hajtani.

### SPEC_CONFLICT

A követelmény nem egyértelmű, hiányos vagy más jóváhagyott követelménnyel ellentmond.

Művelet:

- automatikus fejlesztés leáll;
- a worktree és bizonyítékok megmaradnak;
- emberi követelménytisztázás szükséges.

### ENVIRONMENT_ERROR

Átmeneti környezeti hiba, például process timeout, zárolt erőforrás vagy ismert infrastruktúrahiba.

Művelet:

- runner legfeljebb a konfigurált számban újrapróbálja;
- az újrapróbálás nem számít kódjavítási iterációnak;
- tartós hiba esetén eszkaláció történik.

### POLICY_VIOLATION

Tiltott fájlmódosítás, credential, jogosulatlan művelet vagy provenance-hiba.

Művelet:

- azonnali leállítás;
- normál automatikus javítás nem engedélyezett;
- biztonsági vagy emberi review szükséges.

## 12.2. Prioritási szabály

A triage mindig ebben a sorrendben vizsgál:

1. Mit ír elő a jóváhagyott specifikáció?
2. A teszt pontosan ezt ellenőrzi-e?
3. A kód teljesíti-e a helyes tesztet?
4. A környezet hitelesen végrehajtotta-e az ellenőrzést?

## 12.3. Javítási limitek

Ajánlott alapértékek:

```yaml
repair_policy:
  max_patch_iterations: 5
  max_environment_retries: 1
  max_duration_minutes: 20
  max_cost_usd: null
  on_limit_reached: preserve_worktree_and_escalate
  on_policy_violation: stop_and_escalate
```

Egyszerűbb LLM execution packet esetén szigorúbb, például három javítási iteráció is használható. A limit kimerülésekor a rendszer ne kezdjen korlátlan próbálkozásba.

---

# 13. Projektprofil

A közös módszertani mag technológiafüggetlen. A konkrét projekt szabályai külön profilban legyenek.

## 13.1. A projektprofil tartalma

- stack és támogatott verziók;
- mappastruktúra;
- fájlelnevezések;
- kódolási konvenciók;
- API-válaszformátum;
- UI-szelektor szabályok;
- biztonsági követelmények;
- tesztparancsok;
- lint, typecheck és build parancsok;
- külső szolgáltatások és mockolási politika;
- minőségi kapuk;
- tiltott fájlok és műveletek;
- Git- és PR-szabályok;
- dokumentációs követelmények.

## 13.2. Projektprofil minta

```yaml
project:
  name: example-app
  languages:
    - python: "3.11+"
    - typescript: "5.x"

paths:
  backend: src/**
  frontend: frontend/**
  unit_tests: tests/unit/**
  integration_tests: tests/integration/**
  api_tests: tests/e2e/**
  ui_tests: frontend/e2e/**
  specs: .specs/**

coding_rules:
  type_hints_required: true
  public_docstrings_required: true
  max_file_lines_warning: 200
  max_file_lines_block: 400
  dependency_injection_preferred: true

quality_commands:
  syntax:
    - python -m compileall -q src tests
  targeted: []
  regression:
    - pytest -q
  lint:
    - ruff check src tests
  typecheck:
    - mypy src tests --ignore-missing-imports
  build: []

security:
  input_validation_required: true
  secret_scan_required: true
  xss_prevention_required: true

traceability_policy:
  mode: strict
  structured_metadata_required_for_new_tests: true
  filename_fallback_allowed_for_legacy_tests: false
  commit_message_only_allowed: false
  generate_at_final_safety_gate: true

pull_request:
  auto_create: true
  auto_merge: false
```

---

# 14. Ajánlott repository-szerkezet

```text
project-root/
├── .specs/
│   ├── templates/
│   │   ├── feature-spec.md
│   │   ├── bug-spec.md
│   │   └── change-spec.md
│   ├── domain/
│   │   ├── glossary.md
│   │   ├── invariants.md
│   │   └── entities/
│   └── features/
│       └── FEAT-023-cart-clear/
│           ├── specification.md
│           └── prototype.md
├── src/
├── frontend/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── research/
│   ├── decisions/
│   └── operations/
├── .ai/
│   ├── project-profile.yaml
│   ├── permissions.yaml
│   ├── quality-gates.yaml
│   └── risk-policy.yaml
└── .ai-execution/
    ├── runs/
    ├── evidence/
    ├── reviews/
    ├── manifests/
    └── pr-events/
```

A mappák neve projektenként eltérhet. A lényeg a szerepek és artefaktumok logikai szétválasztása.

---

# 15. Jogosultsági modell

## 15.1. Alapelv

A default hozzáférés `deny`. Az engedélyezett fájlokat szerepkörönként explicit módon kell felsorolni. A runner a fájlrendszer-műveleteknél és a végső Git diff alapján is ellenőriz.

## 15.2. Minta

```yaml
roles:
  spec_author:
    allow:
      - .specs/**
    deny:
      - src/**
      - tests/**
      - .ai-execution/**

  test_author:
    allow:
      - tests/**
      - frontend/e2e/**
    deny:
      - src/**
      - .specs/**
      - .ai-execution/**

  implementer:
    allow:
      - src/**
      - frontend/src/**
    deny:
      - tests/**
      - frontend/e2e/**
      - .specs/**
      - .ai-execution/**

  reviewer:
    allow:
      - .ai-execution/reviews/**
    deny:
      - src/**
      - tests/**
      - .specs/**
      - .ai-execution/manifests/**
      - .ai-execution/pr-events/**

evaluation:
  default: deny
  resolve_symlinks: true
  disallow_parent_traversal: true
  on_equal_specificity: deny
```

## 15.3. Provenance

A final safety gate ellenőrizze, hogy:

- minden módosított fájlhoz hozzárendelhető a jogosult szerepkör;
- tesztet csak Test Author módosított;
- termékkódot csak Implementer módosított;
- specifikációt csak Spec Author vagy jóváhagyott ember módosított;
- manifestet és PR-eseményt csak a runner írt;
- ismeretlen eredetű módosítás nincs a diffben.

---

# 16. Determinisztikus minőségi kapuk

## 16.1. Specifikációs kapuk

- séma és front matter validáció;
- kötelező szakaszok ellenőrzése;
- stabil requirement ID-k;
- ambiguity scan;
- contradiction scan;
- requirement-test terv teljessége;
- human gate állapot.

## 16.2. Pre-test safety gate

Minden fájlmódosítás után, tesztfuttatás előtt:

- allow/deny ellenőrzés;
- parent traversal és symlink ellenőrzés;
- secret scan;
- tiltott fájlok ellenőrzése;
- váratlan nagy diff jelzése;
- dependency-változás ellenőrzése.

## 16.3. Célzott GREEN gate

- minden kapcsolódó új teszt lefutott;
- minden kapcsolódó teszt zöld;
- nincs kihagyott vagy véletlenül letiltott teszt;
- a tesztjelentés strukturáltan elérhető.

## 16.4. Teljes regressziós gate

A célzott tesztek sikere után kötelezően lefut:

- teljes unit suite;
- contract és integration suite;
- projekt által előírt E2E suite;
- lint;
- typecheck;
- build vagy compile;
- szükséges security scan.

A teljes regresszió futtatását nem szabad pusztán summary-ban előírni. A runnernek ténylegesen végre kell hajtania és az exit kódokat rögzítenie.

## 16.5. Final safety gate

PR előtt:

- teljes branch diff scan;
- provenance ellenőrzés;
- secret scan;
- Runner által generált requirement-test traceability;
- minden kötelező command hiteles exit kódja;
- reviewer `APPROVED` státusza;
- szükséges artifactok megléte;
- manifest séma-validáció;
- worktree tisztaságának vagy ismert állapotának ellenőrzése.

---

# 17. Reviewer protokoll

## 17.1. Reviewer bemenete

- jóváhagyott specifikáció;
- domain-invariánsok;
- Runner által generált traceability gráf;
- Git diff;
- célzott és teljes teszteredmények;
- lint, typecheck és build eredmény;
- safety scan eredmény;
- execution packet és iterációs napló.

## 17.2. Reviewer ellenőrzőlista

A reviewer ellenőrzi:

- pontosan a specifikált scope valósult-e meg;
- minden kötelező requirement implementált-e;
- minden invariáns tesztelt-e;
- a tesztek valóban a specifikációt ellenőrzik-e;
- nincs-e tesztgyengítés;
- nincs-e indokolatlan architekturális bonyolítás;
- nincs-e nem engedélyezett dependency;
- nincs-e biztonsági vagy adatkonzisztencia-probléma;
- a hibakezelés és edge case-ek megfelelőek-e;
- a dokumentáció és traceability naprakész-e;
- a futtatási bizonyíték hiteles-e.

## 17.3. Reviewer kimenet

```yaml
feature: FEAT-023
status: APPROVED
requirement_compliance: PASS
test_completeness: PASS
scope_compliance: PASS
security_review: PASS
findings: []
required_actions: []
reviewed_at: 2026-08-28T10:15:00Z
```

Lehetséges státuszok:

- `APPROVED`;
- `REJECTED_FIXABLE`;
- `REJECTED_SCOPE`;
- `ESCALATE_SPEC`;
- `ESCALATE_SECURITY`.

---

# 18. Végrehajtási manifest és audit

## 18.1. A manifest szerepe

A manifest azt bizonyítja, hogy egy konkrét specifikációverzióból, konkrét kódállapot mellett milyen ellenőrzések futottak és milyen eredménnyel.

A manifestet kizárólag a runner generálja. A `PASSED` azt jelenti, hogy a technikai kapuk zöldek és a PR létrejött. Nem jelenti automatikusan, hogy a PR merge-elve lett.

## 18.2. Minta

```json
{
  "executionId": "RUN-FEAT-023-20260828-01",
  "timestamp": "2026-08-28T10:30:00Z",
  "targetSpec": "FEAT-023@v1",
  "baseCommit": "abc1234",
  "resultCommit": "def5678",
  "branch": "ai-feature/FEAT-023",
  "executionStatus": "PASSED",
  "iterations": 2,
  "changedFiles": 3,
  "failedGate": null,
  "verification": {
    "requirementsTotal": 7,
    "requirementsCovered": 7,
    "requirementsPassed": 7,
    "targetedPassCount": 9,
    "regressionPassCount": 182,
    "lintClean": true,
    "typecheckClean": true,
    "buildClean": true,
    "secretScanClean": true,
    "provenanceClean": true
  },
  "artifacts": [
    ".ai-execution/evidence/RUN-FEAT-023-20260828-01/",
    ".ai-execution/reviews/FEAT-023-review.md"
  ],
  "pullRequestUrl": "https://example.invalid/pull/42"
}
```

## 18.3. PR-döntési esemény

Az emberi merge vagy elutasítás ne írja felül a lezárt manifestet. Külön eseményként kerüljön rögzítésre.

```json
{
  "executionId": "RUN-FEAT-023-20260828-01",
  "pullRequestStatus": "MERGED",
  "decidedAt": "2026-08-28T11:00:00Z",
  "decidedBy": "lead-reviewer",
  "mergeCommit": "987zyx6",
  "comments": "A specifikációval és a bizonyítékokkal összhangban."
}
```

---

# 19. Folyamatos E2E és üzemeltetési visszacsatolás

## 19.1. Négy ellenőrzési réteg

### Lokális targeted watch

Fejlesztés közben gyors visszajelzés az aktuális requirementekhez tartozó tesztekből.

### Push vagy PR smoke

Gyors, blokkoló ellenőrzés a kritikus útvonalakra. Célja a gyors regresszióészlelés.

### Nightly full

Teljesebb E2E, accessibility, mobilnézet, trace és integrációs ellenőrzés ütemezetten.

### Production canary

Éles környezetben biztonságosan végrehajtható kritikus smoke és külső függőség-ellenőrzés.

## 19.2. Canary hiba feldolgozása

```text
canary failure
    -> automatikus reprodukciós kísérlet
    -> környezeti hiba kizárása
    -> érintett feature és requirement azonosítása
    -> bizonyíték csatolása
    -> hiba vagy specifikációs javaslat létrehozása
    -> prioritás és kockázati besorolás
    -> normál SPEC -> BUILD -> VERIFY ciklus
```

Az üzemeltetési rendszer nem írja át automatikusan a jóváhagyott követelményt.

---

# 20. Definition of Ready és Definition of Done

## 20.1. Definition of Ready

Egy feature fejlesztésre kész, ha:

- a probléma és kívánt eredmény érthető;
- scope és non-scope rögzített;
- a követelmények azonosítottak és tesztelhetők;
- a kapcsolódó invariánsok ismertek;
- a GUI- vagy API-szerződés megfelelően definiált;
- a releváns állapotok és átmenetek megvannak;
- a happy, edge és error scenario-k megvannak;
- a tesztleképezés teljes;
- a kockázati besorolás elkészült;
- a nyitott blokkoló kérdések száma nulla;
- a szükséges prototípus és jóváhagyás rendelkezésre áll;
- a SPEC READY gate zöld.

## 20.2. Definition of Done

Egy feature kész, ha:

- a jóváhagyott specifikáció minden kötelező requirementje implementált;
- a requirement coverage 100 százalék;
- a RED bizonyíték rendelkezésre áll;
- a célzott tesztek ténylegesen lefutottak és zöldek;
- a teljes regresszió ténylegesen lefutott és zöld;
- lint, typecheck és build zöld;
- nincs policy- vagy provenance-hiba;
- a reviewer jóváhagyta;
- a final safety gate zöld;
- a manifest érvényes és lezárt;
- a PR létrejött;
- a dokumentáció és changelog szükség szerint frissült;
- a release utáni releváns ellenőrzések konfigurálva vannak.

---

# 21. Anti-minták

## 21.1. Hosszú prompt specifikáció helyett

Hiba: többoldalas szabad szöveg stabil requirement ID-k, scope és tesztleképezés nélkül.

Következmény: az LLM eltérően értelmezi, elfelejt részleteket, vagy saját döntéseket hoz.

Helyes megoldás: strukturált feature-specifikáció és kis execution packet.

## 21.2. A teszt módosítása csak azért, hogy zöld legyen

Hiba: bukó teszt esetén az implementer lazítja az assertiont.

Helyes megoldás: a triage előbb a specifikációhoz méri a tesztet. A Test Author és az Implementer jogosultsága különválik.

## 21.3. Minden teszt E2E

Hiba: lassú, instabil és drága suite jön létre.

Helyes megoldás: legalacsonyabb megfelelő tesztszint, plusz E2E a kritikus felhasználói utakra.

## 21.4. User story-k mesterséges szaporítása

Hiba: happy, edge, error és GUI külön dokumentumként ismétli ugyanazt a feature-t.

Helyes megoldás: egy koherens feature-specifikáció több requirementtel és scenario-val. Csak önállóan szállítható eredmény esetén készüljön külön specifikáció.

## 21.5. Univerzális prototípus-gate

Hiba: typo, backend refaktor vagy egyszerű hibajavítás is emberi UX-jóváhagyásra vár.

Helyes megoldás: kockázatalapú prototípus-szabály.

## 21.6. LLM-összefoglaló bizonyítékként

Hiba: „minden teszt sikeres” állítás exit kód és riport nélkül.

Helyes megoldás: runner által futtatott parancsok, strukturált tesztjelentés és lezárt manifest.

## 21.7. Korlátlan autonóm javítás

Hiba: az LLM sok iteráción keresztül egyre nagyobb diffet készít.

Helyes megoldás: patch-, idő- és költséglimit, majd worktree-megőrzés és eszkaláció.

## 21.8. Projektszabályok keverése a közös maggal

Hiba: a módszertan egyetlen konkrét stackhez kötődik.

Helyes megoldás: technológiafüggetlen core és külön projektprofil.

---

# 22. Fokozatos bevezetés

## 22.1. Első szint: Pragmatic Core

Kötelező elemek:

- feature-specifikációs sablon;
- stabil requirement ID-k;
- acceptance scenario-k;
- Runner által generált requirement-test traceability;
- Test Author és Implementer szétválasztása;
- célzott és teljes regresszió tényleges futtatása;
- egyszerű triage;
- javítási limit;
- emberi PR-review.

Ez már jelentősen javítja egy egyszerűbb LLM megbízhatóságát.

## 22.2. Második szint: Enforced Execution

További elemek:

- izolált worktree;
- allow/deny fájljogosultság;
- pre-test safety scan;
- strukturált execution packet;
- automatikus traceability collector és validator;
- reviewer jelentés;
- manifest és evidence mappa.

## 22.3. Harmadik szint: Continuous Verification

További elemek:

- PR smoke;
- nightly full E2E;
- production canary;
- automatikus runtime-feature kapcsolat;
- specifikációs drift-javaslat;
- központi dashboard és trendek.

## 22.4. Negyedik szint: Skálázott optimalizáció

Csak igazolt igény esetén:

- gépi dependency graph;
- intelligens regressziószűkítés;
- policy engine;
- költség- és modellrouting;
- formálisabb szerződések;
- cross-repository requirement graph.

A magasabb szintek nem előfeltételei a módszertan használatának. Először a specifikáció és a tesztbizonyíték minőségét kell stabilizálni.

---

# 23. Minimális működő rendszer

Ha a rendszerből csak a legfontosabb részek vezethetők be, az alábbi minimum szükséges:

1. egy feature egy strukturált specifikációt kap;
2. minden requirement stabil ID-val rendelkezik;
3. minden requirement legalább egy teszthez kapcsolódik;
4. a teszt a kód előtt készül, és RED állapota ténylegesen ellenőrzött;
5. az implementer nem módosíthat tesztet vagy specifikációt;
6. minden kódváltozás után célzott teszt fut;
7. célzott siker után teljes regresszió, lint, typecheck és build fut;
8. a futtatási eredményt gép rögzíti;
9. bukás esetén egyszerű triage történik;
10. a javítási ciklus limitált;
11. kritikus bizonytalanság esetén emberi stop-gate működik;
12. PR előtt független review történik.

Ez a tizenkét pont adja a módszertan legfontosabb értékét.

---

# 24. Záró összefoglalás

A rendszer központi szerződése:

```text
A jóváhagyott követelmény meghatározza a kívánt viselkedést.
A teszt futtatható módon bizonyítja a követelményt.
Az implementáció kizárólag a teszt és a specifikáció teljesítésére készül.
A determinisztikus runner igazolja az eredményt.
Az ember ott dönt, ahol üzleti, biztonsági vagy visszafordíthatatlan kockázat van.
```

Az egyszerűbb LLM megbízhatóságának kulcsa nem egy még hosszabb általános prompt, hanem:

- a pontos és tesztelhető specifikáció;
- a kis végrehajtási scope;
- a zárt fájljogosultság;
- az egyértelmű success és stop condition;
- a követelmény és teszt közötti teljes traceability;
- a célzott és teljes regresszió valós futtatása;
- a determinisztikus ellenőrzés;
- a korlátozott autonómia és világos eszkaláció.

Így a kreatív döntések a specifikációs és terméktervezési szakaszban maradnak, az implementáció pedig egy jól definiált, mérhető és auditálható végrehajtási feladattá válik.
