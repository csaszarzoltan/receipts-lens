## BRIEF-047: Könyvelési időszak lezárása

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-047  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

Egy hónap vagy adózási időszak lezárása előtt több forrásból kell ellenőrizni a hiányokat, és formális lezárás nélkül későbbi módosítások észrevétlenül megváltoztathatják a korábbi riportokat.

## Célcsoport és kontextus

Háztartási tulajdonos, pénzügyi felelős vagy könyvelő, aki ellenőrzött időszakot zár le és bizonyítékot készít.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-047-01:** Könyvelőként szeretném kiválasztani a lezárandó időszakot és látni annak aktuális készültségét, hogy tudjam, elkezdhető-e a zárás.
- **US-047-02:** Könyvelőként szeretnék automatikus előellenőrzést futtatni a hiányzó nyugtákra, párosítatlan tranzakciókra, bizonytalan adatokra, duplikátumokra, visszatérítésekre és hibás felosztásokra, hogy ne maradjon rejtett probléma.
- **US-047-03:** Könyvelőként szeretném a blokkoló hibákat és figyelmeztetéseket forrásukkal és javítási útvonalukkal látni, hogy célzottan elhárítsam őket.
- **US-047-04:** Jogosult felhasználóként szeretném dokumentált indokkal elfogadni a megengedett kivételeket, hogy a lezárás ne akadjon el kezelhető eltérés miatt.
- **US-047-05:** Könyvelőként szeretném lezárás előtt az összesítések, nyitó és záró egyenlegek, importok és exportok előnézetét ellenőrizni, hogy tudatos döntést hozzak.
- **US-047-06:** Könyvelőként szeretném külön megerősítéssel lezárni az időszakot, hogy a művelet ne történjen véletlenül.
- **US-047-07:** Felhasználóként szeretném, hogy lezárt időszak adatait a rendszer alapértelmezetten védje a csendes módosítástól, hogy a korábbi eredmény reprodukálható maradjon.
- **US-047-08:** Jogosult felhasználóként szeretnék szabályozott újranyitást indoklással és megfelelő jóváhagyással, hogy szükséges korrekció elvégezhető legyen.
- **US-047-09:** Könyvelőként szeretnék lezárási bizonyítékot kapni az időszakról, ellenőrzésekről, kivételekről, felelősökről és forrásverziókról, hogy a zárás auditálható legyen.
- **US-047-10:** Felhasználóként szeretném összehasonlítani az újranyitás előtti és utáni eredményt, majd új verzióként lezárni, hogy a változás története megmaradjon.

## Scope

- Havi, negyedéves vagy megadott adózási időszak zárási munkafolyamata.
- Előellenőrzések, blokkolók, figyelmeztetések, kivételek és jóváhagyás.
- Lezárt adatok módosításvédelme, szabályozott újranyitás és verziózott újrazárás.
- Letölthető vagy archiválható lezárási bizonyíték és reprodukálhatóság.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Jogszabály szerinti hivatalos könyvvizsgálat vagy adóbevallás benyújtása.
- Adatmegőrzési kötelezettség országonkénti jogi meghatározása.
- A lezárt időszak forrásadatainak visszafordíthatatlan törlése.
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
