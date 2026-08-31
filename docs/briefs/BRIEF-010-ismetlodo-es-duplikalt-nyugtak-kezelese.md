# BRIEF-010: Ismétlődő és duplikált nyugták kezelése

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-010  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

Ugyanannak a vásárlásnak a többszöri rögzítése torzíthatja a költéseket és a könyvelési eredményeket.

## Célcsoport és kontextus

Felhasználó, aki több hasonló vagy ugyanarról a vásárlásról készült nyugtát tölt fel.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-010-01:** Felhasználóként szeretném, hogy a rendszer jelezze a lehetséges duplikátumokat, hogy ne számoljam el kétszer ugyanazt a vásárlást.
- **US-010-02:** Felhasználóként szeretném látni, milyen egyezések alapján merült fel a duplikáció gyanúja, hogy megalapozott döntést hozzak.
- **US-010-03:** Felhasználóként szeretném egymás mellett összehasonlítani a gyanús nyugtákat, hogy eldönthessem, valóban ugyanarról a vásárlásról van-e szó.
- **US-010-04:** Felhasználóként szeretném megtartani mindkét nyugtát, ha külön vásárlások, hogy a rendszer ne töröljön helyes adatot.
- **US-010-05:** Felhasználóként szeretném kizárni vagy összekapcsolni a valódi duplikátumot, hogy az összesítésekben csak egyszer szerepeljen.

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
