## BRIEF-048: Mobil nyugtakezelési munkafolyamat optimalizálása

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-048  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

Az általánosan reszponzív felület nem biztosítja, hogy a teljes nyugta-életciklus telefonon, egy kézzel, megszakítások és lassú kapcsolat mellett is gyorsan, hozzáférhetően és adatvesztés nélkül végigvihető legyen.

## Célcsoport és kontextus

Telefonról nyugtát rögzítő és feldolgozó felhasználó, beleértve a képernyőolvasót, nagyítást vagy korlátozott kézügyességet használó személyeket.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-048-01:** Mobilos felhasználóként szeretném a kamerás nyugtarögzítést a lehető legkevesebb döntéssel elindítani, hogy az üzletben gyorsan eltehessem a bizonylatot.
- **US-048-02:** Mobilos felhasználóként szeretnék fényképezés után jól látható előnézetet, újrafotózási és elfogadási lehetőséget kapni, hogy olvasható képet küldjek be.
- **US-048-03:** Mobilos felhasználóként szeretném, hogy nagy kép lassú kapcsolaton ésszerűen tömörítve, a szükséges olvashatóság megőrzésével töltődjön fel, és lássam az adatforgalmi hatást, hogy kontrolláljam a feltöltést.
- **US-048-04:** Mobilos felhasználóként szeretném nyugtánként követni a várakozás, feltöltés, feldolgozás, ellenőrzésre várás, siker és hiba állapotát, hogy az oldal elhagyása után is tudjam, mi történt.
- **US-048-05:** Mobilos felhasználóként szeretném a képet és a felismert adatokat gyorsan váltva vagy megfelelően nagyítva összehasonlítani, hogy kis képernyőn is megbízhatóan javítsak.
- **US-048-06:** Mobilos felhasználóként szeretném elsőként a bizonytalan vagy hibás mezőket végigvenni, nagy érintési célokkal és egyértelmű következő művelettel, hogy kevés görgetéssel fejezzem be az ellenőrzést.
- **US-048-07:** Mobilos felhasználóként szeretném, hogy a dátum-, összeg-, pénznem- és szövegmezők a megfelelő mobilbillentyűzetet nyissák meg, és a billentyűzet ne takarja el az aktív mezőt vagy a mentést.
- **US-048-08:** Mobilos felhasználóként szeretném a folyamat legfontosabb műveleteit hüvelykujjal elérhető alsó műveletsávból használni, hogy egy kézzel is kezelhető legyen.
- **US-048-09:** Mobilos felhasználóként szeretném, hogy hálózatvesztés, hívás, képernyőzár, háttérbe helyezés vagy véletlen navigáció után a kép, javítások és folyamatállapot megmaradjanak, hogy ne kelljen újrakezdenem.
- **US-048-10:** Mobilos felhasználóként szeretném a piszkozatot tudatosan félbehagyni és később ugyanonnan folytatni, hogy rövid időablakokban is dolgozhassak.
- **US-048-11:** Képernyőolvasót használó mobilos felhasználóként szeretném a kamera, feltöltési előrehaladás, bizonytalanság, mezőhibák és jóváhagyás állapotát érthető nevekkel és bejelentésekkel elérni, hogy önállóan végigvihessem a folyamatot.
- **US-048-12:** Mobilos felhasználóként szeretném a jóváhagyott nyugtát azonnal visszakeresni és megnyitni, hogy meggyőződjek a sikeres mentésről.
- **US-048-13:** Termékfelelősként szeretném, hogy a teljes fényképezés → feltöltés → feldolgozás → javítás → jóváhagyás → visszakeresés út valódi telefonméreteken és mobilos megszakításokkal E2E ellenőrzött legyen, hogy a mobil használhatóság ne csak elméleti reszponzivitás legyen.

## Scope

- A teljes mobil nyugta-életciklus optimalizálása a kamerás rögzítéstől a későbbi visszakeresésig.
- Egykezes használat, nagy érintési célok, alsó fő műveletek, mobilbillentyűzet és kis képernyős javítás.
- Kép-adat összehasonlítás, állapotkövetés, piszkozat, megszakítás- és hálózatvesztés-kezelés.
- Lassú kapcsolat, képtömörítés, mobilos hozzáférhetőség és valódi telefonméretű E2E utak.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Pusztán töréspontok és reszponzív navigáció általános meghatározása, amelyet a BRIEF-027 fed le.
- Natív iOS- vagy Android-alkalmazás kötelező létrehozása, ha a cél webes/PWA felületen is teljesíthető.
- A BRIEF-045 teljes offline szinkronmotorjának megismétlése; itt a mobil életút használhatósága és folytonossága a fókusz.
- OCR-modell vagy banki párosítás üzleti logikájának újradefiniálása.
- Belső komponensszerkezet, konkrét technológia, adatbázisséma vagy fejlesztési feladatlista; ezek a későbbi feature-specifikáció és ADR hatáskörébe tartoznak.

## Érintett rendszerek

- A nyugta-, tranzakció- és háztartási munkaterület kapcsolódó felületei.
- Az alkalmazási, tartós adatkezelési, keresési és auditálási réteg.
- Az értesítési, feldolgozási és integrációs szolgáltatások, ha a történet ezeket igényli.

## Kapcsolódó meglévő BRIEF-ek

- BRIEF-006: Nyugta feltöltése és feldolgozási sor.
- BRIEF-007: AI-alapú nyugtafelismerés és bizonytalanság.
- BRIEF-009: Nyugtaellenőrzés és javítás.
- BRIEF-016: Háztartási együttműködés és családi postafiók.
- BRIEF-019: Szinkronizálás és egyeztetés.
- BRIEF-020: Jóváhagyások és kontrollált változtatások.
- BRIEF-026: Értesítések és állapotüzenetek.
- BRIEF-027: Hozzáférhetőség és reszponzív navigáció.
- A kapcsolat nem jelent funkcionális átfedést: a jelen BRIEF saját felhasználói eredményét és életciklusát határozza meg.

## Bizonytalanságok

- A pontos üzleti küszöbök, határidők, alapértelmezések és jogosultsági mátrix termékdöntést igényelnek.
- A támogatott külső források, eszközök, csatornák és országfüggő szabályok köre külön kutatást vagy ADR-t igényelhet.
- A javaslatok bizonyossági szintjeit, magyarázatát, felülbírálását és tanulási hatását a SPEC-ben mérhető szerződésként kell rögzíteni.
- A SPEC-nek külön kell választania a blokkoló hibát, a felhasználó által elfogadható figyelmeztetést és az információs jelzést.
- A kötelező követelményekhez Given/When/Then acceptance scenario, RED tesztbizonyíték, célzott teszt és teljes regresszió szükséges a projekt módszertana szerint.
