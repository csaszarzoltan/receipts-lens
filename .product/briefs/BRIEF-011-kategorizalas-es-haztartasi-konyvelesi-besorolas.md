# BRIEF-011: Kategorizálás és háztartási könyvelési besorolás

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-011  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A vásárlások egységes besorolása nélkül nehéz megérteni, mire megy el a pénz.

## Célcsoport és kontextus

Háztartási felhasználó vagy könyvelő, aki nyugtákat és tételeket kategorizál.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-011-01:** Felhasználóként szeretném, hogy a rendszer kategóriát javasoljon a vásárláshoz, hogy gyorsabban rendszerezzem a kiadásaimat.
- **US-011-02:** Felhasználóként szeretném a javasolt kategóriát felülbírálni, hogy a saját háztartási logikám szerint tarthassam nyilván a költést.
- **US-011-03:** Felhasználóként szeretném látni, ha egy besorolás bizonytalan, hogy ellenőrizhessem a kimutatások előtt.
- **US-011-04:** Könyvelőként szeretném az aktuális besorolási szabályokat áttekinteni és verziózottan módosítani, hogy a későbbi exportok következetesek legyenek.

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
