# BRIEF-023: Adózási munkaterület és auditcsomag

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-023  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

Az adózási célú összesítéshez bizonyítható forráskapcsolat, hiányosságjelzés és letölthető dokumentáció szükséges.

## Célcsoport és kontextus

Adózási feladatot végző tulajdonos vagy könyvelő.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-023-01:** Könyvelőként szeretném az adózási szempontból releváns nyugtákat és összegeket egy munkaterületen áttekinteni, hogy előkészítsem a bevallási munkát.
- **US-023-02:** Könyvelőként szeretném látni a hiányzó vagy kockázatos bizonyítékokat, hogy még időben pótolhassam őket.
- **US-023-03:** Könyvelőként szeretném a levonhatósági vagy adóbesorolási javaslat bizonyosságát és indokát látni, hogy ne kezeljem automatikus döntésként.
- **US-023-04:** Könyvelőként szeretnék auditálható összesítést és dokumentumcsomagot letölteni, hogy a számítások visszakövethetők legyenek.
- **US-023-05:** Felhasználóként szeretném, hogy adózási művelet hibájánál a forrásadat változatlan maradjon, hogy a javítás biztonságosan újrapróbálható legyen.

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
