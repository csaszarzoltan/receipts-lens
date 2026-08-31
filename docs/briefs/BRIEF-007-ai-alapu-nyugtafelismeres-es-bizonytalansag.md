# BRIEF-007: AI-alapú nyugtafelismerés és bizonytalanság

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-007  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A felismert nyugtaadatok nem mindig pontosak, ezért a felhasználónak látnia kell, miben bízhat és mit kell ellenőriznie.

## Célcsoport és kontextus

Nyugtát feldolgozó felhasználó, különösen rossz minőségű vagy többnyelvű képek esetén.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-007-01:** Felhasználóként szeretném, hogy a rendszer azonosítsa a kereskedőt, dátumot, pénznemet, végösszeget és tételeket, hogy ne kelljen mindent kézzel begépelnem.
- **US-007-02:** Felhasználóként szeretném mezőnként látni a felismerés bizonyosságát, hogy a kockázatos adatokat célzottan ellenőrizhessem.
- **US-007-03:** Felhasználóként szeretném a nyugta eredeti képét a felismert adatok mellett megtekinteni, hogy össze tudjam hasonlítani őket.
- **US-007-04:** Többnyelvű nyugta feldolgozásakor szeretném, hogy az eredeti tartalom értelmezhetően kerüljön rögzítésre, hogy külföldi vásárlásaimat is kezelhessem.
- **US-007-05:** Felhasználóként szeretném, hogy bizonytalan eredmény ne váljon észrevétlenül végleges adattá, hogy elkerüljem a hibás kimutatásokat.
- **US-007-06:** Felhasználóként szeretnék érthető állapotot kapni, ha a felismerő szolgáltatás nem érhető el, hogy később újrapróbálhassam vagy kézzel folytathassam.

## Scope

- A fenti történetekben megnevezett, jelenleg megfigyelhető felhasználói folyamatok.
- A sikeres, üres, hibás, részleges és jogosultság által korlátozott állapotok, ahol azok a jelenlegi működésben relevánsak.
- A felhasználói kontroll, a téves adatok javítása és a biztonságos újrapróbálás.

## Non-scope

- A forrásban, tesztekben vagy működő felületen nem igazolt jövőbeli képességek.
- Új üzleti szabály, új integráció vagy a jelenlegi termék viselkedésének áttervezése.
- Technikai megvalósítás, belső komponensszerkezet vagy fejlesztési feladatlista.

## Érintett rendszerek

- A kapcsolódó felhasználói felület és navigáció.
- A műveletet kiszolgáló alkalmazási és adatkezelési réteg.
- A kapcsolódó külső szolgáltatás, ha a történet ilyen együttműködést igényel.

## Bizonytalanságok

- A BRIEF csak a jelenlegi forrásból bizonyítható viselkedést tekinti meglévőnek.
- A pontos válaszformák, technikai állapotkódok és belső szerződések a későbbi feature-specifikációhoz tartoznak.
