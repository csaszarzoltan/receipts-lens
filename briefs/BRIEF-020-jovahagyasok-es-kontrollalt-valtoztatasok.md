# BRIEF-020: Jóváhagyások és kontrollált változtatások

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-020  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A pénzügyi hatású műveletekhez a végrehajtás előtt megfelelő szerepkörű jóváhagyás szükséges.

## Célcsoport és kontextus

Jóváhagyó, kérelmező és adminisztrátor közös munkafolyamata.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-020-01:** Kérelmezőként szeretném jóváhagyásra elküldeni a pénzügyi műveletet, hogy az ne történjen meg jogosulatlanul.
- **US-020-02:** Jóváhagyóként szeretném egy helyen látni a várakozó kérelmeket és azok lényeges hatását, hogy felelős döntést hozzak.
- **US-020-03:** Jóváhagyóként szeretném elfogadni vagy indoklással elutasítani a kérelmet, hogy a döntés érthető és visszakereshető legyen.
- **US-020-04:** Kérelmezőként szeretném látni a kérelem aktuális állapotát és döntését, hogy tudjam, mi a következő lépés.
- **US-020-05:** Jóváhagyóként szeretném, hogy már eldöntött vagy közben módosult kérelmet ne lehessen elavult állapotból újra jóváhagyni, hogy elkerüljük a konfliktust.

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
