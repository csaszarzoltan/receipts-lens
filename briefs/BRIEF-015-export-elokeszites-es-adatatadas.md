# BRIEF-015: Export-előkészítés és adatátadás

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-015  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

Hibás vagy hiányos nyugtákat nem szabad észrevétlenül külső feldolgozásra átadni.

## Célcsoport és kontextus

Könyvelő vagy üzleti módot használó felhasználó, aki adatcsomagot készít.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-015-01:** Könyvelőként szeretném export előtt látni, mely nyugták készek és melyek blokkoltak, hogy csak ellenőrzött adatot adjak át.
- **US-015-02:** Könyvelőként szeretném megérteni minden blokkolás okát, hogy célzottan javíthassam a hiányosságokat.
- **US-015-03:** Könyvelőként szeretnék előnézetet kapni az export tartalmáról és formátumáról, hogy megerősítés előtt ellenőrizhessem.
- **US-015-04:** Könyvelőként szeretném a megfelelő profilban létrehozni és letölteni az exportot, hogy az illeszkedjen a célrendszerhez.
- **US-015-05:** Könyvelőként szeretném a korábbi exportok állapotát és eredményét visszakeresni, hogy auditálható legyen az adatátadás.
- **US-015-06:** Felhasználóként szeretném, hogy képletnek tűnő szöveg se válhasson veszélyes táblázatutasítássá, hogy a letöltött állomány biztonságosan megnyitható legyen.

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
