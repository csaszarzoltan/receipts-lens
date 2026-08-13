# BUG-011: API kép-feldolgozás limit — a fejlesztő a határt túllépve próbált képeket feldolgozni

- **Dátum:** 2026-08-13
- **Projekt:** receipts-lens
- **Státusz:** Accepted

## Mi volt a hiba / döntés?

A képek feldolgozásánál a fejlesztő 200 feletti képszámot próbált feldolgozni,
ami túllépte az API határt (max 200) — a feldolgozás hibát dobott.

## Gyökér-ok

A határ (200) a dokumentációban és a kódban is létezett, de a worker nem
ismerte fel időben, és a határon túli kérést küldött az API-nak.

## Fix / döntés

A limit ellenőrzése a kérések előtt (client-side guard), a hibaüzenet pedig
egyértelműen jelzi a limitet. A tesztek is lefedik a 200-as határt.

## Amit NE csináljunk többé (anti-minta)

- Ne küldjünk a dokumentált limit feletti kérést az API-nak — előbb ellenőrizd
- Ne feltételezd, hogy a worker tudja a limitet — írd bele a promptba/kontraktusba

## Helyette EZT csináljuk

- A limit-eket a kódban és a dokumentációban is tartsd karban; a tesztek
  lefedik a határértékeket (boundary + over-limit)

## Verifikáció

A BUG-011-hez tartozó tesztek zöldek; a feldolgozás 200-ig megy, afelett
egyértelmű hibát ad.
