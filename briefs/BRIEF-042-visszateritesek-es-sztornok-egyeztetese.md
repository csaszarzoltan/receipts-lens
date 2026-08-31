## BRIEF-042: Visszatérítések és sztornók egyeztetése

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-042  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A visszatérítések, részleges jóváírások és sztornók gyakran más dátummal vagy leírással jelennek meg, ezért könnyen leválhatnak az eredeti vásárlásról és hibás nettó költést eredményezhetnek.

## Célcsoport és kontextus

Háztartási felhasználó vagy könyvelő, aki jóváírásokat az eredeti vásárlással és bizonylatokkal egyeztet.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-042-01:** Felhasználóként szeretném, hogy a rendszer felismerje a lehetséges visszatérítési és sztornó tranzakciókat, hogy ne kelljen minden jóváírást kézzel keresnem.
- **US-042-02:** Felhasználóként szeretném az összeg, pénznem, kereskedő, dátum és korábbi kapcsolat alapján rangsorolt eredeti vásárlásokat látni, hogy megtaláljam a megfelelő forrást.
- **US-042-03:** Felhasználóként szeretném látni a javaslat indokát és bizonyosságát, hogy a jóváírás ne kapcsolódjon észrevétlenül rossz vásárláshoz.
- **US-042-04:** Felhasználóként szeretnék teljes vagy részleges visszatérítést egy eredeti nyugtához, annak tételeihez és terheléséhez kapcsolni, hogy a nettó összeg helyesen számolódjon.
- **US-042-05:** Felhasználóként szeretném több részletben érkező visszatérítéseket külön követni, hogy a még hiányzó összeg látható maradjon.
- **US-042-06:** Felhasználóként szeretném kezelni, ha a visszatérítés eltérő fizetési eszközre vagy pénznemben érkezik, hogy a különbség ne tűnjön hibának.
- **US-042-07:** Felhasználóként szeretném megkülönböztetni a függő, teljesült, meghiúsult és visszavont jóváírást, hogy csak a tényleges pénzmozgás csökkentse a költést.
- **US-042-08:** Felhasználóként szeretném a hibás kapcsolatot felbontani vagy újra hozzárendelni, hogy a javítás auditálható legyen.
- **US-042-09:** Könyvelőként szeretném látni az eredeti bruttó összeget, a kapcsolt visszatérítéseket és a fennmaradó nettó összeget, hogy az export és zárás ellenőrizhető legyen.

## Scope

- Jóváírások és sztornók felismerése, javasolt és kézi kapcsolat az eredeti vásárlással.
- Teljes, részleges, többlépcsős és eltérő pénznemű visszatérítések.
- Állapotkövetés, nettó összeg, eltérés és fennmaradó követelés.
- Kapcsolatjavítás és auditálható előzmény.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Visszatérítés kezdeményezése a kereskedőnél vagy banknál.
- Chargeback jogi vagy banki folyamatának automatizálása.
- Jövőbeni jóváírás biztos pénzmozgásként való előre könyvelése.
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
