## BRIEF-044: Kiadási célok és megtakarítási lehetőségek

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-044  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A költési keret önmagában csak eltérést jelez, de nem segít konkrétan megérteni, mely szokások változtatásával érhető el a cél, és az automatikus javaslatok felhasználói kontroll nélkül félrevezetők lehetnek.

## Célcsoport és kontextus

Háztartási tulajdonos vagy tag, aki kategóriánként kiadási célt követ és megvalósítható megtakarítási ötleteket keres.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-044-01:** Felhasználóként szeretnék kategóriánként időszakos kiadási célt és kívánt megtakarítási összeget megadni, hogy mérhető tervem legyen.
- **US-044-02:** Felhasználóként szeretném a cél teljesülését a tényleges, visszatérítésekkel és felosztásokkal korrigált költéshez mérni, hogy a haladás valós legyen.
- **US-044-03:** Felhasználóként szeretném látni, mely költések és trendek okozzák a céltól való eltérést, hogy megértsem a helyzetet.
- **US-044-04:** Felhasználóként szeretnék konkrét, számszerűsített megtakarítási javaslatokat kapni a saját adataim alapján, hogy legyen következő lépésem.
- **US-044-05:** Felhasználóként szeretném minden javaslatnál látni a becsült hatást, időtávot, bizonytalanságot és alapul szolgáló adatokat, hogy ne kezeljem biztos ígéretként.
- **US-044-06:** Felhasználóként szeretném elfogadni, módosítani, elhalasztani vagy elutasítani a javaslatot, hogy a döntés nálam maradjon.
- **US-044-07:** Felhasználóként szeretném megadni, mely kiadások alapvetők vagy nem csökkenthetők, hogy a rendszer ne ismételjen irreális javaslatokat.
- **US-044-08:** Felhasználóként szeretném egy elfogadott javaslat eredményét később értékelni és visszajelzést adni, hogy a további ajánlások javuljanak.
- **US-044-09:** Felhasználóként szeretném, hogy kevés, bizonytalan vagy torz adat esetén a rendszer ezt jelezze és ne adjon túl magabiztos tanácsot.
- **US-044-10:** Felhasználóként szeretném a célokat és ajánlásokat háztartási szerepkörök szerint megosztani vagy korlátozni, hogy az érzékeny pénzügyi döntések kontrolláltak legyenek.

## Scope

- Kategória- és időszakalapú kiadási, illetve megtakarítási célok.
- Magyarázható, becsült hatású javaslatok saját adatokból.
- Felhasználói felülbírálás, kizárások, visszajelzés és eredménykövetés.
- Bizonytalanság, adatminőség és jogosultság látható kezelése.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Befektetési, hitel-, adó- vagy egyéb szabályozott pénzügyi tanácsadás.
- Automatikus vásárláslemondás vagy pénzügyi döntés felhasználói jóváhagyás nélkül.
- Garantált megtakarítás ígérete.
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
