# BRIEF-012: Háztartási keretek és riasztások

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-012  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A felhasználó későn veszi észre, ha egy költési kategória megközelíti vagy túllépi a tervezett keretet.

## Célcsoport és kontextus

Keretet tervező háztartási tulajdonos vagy felnőtt tag.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-012-01:** Háztartási tulajdonosként szeretnék időszakos költési keretet létrehozni egy kategóriához, hogy előre szabályozzam a kiadásokat.
- **US-012-02:** Háztartási tulajdonosként szeretném a keretet módosítani vagy törölni, hogy kövessem a megváltozott terveket.
- **US-012-03:** Háztartási felhasználóként szeretném látni a felhasznált és fennmaradó összeget, hogy időben korrigálhassam a költést.
- **US-012-04:** Háztartási felhasználóként szeretnék figyelmeztetést kapni a beállított küszöb elérésekor vagy túllépésekor, hogy elkerüljem a váratlan hiányt.
- **US-012-05:** Felhasználóként szeretném a már kezelt figyelmeztetést nyugtázni, hogy a teendőlistámban csak az aktuális ügyek maradjanak.

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
