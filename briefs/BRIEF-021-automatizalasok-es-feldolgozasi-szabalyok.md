# BRIEF-021: Automatizálások és feldolgozási szabályok

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-021  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

Az ismétlődő feldolgozási lépések kézi végrehajtása időigényes, de az automatizmusoknak átláthatónak és szabályozhatónak kell maradniuk.

## Célcsoport és kontextus

Jogosult felhasználó, aki ismétlődő pénzügyi feldolgozást állít be.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-021-01:** Jogosult felhasználóként szeretnék automatizálási szabályt létrehozni, hogy az ismétlődő feladatok kevesebb kézi munkát igényeljenek.
- **US-021-02:** Jogosult felhasználóként szeretném a szabály feltételeit és várható hatását ellenőrizni, hogy ne induljon túl tág automatizmus.
- **US-021-03:** Jogosult felhasználóként szeretném a szabályt szüneteltetni, módosítani vagy törölni, hogy mindig nálam maradjon a kontroll.
- **US-021-04:** Jogosult felhasználóként szeretném látni a futások eredményét és hibáját, hogy az automatizmus működése auditálható legyen.
- **US-021-05:** Jogosult felhasználóként szeretném a sikertelen futást biztonságosan újrapróbálni, hogy ne keletkezzen duplikált eredmény.

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
