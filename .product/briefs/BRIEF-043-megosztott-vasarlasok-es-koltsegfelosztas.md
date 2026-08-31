## BRIEF-043: Megosztott vásárlások és költségfelosztás

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-043  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

Egy vásárlás költsége gyakran több háztartási taghoz, kategóriához vagy költségviselőhöz tartozik, és pontos felosztás nélkül a kimutatások és elszámolások félrevezetők.

## Célcsoport és kontextus

Háztartási felhasználó vagy pénzügyi felelős, aki közös és személyes költségeket oszt fel.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-043-01:** Felhasználóként szeretném egy nyugta vagy tranzakció teljes összegét több részre osztani, hogy a költség a megfelelő viselőkhöz és kategóriákhoz kerüljön.
- **US-043-02:** Felhasználóként szeretnék fix összeg, százalék, egyenlő arány vagy nyugtatétel alapján felosztani, hogy a valós megállapodást tükrözhessem.
- **US-043-03:** Felhasználóként szeretném személyhez, háztartási csoporthoz, kategóriához, projekthez vagy külső költségviselőhöz rendelni a részeket, hogy többféle elszámolási cél kezelhető legyen.
- **US-043-04:** Felhasználóként szeretném mentés előtt látni, hogy a részek összege pontosan kiadja-e a teljes összeget, hogy ne maradjon hiány vagy túlosztás.
- **US-043-05:** Felhasználóként szeretném kezelni a kerekítési maradványt és kiválasztani, melyik rész viselje, hogy a pénzügyi összeg konzisztens maradjon.
- **US-043-06:** Felhasználóként szeretnék korábbi felosztást sablonként használni ismétlődő vásárlásnál, hogy kevesebb kézi munkára legyen szükség.
- **US-043-07:** Érintett háztartási tagként szeretném látni és szükség esetén jóváhagyni vagy vitatni a rám osztott részt, hogy ne keletkezzen rejtett kötelezettség.
- **US-043-08:** Felhasználóként szeretném a felosztást később módosítani, miközben a korábbi állapot visszakereshető marad, hogy a javítás auditálható legyen.
- **US-043-09:** Felhasználóként szeretném a riportokban és exportokban az eredeti vásárlást és a felosztott részeket kettős számolás nélkül látni, hogy az összesítések helyesek legyenek.

## Scope

- Nyugta, tranzakció vagy nyugtatétel költségének felosztása.
- Fix, százalékos, egyenlő és tételalapú módszer, kerekítés és validáció.
- Résztvevői jóváhagyás vagy vita, sablon és auditálható módosítás.
- Riport-, kategória- és exporthatás kettős elszámolás nélkül.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Pénz automatikus beszedése vagy átutalása a résztvevők között.
- Teljes követeléskezelő vagy adósságbehajtó rendszer.
- Olyan külső személy pénzügyi adatainak kezelése, akihez nincs megfelelő hozzájárulás vagy meghívás.
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
