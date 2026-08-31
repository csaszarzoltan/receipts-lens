# BRIEF-025: Adatvédelem, megőrzés és törlés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-025  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A pénzügyi képek és adatok érzékenyek, ezért a felhasználónak átlátható megőrzési és törlési kontrollra van szüksége.

## Célcsoport és kontextus

Saját adataiért felelős felhasználó vagy háztartási tulajdonos.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-025-01:** Felhasználóként szeretném látni, milyen adatokat őriz a szolgáltatás rólam és a nyugtáimról, hogy tudatosan használhassam.
- **US-025-02:** Háztartási tulajdonosként szeretném beállítani a megőrzési időt, hogy az adatok csak a szükséges ideig maradjanak meg.
- **US-025-03:** Felhasználóként szeretnék adateltávolítás előtt előnézetet kapni a következményekről, hogy elkerüljem a véletlen veszteséget.
- **US-025-04:** Felhasználóként szeretném külön megerősítéssel végrehajtani a végleges törlést, hogy a visszafordíthatatlan művelet tudatos legyen.
- **US-025-05:** Felhasználóként szeretném, hogy sikertelen törlés ne jelenjen meg sikeresként, és az érintett adatok állapota egyértelmű maradjon.

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
