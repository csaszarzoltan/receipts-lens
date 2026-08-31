# BRIEF-019: Szinkronizálás és egyeztetés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-019  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A külső rendszer és a helyi nyilvántartás eltérései csendes adatvesztést vagy kettős rögzítést okozhatnak.

## Célcsoport és kontextus

Könyvelő vagy adminisztrátor, aki külső könyvelési rendszerrel szinkronizál.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-019-01:** Könyvelőként szeretném előnézetben látni, milyen adatok kerülnének szinkronizálásra, hogy a változtatás előtt ellenőrizhessem a hatást.
- **US-019-02:** Könyvelőként szeretném megerősíteni a szinkronizálást, hogy csak tudatos döntés után történjen külső módosítás.
- **US-019-03:** Könyvelőként szeretném tételesen látni a sikeres, kihagyott és hibás eredményeket, hogy a részleges végrehajtást kezelhessem.
- **US-019-04:** Könyvelőként szeretném ismételt kérés esetén elkerülni a duplikált külső bejegyzéseket, hogy biztonságosan újrapróbálhassak.
- **US-019-05:** Könyvelőként szeretném a helyi és külső eltéréseket egyeztetni, hogy a két rendszer közötti állapot tisztázható legyen.

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
