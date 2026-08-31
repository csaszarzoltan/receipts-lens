# BRIEF-036: Pénznemváltás és átváltási árfolyam kezelése

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-036  
**Forrás:** jelenlegi felület, alkalmazási működés és tesztbizonyíték alapján rekonstruálva

## Probléma

Külföldi nyugták esetén a felhasználónak átláthatóan kell látnia az eredeti és az alap pénznemben számított értéket.

## Célcsoport és kontextus

Több pénznemben vásárló felhasználó vagy könyvelő.

## Kívánt eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-036-01:** Felhasználóként szeretném a nyugta eredeti pénznemét és összegét megőrizni, hogy a forrásadat visszakövethető maradjon.
- **US-036-02:** Felhasználóként szeretném az összeget a háztartás alap pénznemében is látni, hogy összehasonlítható legyen a többi költéssel.
- **US-036-03:** Jogosult felhasználóként szeretném megadni vagy javítani az alkalmazott árfolyamot, hogy hibás automatikus alapadat esetén kontrollálhassam az átváltást.
- **US-036-04:** Felhasználóként szeretném látni az átváltás során használt árfolyamot és kerekítést, hogy a számítás auditálható legyen.
- **US-036-05:** Felhasználóként szeretnék hiányzó vagy érvénytelen árfolyamnál egyértelmű blokkolást kapni, hogy a rendszer ne találjon ki pénzügyi értéket.

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
