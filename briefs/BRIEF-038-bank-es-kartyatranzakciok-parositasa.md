## BRIEF-038: Bank- és kártyatranzakciók párosítása

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-038  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A nyugták és a tényleges bank- vagy kártyaterhelések külön életciklusban érkeznek, ezért automatikus párosítás nélkül nehéz bizonyítani, hogy egy bizonylat mely pénzmozgáshoz tartozik, a téves automatikus összekapcsolás pedig hibás elszámolást okozhat.

## Célcsoport és kontextus

Háztartási felhasználó, pénzügyi felelős vagy könyvelő, aki importált tranzakciókat és feldolgozott nyugtákat egyeztet.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-038-01:** Felhasználóként szeretném egy helyen látni a párosítatlan nyugtákat és tranzakciókat, hogy gyorsan felmérjem az egyeztetési hátralékot.
- **US-038-02:** Felhasználóként szeretném, hogy a rendszer összeg, pénznem, dátum, kereskedő és fizetési mód alapján rangsorolt párosítási javaslatokat készítsen, hogy kevesebb kézi keresésre legyen szükség.
- **US-038-03:** Felhasználóként szeretném látni a javaslat bizonyosságát és az egyező vagy eltérő jellemzőket, hogy megértsem, miért ajánlotta a rendszer a kapcsolatot.
- **US-038-04:** Felhasználóként szeretném a nagy bizonyosságú javaslatot jóváhagyni, hogy a nyugta és a terhelés ellenőrzött kapcsolatként jelenjen meg.
- **US-038-05:** Felhasználóként szeretném visszautasítani a hibás javaslatot és másik tételt keresni, hogy a rendszer ne rögzítsen téves kapcsolatot.
- **US-038-06:** Felhasználóként szeretnék kézzel összekapcsolni egy nyugtát és tranzakciót, ha az automatikus keresés nem talál megfelelő jelöltet, hogy a folyamat ellenőrizhetően a kívánt eredménnyel záruljon.
- **US-038-07:** Felhasználóként szeretném kezelni az egy nyugtához tartozó több terhelést, illetve az egy terhelést igazoló több bizonylatot, hogy a részfizetéses és összevont fizetések is egyeztethetők legyenek.
- **US-038-08:** Felhasználóként szeretném egy jóváhagyott párosítást indoklással felbontani vagy javítani, hogy a később felfedezett hibák auditálhatóan korrigálhatók legyenek.
- **US-038-09:** Felhasználóként szeretném, hogy függő, könyvelt és visszavont banki tételek állapotváltozása ne hozzon létre duplikált párosítást, hogy az egyeztetés stabil maradjon.
- **US-038-10:** Könyvelőként szeretném visszakeresni, ki, mikor és milyen javaslat alapján hagyta jóvá a párosítást, hogy az eredmény bizonyítható legyen.

## Scope

- Tranzakcióimportból vagy csatlakoztatott pénzügyi forrásból elérhető terhelések egyeztetése feldolgozott nyugtákkal.
- Automatikus javaslat, magyarázható bizonyosság, kézi keresés, jóváhagyás, elutasítás és kapcsolatbontás.
- Egy-egy, egy-több és több-egy kapcsolatok, részfizetés, borravaló, deviza- és dátumeltérés kezelése.
- Sikeres, üres, bizonytalan, konfliktusos, jogosultsági és újrapróbálható hibaállapotok.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Banki átutalás vagy fizetés kezdeményezése.
- Banki hitelesítő adatok tárolási megoldásának megtervezése.
- Teljes főkönyvi egyeztetés vagy automatikus könyvelési döntés felhasználói kontroll nélkül.
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
