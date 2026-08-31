# BRIEF-005: Háztartási áttekintő és napi teendők

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-005  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A felhasználónak egyetlen helyen kell látnia a pénzügyi helyzetét és a következő fontos teendőket.

## Célcsoport és kontextus

Bejelentkezett háztartási felhasználó, aki gyors napi áttekintést szeretne.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-005-01:** Háztartási felhasználóként szeretném látni az aktuális költést, keretállapotot és feldolgozási helyzetet, hogy gyorsan megértsem a háztartás pénzügyi állapotát.
- **US-005-02:** Háztartási felhasználóként szeretném a bizonytalan vagy jóváhagyásra váró tételeket kiemelve látni, hogy először a figyelmet igénylő ügyeket intézzem el.
- **US-005-03:** Háztartási felhasználóként szeretnék az összesítőből közvetlenül a kapcsolódó nyugtához vagy feladathoz jutni, hogy kevés lépésből intézkedhessek.
- **US-005-04:** Új háztartás tagjaként szeretnék hasznos üres állapotot látni, hogy tudjam, melyik első művelet hoz létre adatot.
- **US-005-05:** Felhasználóként szeretném tudni, mikor frissült utoljára az összesítés, hogy helyesen értelmezzem az adatokat.

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
