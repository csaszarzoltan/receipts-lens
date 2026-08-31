## BRIEF-040: Garanciák és visszaküldési határidők

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-040  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A vásárláshoz kapcsolódó visszaküldési és garanciális határidők könnyen lejárnak, ha a szükséges nyugta, termékadat és teendő nincs egy helyen követve.

## Célcsoport és kontextus

Háztartási felhasználó, aki tartós terméket vásárolt, visszaküldést vagy garanciális ügyintézést tervez.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-040-01:** Felhasználóként szeretném egy nyugta tételét garanciális vagy visszaküldhető termékként megjelölni, hogy a fontos határidők követhetők legyenek.
- **US-040-02:** Felhasználóként szeretném a vásárlási dátumból javasolt visszaküldési és garanciális határidőt látni, hogy gyorsabban rögzítsem az adatot.
- **US-040-03:** Felhasználóként szeretném a javasolt dátumot és feltételeket felülbírálni, hogy a kereskedő tényleges szabályai érvényesüljenek.
- **US-040-04:** Felhasználóként szeretnék terméknevet, sorozatszámot, kereskedői hivatkozást és kapcsolódó dokumentumokat rögzíteni, hogy ügyintézéskor minden bizonyíték elérhető legyen.
- **US-040-05:** Felhasználóként szeretnék a határidő előtt több, szabályozható emlékeztetőt kapni, hogy legyen időm dönteni és intézkedni.
- **US-040-06:** Felhasználóként szeretném egy közelgő határidőből megnyitni a nyugtát, a terméket és a kapcsolódó teendőt, hogy ne kelljen külön keresnem.
- **US-040-07:** Felhasználóként szeretném a visszaküldést vagy garanciális ügyet elindított, elküldött, elfogadott, elutasított vagy lezárt állapotban követni, hogy lássam a folyamat helyzetét.
- **US-040-08:** Felhasználóként szeretném a visszatérítést a kapcsolódó ügyhöz és eredeti vásárláshoz kötni, hogy a pénzügyi eredmény is követhető legyen.
- **US-040-09:** Felhasználóként szeretném megkülönböztetni a gyártói, kereskedői és önkéntes garanciát, hogy ne keverjem össze az eltérő feltételeket.

## Scope

- Nyugtatételhez kapcsolódó visszaküldési és garanciális nyilvántartás.
- Javasolt, kézzel javítható dátumok és feltételek, kapcsolódó dokumentumok.
- Határidőnézet, emlékeztetők és ügyállapotok.
- Kapcsolat a nyugtával, termékkel, feladattal és visszatérítéssel.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Jogi garanciafeltételek automatikus meghatározása vagy jogi tanácsadás.
- Kereskedőnél történő automatikus reklamációbenyújtás.
- Készlet- vagy eszközmenedzsment teljes funkcionalitása.
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
