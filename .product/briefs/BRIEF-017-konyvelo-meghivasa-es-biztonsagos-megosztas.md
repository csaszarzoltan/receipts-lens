# BRIEF-017: Könyvelő meghívása és biztonságos megosztás

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-017  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A külső könyvelőnek ellenőrizhető, korlátozott és visszavonható hozzáférésre van szüksége.

## Célcsoport és kontextus

Háztartási tulajdonos és külső könyvelő vagy tanácsadó.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-017-01:** Háztartási tulajdonosként szeretnék lejáró meghívást küldeni a könyvelőmnek, hogy biztonságosan bevonhassam.
- **US-017-02:** Könyvelőként szeretném a meghívás elfogadása előtt látni, mely háztartáshoz és milyen szerepkörrel csatlakozom, hogy tudatos döntést hozzak.
- **US-017-03:** Könyvelőként szeretném a számomra engedélyezett nyugtákat és exportfeladatokat elérni, hogy elvégezhessem a megbízást.
- **US-017-04:** Háztartási tulajdonosként szeretném a könyvelő hozzáférését visszavonni, hogy a megbízás megszűnése után ne lássa az adatokat.
- **US-017-05:** Meghívottként szeretnék lejárt vagy már felhasznált meghívásnál egyértelmű tájékoztatást kapni, hogy új meghívást kérhessek.

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
