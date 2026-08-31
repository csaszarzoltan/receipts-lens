# BRIEF-014: Jelentések létrehozása és letöltése

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-014  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A felhasználónak megosztható, újra előállítható összesítésre van szüksége a kiválasztott időszakról.

## Célcsoport és kontextus

Háztartási felhasználó vagy könyvelő, aki jelentést készít.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-014-01:** Felhasználóként szeretném kiválasztani a jelentés időszakát és tartalmát, hogy a célomhoz illeszkedő összesítést kapjak.
- **US-014-02:** Felhasználóként szeretném a létrehozás állapotát követni, hogy hosszabb feldolgozásnál is tudjam, mi történik.
- **US-014-03:** Felhasználóként szeretném a kész jelentést megtekinteni és letölteni, hogy archiválhassam vagy megoszthassam.
- **US-014-04:** Felhasználóként szeretnék részleges vagy sikertelen jelentéskészítésnél érthető hibát és újrapróbálást kapni, hogy ne kelljen a beállításokat újra megadnom.

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
