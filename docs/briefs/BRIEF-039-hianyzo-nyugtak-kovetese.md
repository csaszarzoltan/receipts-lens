## BRIEF-039: Hiányzó nyugták követése

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-039  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A tranzakciók egy részéhez nem érkezik nyugta, ezért a bizonyítékok pótlása elmaradhat, a felelősség tisztázatlan maradhat, és a zárás vagy export későn akad el.

## Célcsoport és kontextus

Háztartási tag, pénzügyi felelős vagy könyvelő, aki a nyugta nélküli tranzakciók pótlását koordinálja.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-039-01:** Felhasználóként szeretném automatikusan felismerni a nyugtával nem rendelkező, bizonylatot igénylő tranzakciókat, hogy a hiányok ne maradjanak rejtve.
- **US-039-02:** Felhasználóként szeretném látni, miért minősült egy tranzakció nyugtahiányosnak, hogy kizárhassam a bizonylatot nem igénylő eseteket.
- **US-039-03:** Pénzügyi felelősként szeretném a hiányzó nyugtát egy háztartási taghoz rendelni és határidőt adni, hogy egyértelmű legyen a felelős.
- **US-039-04:** Felelősként szeretnék a tranzakcióból közvetlenül nyugtát feltölteni vagy meglévő nyugtát kapcsolni, hogy a feladat elvégzése kevés lépést igényeljen.
- **US-039-05:** Felelősként szeretném jelezni, ha nyugta nem szerezhető be, és indoklást vagy helyettesítő dokumentumot csatolni, hogy a kivétel ellenőrizhető legyen.
- **US-039-06:** Felhasználóként szeretnék az esedékesség előtt és után szabályozható emlékeztetőket kapni, hogy időben pótoljam a bizonylatot.
- **US-039-07:** Háztartási tulajdonosként szeretném az emlékeztetők gyakoriságát, csendes időszakát és csatornáját szabályozni, hogy a jelzések hasznosak, ne zaklatóak legyenek.
- **US-039-08:** Könyvelőként szeretném állapot, felelős, kor és összeg szerint szűrni a hiányokat, hogy a legfontosabb ügyeket kezeljem először.
- **US-039-09:** Felhasználóként szeretném, hogy a megfelelő nyugta összekapcsolása automatikusan lezárja a feladatot, de a kapcsolat későbbi felbontása újranyissa, hogy az állapot következetes maradjon.

## Scope

- Nyugta nélküli, bizonylatot igénylő tranzakciók felismerése és feladatként követése.
- Felelős, határidő, prioritás, megjegyzés, kivétel és helyettesítő bizonyíték kezelése.
- Alkalmazáson belüli és konfigurálható külső emlékeztetők.
- Összesítő, szűrés, késésjelzés, lezárás és újranyitás.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Jogi vagy adózási állásfoglalás arról, mikor kötelező nyugta.
- Más személy nevében automatikus dokumentumhamisítás vagy nyugtapótlás.
- Általános projektfeladat-kezelő létrehozása.
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
