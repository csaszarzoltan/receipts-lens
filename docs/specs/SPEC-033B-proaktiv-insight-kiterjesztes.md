---
id: FEAT-033B
title: Proaktív insight-kiterjesztés (FEAT-033 + FEAT-026)
status: draft
version: 1
risk: medium
owner: documenter
related_brief: none
extends: FEAT-033
---

# FEAT-033B: Proaktív insight-kiterjesztés a szokatlan költésekre

> Előretekintő (forward) kiterjesztés-specifikáció a VERITAS 1.1 §4.5
> 16-fejezetes szerkezetében. Ez NEM új FEAT: a FEAT-033
> (SPEC-033-szokatlan-koltesek) és a FEAT-026
> (SPEC-026-ertesitesek) meglévő képességeire épülő kiterjesztés.
> Forrás: `docs/research/2026-09-11-ai-chat-deep-dive.md` 2(c) fejezete
> (RL RESEARCH-1, t_e8a9057c). Döntés: olvasó-chat + proaktív insight
> együtt szállítandó; ez a SPEC a proaktív ágat fedi le.
>
> FIGYELEM — függőség feloldva: a "Megnyitás a chatben" mélylink célja a
> FEAT-049 olvasó-chat (`docs/specs/SPEC-049-ai-olvoso-chat.md`,
> `POST /api/v2/chat/ask` + chat-panel a Nyugták-listán belül).
> Kód és teszt nem tartozik e SPEC-hez;
> a 10. és 12. fejezet CÉL-szerződéseket (nem megvalósított viselkedést)
> rögzít.

## 1. Cél és felhasználói eredmény

A passzív felhasználó — aki nem nyitja meg a költéselemzést — háttérben
futtatott, ütemezett kiértékelés alapján értesítés-kártyát kap, ha a
saját háztartásában szokatlan költési jel (FEAT-033) vagy keret-közeli
állapot (FEAT-012) keletkezik. A kártya magyarázza a jelet ("mihez
képest szokatlan"), egy kattintással megnyitható a chatben (FEAT-049),
téves jelzésként visszajelezhető, és az insight-értesítések
leiratkozással kikapcsolhatók — így a proaktív csatorna nem válik
zajforrássá.

Mérhető készültségi feltétel: minden alábbi REQ-033B követelményhez
AC-scenario tartozik (11. fejezet); küszöb alatti jel nem generál
kártyát; azonos jel nem duplikálódik; a "téves jelzés" arány
megfigyelhető (15. fejezet).

## 2. Kontextus és források

Kanonikus források:

- `docs/research/2026-09-11-ai-chat-deep-dive.md` 2(c) fejezet
  (adat-scope: olvasó-scope + FEAT-033 jelek + FEAT-012 keretek;
  háttérben futó ütemezett kiértékelés; értesítés-kártya FEAT-026
  csatornákon + mélylink; zaj-kontroll küszöbbel és REQ-033-05 szerinti
  visszajelzéssel; RICE-győztes opció, 180 pont)
- `docs/specs/SPEC-033-szokatlan-koltesek-felismerese-es-magyarazata.md`
  (REQ-033-01..08: jel-lista, REQ-033-02 magyarázhatóság, REQ-033-04
  kevés-adat jelzés, REQ-033-05 téves-jelzés visszajelzés)
- `docs/specs/SPEC-026-ertesitesek-es-allapotuzenetek.md` (REQ-026-01..05:
  panel, olvasatlan-kezelés, mélynavigáció, elvetés, csatorna-beállítás)
- `docs/specs/SPEC-012-haztartasi-keretek-es-riasztasok.md` (keretek,
  küszöb-riasztások, nyugtázás)
- FEAT-049 olvasó-chat (`docs/specs/SPEC-049-ai-olvoso-chat.md`,
  `POST /api/v2/chat/ask` + chat-panel a Nyugták-listán belül) — élő
  függőség, a mélylink célja
- `VERITAS_1_1_adaptiv_egyseges_fejlesztesi_modszertan.md` §4.5, §6 (R2)

Kapcsolódó domain-invariánsok: szerveroldali jogosultság, háztartási
adatelkülönítés, explicit megerősítés helyett zaj-kontroll (küszöb +
leiratkozás), hibánál részleges állapot tilalma, ismételt kiértékelés
biztonsága (dedup).

## 3. Scope és non-scope

### Benne van

- Ütemezett, háttérben futó kiértékelés a FEAT-033 jelekre és a FEAT-012
  keret-állapotokra a saját háztartás adatain.
- Értesítés-kártya a FEAT-026 csatornákon (értesítési panel + toast) a
  küszöb feletti, magyarázható jelekről.
- "Megnyitás a chatben" mélylink a kártyán a FEAT-049 felületre
  (élő függőség: `docs/specs/SPEC-049-ai-olvoso-chat.md`).
- Zaj-kontroll: konfidencia-küszöb, REQ-033-02 szerinti magyarázhatóság,
  REQ-033-05 szerinti "téves jelzés" visszajelzés, leiratkozás.
- Dedup: azonos jel ismételt kiértékelése nem generál új kártyát.

### Nincs benne

- Új detekciós algoritmus: a jelképzés a FEAT-033 hatásköre, ez a SPEC
  csak a proaktív kézbesítést és zaj-kontrollt definiálja.
- Maga a chat-felület: az a SPEC-049 (FEAT-049) hatásköre.
- Író-chat (kategória-javítás, szabály-állítás): külön R3-as SPEC
  hatásköre (kutatási doksi 2(b) opciója).
- Új értesítési csatorna (push/SMS): csak a FEAT-026-ban meglévő
  csatornák használhatók.

## 4. Szereplők és előfeltételek

- ACT-033B-01: háztartási felhasználó (kártyát kap, chatben megnyit,
  téves jelzést jelez, leiratkozik).
- ACT-033B-02: háztartási tulajdonos (kereteket állít be — FEAT-012 —,
  ezzel az insight-kontextust is hangolja).
- ACT-033B-03: termékfelelős (küszöb-defaultot és ütemezési gyakoriságot
  állít be, a "téves jelzés" arányt figyeli).

- PRE-033B-01: a FEAT-033 jelforrás (`GET /forecasts/anomalies`
  szerinti anomália-jelek) és a FEAT-012 keret-állapotok elérhetők a
  saját háztartásra.
- PRE-033B-02: a FEAT-026 értesítési csatornák (panel + toast) működnek.
- PRE-033B-03: a FEAT-049 olvasó-chat elérhető a mélylink céljaként
  (`docs/specs/SPEC-049-ai-olvoso-chat.md` szerint).

## 5. Funkcionális követelmények

- REQ-033B-01 [MUST]: A rendszer felhasználói kérés nélkül, ütemezetten
  kiértékeli a saját háztartás FEAT-033 anomália-jeleit (háttérben futó,
  kötegelt kiértékelés).
- REQ-033B-02 [MUST]: A kiértékelés figyelembe veszi a FEAT-012
  keret-állapotokat; keret-közeli vagy keretet túllépő kategória
  kontextusként megjelenik a kártyán.
- REQ-033B-03 [MUST]: Küszöb feletti jel esetén értesítés-kártya jelenik
  meg a FEAT-026 csatornákon (értesítési panel + toast), a REQ-026-01..04
  szerinti viselkedéssel (olvasatlan-megkülönböztetés, kapcsolódó
  feladathoz jutás, elolvasott/elvetett állapot).
- REQ-033B-04 [MUST]: A kártya "Megnyitás a chatben" mélylinket
  tartalmaz, amely a FEAT-049 olvasó-chat felületére visz az insight
  kontextusával (`docs/specs/SPEC-049-ai-olvoso-chat.md` szerint).
- REQ-033B-05 [MUST]: Csak konfidencia-küszöb feletti, magyarázható jel
  generálhat kártyát; a kártya tartalmazza a REQ-033-02 szerinti
  magyarázatot ("milyen korábbi mintához képest szokatlan"); küszöb
  alatti jel nem generál értesítést. Kevés adat esetén a REQ-033-04
  szerinti "nem megállapítható" jelzés érvényesül (nincs kártya hamis
  bizonyossággal).
- REQ-033B-06 [MUST]: A kártyán elérhető a REQ-033-05 szerinti "Téves
  jelzés" visszajelzés és az insight-értesítésekről való leiratkozás; a
  visszajelzés naplózódik a későbbi értelmezés pontosításához;
  leiratkozott felhasználó nem kap új insight-kártyát.
- REQ-033B-07 [MUST NOT]: A kiértékelés és a kártya nem teheti
  elérhetővé más háztartás vagy más felhasználó védett adatait
  jogosultság nélkül (REQ-033-06 minta).
- REQ-033B-08 [ALWAYS]: Sikertelen vagy megszakított kiértékelés nem
  generálhat kártyát és nem jelenhet meg sikeres insight-ként; a hiba
  naplózódik, a következő ütemezett futás pótolja.
- REQ-033B-09 [CONCURRENCY]: Azonos jel ismételt vagy párhuzamos
  kiértékelése nem hozhat létre duplikált kártyát; az ütközést a
  jel-azonosító alapú dedup determinisztikusan kezeli.

## 6. Nem funkcionális követelmények

- NFR-033B-01 [PERFORMANCE]: a kiértékelés kötegelt háttér-feladatként
  fut, felhasználó-arányos LLM-költség nélkül futtatható (kutatási doksi
  3. fejezete); a kártya-kézbesítés UI-visszajelzése a FEAT-026 500
  ms-os szabályát követi.
- NFR-033B-02 [ACCESSIBILITY]: a kártya és műveletei (megnyitás,
  téves-jelzés, leiratkozás) billentyűzettel végigvihetők, a fókusz
  sorrendje determinisztikus, az állapotváltozás segítő technológiával
  érzékelhető (NFR-026-02 minta).
- NFR-033B-03 [SECURITY]: a szerveroldali identitás és jogosultság az
  autoritatív; a kiértékelés tenant-szűrt; a mélylink célja is csak a
  saját háztartás adatait nyithatja meg.
- NFR-033B-04 [PRIVACY]: a kártya, a naplók és a visszajelzés-tároló
  csak a feladat elvégzéséhez szükséges adatot tartalmazhatják
  (összeg, kategória, indok); teljes OCR-szöveg és kép soha nem kerül
  értesítésbe vagy prompt-naplóba.

## 7. UI-szerződés

- UI-033B-01: insight-kártya a meglévő `NotificationPanel` /
  `Toast` felületeken (FEAT-026): összeg + kategória + "mihez képest
  szokatlan" magyarázat (REQ-033-02) + opcionális keret-kontextus
  (FEAT-012); üres/hibás állapotban érthető következő lépés.
- UI-033B-02: "Megnyitás a chatben" művelet a kártyán — mélylink a
  FEAT-049 felületre az insight kontextusával
  (`docs/specs/SPEC-049-ai-olvoso-chat.md` szerint).
- UI-033B-03: "Téves jelzés" visszajelző művelet + leiratkozási belépő a
  kártyán (REQ-033-05 minta); leiratkozott állapotban új kártya nem
  jelenik meg, a beállítás visszavonható.

## 8. Felhasználói és GUI-folyamat

1. Az ütemezett kiértékelés lefut a háztartás FEAT-033 jelein és
   FEAT-012 keret-állapotain (felhasználói indítás nélkül).
2. Küszöb alatti vagy nem magyarázható jel esetén nincs értesítés
   (csendes ág); kevés adat esetén nincs kártya (REQ-033-04).
3. Küszöb feletti, magyarázható jel esetén — ha a felhasználó nincs
   leiratkozva és azonos jelhez még nincs élő kártya — értesítés-kártya
   jelenik meg a FEAT-026 csatornákon.
4. A felhasználó a kártyáról megnyitja az érintett nyugtát vagy a
   "Megnyitás a chatben" mélylinkkel a FEAT-049 felületet.
5. Téves jel esetén "Téves jelzés" visszajelzést ad; a visszajelzés
   naplózódik.
6. Zavaró mennyiség esetén leiratkozik az insight-értesítésekről; a
   leiratkozás azonnal érvényesül és visszavonható.
7. Sikertelen kiértékelés esetén nincs kártya; a hiba naplózódik, a
   következő ütemezett futás pótolja.

## 9. Állapotmodell

Ütemezett kiértékelési és kártya-életút (CÉL-modell, nincs
implementálva):

- `IDLE` + ütemezett futás -> `EVALUATING`
- `EVALUATING` + nincs küszöb feletti jel -> `QUIET`
- `EVALUATING` + küszöb feletti, magyarázható jel -> `PENDING_CARD`
- `EVALUATING` + hiba -> `FAILED` (nincs kártya; naplózás; következő
  futás pótol)
- `PENDING_CARD` + leiratkozott felhasználó vagy élő duplikátum ->
  `SUPPRESSED` (dedup/leiratkozás elnyeli)
- `PENDING_CARD` + kézbesítés -> `DELIVERED`
- `DELIVERED` + megnyitás (nyugta vagy chat-mélylink) -> `OPENED`
- `DELIVERED` + "téves jelzés" -> `DISMISSED_FEEDBACK` (visszajelzés
  naplózva)
- `DELIVERED` + elolvasott/elvetett -> `READ` (REQ-026-04 minta)
- `DELIVERED` + leiratkozás -> `UNSUBSCRIBED` (új kártya nem generálható)

## 10. API-, esemény- és adatszerződés

CÉL-szerződések (nincs implementálva — a megvalósítás ezeket hozza
létre vagy a meglévőket bővíti):

### Újrafelhasznált (meglévő)

| Szerződés | Forrás | Szerep |
| :--- | :--- | :--- |
| `GET /forecasts/anomalies` | API-033-01 (SPEC-033) | jelforrás a kiértékeléshez |
| `GET /api/v2/notifications`, `PUT /api/v2/notifications/{id}/read`, `POST /api/v2/notifications/mark-all-read` | API-026-01..03 (SPEC-026) | kártya-kézbesítés és olvasott-kezelés |
| FEAT-012 keret-állapotok | SPEC-012 | keret-kontextus a kártyán |

### Tervezett (CÉL)

- Ütemezett kiértékelő feladat: háttér-feladat (gyakoriság termékdöntés,
  lásd 14. fejezet), tenant-szűrt, kötegelt; bemenet a fenti jelforrások,
  kimenet küszöb feletti insight-jelöltek.
- Insight-kártya payload (CÉL): jel-azonosító (dedup-kulcs),
  konfidencia, REQ-033-02 szerinti magyarázat-hivatkozás, opcionális
  keret-kontextus, FEAT-049 mélylink (`.../chat?insight=<jel-id>` —
  a pontos alakot a megvalósító a SPEC-049-cel összhangban rögzíti;
  a SPEC-049 OPEN-049-04 pontja a 033B-oldali szerződést várja).
- Visszajelzés-tároló (CÉL): "téves jelzés" események + leiratkozási
  állapot háztartás/felhasználó szinten; PII-maszkolt naplózás.

### Események

Új eseménybusz nincs; az ütemező a kiértékelőt indítja, a kiértékelő a
FEAT-026 kézbesítést használja. LLM-számítás nincs a kritikus úton: a
számítást determinisztikus lekérdezés/aggregáció végzi (FEAT-049
REQ-049-04 mintája).

## 11. Acceptance scenario-k

### AC-033B-01: ütemezett kiértékelés (REQ-033B-01)

Given saját háztartás FEAT-033 jelekkel
When az ütemezett kiértékelés lefut felhasználói indítás nélkül
Then a küszöb feletti jelek jelöltekké válnak, küszöb alattiak nem.

### AC-033B-02: keret-kontextus (REQ-033B-02)

Given keret-közeli vagy keretet túllépő kategória (FEAT-012)
When insight-jelölt keletkezik az adott kategóriában
Then a kártya a keret-kontextust is mutatja.

### AC-033B-03: kártya FEAT-026 csatornákon (REQ-033B-03)

Given küszöb feletti, magyarázható jel
When a kézbesítés megtörténik
Then a kártya megjelenik a panelen/toastban, olvasatlanul
megkülönböztetve, elvethetően.

### AC-033B-04: mélylink a chatbe (REQ-033B-04)

Given kézbesített insight-kártya (és elérhető FEAT-049 felület)
When a felhasználó a "Megnyitás a chatben" műveletet választja
Then a chat az insight kontextusával nyílik meg.
Megjegyzés: a mélylink-cél szerződése SPEC-049 szerint adott; a pontos
URL-alakot a megvalósító a két SPEC összhangjában rögzíti.

### AC-033B-05: küszöb + magyarázhatóság (REQ-033B-05)

Given küszöb alatti vagy nem magyarázható jel, illetve kevés adat
When a kiértékelés lefut
Then nem generálódik kártya; kevés adat esetén hamis bizonyosság
helyett mellőzés (REQ-033-04 minta).

### AC-033B-06: visszajelzés + leiratkozás (REQ-033B-06)

Given kézbesített kártya
When a felhasználó "Téves jelzés"-t jelez vagy leiratkozik
Then a visszajelzés naplózódik; leiratkozás után új kártya nem érkezik,
a beállítás visszavonható.

### AC-033B-07: tenant-izoláció (REQ-033B-07)

Given két háztartás adatai
When a kiértékelés és kézbesítés fut
Then egyik kártya sem tartalmaz idegen háztartás adatot.

### AC-033B-08: sikertelen kiértékelés (REQ-033B-08)

Given hibás jelforrás vagy megszakított futás
When a kiértékelés meghiúsul
Then nem jelenik meg kártya/siker; a hiba naplózódik, a következő
ütemezett futás pótolja.

### AC-033B-09: dedup (REQ-033B-09)

Given azonos jelhez már élő/kézbesített kártya tartozik
When a kiértékelés újra lefut
Then új kártya nem duplikálódik.

## 12. Tesztleképezés

CÉL-leképezés (implementáció hiányában mindegyik TERVEZETT; a
megvalósító commit tölti ki a fájl:sor hivatkozásokat):

| REQ | AC | Cél-teszt (státusz) |
| :--- | :--- | :--- |
| REQ-033B-01 | AC-033B-01 | ütemezett kiértékelő-teszt — TERVEZETT |
| REQ-033B-02 | AC-033B-02 | keret-kontextus teszt — TERVEZETT |
| REQ-033B-03 | AC-033B-03 | kártya-kézbesítés teszt (FEAT-026 csatornák) — TERVEZETT |
| REQ-033B-04 | AC-033B-04 | mélylink-teszt (SPEC-049 felületre) — TERVEZETT |
| REQ-033B-05 | AC-033B-05 | küszöb/magyarázhatóság-teszt — TERVEZETT |
| REQ-033B-06 | AC-033B-06 | visszajelzés/leiratkozás-teszt — TERVEZETT |
| REQ-033B-07 | AC-033B-07 | kereszt-tenant szivárgási teszt (negatív) — TERVEZETT |
| REQ-033B-08 | AC-033B-08 | hibaági teszt (nincs kártya) — TERVEZETT |
| REQ-033B-09 | AC-033B-09 | dedup-teszt — TERVEZETT |

Minőségi kapu: minden REQ-033B azonosító legalább egy AC-azonosítóhoz
és legalább egy célzott teszthez kapcsolódik; a megvalósításkor a
célzott teszteket a teljes regresszió mellett futtatni kell.

## 13. Kockázatok és emberi döntések

- HR-033B-01 (validity-kockázat): a hamis riasztás pénzügyi döntést
  terelhet (pl. indokolatlan költés-visszafogás) — ezért kötelező a
  konfidencia-küszöb (REQ-033B-05), a REQ-033-02 szerinti magyarázhatóság
  és a "téves jelzés" visszajelzés (REQ-033B-06). A "téves jelzés" arány
  termékmetrika (15. fejezet); romlása küszöb-szigorítást von maga után.
- HR-033B-02 (zaj/spam): a túl gyakori kártya az értesítési csatorna
  értékét rombolja — ezért kötelező a dedup (REQ-033B-09), a küszöb és a
  leiratkozás; az ütemezési gyakoriság termékdöntés (14. fejezet).
- Adatvédelem: kártya/napló nem tartalmazhat teljes OCR-t, képet vagy
  hitelesítő adatot (NFR-033B-04); prompt-naplózás tiltott vagy
  PII-maszkolt (kutatási doksi 4. fejezete).
- Jogosultsági megkerülés: minden védett erőforrás szerveroldali
  tenant-szűrést igényel (REQ-033B-07).
- Függőségi kockázat: a mélylink célja (SPEC-049) SPEC-oldalon adott,
  de implementáció oldalán még nincs meg — a kártya chat nélkül is
  értékes (nyugta-megnyitás REQ-033-03 mintára).

## 14. Nyitott kérdések és SPEC-GAP

Nyitott termékdöntések (nem blokkolják a SPEC-et, de a megvalósítást
igen):

- OQ-033B-01: ütemezési gyakoriság (napi? heti? eseményvezérelt, pl.
  új nyugta után?).
- OQ-033B-02: konfidencia-küszöb default értéke és ki állíthatja
  (termékfelelős vs. felhasználó).
- OQ-033B-03: opt-in vagy opt-out modell az insight-értesítésekre.

SPEC-GAP (a SPEC többet állít, mint a meglévő kód):

- SPEC-GAP-033B-01: a FEAT-049 olvasó-chat SPEC-oldala adott
  (`docs/specs/SPEC-049-ai-olvoso-chat.md`), de implementációja még
  nincs; a pontos mélylink-URL-t a megvalósító a két SPEC összhangjában
  rögzíti (SPEC-049 OPEN-049-04).
- SPEC-GAP-033B-02: az ütemezett kiértékelő motor és a dedup-tároló
  nincs implementálva; a 10. fejezet CÉL-szerződései terv-státuszúak.
- SPEC-GAP-033B-03: a "téves jelzés" visszajelzés-tároló és a
  leiratkozási állapot perzisztenciája nincs implementálva.

## 15. Rollback és megfigyelhetőség

- Rollback: migráció nincs; a funkció feature-flag mögött kapcsolható
  (kártya-generálás letiltása); leiratkozási állapotok megmaradnak.
  Visszaállítás telepítéssel, adatmigráció nélkül.
- Megfigyelhetőség (CÉL-metrikák): kiértékelési futások száma/sikere;
  küszöb feletti vs. küszöb alatti jelek aránya; kézbesített kártyák;
  elnyomott duplikátumok (dedup-találatok); "téves jelzés" arány;
  leiratkozások száma; chat-mélylink megnyitási arány (SPEC-049 után).
  A "téves jelzés" arány romlása küszöb-felülvizsgálati riasztást vált ki.

## 16. Definition of Done

- [ ] mind a 9 REQ-hez AC (9/9 megvan ebben a SPEC-ben).
- [ ] célzott tesztek implementálva és zöldek (12. fejezet — a
  megvalósító tölti ki).
- [ ] kereszt-tenant szivárgási teszt negatív.
- [ ] küszöb alatti jel nem generál kártyát (AC-033B-05 zöld).
- [ ] dedup igazolt (AC-033B-09 zöld).
- [ ] SPEC-049 implementációjakor AC-033B-04 zöld (mélylink-cél
  SPEC-oldala adott, a pontos URL-t a megvalósító rögzíti).
- [ ] visszamutatás SPEC-033B ↔ SPEC-033/026/012/049
  (`docs/traceability-index.md` §7).
- [x] production kód nem változott (docs-only SPEC).
