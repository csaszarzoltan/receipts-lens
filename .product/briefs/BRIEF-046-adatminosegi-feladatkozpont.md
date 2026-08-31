## BRIEF-046: Adatminőségi feladatközpont

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-046  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A hiányos, ellentmondásos és bizonytalan adatok több külön nézetben jelennek meg, ezért a felhasználó nem látja egységesen, mit kell javítani és mi blokkol egy fontos folyamatot.

## Célcsoport és kontextus

Háztartási felhasználó, ellenőrző vagy könyvelő, aki nyugták, tranzakciók és besorolások minőségét javítja.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-046-01:** Felhasználóként szeretném egy közös javítási listában látni a nyugták, tranzakciók, párosítások, kategóriák és kapcsolódó dokumentumok adatminőségi problémáit, hogy ne kelljen több helyen keresnem.
- **US-046-02:** Felhasználóként szeretném probléma típusa, súlyosság, határidő, összeg, felelős, forrás és blokkolt folyamat szerint szűrni és rendezni a feladatokat, hogy megfelelő sorrendben dolgozzak.
- **US-046-03:** Felhasználóként szeretném minden feladatnál látni a probléma érthető magyarázatát, bizonyosságát és hatását, hogy tudjam, miért szükséges a javítás.
- **US-046-04:** Felhasználóként szeretnék a feladatból közvetlenül a megfelelő javítófelületre jutni, majd a mentés után a következő releváns feladattal folytatni, hogy gyors legyen a feldolgozás.
- **US-046-05:** Felhasználóként szeretném a problémát felelőshöz rendelni, megjegyzéssel továbbadni vagy későbbre halasztani, hogy a csapatmunka követhető legyen.
- **US-046-06:** Felhasználóként szeretnék több hasonló, biztonságosan javítható tételen közös műveletet végezni előnézettel és visszavonási lehetőséggel, hogy csökkenjen a kézi munka.
- **US-046-07:** Felhasználóként szeretném egy tévesen jelzett problémát indoklással kivételként lezárni, hogy ne térjen vissza indokolatlanul.
- **US-046-08:** Felhasználóként szeretném, hogy a forrásadat változása automatikusan újraértékelje és szükség esetén megnyissa vagy lezárja a feladatot, hogy a lista ne avuljon el.
- **US-046-09:** Könyvelőként szeretném látni a hátralék alakulását, az öregedő és zárást blokkoló tételeket, hogy felmérjem a készültséget.
- **US-046-10:** Felhasználóként szeretném, hogy jogosultság hiányában csak az engedélyezett adatot és a megfelelő továbbítási lehetőséget lássam, hogy az érzékeny információ ne szivárogjon ki.

## Scope

- Egységes adatminőségi inbox nyugtákhoz, tranzakciókhoz, párosításokhoz és besorolásokhoz.
- Prioritás, felelős, hatás, szűrés, tömeges javítás, kivétel és újraértékelés.
- Közvetlen javítási útvonal és folyamatos következő feladat.
- Minőségi trend és zárást blokkoló hátralék áttekintése.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Általános célú kanban vagy projektmenedzsment rendszer.
- Bizonytalan adat automatikus véglegesítése megfelelő szabály vagy felhasználói kontroll nélkül.
- A forrásrendszerek minden szakmai hibájának automatikus javítása.
- Belső komponensszerkezet, konkrét technológia, adatbázisséma vagy fejlesztési feladatlista; ezek a későbbi feature-specifikáció és ADR hatáskörébe tartoznak.

## Érintett rendszerek

- A nyugta-, tranzakció- és háztartási munkaterület kapcsolódó felületei.
- Az alkalmazási, tartós adatkezelési, keresési és auditálási réteg.
- Az értesítési, feldolgozási és integrációs szolgáltatások, ha a történet ezeket igényli.

## Kapcsolódó meglévő BRIEF-ek

- BRIEF-006: Nyugta feltöltése és feldolgozási sor.
- BRIEF-007: AI-alapú nyugtafelismerés és bizonytalanság.
- BRIEF-009: Nyugtaellenőrzés és javítás.
- BRIEF-016: Háztartási együttműködés és családi postafiók.
- BRIEF-019: Szinkronizálás és egyeztetés.
- BRIEF-020: Jóváhagyások és kontrollált változtatások.
- BRIEF-026: Értesítések és állapotüzenetek.
- BRIEF-027: Hozzáférhetőség és reszponzív navigáció.
- A kapcsolat nem jelent funkcionális átfedést: a jelen BRIEF saját felhasználói eredményét és életciklusát határozza meg.

## Bizonytalanságok

- A pontos üzleti küszöbök, határidők, alapértelmezések és jogosultsági mátrix termékdöntést igényelnek.
- A támogatott külső források, eszközök, csatornák és országfüggő szabályok köre külön kutatást vagy ADR-t igényelhet.
- A javaslatok bizonyossági szintjeit, magyarázatát, felülbírálását és tanulási hatását a SPEC-ben mérhető szerződésként kell rögzíteni.
- A SPEC-nek külön kell választania a blokkoló hibát, a felhasználó által elfogadható figyelmeztetést és az információs jelzést.
- A kötelező követelményekhez Given/When/Then acceptance scenario, RED tesztbizonyíték, célzott teszt és teljes regresszió szükséges a projekt módszertana szerint.
