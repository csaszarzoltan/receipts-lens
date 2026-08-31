---
description: "A ReceiptLens követelményvezérelt módszertanának (METHODOLOGY.md) kötelező érvényesítése"
always_on: true
---

# Követelményvezérelt Módszertan (METHODOLOGY.md) Betartása

## 1. Alapelv
A projekt kizárólagos és autoritatív módszertana a gyökérkönyvtárban található `METHODOLOGY.md` (Requirements-driven Verified AI Development - RVAD 1.1).

## 2. Kötelező szabályok minden művelethez
1. **Specifikációvezérelt működés (SPEC fázis):**
   - Minden új funkciót vagy módosítást a `METHODOLOGY.md` 4. fejezete szerinti 14 pontos sablon alapján kell specifikálni.
   - Nincs kódolás elfogadott specifikáció és minőségi kapu (`SPEC_READY`) nélkül.

2. **Viselkedésalapú megközelítés (Behavior-first & BUILD fázis):**
   - Először a futtatható teszt készül el a specifikáció acceptance scenario-i (`AC-xxx`) alapján.
   - RED bizonyíték szükséges: igazolni kell, hogy a teszt elindul és valódi hiány miatt bukik el.
   - Csak ezután jöhet a minimális forráskód-módosítás (GREEN állapot elérése).

3. **Követelmény-lefedettség és Traceability (VERIFY fázis):**
   - Minden kötelező funkcionális követelményhez (`REQ-xxx [MUST]`) legalább egy futtatható tesztnek kell tartoznia (100% requirement coverage).
   - A teszteknek hivatkozniuk kell a pontos `REQ-xxx` és `AC-xxx` azonosítókra.

4. **Kód- és QA határok:**
   - QA szerepkörben szigorúan tilos az alkalmazáskód (`src/`, `app/`, `frontend/`) módosítása.
   - Az LLM saját szöveges állítása nem bizonyíték; kizárólag determinisztikus eszközök (tesztfuttató, linter, typecheck) dönthetnek a sikerről.
