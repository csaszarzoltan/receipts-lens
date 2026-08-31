# BRIEF-037: Diagnosztikai csomag és támogatási hibaelemzés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-037  
**Forrás:** jelenlegi felület, alkalmazási működés és tesztbizonyíték alapján rekonstruálva

## Probléma

Összetett hiba esetén a felhasználónak úgy kell támogatási adatot átadnia, hogy érzékeny nyugtatartalom vagy hitelesítő adat ne szivárogjon ki.

## Célcsoport és kontextus

Hibát tapasztaló felhasználó, támogatási munkatárs vagy üzemeltető.

## Kívánt eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-037-01:** Felhasználóként szeretném a rendszer diagnosztikai állapotát áttekinteni, hogy megértsem, mely szolgáltatás működik vagy hibás.
- **US-037-02:** Felhasználóként szeretnék letölthető diagnosztikai csomagot készíteni, hogy a támogatás reprodukálni tudja a hibát.
- **US-037-03:** Felhasználóként szeretném a letöltés előtt tudni, milyen adat kerül a csomagba, hogy ellenőrizhessem az adatvédelmi hatást.
- **US-037-04:** Felhasználóként szeretném, hogy a diagnosztikai csomag ne tartalmazzon jelszót, hozzáférési kulcsot vagy teljes nyugtatartalmat, hogy biztonságosan megoszthassam.
- **US-037-05:** Üzemeltetőként szeretném a környezeti és függőségi állapotot időbélyeggel látni, hogy a hibát a megfelelő rendszerállapothoz kapcsolhassam.

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
