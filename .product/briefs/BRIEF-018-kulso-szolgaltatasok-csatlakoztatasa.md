# BRIEF-018: Külső szolgáltatások csatlakoztatása

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-018  
**Forrás:** a jelenlegi alkalmazás felülete, működése, tesztjei és dokumentációja alapján rekonstruálva

## Probléma

A könyvelési és nyugtaforrások kézi mozgatása időigényes, a kapcsolatok állapota pedig átláthatóságot igényel.

## Célcsoport és kontextus

Üzleti módot használó jogosult felhasználó, aki külső szolgáltatást kapcsol.

## Kívánt eredmény

A felhasználó a kapcsolódó feladatot a rendszer jelenlegi képességeivel végig tudja vinni, közben érthető állapotot, kontrollt és javítási lehetőséget kap, és csak a ténylegesen sikeres művelet jelenik meg befejezettként.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-018-01:** Jogosult felhasználóként szeretném látni az elérhető és már csatlakoztatott szolgáltatásokat, hogy kezelhessem az adatkapcsolatokat.
- **US-018-02:** Jogosult felhasználóként szeretném biztonságos jóváhagyási folyamattal összekapcsolni a szolgáltatást, hogy ne kelljen hozzáférési adatot másolnom.
- **US-018-03:** Jogosult felhasználóként szeretném a kapcsolat állapotát, utolsó szinkronját és esetleges hibáját látni, hogy eldönthessem, szükséges-e beavatkozás.
- **US-018-04:** Jogosult felhasználóként szeretném a kapcsolatot megszüntetni, hogy a külső hozzáférés és tárolt jogosultság eltávolítható legyen.
- **US-018-05:** Felhasználóként szeretném, hogy hibás vagy manipulált visszatérési cím ne téríthesse el a csatlakoztatási folyamatot, hogy a fiókom biztonságban maradjon.

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
