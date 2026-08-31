## BRIEF-045: Offline nyugtarögzítés és későbbi szinkronizálás

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-045  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

Gyenge vagy hiányzó internetkapcsolat esetén a nyugtarögzítés megszakadhat, a kép vagy a javítás elveszhet, és az ismételt feltöltés duplikátumot hozhat létre.

## Célcsoport és kontextus

Mobilos felhasználó, aki üzletben, utazás közben vagy instabil hálózaton rögzít nyugtát.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-045-01:** Felhasználóként szeretnék kapcsolat nélkül is új nyugtát fényképezni vagy fájlból hozzáadni, hogy a rögzítés ne függjön a hálózattól.
- **US-045-02:** Felhasználóként szeretném a minimális metaadatokat és megjegyzést offline piszkozatként menteni, hogy később folytathassam.
- **US-045-03:** Felhasználóként szeretném egyértelműen látni, mely elemek csak az eszközön vannak, melyek várnak feltöltésre, és melyek szinkronizálódtak, hogy ismerjem az adat helyzetét.
- **US-045-04:** Felhasználóként szeretném, hogy a kapcsolat visszatérésekor a rendszer biztonságosan és ismételhetően folytassa a feltöltést, hogy ne kelljen újrakezdenem.
- **US-045-05:** Felhasználóként szeretném szüneteltetni vagy csak Wi-Fi-re korlátozni a képfeltöltést, hogy kontrolláljam a mobiladat-használatot.
- **US-045-06:** Felhasználóként szeretném, hogy háttérbe helyezés, alkalmazásbezárás vagy eszköz-újraindítás után a piszkozat és előrehaladás megmaradjon, hogy ne vesszen el munka.
- **US-045-07:** Felhasználóként szeretném a sikertelen elemeket külön újrapróbálni, hogy egyetlen hiba ne blokkolja az egész sort.
- **US-045-08:** Felhasználóként szeretném, hogy ugyanannak az offline nyugtának az ismételt küldése ne hozzon létre duplikátumot, hogy az összesítések helyesek maradjanak.
- **US-045-09:** Felhasználóként szeretném a helyi és szerveroldali módosítás ütközésekor mindkét változatot érthetően összehasonlítani és választani, hogy ne történjen csendes felülírás.
- **US-045-10:** Felhasználóként szeretném a még fel nem töltött helyi adatokat eszközcsere, kijelentkezés vagy törlés előtt figyelmeztetéssel és biztonságos döntési lehetőséggel kezelni, hogy elkerüljem az adatvesztést.

## Scope

- Offline kép- és piszkozat-rögzítés támogatott mobil környezetben.
- Tartós helyi várólista, látható szinkronállapot, folytatható és idempotens feltöltés.
- Hálózati szabályok, háttérbe helyezés, részleges hiba és újrapróbálás.
- Konfliktusfeloldás és duplikációvédelem felhasználói kontrollal.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Teljes alkalmazás minden funkciójának offline elérhetősége.
- Korlátlan idejű vagy garantált helyi tárolás az eszköz korlátaitól függetlenül.
- Felhőszinkron nélkül elveszett vagy eltávolított eszköz adatainak visszaállítási garanciája.
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
