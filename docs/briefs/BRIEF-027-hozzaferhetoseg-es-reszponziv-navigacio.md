# BRIEF-027: Hozzáférhetőség és reszponzív navigáció

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-027  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A pénzügyi munkafolyamatoknak egér nélkül, segítő technológiával és különböző képernyőméreteken is elvégezhetőnek kell lenniük.

## Célcsoport és kontextus

Billentyűzetet, képernyőolvasót vagy mobil eszközt használó felhasználó.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-027-01:** Billentyűzetet használó felhasználóként szeretném logikus sorrendben elérni az összes interaktív elemet, hogy egér nélkül is befejezhessem a feladataimat.
- **US-027-02:** Képernyőolvasót használó felhasználóként szeretném érthető nevekkel és állapotokkal elérni a navigációt, űrlapokat és párbeszédablakokat, hogy önállóan használjam a szolgáltatást.
- **US-027-03:** Mobilos felhasználóként szeretném a fő területeket alsó navigációból vagy összecsukható menüből elérni, hogy kis képernyőn se vesszek el.
- **US-027-04:** Felhasználóként szeretném, hogy betöltés, siker és hiba állapota vizuálisan és segítő technológiával is érzékelhető legyen, hogy mindig tudjam, mi történt.
- **US-027-05:** Felhasználóként szeretném a párbeszédablakot megszakítani és a fókuszt a kiinduló elemre visszakapni, hogy a munkafolyamat kiszámítható maradjon.

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
