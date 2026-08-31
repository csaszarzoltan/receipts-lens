# BRIEF-026: Értesítések és állapotüzenetek

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-026  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A háttérben befejeződő vagy beavatkozást igénylő műveletek könnyen észrevétlenek maradnak.

## Célcsoport és kontextus

Aktív vagy visszatérő felhasználó, aki feldolgozási, kvóta- vagy együttműködési eseményekről értesül.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-026-01:** Felhasználóként szeretném egy értesítési panelen látni az új eseményeket, hogy ne maradjak le a fontos változásokról.
- **US-026-02:** Felhasználóként szeretném külön felismerni az olvasatlan és intézkedést igénylő értesítéseket, hogy megfelelő sorrendben reagáljak.
- **US-026-03:** Felhasználóként szeretnék az értesítésből a kapcsolódó feladathoz jutni, hogy gyorsan intézkedhessek.
- **US-026-04:** Felhasználóként szeretném az értesítést elolvasottnak jelölni vagy elvetni, hogy a lista kezelhető maradjon.
- **US-026-05:** Felhasználóként szeretném beállítani az előfizetéssel kapcsolatos e-mailes figyelmeztetéseket, hogy a kívánt csatornán kapjak jelzést.

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
