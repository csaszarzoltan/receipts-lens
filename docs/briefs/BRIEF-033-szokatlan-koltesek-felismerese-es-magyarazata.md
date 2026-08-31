# BRIEF-033: Szokatlan költések felismerése és magyarázata

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-033  
**Forrás:** jelenlegi felület, alkalmazási működés és tesztbizonyíték alapján rekonstruálva

## Probléma

A felhasználó nehezen veszi észre azokat a vásárlásokat, amelyek jelentősen eltérnek a megszokott mintától.

## Célcsoport és kontextus

Háztartási felhasználó, aki a költési előrejelzés mellett kiugró eseményeket vizsgál.

## Kívánt eredmény

A felhasználó a képességet érthető, kontrollálható és ellenőrizhető folyamatban használja, amely hibánál nem állít valótlan sikert és nem módosít rejtetten más adatot.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-033-01:** Felhasználóként szeretném látni a szokatlannak jelölt költéseket, hogy gyorsan ellenőrizhessem a váratlan eltéréseket.
- **US-033-02:** Felhasználóként szeretném érteni, milyen korábbi mintához képest számít egy költés szokatlannak, hogy ne kezeljem indokolatlan riasztásként.
- **US-033-03:** Felhasználóként szeretném a jelzésből megnyitni az érintett nyugtát, hogy ellenőrizhessem vagy javíthassam az alapadatot.
- **US-033-04:** Felhasználóként szeretném tudni, ha kevés adat miatt nem állapítható meg megbízható eltérés, hogy ne kapjak hamis bizonyosságot.
- **US-033-05:** Felhasználóként szeretném a téves jelzést visszajelzéssel ellátni, hogy a későbbi értelmezés pontosabb lehessen.

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
