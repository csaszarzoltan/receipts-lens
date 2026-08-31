# BRIEF-006: Nyugta feltöltése és feldolgozási sor

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-006  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A papír- és digitális nyugták rögzítése lassú, a több fájlból álló feldolgozás állapota pedig könnyen követhetetlenné válik.

## Célcsoport és kontextus

Felhasználó, aki egy vagy több nyugtát fájlból, húzással vagy kamerával ad hozzá.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-006-01:** Felhasználóként szeretnék egy vagy több támogatott nyugtaképet kijelölni vagy behúzni, hogy gyorsan elindíthassam a rögzítést.
- **US-006-02:** Mobilos felhasználóként szeretném a kamerával közvetlenül lefényképezni a nyugtát, hogy ne kelljen előbb külön fájlt készítenem.
- **US-006-03:** Felhasználóként szeretném feltöltés előtt látni a kiválasztott fájlokat és eltávolítani a tévesen kiválasztott elemeket, hogy csak a szükséges nyugták kerüljenek sorba.
- **US-006-04:** Felhasználóként szeretném fájlonként látni a feltöltés és feldolgozás állapotát, hogy tudjam, mi készült el és mi várakozik.
- **US-006-05:** Felhasználóként szeretnék egy sikertelen elemnél újrapróbálási lehetőséget kapni anélkül, hogy a sikeres elemeket újra fel kellene töltenem.
- **US-006-06:** Felhasználóként szeretnék egyértelmű visszajelzést kapni nem támogatott vagy túl nagy fájlról, hogy megfelelő bemenettel folytathassam.
- **US-006-07:** Felhasználóként szeretném megszakítás után is megtalálni a még feldolgozás alatt álló feladatokat, hogy később ellenőrizhessem az eredményüket.

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
