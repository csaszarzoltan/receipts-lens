# BRIEF-030: Jelszó nélküli belépés e-mailes hivatkozással

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-030  
**Forrás:** jelenlegi felület, alkalmazási működés és tesztbizonyíték alapján rekonstruálva

## Probléma

A felhasználó jelszó megadása nélkül is biztonságosan szeretne hozzáférni a saját háztartási munkaterületéhez.

## Célcsoport és kontextus

Visszatérő vagy meghívott felhasználó, aki e-mailben kapott egyszer használható belépési hivatkozást használ.

## Kívánt eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-030-01:** Felhasználóként szeretnék e-mailes belépési hivatkozást kérni, hogy elfelejtett jelszó nélkül is hozzáférhessek a fiókomhoz.
- **US-030-02:** Felhasználóként szeretném ugyanazt a semleges visszajelzést kapni attól függetlenül, hogy az e-mail-cím ismert-e, hogy a rendszer ne árulja el mások fiókjának létezését.
- **US-030-03:** Felhasználóként szeretném az érvényes belépési hivatkozással megnyitni a saját munkaterületemet, hogy folytathassam a feladataimat.
- **US-030-04:** Felhasználóként szeretnék lejárt, hibás vagy már felhasznált hivatkozásnál egyértelmű tájékoztatást és új igénylési lehetőséget kapni, hogy biztonságosan újrapróbálhassam.

## Scope

- A felsorolt jelenlegi felhasználói folyamatok és megfigyelhető állapotok.
- A javítás, megszakítás, újrapróbálás és jogosultsági korlát, ahol a folyamatban releváns.

## Non-scope

- A forrásban vagy tesztekben nem igazolt jövőbeli működés.
- A technikai megvalósítás részletei és belső szerződései.

## Érintett rendszerek

- A kapcsolódó felhasználói felület.
- Az alkalmazási és tartós adatkezelési folyamat.
- A kapcsolódó külső szolgáltatás, amennyiben a felhasználói eredmény megköveteli.

## Bizonytalanságok

- A pontos technikai hibakódok és belső mezők a feature-specifikációhoz tartoznak.
- A BRIEF nem terjeszti ki a működést a jelenlegi bizonyítékon túl.
