# BRIEF-013: Költési elemzés és előrejelzés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-013  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A múltbeli adatok önmagukban nem mutatják meg könnyen a trendeket és a várható jövőbeli terhelést.

## Célcsoport és kontextus

Felhasználó, aki kategóriánkénti, időbeli és előrejelzett költést vizsgál.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-013-01:** Felhasználóként szeretném időszak és kategória szerint látni a költéseimet, hogy felismerjem a fontos trendeket.
- **US-013-02:** Felhasználóként szeretném összehasonlítani a tényleges költést a keretekkel, hogy lássam, hol tértem el a tervtől.
- **US-013-03:** Felhasználóként szeretném a várható költést és annak bizonytalanságát megtekinteni, hogy megalapozottabban tervezzek.
- **US-013-04:** Felhasználóként szeretném tudni, ha kevés adat miatt az előrejelzés nem megbízható, hogy ne kezeljem biztos tényként.
- **US-013-05:** Felhasználóként szeretnék üres időszaknál is érthető magyarázatot és következő lépést kapni, hogy tudjam, milyen adat szükséges az elemzéshez.

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
