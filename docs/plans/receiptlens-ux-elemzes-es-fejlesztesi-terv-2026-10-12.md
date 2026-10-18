# ReceiptLens – részletes használhatósági elemzés és fejlesztési terv

**Dátum:** 2026. október 12.  
**Státusz:** véleményezésre kész javaslat; nem elfogadott implementációs specifikáció.  
**Cél:** könnyebben megtanulható, megbízhatóbb és szívesebben használt alkalmazás kialakítása.  
**Elsődleges célcsoport a tervben:** magánszemélyek és háztartások. Az üzleti és könyvelői használat külön belépési pontot kapna.

## 1. Vezetői összefoglaló

**Célcsoport-döntés ebben a tervben:** a magánszemélyek és háztartások használata az elsődleges. A navigációt, a kezdőoldalt és az első használat folyamatát ehhez igazítjuk. A vállalkozói és könyvelői funkciók külön üzleti munkaterületen maradnak elérhetők; a célcsoport kiválasztása nem nyitott véleményezési kérdés.

A ReceiptLens értékes problémát old meg: a nehezen áttekinthető nyugtákból használható kiadási adatokat készít, és ezekhez költségkeretet, garanciákat, előfizetéseket és pénzügyi áttekintést kapcsol. A legjobb termékígéret: **„Fotózd le a nyugtát, ellenőrizd az összeget, és lásd, mire ment el a pénzed.”**

A jelenlegi felépítésben az alapfeladat köré sok különálló felület épült. Egy új felhasználónak ezért túl korán kell eldöntenie, melyik funkció mire való, hogyan függnek össze a státuszok, és hol javíthatja ki a felismert adatokat. A használhatóságot néhány konkrét működési hiba is gyengíti.

Az első lépés a feltöltés, az ellenőrzés és a keresés rendbetétele. Ezt kövesse a navigáció egyszerűsítése és a kezdőoldal átalakítása. Az új funkciók bővítését későbbre tenném, amíg az alapfolyamat nem működik következetesen.

**Előzetes értékelés: körülbelül 6/10 egy új, nem szakértő felhasználó számára.** Ez kvalitatív szakmai becslés, nem mért használhatósági eredmény. A termékben megvan az érték, de a felület még nem mindenhol teszi könnyen hozzáférhetővé.

## 2. Az elemzés módszere és korlátai

Az elemzés a helyi projekt frontendjének forráskódjára és a README termékleírására épül. Átnézett területek: navigáció, alkalmazáskeret, kezdőoldal, belépés, bevezetés, feltöltés, feltöltési állapotok, nyugtalista, részletező oldal, ellenőrzési felület, közös dialógus és alapstílusok.

**Az eredeti elemzés szerzője nem végzett élő böngészős tesztet.** A véleményező későbbi beszámolója szerint a fejlesztés során 20 fő oldalt élő böngészőben, magyarul, két szélességen, axe-vel ellenőrzött: az `/inbox` duplikált main landmarkjának javítása után az ellenőrzött oldalak automatizált vizsgálata tisztán futott. Ez a véleményező által közölt eredmény, itt nem újrafuttatott ellenőrzés; **a billentyűzetes és képernyőolvasós használat továbbra sincs tesztelve**. Az automatizált eredmény nem bizonyít teljes akadálymentességet. Az eredeti elemzésben OCR-pontosságmérés és felhasználói interjú sem történt; a betöltési sebesség és a kamerahasználat eszközönkénti viselkedése külön ellenőrzést igényel. A dokumentum nem biztonsági vagy jogi audit.

**Későbbi véleményezési frissítés:** a véleményező az UX-megvalósítást élő scratch-szerveren, desktop és 390 px mobil nézetben is bejárta. A repóbeli Playwright-suite 4/8, a három tesztállítás javításával készített scratch-változat 8/8 eredményt adott; a mobil onboardingban ettől független, ténylegesen levágott fő műveletet talált. Az élő feltöltési idempotenciát is ellenőrizte. A javítások, a production DB másolatának migrációs próbája és a fennmaradó kiadási kapu a [megvalósítási jelentés 8. fejezetében](receiptlens-ux-megvalositas-2026-10-12.md) szerepelnek.

A megállapítások jelölése:

- **Kóddal igazolt:** közvetlenül látható a jelenlegi megvalósításban.
- **Véleményező által jelzett:** külső ellenőrzésből közölt megfigyelés; a dokumentum szerzője nem reprodukálta, a gyökérok külön vizsgálatot igényelhet.
- **UX-következtetés:** a felépítésből valószínűsíthető használati nehézség; próbával kell ellenőrizni.
- **Javaslat:** tervezett változtatás, amely még nem része az alkalmazásnak.

A felhasználói elégedettség és megtartás javulása hipotézis. A dokumentum egyik célja, hogy ezeket mérhetővé tegye.

## 3. Kinek készül a jobb felület?

| Felhasználó | Fő feladat | Mitől lesz elégedett? |
|---|---|---|
| Alkalmi használó | Egy nyugta elmentése és későbbi megtalálása | Kevés lépés, egyértelmű mentési visszajelzés |
| Tudatos háztartási költő | Költések követése, keret beállítása | Érthető, kellően teljes adatok és hasznos figyelmeztetés |
| Garanciát követő vásárló | Vásárlási bizonylat és határidő visszakeresése | A nyugtából közvetlen garanciarögzítés |
| Könyvelő vagy vállalkozás | Ellenőrzés, jóváhagyás, export | Pontos státuszok, ellenőrizhető adatok, hatékony tömeges műveletek |

A háztartási felület egyszerűsítését úgy kell megoldani, hogy a szakértői munkafolyamatok elérhetők maradjanak. Az egyszerűbb felirat nem fedheti el az export és a jóváhagyás közötti különbséget.

## 4. Megőrzendő erősségek

1. **Hasznos fő feladat:** a papírnyugtákból kereshető és összesíthető adat lesz.
2. **Kamerás és fájlos bevitel:** a `DropZone` több beviteli módot támogat.
3. **Eredeti kép és felismert adatok:** a részletező oldalon egymás mellé kerülnek asztali elrendezésben.
4. **Bizonytalanság jelzése:** léteznek megbízhatósági jelvények és külön ellenőrzési folyamatok; ezek értékesek, ha helyesen kommunikálnak.
5. **Gyakorlati pénzügyi kérdések:** a napi keret, garancia és előfizetés közelebb áll a felhasználó céljaihoz, mint a puszta adatexport.
6. **Új felhasználók támogatása:** kihagyható bevezetés, üres állapotok és mintanyugta.
7. **Vizuális alapok:** közös gomb- és kártyastílus, sötét téma, többnyelvű katalógus, csökkentett mozgást figyelembe vevő CSS.

Ezek megléte nem bizonyít teljes akadálymentességet vagy minden eszközön jó használhatóságot, de megfelelő alapot ad a fejlesztéshez.

## 5. Részletes megállapítások

### 5.1. Navigáció és információs felépítés

**Kóddal igazolt:** a fő navigáció 16 elemet, az üzleti csoport további 5 elemet tartalmaz. A mobil alsó sáv az első öt fő menüpontot és egy további menügombot jelenít meg. Az Ellenőrzés és Duplikátumok külön elsődleges mobil célpontok.

**UX-következtetés:** a felhasználónak több belső munkafázist kell megértenie, mielőtt egyszerűen elmentene egy vásárlást. A nyugta, ellenőrzés és duplikátum inkább ugyanazon feladat külön nézete lehetne.

**Javaslat:** négy fő célpont és egy központi hozzáadási művelet. A részletes modulok fokozatosan legyenek elérhetők. Az üzleti mód külön navigációt kapjon, de a módváltás ne változtasson jogosultságot.

### 5.2. Kezdőoldal és az első hasznos eredmény

**Kóddal igazolt:** a dashboard többek között napi keretet, háztartási állapotot, havi kategóriákat, árváltozásokat, határidőket, lemondható előfizetéseket, friss nyugtákat és megtakarítási lehetőségeket mutat. A blokkoknak külön üres állapotuk lehet.

**UX-következtetés:** új fióknál több üres kártya ismétli, hogy még nincs adat. A felület egyszerre kérhet feltöltést, keretbeállítást és további konfigurációt.

**Javaslat:** adat nélküli állapotban egy domináns „Első nyugta hozzáadása” kártya és egy rövid példa. Később a fő sorrend: havi költés → ellenőrzési teendő → friss nyugták → releváns figyelmeztetések.

### 5.3. Feltöltés és kamerahasználat

**Kóddal igazolt problémák:**

- A „Fájl kiválasztása” vizuális elem `span`, kattintási művelet nélkül. A nagy feltöltési terület külön működik.
- A feltöltési sorban hiba és eltávolítás van, közvetlen újrapróbálási művelet nincs.
- A sor eltávolítása és törlése csak a helyi bejegyzéseket távolítja el; a folyamatban lévő kérést nem állítja le.
- A feltöltési kód fájlnév alapján keresi vissza a fájlt. Két azonos nevű, eltérő tartalmú fájlnál ugyanaz az első fájl kerülhet mindkét kérésbe.
- Az oldal a nem elérhető AI Scan funkció ajánlóját is megjelenítheti.

**Javaslat:** valódi, billentyűzettel is működő fájlválasztó gomb; közvetlen fájl–sor hozzárendelés; újrapróbálás; a „listából elrejtés” és „feltöltés megszakítása” megkülönböztetése. A feldolgozás külön állapot legyen a feltöltéstől.

A kameránál ellenőrizni kell az engedélykérés elutasítását, az előnézet indulását, az oldal elhagyásakor a kamera leállítását és a gyenge kép javításának útját. Ezekhez valódi mobilos próbák szükségesek.

### 5.4. Nyugtaellenőrzés és bizalom

**Kóddal igazolt:** a részletező oldalon a megbízhatósági átlag csak a nullánál nagyobb értékeket veszi figyelembe. Ha ilyen nincs, az érték 1, vagyis 100%. Az ellenőrzési oldal ettől eltérő aggregálási logikát használ.

**Következmény:** a felület kedvező megbízhatóságot jelezhet akkor is, amikor az adatok hiányoznak vagy egyes mezők nulla értéket kaptak. Az oldalak egymással sem feltétlenül következetesek.

**Javaslat:** közös, dokumentált megbízhatósági szabály. A hiányzó érték legyen „nem ismert”; a nulla érték ne tűnjön el automatikusan. Az OCR pontszámot ne kommunikáljuk a helyesség garantált valószínűségeként. A felhasználó elsőként a teendőt lássa: „Ellenőrizd a végösszeget.”

Az összeg és pénznem különösen fontos. A tételek egyezése önmagában nem bizonyítja, hogy a nyugta minden mezője helyes. A tömeges jóváhagyás előtt a jóváhagyási feltételeket külön meg kell határozni.

### 5.5. Keresés és szűrés

**Kóddal igazolt:** a nyugtalista API-kérése keresést, státuszt és lapozást használ; a kategória- és dátumszűrést a kliens a már betöltött, legfeljebb 50 elemre alkalmazza. A kategóriaválasztó is ebből az oldalból készül.

**Következmény:** a teljes gyűjteményben meglévő találat nem feltétlenül látható, és egy kategória hiányozhat a választóból. A kijelzett teljes elemszám nem a kliensoldali szűrés eredménye.

**Javaslat:** a szűrés történjen a teljes, jogosultsággal elérhető gyűjteményen, a lapozás előtt. A dátum, kategória, találatszám és lapozás ugyanazokat a feltételeket használja. A szűrők kerüljenek az URL-be, hogy a visszalépés és megosztás megőrizze őket.

### 5.6. Nyelvezet és állapotnevek

**Kóddal igazolt:** a nyelvi katalógus mellett több komponensben maradtak angol szövegek, például a feltöltési sorban, a mobil menüben és a nyugtaadatok címkéinél. A státuszszűrőben a `completed` és `approved` azonos címkét kap, míg a `rejected` a megszakítás feliratát használja.

**Javaslat:** a teljes fő folyamat fordítása, beleértve a képernyőolvasó címkéit és hibaüzeneteit. A státuszok jelentése legyen egyértelmű. A felhasználó számára megjelenített státuszokat külön kell megfeleltetni a belső állapotoknak; pénzügyi jelentésüket nem szabad összevonni.

### 5.7. Bevezetés és belépés

**Elkészült P0 javítás – belépés:** a véleményező beszámolója szerint a korábbi megtévesztő működés (a „Belépés” dashboardot mutatott tényleges belépés nélkül) javítva és élesítve lett. A jelenlegi login kód saját e-mail-címet kér, és a normál belépési folyamat nem választ csendben demo-háztartást: a dashboardra irányítás tokenellenőrzés után történik. A demo-gomb külön fejlesztési kapcsolóhoz (`NEXT_PUBLIC_DEMO_LOGIN=1`) kötött. A normál belépési út változása kóddal ellenőrzött; az élesítés ténye a véleményező közlése. Ez a javítás elkészült tétel, nem új fejlesztési feladat.

**Kóddal igazolt:** a bejelentkezett keretben megjelenő bevezető modal szöveges lépéseket mutat és a dashboardra vezet. A külön onboarding oldal feltöltési lehetőséget is tartalmaz. Mindkettő nem végzetes hibaként kezeli a befejezés mentésének sikertelenségét.

**UX-következtetés:** két eltérő út van az első sikerhez, és sikertelen állapotmentés után a bevezetés ismét megjelenhet.

**Javaslat:** egyetlen közös bevezetési folyamat, amely a regisztrációval és belépéssel összhangban vezet az első mentett nyugtához. A kihagyás mindig legyen lehetséges. Belépési link kérésekor világosan látszódjon a következő lépés, a cél e-mail-cím és az újraküldés módja.

### 5.8. Hálózati hibák és munkamenet

**Kóddal igazolt:** az `AppShell` minden session-ellenőrzési hibánál törli a helyi tokent és a belépőoldalra irányít. Átmeneti hálózati vagy szerverhiba is ugyanezt az ágat érheti el.

**Javaslat:** külön kezeljük az érvénytelen munkamenetet, a hálózati hibát és a szerverhibát. Átmeneti hibánál maradjon meg a token, jelenjen meg egy újrapróbálható állapot. Védett adatok érvényes ellenőrzés nélkül továbbra se jelenjenek meg.

### 5.9. Akadálymentesség

**Kóddal igazolt:** vannak fókuszjelzések, aria-címkék és csökkentett mozgás támogatás. A közös `Modal` kezeli az Escape billentyűt és a háttér görgetését, de a megvalósításban nem látható kezdőfókusz, fókuszcsapda vagy visszaadott fókusz. A mobil menüben sem látható teljes fókuszkezelés.

**Javaslat:** közös dialógusviselkedés, billentyűzetes bejárhatóság, képernyőolvasóval közölt állapotváltozások. A kontrasztot és érintési célokat renderelt felületen is mérni kell.

### 5.10. Pénznem új háztartásban

**Véleményező által jelzett, még nem reprodukált P0 megfigyelés:** a helyi tesztben egy magyar nyelvű, üres háztartás költségkeret-kártyája `0,00 USD` értéket mutatott, angolul pedig `$0.00` jelent meg. A gyökérok nem ismert. A magyar nyelv önmagában nem bizonyítja, hogy a helyes pénznem HUF; ellenőrizni kell a háztartás tárolt pénznemét, az új fiók alapértékét, az API-választ és a megjelenítési formázást.

**Javaslat (UX-19):** a beállított pénznem következetes használata minden kapcsolódó összegzésben; ha a pénznem még nincs meghatározva, egyértelmű kiválasztás vagy jelzés a csendes USD-fallback helyett. A nyelvváltás a formázást változtathatja, a tárolt pénznemet nem. A feladat P0 kivizsgálásként indul; reprodukálás után határozható meg, hogy kliens-, API- vagy adatjavítás szükséges.

## 6. Javasolt kinézet

### 6.1. Vizuális irány

Nyugodt, áttekinthető pénzügyi segéd legyen az összhatás. A meglévő világos háttér, kék főszín és kártyák megtarthatók, de azonos súlyú kártyák helyett világos hierarchia kell.

| Elem | Javaslat | Miért? |
|---|---|---|
| Főszín | A jelenlegi kék a fő műveleteknél és kijelölt navigációnál | Egyértelmű következő lépés |
| Állapotszínek | Zöld: megerősített; borostyán: ellenőrzendő; piros: hiba | Következetes jelentés, mindig szöveggel együtt |
| Szövegméret | Alapszöveg jellemzően 16 px, másodlagos szöveg legalább 14 px | Mobilos olvashatóság |
| Érintési cél | Fő műveletek legalább 44 × 44 px | Könnyebb egykezes használat |
| Ikonok | Egységes SVG-készlet a navigációban | Következetes megjelenés eszközök között |
| Kártyák | Visszafogott keret és árnyék; kevesebb külön doboz | A tartalom kapjon hangsúlyt |
| Animáció | Rövid, állapotot jelző átmenetek | Visszajelzés figyelemelvonás nélkül |

Az ikonok neve és a szöveges felirat maradjon elérhető. A sötét témához külön vizuális ellenőrzés kell, nem elegendő a világos színek mechanikus cseréje.

### 6.2. Új navigáció

**Asztali fő menü:** Áttekintés, Nyugták, Pénzügyeim, Továbbiak. A „Nyugta hozzáadása” állandó fő művelet. Beállítások és profil a profilmenüben.

**Mobil alsó sáv:** Áttekintés | Nyugták | + Hozzáadás | Pénzügyeim | Továbbiak.

| Jelenlegi funkció | Javasolt hely |
|---|---|
| Feltöltés | Központi hozzáadási művelet |
| Ellenőrzés | Nyugták → Ellenőrzendő fül és darabszám |
| Duplikátumok | Nyugták → Lehetséges másolatok |
| E-mailes beérkezés | Nyugták → Beérkezett dokumentumok |
| Költségkeret, kimutatások, előrejelzés | Pénzügyeim |
| Előfizetések | Pénzügyeim; kapcsolódó figyelmeztetés az áttekintésen |
| Garanciák | Továbbiak; közvetlen link a nyugtából |
| Chat, tippek, adózási funkciók | Továbbiak, célcsoport szerinti elérhetőséggel |
| Jóváhagyás, export, könyvelés, integrációk, automatizációk | Üzleti munkaterület |

A meglévő útvonalakat nem szükséges azonnal átnevezni. A régi linkeknek és közvetlen hivatkozásoknak működniük kell.

### 6.3. Kezdőoldal – szöveges vázlat

```text
ÁTTEKINTÉS                         [+ Nyugta hozzáadása]

E havi rögzített költés: 84 250 Ft
12 mentett nyugta · 2 összeg még ellenőrzendő

[2 nyugta ellenőrzést kér]            [Ellenőrzöm]

Legutóbbi vásárlások
Lidl          okt. 10.       8 420 Ft        Megerősített
Drogéria      okt. 09.       3 890 Ft        Ellenőrzendő

[Költéseim kategóriánként]       [Keret és hátralévő összeg]

Csak ha releváns:
Közelgő garanciahatáridő / előfizetés megújulása
```

Ez koncepció, nem kész képernyőterv. A példaszámok szemléltető adatok.

Adat nélküli állapotban a fenti blokkok helyett: rövid ígéret, első nyugta gomb, mintanyugta. A keretbeállítás másodlagos lehetőség legyen.

### 6.4. Feltöltés és nyugta részletei

Mobilon a feltöltés fő gombja „Nyugta fotózása”, másodlagosan „Kép kiválasztása”. Asztali gépen a fájlválasztás és drag-and-drop legyen elsődleges. Az elfogadott formátumok és mérethatár röviden, az API valós képességeivel összhangban jelenjenek meg.

A részletező oldalon a végösszeg, pénznem, üzlet, dátum és kategória kerüljön előre. Mobilon a nyugtakép összehajtható vagy külön nagyítható legyen, hogy a javítandó mező gyorsan elérhető maradjon. Tételek, OCR-részletek és előzmények másodlagos szakaszokba kerüljenek.

## 7. Javasolt működés

### 7.1. Fő folyamat

```text
Fotó / fájl kiválasztása
  → rövid előnézet
  → feltöltés
  → feldolgozás
  → összeg, üzlet, dátum és pénznem ellenőrzése
  → mentési visszajelzés
  → következő nyugta vagy áttekintés
```

Az előnézetben az ismételt fotózás legyen könnyű. Automatikus körbevágás és elmosódottság-ellenőrzés későbbi fejlesztésként kerülhet be, ha valódi képeken bizonyíthatóan segít.

### 7.2. Feltöltési állapotok

| Állapot | Látható üzenet | Művelet |
|---|---|---|
| Várakozik | „Feltöltésre vár” | Eltávolítás |
| Feltöltés | „Kép feltöltése…” | Megszakítás, ha ténylegesen támogatott |
| Feldolgozás | „A nyugta adatainak felismerése…” | A folyamat állapotának követése |
| Ellenőrzendő | „A végösszeget ellenőrizd” | Javítás / megerősítés |
| Elkészült | „A nyugtát elmentettük” | Megnyitás / új nyugta |
| Sikertelen | Konkrét, közérthető ok | Újrapróbálás / másik kép |

A százalék csak olyan műveletet jelöljön, amelynél ismert a haladás. A feltöltés 100%-a nem egyenlő az OCR elkészültével.

**UX-06 kötelező API-előfeltétele:** a `/product/receipts/upload` jelenleg nem fogad `Idempotency-Key` fejlécet. A munkaterület-PATCH elfogad ilyen fejlécet, de eldobja; ez nem biztosít feltöltési másolatvédelmet. A biztonságos újrapróbáláshoz ezért szerveroldali idempotenciát kell megvalósítani a feltöltési végponton, majd ehhez kapcsolni a kliens újrapróbálási műveletét.

Az API-változtatás specifikációjának legalább az alábbiakat kell rögzítenie:

- A kliens egy logikai feltöltéshez egy kulcsot rendel, és újrapróbáláskor ugyanazt használja.
- A kulcs a hitelesített háztartáshoz/munkaterülethez kötött, és a fájltartalom, valamint a feldolgozási opciók azonosíthatóak.
- Azonos kulcs és azonos kérés ismétlésekor ugyanaz a nyugtaazonosító/eredmény érhető el, új nyugta létrehozása nélkül. Ez elveszett válasz és párhuzamos kérés esetén is teljesüljön.
- Azonos kulcs eltérő tartalommal vagy opciókkal nem használható csendben újra; a szerver dokumentált konfliktust jelezzen.
- A tárolás, a megőrzési idő, a folyamatban lévő kérés és a hibás feldolgozás újrapróbálása legyen dokumentált. A támogatott újrapróbálási időablakban szerver-újraindítás után is fenn kell maradnia a védelemnek.

Ez az ismételt kérés elleni védelem; az eltérő kulccsal újra feltöltött azonos nyugta felismerése külön duplikátumkezelési feladat. A UX-06 csak az API-garancia és a kliensintegráció együttes ellenőrzése után tekinthető késznek.

### 7.3. Pénzügyi adatok és teljesség

A havi költés mellett szerepeljen, hogy rögzített adatokból számolunk. Ismeretlen összegű nyugták esetén a hiány külön jelzés legyen, ne nulla költés. A napi keret mellett látszódjon a számítás alapja és a hiányos adatok hatása.

Nem kell minden oldalon hosszú magyarázat. Rövid jelzés és megnyitható részletezés elegendő: „2 nyugta összege még hiányzik.”

### 7.4. Kategorizálás és garanciák

A felhasználó által javított üzlet–kategória kapcsolat később felajánlható alapértelmezésként. Ne írjuk át észrevétlenül a korábbi nyugtákat. A tanult javaslat legyen felülírható.

A nyugtából indított garanciarögzítésben a már ismert üzlet és vásárlási dátum legyen előtöltve, de a garancia időtartamát ne tekintsük automatikusan bizonyítottnak. A felhasználó erősítse meg a szükséges adatokat.

### 7.5. Értesítések és visszatérés

Az értesítés konkrét következő lépéshez vezessen. Előfizetésnél például a részletekhez és lemondási útmutatóhoz; garanciánál a kapcsolódó nyugtához. Gyakoriság és csatorna legyen szabályozható. Hasonló figyelmeztetéseket össze kell fogni.

Teljes offline nyugtakezelést csak külön validált adattárolási, adatvédelmi és szinkronizációs terv után vezetnék be. Elsőként az átmeneti hibák és el nem mentett javítások kezelését kell megoldani.

## 8. Prioritásos fejlesztési lista

**P0:** hibás vagy megtévesztő alapviselkedés. **P1:** fő folyamat egyszerűsítése. **P2:** használatot ösztönző kiegészítések.

| ID | Prioritás | Változtatás | Elfogadási feltétel |
|---|---|---|---|
| UX-01 | P0 | Valódi fájlválasztó gomb | Kattintásra és billentyűzettel megnyílik a választó |
| UX-02 | P0 | Fájlok egyértelmű hozzárendelése | Két azonos nevű, eltérő fájl a saját tartalmával kerül feltöltésre |
| UX-03 | P0 | Megbízhatósági jelzés javítása | Hiányzó pontszám nem jelenik meg 100%-ként; nulla érték nem vész el |
| UX-04 | P0 | API-bővítés kategória- és dátumszűréshez, majd kliensintegráció | A szűrés a lapozás előtt történik; az 50. elem utáni megfelelő találat is megtalálható; találatszám helyes |
| UX-05 | P0 | Hálózati és session-hibák szétválasztása | Hálózati hiba megőrzi a tokent; érvénytelen session belépést kér |
| UX-06 | P0 | Feltöltési API idempotenciájának megvalósítása és kliensoldali újrapróbálás | Azonos kulcsú újrapróbálás, elveszett válasz és párhuzamos kérés sem hoz létre új nyugtát; eltérő tartalmú kulcsújrahasználat konfliktust jelez; az újrapróbálás ugyanazon a felületen elérhető |
| UX-07 | P1 | Teljes főfolyamat magyarítása | Magyar beállításnál nincs indokolatlan angol műveleti vagy állapotfelirat |
| UX-08 | P1 | Egyszerű fő navigáció | Legfeljebb öt mobil fő elem; korábbi funkciók és linkek elérhetők |
| UX-09 | P1 | Kontextus szerinti kezdőoldal | Új fióknál egy domináns első lépés; meglévő adatnál hasznos összegzés |
| UX-10 | P1 | Közös bevezetés | Belépéstől az első mentett nyugtáig következetes út; kihagyható |
| UX-11 | P1 | Mezőszintű ellenőrzési útmutató | Az érintett mező és a javítás művelete közvetlenül látható |
| UX-12 | P1 | Dialógusok fókuszkezelése | Kezdőfókusz, fókuszcsapda, Escape és visszaállított fókusz működik |
| UX-13 | P1 | Költési adatok teljességének jelzése | Hiányzó összeg megjelenik a havi és napi összegzés mellett |
| UX-14 | P1 | Státuszok és szűrők tisztázása | Megszakítás és elutasítás nem kap azonos jelentést; visszalépés megőrzi a szűrést |
| UX-15 | P2 | Egységes ikonok és vizuális hierarchia | Fő képernyőkön közös méret-, szín- és állapotrendszer |
| UX-16 | P2 | Tanulható kategóriajavaslatok | Felülírható javaslat; nincs csendes történeti átírás |
| UX-17 | P2 | Értesítési beállítások | Csatorna és gyakoriság állítható; értesítés konkrét célhoz vezet |
| UX-18 | P2 | Gyors sorozatos fotózás | Mentés után közvetlenül indítható a következő nyugta |
| UX-19 | P0 | Új háztartás pénznemének kivizsgálása és szükséges javítása | Az új háztartás esete reprodukált és a gyökérok dokumentált; meghatározott pénznemnél minden összegzés azt használja; hiányzó pénznem egyértelműen jelzett; nyelvváltás nem változtat pénznemet |

## 9. Megvalósítási terv és függőségek

Az időigény tájékoztató becslés egy, a projektet ismerő fejlesztő számára. Nem vállalási határidő; az API módosítása és a feltárt hibák növelhetik. A munka elfogadott részspecifikáció és a projekt minőségi kapui után kezdődhet.

| Szakasz | Tartalom | Becsült ráfordítás | Kilépési feltétel |
|---|---|---|---|
| 0. Kiinduló ellenőrzés | Élő felület, mobil próba, célcsoport és mérési alap | 2–3 munkanap | Dokumentált fő elakadások, jóváhagyott prioritások |
| 1/A. Kliensoldali alapjavítások | UX-01, UX-02, UX-03 és UX-05 | Külön becslendő | Célzott regressziós tesztek és kézi főfolyamat-próba sikeres |
| 1/B. API-t és klienst érintő javítások | UX-04 szerveroldali szűrés és UX-06 feltöltési idempotencia, kliensintegrációval | Az API-részspecifikációk után külön becslendő | Szűrés és találatszám helyes; ismételt feltöltési kérés nem készít új nyugtát |
| 2. Fő élmény | UX-07–14; navigáció, dashboard, onboarding, ellenőrzés | 7–12 munkanap | Mobil és asztali prototípus, majd ellenőrzött megvalósítás |
| 3. Finomítás | UX-15–18; vizuális rendszer és kényelmi funkciók | 5–10 munkanap | Használhatósági próba és működési ellenőrzés |
| 4. Visszamérés | Azonos feladatokkal ismételt vizsgálat | 2–3 munkanap, külön toborzási idővel | Javulás vagy további módosítások bizonyítéka |

**Függőségek:**

- A UX-19 jelenleg kivizsgálási feladat; a javítás rétege és ráfordítása a reprodukálás után állapítható meg. Nem tekintjük automatikusan az A vagy B csomag részének.
- A teljes adatállományra szűréshez szerveroldali támogatás és egységes lapozási szerződés kell.
- A UX-06-hoz kötelező a feltöltési API idempotenciájának megvalósítása; a jelenlegi API nem ad ilyen garanciát. A megszakítás külön szerződést igényel, ha bekerül a felületbe.
- A dashboard adatteljesítési jelzéseihez egységes definíció kell a megerősített és hiányos összegekre.
- A fő navigáció előtt meg kell határozni a háztartási és üzleti felhasználók elérési útjait.
- A felhasználói állapotcímkékhez előbb tisztázni kell a backend állapotainak jelentését.

A korábbi, az alapműködésre adott 5–8 munkanapos becslést a két API-változtatás részletes specifikálásáig nem használjuk vállalási alapként. A táblázatból jelenleg nem képezhető megalapozott teljes projektbecslés.

A módosítások kisebb, önállóan ellenőrizhető csomagokban készüljenek. A termék működését most ez a dokumentum nem változtatja meg.

## 10. Ellenőrzési és mérési terv

### 10.1. Használhatósági próba

Első körben öt új felhasználóval végeznék rövid, moderált vizsgálatot. Legyen köztük kevésbé technikai résztvevő is. Ez a minta fő elakadások feltárására alkalmas, statisztikai bizonyítékra nem.

| Feladat | Mit figyelünk? |
|---|---|
| Első nyugta feltöltése mobilról | Megtalálja-e a fotózást, érti-e a feldolgozást és a mentést? |
| Hibás összeg javítása | Megtalálja-e a mezőt, el tudja-e menteni, érti-e az állapotot? |
| Korábbi nyugta megtalálása | Keresés, kategória, dátum és visszalépés működése |
| Havi költés értelmezése | Észreveszi-e a hiányzó vagy nem megerősített összegeket? |
| Garancia rögzítése | Megérti-e a kapcsolatot a nyugtával és a szükséges adatokkal? |

Mérjük a sikeres befejezést, az eltelt időt, a segítségkéréseket és a feladat utáni 1–7-es könnyűségi értékelést. A hálózati és OCR-időt külön rögzítsük az interakciós időtől.

### 10.2. Javasolt célértékek

Ezek tervezési célok, nem jelenlegi eredmények:

- Az első mentett nyugtáig tartó medián idő legalább 30%-kal csökkenjen az azonos körülmények között mért kiinduló értékhez képest.
- Az alapfeladatokat legalább 4/5 résztvevő segítség nélkül fejezze be a feltáró körben.
- A hiányos havi összegzést legalább 4/5 résztvevő helyesen értelmezze.
- Egyetlen ismert, kritikus mentési vagy félrevezető állapotjelzési hiba se maradjon a kiadásban.

Valós termékhasználatnál követhető a belépés → első mentés arány, a sikertelen feltöltések aránya, az ellenőrzés befejezése és a 7/30 napos visszatérés. A méréshez adatminimalizáló eseményeket használjunk, nyugtakép és nyers OCR-tartalom naplózása nélkül. Az elemzési feltételeket előre kell rögzíteni.

### 10.3. Technikai és kézi ellenőrzések

- Regressziós teszt azonos fájlnevekre, hiányzó és nulla confidence-ra, 50 elem fölötti szűrésre, valamint hálózati és hitelesítési hibákra.
- A nyugta életútja feltöltéstől megerősítésig és keresésig, valós API-val.
- Android Chrome és iOS Safari próba, kamerával és engedélymegtagadással.
- Keskeny mobil és asztali nézet; nagyított szöveg, hosszú üzletnév és hosszabb fordítások.
- Billentyűzet, képernyőolvasó és automatizált akadálymentességi ellenőrzés együtt.
- Világos és sötét téma, látható fókusz, állapotok szöveges megkülönböztetése.

## 11. Kockázatok és kompromisszumok

| Változtatás | Kockázat | Kezelés |
|---|---|---|
| Kevesebb fő menüpont | Régi felhasználó nehezebben talál meg egy modult | Stabil közvetlen linkek, érthető alnézetek, rövid változásjelzés |
| Egyszerűbb állapotok | Pénzügyileg eltérő állapotok összemosódnak | Dokumentált megfeleltetés, üzleti módban pontos részletek |
| Több automatikus javaslat | Téves adat könnyebben elfogadásra kerül | Látható bizonytalanság és egyszerű felülírás |
| Új feltöltési folyamat | Több lépés lassítja a rutinos felhasználót | Csak szükséges ellenőrzés, gyors következő nyugta |
| Erősebb megtartási értesítések | Zavaró vagy bűntudatkeltő élmény | Szabályozható gyakoriság, tárgyszerű szöveg |
| Offline tárolás | Érzékeny adat marad a készüléken | Külön specifikáció; első körben nem feltételezzük kész megoldásnak |

## 12. Véleményezési kérdések

Ezeket érdemes a terv átnézésekor a véleményezőkkel megbeszélni:

1. Mi legyen az első percek fő sikere: nyugta elmentése, költési összegzés vagy garancia követése?
2. Érthető-e a négy fő célpont és a központi hozzáadás?
3. Mely funkciók fontosak napi használatban, és melyek kerülhetnek másodlagos helyre?
4. Elég világos-e, hogy a költési összegzés csak a rögzített adatokból dolgozik?
5. Mely változtatások kerüljenek az első kiadásba: csak P0 hibák, vagy a P1 egyszerűsítés is?
6. Milyen mobilokon és milyen nyugtákkal kell feltétlenül próbálni?

**Javasolt jóváhagyási csomagok:**

- **A – önálló kliensoldali P0 javítások:** UX-01, UX-02, UX-03 és UX-05. Ezek az API-bővítéstől függetlenül ellenőrizhetők és kiadhatók.
- **B – API-t és klienst érintő P0 javítások:** UX-04 és UX-06. A csomag része a szerveroldali kategória-/dátumszűrés és a feltöltési idempotencia megvalósítása, a kliensintegráció és a közös ellenőrzés. Pusztán frontend-módosítással nem teljesíthető.

A fő felületek magyarítása és a navigáció/kezdőoldal prototípusa külön P1 előkészítés. A nagyobb vizuális átalakításról a prototípus és a használhatósági próba után érdemes dönteni.

**További P0 kivizsgálás:** a UX-19 pénznemeltérését az első kiadás előtt tisztázni kell. A reprodukálás eredménye alapján a szükséges javítás külön becslést és csomagba sorolást kap.

## 13. Források a projektben

Az alábbi fájlok a jelen elemzés konkrét bizonyítékai. A linkek a dokumentum helyéhez képest relatívak, így a repóban is használhatók.

| Terület | Forrás |
|---|---|
| Termék célja és munkafolyamatok | [README](../../README.md) |
| Menüelemek és mobil fő célpontok | [nav.ts](../../frontend/lib/nav.ts) |
| Asztali navigáció | [Sidebar.tsx](../../frontend/components/Sidebar.tsx) |
| Mobil navigáció | [MobileNav.tsx](../../frontend/components/MobileNav.tsx) |
| Munkamenet és alkalmazáskeret | [AppShell.tsx](../../frontend/components/AppShell.tsx) |
| Felső sáv | [Topbar.tsx](../../frontend/components/Topbar.tsx) |
| Kezdőoldal | [dashboard/page.tsx](../../frontend/app/%28app%29/dashboard/page.tsx) |
| Feltöltőoldal | [upload/page.tsx](../../frontend/app/%28app%29/upload/page.tsx) |
| Fájlválasztó és kamera | [DropZone.tsx](../../frontend/components/DropZone.tsx) |
| Feltöltési sor és fájlkezelés | [UploadQueue.tsx](../../frontend/components/UploadQueue.tsx), [useUpload.ts](../../frontend/lib/hooks/useUpload.ts) |
| Feltöltési API és jelenlegi idempotenciahiány | [product_api.py](../../app/product_api.py) |
| Nyugtalista és szűrés | [receipts/page.tsx](../../frontend/app/%28app%29/receipts/page.tsx) |
| Nyugta részletei és megbízhatóság | [receipts/[id]/page.tsx](../../frontend/app/%28app%29/receipts/%5Bid%5D/page.tsx), [ConfidenceBadge.tsx](../../frontend/components/ConfidenceBadge.tsx) |
| Ellenőrzési folyamat | [review/page.tsx](../../frontend/app/%28app%29/review/page.tsx) |
| Bevezetés | [Onboarding.tsx](../../frontend/components/Onboarding.tsx), [onboarding/page.tsx](../../frontend/app/onboarding/page.tsx) |
| Belépés | [login/page.tsx](../../frontend/app/%28auth%29/login/page.tsx) |
| Nyelvi katalógus | [i18n.ts](../../frontend/lib/i18n.ts) |
| Dialógusok | [Modal.tsx](../../frontend/components/Modal.tsx) |
| Közös vizuális alapok | [globals.css](../../frontend/app/globals.css) |

## 14. Következő lépés a véleményezés után

Az elfogadott pontokat külön végrehajtási specifikációvá kell alakítani a projekt módszertana szerint, konkrét követelményekkel és futtatható elfogadási esetekkel. Ezután készülhet képernyőprototípus, célzott teszt és implementáció. A terv véleményezése önmagában nem bizonyítja a változtatások használhatóságát; azt az ellenőrzési köröknek kell alátámasztaniuk.
