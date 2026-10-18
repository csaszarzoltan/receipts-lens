---
id: UX-2026-10-12
status: SPEC_READY
version: 1
---

# Felhasználóbarát munkaterület – végrehajtási specifikáció

## 1. Cél
A jóváhagyott UX-terv végrehajtása, háztartási elsődleges célcsoporttal.

## 2. Kontextus és források
[UX-terv](../plans/receiptlens-ux-elemzes-es-fejlesztesi-terv-2026-10-12.md). A felhasználó „Implementáld a tervet” utasítása adja a végrehajtási felhatalmazást. A gyökér METHODOLOGY.md jelenleg nem található; a meglévő SPEC-006 14 fejezetes szerkezetét és .agents/rules/methodology.md szabályait használjuk.

## 3. Scope
Frontend/API javítások és regressziós ellenőrzés. Publikálás, commit és felhasználói interjú nem része az implementációnak. A vizsgálati eredményeket nem helyettesítjük kódra alapozott állítással.

## 4. Szereplők és előfeltételek
Hitelesített háztartási felhasználó; tenant-szigetelés és írási jogosultság változatlan. Meglévő útvonalak megtartása.

## 5. Követelmények
- REQ-UX-01 [MUST]: A fájlválasztó kattintással és billentyűzettel működik.
- REQ-UX-02 [MUST]: Azonos nevű fájlok saját tartalmukkal kerülnek feltöltésre.
- REQ-UX-03 [MUST]: Hiányzó megbízhatóság ismeretlen, nulla érték megmarad.
- REQ-UX-04 [MUST]: Kategória és dátum a teljes gyűjteményen szűr, lapozás előtt.
- REQ-UX-05 [MUST]: Átmeneti hálózati hiba nem törli a munkamenetet.
- REQ-UX-06 [MUST]: Feltöltés azonos idempotenciakulccsal nem hoz létre másolatot, újraindítás után sem.
- REQ-UX-07 [MUST]: A fő folyamat magyar feliratai következetesek.
- REQ-UX-08 [MUST]: Legfeljebb öt mobil fő célpont, régi útvonalak elérhetők.
- REQ-UX-09 [MUST]: Üres dashboard egy fő lépést mutat.
- REQ-UX-10 [MUST]: Közös, kihagyható bevezetés az első nyugtához vezet.
- REQ-UX-11 [MUST]: Bizonytalan nyugtánál közvetlen ellenőrzési művelet látszik.
- REQ-UX-12 [MUST]: Dialógus fókuszt tart, Escape bezár és visszaadja a fókuszt.
- REQ-UX-13 [MUST]: Hiányos költési adatok a napi/havi összegzésben látszanak.
- REQ-UX-14 [MUST]: Státuszok különböznek és a szűrők visszalépéskor megmaradnak.
- REQ-UX-15 [MUST]: Egységes ikon-, állapot- és érintési rendszer.
- REQ-UX-16 [MUST]: Kategóriajavaslat megerősíthető, felülírható; történeti adatok nem változnak.
- REQ-UX-17 [MUST]: Értesítés közvetlen célhoz vezet és beállítható.
- REQ-UX-18 [MUST]: Mentés után következő nyugta közvetlenül rögzíthető.
- REQ-UX-19 [MUST]: Pénznem beállításból származik; hiányában nincs csendes USD-összegzés.

## 6. Nem funkcionális követelmények
Érintési célok legalább 44 px; látható fókusz; segítő technológia állapotjelzés; titok és nyugtatartalom nincs új analitikában. Külső szolgáltatás nem szükséges a tesztekhez.

## 7. UI-szerződés
Áttekintés, Nyugták, Hozzáadás, Pénzügyeim, Továbbiak; részletes üzleti utak a Továbbiak alatt. Üres, betöltő, hibás és sikeres állapotok különböznek.

## 8. GUI-folyamat
Belépés → közös bevezetés → fotó/fájl → feltöltés/feldolgozás → mezők ellenőrzése → nyugta → következő feltöltés. Keresés URL-alapú szűrőkkel.

## 9. Állapotmodell
Feltöltés: queued → uploading → processing → done/error; error → retry ugyanazzal a kulccsal. A törlés csak befejezett/hibás helyi sor elrejtése, nem szerveroldali megszakítás. Session: checking → authenticated/retryable_error/unauthenticated.
Idempotencia: tenant + kulcs + tartalom/opciók ujjlenyomat; sikeres eredmény tartós, automatikus lejárat nélkül. Eltérő kérés azonos kulccsal 409. Sikertelen tranzakció visszagörgethető és újrapróbálható. Másik folyamat foglalt adatbázisa 503 és Retry-After lehet; nem készít másolatot. Retencióval törölt nyugta eredménye tartalommentes tombstone lesz; régi kulcs újrajátszása 409, nem hozza vissza a törölt adatot.

## 10. Acceptance scenario-k
- AC-UX-01: a REQ-UX-01 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-02: a REQ-UX-02 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-03: a REQ-UX-03 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-04: a REQ-UX-04 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-05: a REQ-UX-05 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-06: a REQ-UX-06 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-07: a REQ-UX-07 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-08: a REQ-UX-08 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-09: a REQ-UX-09 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-10: a REQ-UX-10 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-11: a REQ-UX-11 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-12: a REQ-UX-12 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-13: a REQ-UX-13 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-14: a REQ-UX-14 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-15: a REQ-UX-15 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-16: a REQ-UX-16 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-17: a REQ-UX-17 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-18: a REQ-UX-18 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.
- AC-UX-19: a REQ-UX-19 szerinti művelet az elvárt megfigyelhető viselkedést adja; a regressziós teszt külön hivatkozik az azonosítóra.

## 11. Hibák és szélső esetek
Elveszett feltöltési válasz, párhuzamos kulcs, eltérő tenant, szerver újraindítás, feldolgozási hiba, nulla confidence, 50 elemen túli találat, érvénytelen dátum, API-hiba, ismeretlen pénznem.

## 12. Adat- és API-szerződés
/product/receipts category/date_from/date_to és kategóriafacetta. /product/receipts/upload Idempotency-Key; eredménnyel közös SQLite tranzakció. Új verziózott migráció az upload_commands táblához. Dashboard explicit pénznem + ismert/ismeretlen forrás. Kategóriaajánlás háztartáson belül, kizárólag megerősített mintából.

## 13. Tesztleképezés és minőségi kapu
Backend: tests/test_ux_plan.py. Frontend: frontend/tests/ux-regressions.cjs és frontend/e2e/ux-plan.spec.ts. Kötelező sorrend: specifikáció → futtatható RED → implementáció → célzott GREEN → typecheck/build/regresszió. SPEC_READY: minden tervtétel azonosított, scope és API-szerződés rögzített, végrehajtási felhatalmazás meglévő felhasználói utasításból.

## 14. Kockázatok
Hosszú OCR tranzakció adatbázisírókat várakoztathat; foglaltság újrapróbálható. A kvóta jelenlegi memóriabeli tárolását nem tekintjük tartós számlázási garanciának. Az offline folyamat és valódi felhasználói próba külön validálás marad. A teljes terv készültségét az átadási jelentés követelményenként rögzíti.

## Véleményezési kiegészítés (2026. október 12.)

A végrehajtási felhatalmazás a mobil onboarding, a hibás tesztállítások, a hidratálás és a kvótafrissítés javítására is kiterjed. REQ-UX-10/AC-UX-10 kiegészítés: 390×844-en a fő gomb a modal görgethető területén elérhető és kattintása a feltöltéshez vezet, nem a háttérbezárást aktiválja. REQ-UX-07/AC-UX-07: a hydration snapshot szerver/kliens között egyezik, majd a tárolt nyelv aktiválódik; magyar újrapróbálási címke „Újrapróbálás”. REQ-UX-06/AC-UX-06: lezárult feltöltés után a kvótakérés újraérvényesül. A migrációt kizárólag privát, helyi read-only backup másolaton ellenőrizzük, személyes adatok naplózása nélkül. A production eredeti adatbázis nem módosítható a próba során.


## Kamerafolyamat és tesztszerződések kiegészítése (2026. október 13.)

REQ-UX-18/AC-UX-18: egy függő kameranyitási kérés alatt az ismételt aktiválás nem indít második kérést. A várakozás megszakítható; bezárás vagy komponens-eltávolítás után később beérkező stream minden trackjét le kell állítani. A fotógomb csak az előnézet betöltése után használható. Egy kép kódolása alatt további fotó nem indulhat; bezárás vagy eltávolítás után visszaérkező kódolási eredmény nem adhat hozzá fájlt. Sikertelen képkódolás a dialógusban olvasható hibát ad, és a kamera megtartásával újrapróbálható. Egy sikeres kép pontosan egyszer kerül a feltöltési sorba.

REQ-UX-12/AC-UX-12 kamerás böngészős regresszió: billentyűzettel a fókusz a kameradialógusban marad, Escape bezár, fókusz visszakerül a kameragombra, a videotrack véget ér. A szintetikus canvas-stream nem helyettesíti a valódi kamera vagy képernyőolvasó próbáját.

A korábbi F1.5 három bevezető diát előíró szerződését a jóváhagyott REQ-UX-10 közös, közvetlen nyugtarögzítési folyamata váltja fel. A korábbi US-019 közvetlen üzleti menüje a REQ-UX-08 szerint a Továbbiak oldalon marad elérhető. A régi forrásalakot ellenőrző tesztek helyett a közös folyamat bekötését, a frontend futtatható mentési/hibakezelési regresszióit és a megmaradó üzleti elérhetőséget ellenőrizzük.


## Teljes véleményezésből származó kötelező regressziók

REQ-UX-12: kameraindításkor a foglaltságjelzés nem szüntetheti meg az indítógomb fókuszálhatóságát; a bezárás utáni fókuszvisszaadás böngészőben ellenőrizendő. REQ-UX-09/13: a dashboard egyszerűsítése nem törölheti a meglévő háztartás tagjait, közös pénzügyi állapotát vagy a megtakarítási lehetőségek megjelenítését. Ezek a nyugtákkal rendelkező nézetben maradnak, az első nyugtás üres nézetben nem adunk hozzá másodlagos pénzügyi kártyákat.
