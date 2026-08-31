# BRIEF-024: Profil, nyelv, pénznem és megjelenés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-024  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A különböző háztartások eltérő nyelvi, pénznemi és megjelenítési igényekkel használják a szolgáltatást.

## Célcsoport és kontextus

Bármely bejelentkezett felhasználó, valamint belépés előtti látogató a saját eszközén.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-024-01:** Felhasználóként szeretném a megjelenített nevemet és alapbeállításaimat módosítani, hogy a munkaterület engem tükrözzön.
- **US-024-02:** Felhasználóként szeretnék a támogatott nyelvek között váltani, hogy a teljes felületet az általam értett nyelven használjam.
- **US-024-03:** Felhasználóként szeretném az alap pénznemet beállítani, hogy az összegek következetesen jelenjenek meg.
- **US-024-04:** Felhasználóként szeretnék világos, sötét vagy rendszerhez igazodó témát választani, hogy kényelmesen használjam a felületet.
- **US-024-05:** Látogatóként szeretném már bejelentkezés előtt nyelvet és témát váltani, hogy a belépési folyamat is megfelelő legyen.
- **US-024-06:** Felhasználóként szeretném, hogy választásaim újranyitáskor is megmaradjanak, hogy ne kelljen minden alkalommal újra beállítanom őket.

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
