# BRIEF-016: Háztartási együttműködés és családi postafiók

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-016  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A közösen kezelt nyugtákhoz egyértelmű tagságra, szerepkörökre és feladatmegosztásra van szükség.

## Célcsoport és kontextus

Háztartási tulajdonos, felnőtt tag, korlátozott tag vagy tanácsadó.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-016-01:** Háztartási tulajdonosként szeretnék tagot meghívni, hogy közösen kezelhessük a háztartás nyugtáit.
- **US-016-02:** Meghívottként szeretném a meghívás részleteit megtekinteni és elfogadni, hogy a megfelelő háztartáshoz csatlakozzak.
- **US-016-03:** Háztartási tulajdonosként szeretném a tagok szerepkörét és hozzáférését kezelni, hogy mindenki csak a szükséges műveleteket végezhesse.
- **US-016-04:** Háztartási tagként szeretném egy közös postafiókban látni a rám vagy a háztartásra váró feladatokat, hogy ne maradjon el ellenőrzés vagy jóváhagyás.
- **US-016-05:** Háztartási tagként szeretném a feladatok olvasott és elintézett állapotát kezelni, hogy követhető legyen az együttműködés.
- **US-016-06:** Felhasználóként szeretném, hogy más háztartás adatai sem kereséssel, sem közvetlen hivatkozással ne legyenek elérhetők, hogy a pénzügyi adatok elkülönüljenek.

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
