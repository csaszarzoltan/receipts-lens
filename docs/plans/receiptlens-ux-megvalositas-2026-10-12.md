# ReceiptLens UX-terv – megvalósítás és ellenőrzési jelentés

**Dátum:** 2026. október 12.  
**Állapot:** a véleményező legfrissebb, befejezett ellenőrzése zöld: 23 frontendteszt, 21 US-023 teszt, 10/10 Playwright production build másolatán és teljes pytest 1913 sikeres / 10 kihagyott, exit 0. Az éles rendszer továbbra is a helyreállított HEAD-et szolgálja ki; az új UX-verzió nincs élesítve. A legfrissebb bizonyítékokat a 14. fejezet rögzíti.  
**Forrás:** [jóváhagyott UX-terv](receiptlens-ux-elemzes-es-fejlesztesi-terv-2026-10-12.md), [végrehajtási specifikáció](../specs/SPEC-UX-2026-10-12-felhasznalobarat-munkaterulet.md).

## 1. Látható változások

- Mobilon öt fő célpont: Áttekintés, Nyugták, Hozzáadás, Pénzügyeim, Továbbiak.
- Asztali gépen négy fő menüpont és külön nyugtahozzáadási gomb. A régi útvonalak továbbra is léteznek.
- A Pénzügyeim összegyűjti a keretet, kimutatásokat, előrejelzést és előfizetéseket; a Továbbiak alatt találhatók a garanciák, egyéb eszközök és az üzleti funkciók.
- Új fióknál az első nyugta rögzítése a fő kezdőoldali művelet. Több üres pénzügyi kártya helyett mintanyugta és szükség esetén pénznemválasztás jelenik meg.
- Meglévő nyugtáknál a kezdőoldal a rögzített költést, ellenőrzési teendőket és friss vásárlásokat mutatja először.
- A bevezető modal és a külön bevezetőoldal közös feltöltőkomponenst használ. Befejezéskor a választott pénznem is mentésre kerül. Sikertelen mentés nem léptet tovább csendben.
- A feltöltés állapotai magyarul különböztetik meg a feltöltést és az adatok felismerését. A még nem elérhető AI Scan ajánlója kikerült a fő feltöltési folyamatból; az elérhető kapcsoló megmaradt.
- A részletező oldalról közvetlenül indítható új nyugta hozzáadása vagy a konkrét nyugta ellenőrzése; a kép teljes méretben megnyitható. A metaadatok és előzmények összecsukhatók.
- A nyugtalistában kategória-, dátum- és státuszszűrés, URL-ben tárolt állapot és pontos találatszám szerepel. Megszűnt a párhuzamosan megjelenített rövid második táblázat.
- A fő navigáció egységes SVG ikonokat használ. A fő mobil célok legalább 44 px-es érintési célt kapnak, az alsó navigáció figyelembe veszi a készülék biztonságos területét.

## 2. Tervtételek és ellenőrzésük

Az „elkészült” az implementációra és a megnevezett célzott ellenőrzésre vonatkozik. Nem jelent lezárt felhasználói kutatást vagy teljes körű böngészős elfogadást.

| Tétel | Megvalósítás | Futtatott ellenőrzés / fennmaradó ellenőrzés |
|---|---|---|
| UX-01 | Valódi fájlválasztó gomb; tiltott állapotban a billentyűzetes aktiválás sem működik | Frontend komponens-regresszió; valódi fájlválasztóhoz Playwright eset készült |
| UX-02 | A sor közvetlenül a saját fájlját tárolja; nincs fájlnév szerinti visszakeresés | Azonos nevű, eltérő fájlok és újrapróbálás frontend tesztje sikeres |
| UX-03 | Közös confidence-átlag; nulla megmarad, hiányzó adat ismeretlen | Nulla, üres, nem numerikus és NaN értékek tesztje sikeres |
| UX-04 | API kategória-/dátumszűrés lapozás előtt; teljes tenant kategóriafacetta | 50 elemen túli találat, tenant-szigetelés, érvénytelen dátum tesztje sikeres |
| UX-05 | Csak 401 töröl tokent; átmeneti hiba újrapróbálható, védett tartalom nélkül | Frontend 503/401 regresszió sikeres |
| UX-06 | Tartós feltöltési idempotencia és azonos kulcsú kliens-újrapróbálás | Újraindítás, párhuzamos kapcsolatok, konfliktus, rollback, OCR egyszeri futás és félkész adat elrejtése tesztelt |
| UX-07 | A módosított fő felületek és feltöltési állapotok magyar szöveget használnak | Magyar szövegkatalógus és komponens-regresszió; teljes nyelvi/böngészős audit még szükséges |
| UX-08 | Egyszerű fő navigáció, külön funkciógyűjtő oldalak; régi utak megmaradtak | Öt mobil célpont és navigációs elemek tesztje sikeres; oldalak buildje sikeres |
| UX-09 | Kontextus szerinti, egyszerűbb kezdőoldal | Üres háztartás egy fő feltöltési művelettel, ismétlődő keretfelszólítás nélkül tesztelt |
| UX-10 | Közös OnboardingFlow; kihagyás, pénznemmentés, mentési hiba kezelése | Frontend mentés/hiba regresszió sikeres; modal/page böngészős eset elkészült |
| UX-11 | Feltöltésből és értesítésből a konkrét nyugta ellenőrzéséhez vezető út | Célzott review lekérdezés az első lap után is tesztelt; linkteszt sikeres |
| UX-12 | Közös dialógus-fókuszkezelés: kezdőfókusz, Tab/Shift+Tab, Escape, fókuszvisszaadás, háttér inert | Szimulált DOM-os billentyűzetteszt sikeres; valódi képernyőolvasós próba még szükséges |
| UX-13 | Hiányzó összegek és más pénznemek jelzése; napi keret pénznemenként számol | Frontend havi/napi hiányjelzés és pénznem-regresszió sikeres |
| UX-14 | Elkészített, jóváhagyott és elutasított állapot külön felirat; URL-alapú szűrés | Szűrő továbbítása és URL-módosítás tesztelt; böngésző-visszalépésre Playwright eset készült |
| UX-15 | Egységes navigációs ikonok, fókuszjelzés, visszafogottabb kártyák, érintési célok | Komponens-regresszió és build sikeres; vizuális/kontrasztellenőrzés még szükséges |
| UX-16 | Kézzel menthető kategória; azonos üzlet korábbi, megerősített felhasználói kategóriájából javaslat | Tenant-szigetelés, megerősítés, történeti adatok megőrzése és dashboard kategória tesztelt |
| UX-17 | Értesítési célpontok, hiba-visszajelzés, pénzügyi tippek napi/heti/kikapcsolt gyakorisága | Preferenciamentés, gyakoriság érvényesítése, manuális kiértékelés és értesítési linkteszt sikeres |
| UX-18 | Sikeres feltöltés után ugyanott hozzáadható új nyugta; a részletezőből közvetlen hozzáadási link | Feltöltési és komponens-regresszió; valódi sorozatos kamerás próba még szükséges |
| UX-19 | Üres dashboard nem esik vissza USD-re; beállított pénznem használata, külön választási lehetőség | Üres háztartás, HUF választás, nyelvváltás és szerepkör szerinti beállítás tesztelt |

### Kategóriajavaslatok

A rendszer kizárólag az adott háztartás megerősített nyugtáiból, felhasználó által választott kategóriát ajánl. A javaslat nem írja át automatikusan az új vagy korábbi nyugtákat. A felhasználó a javaslatot beemeli a szerkesztőbe, majd külön menti. Egyéni kategórianév legfeljebb 100 karakter lehet.

### Értesítési gyakoriság pontos hatóköre

A napi/heti/kikapcsolt gyakoriság **a pénzügyi tippek kiértékelésére** vonatkozik. A kézi „Kiértékelés most” felülírhatja az időközt, a leiratkozást nem. A nyugtaellenőrzési értesítések és az előfizetési e-mailek külön folyamatok. Az előfizetési e-mailek meglévő, előfizetésenkénti beállításai az Előfizetések oldalon érhetők el. Nem készült új heti e-mailes összefoglaló küldőrendszer.

## 3. API és adatbázis

### Feltöltés

A `/product/receipts/upload` fogadja az `Idempotency-Key` fejlécet. A böngészős feltöltési sor minden logikai művelethez egy kulcsot készít; újrapróbáláskor megőrzi a fájlt, az opciókat és a kulcsot.

- Azonos tenant + kulcs + fájltartalom/név/típus/AI-opció ugyanazt az eredményt adja vissza.
- Eltérő tartalom vagy opció azonos kulccsal 409 konfliktus.
- A nyugta, a kapcsolódó adatbázis-mellékhatások és az idempotenciaeredmény közös tranzakcióban mentődnek; sikertelen tranzakció visszagörgethető.
- A versengő írásokat SQLite `BEGIN IMMEDIATE` és megosztott kapcsolaton tranzakciós zárolás kezeli. Foglalt adatbázis 503 + `Retry-After` választ adhat; ugyanazzal a kulccsal újrapróbálható.
- A sikeres kulcsok nem járnak le automatikusan. Retenciós törléskor a mentett pénzügyi eredmény helyett tartalommentes tombstone marad, és a korábbi kulcs nem hozza vissza a törölt nyugtát.
- Kulcs nélküli feltöltés kompatibilitási okból elérhető marad; ahhoz a szerver nem ad idempotenciagaranciát.

A meglévő munkaterület-PATCH idempotenciája nem változott: ez a megvalósítás a feltöltési út garanciáját adja. A munkaterület mentése továbbra is verzióellenőrzést használ.

### Migráció

Az új `product_migrations` / `upload_commands` migráció a ProductService indulásakor fut, megismételhető és tranzakciós. Az alkalmazás meglévő adatbázisfájlját és nyugtaazonosítóit megtartja. Nem futott éles adatbázis-törlés vagy éles migráció külön telepítési lépésként.

### Szűrés és pénznem

A nyugtalista API új paraméterei: `category`, `date_from`, `date_to`. A dátum ISO `YYYY-MM-DD`; fordított intervallum hibás. A válasz `categories` mezője a teljes, azonos tenant gyűjteményéből származik.

A konkrét nyugta ellenőrzését a review API `receipt_id` paramétere támogatja. A dashboard előnyben részesíti a hitelesített szerepkör mentett pénznemét; nincs csendes nyelv→pénznem átváltás. Más pénznemű kiadások külön szerepelnek, nem adódnak össze átváltás nélkül.

## 4. Futtatott ellenőrzések és bizonyítékok

| Ellenőrzés | Eredmény | Bizonyíték |
|---|---|---|
| Kezdeti backend RED | 6 valós hiány miatt bukó teszt | [backend-red.txt](../verification/receiptlens-ux-2026-10-12/backend-red.txt) |
| Célzott backend és meglévő service regresszió | 63 sikeres teszt | [backend-green.txt](../verification/receiptlens-ux-2026-10-12/backend-green.txt) |
| Meglévő előfizetési konkurencia-/claim-release regresszió | 6 sikeres teszt | [concurrency-green.txt](../verification/receiptlens-ux-2026-10-12/concurrency-green.txt) |
| Frontend komponens-/hook-regresszió | 13 sikeres teszt | [frontend-green.txt](../verification/receiptlens-ux-2026-10-12/frontend-green.txt) |
| TypeScript | Sikeres, nincs típushiba | [typecheck.txt](../verification/receiptlens-ux-2026-10-12/typecheck.txt) |
| Next.js production build | Sikeres | [build.txt](../verification/receiptlens-ux-2026-10-12/build.txt) |
| Ruff a módosított Python modulokon és az új teszteken | Sikeres | Az alábbi parancs újrafuttatható |
| Git diff whitespace-ellenőrzés | Sikeres | `git diff --check` |
| Új Playwright-suite betöltése | 8 eset sikeresen listázva | `npm run test:ux:e2e -- --list` |
| Playwright futtatási kísérlet | A fejlesztőszerver nem indulhatott el a sandboxban | [browser-attempt.txt](../verification/receiptlens-ux-2026-10-12/browser-attempt.txt) |

A frontend tesztek TypeScript-transzpilálással és kontrollált React-hook/DOM környezettel futnak: a kérések, állapotok, linkek és billentyűzetkezelés regresszióit ellenőrzik, **nem valódi böngészőrenderelést vagy képernyőolvasót**.

A teljes pytest-suite nem tekinthető ellenőrzöttnek. A Starlette TestClient-alapú HTTP-esetek ebben a környezetben elakadtak; az elakadt folyamatokat leállítottam. A célzott service futásból négy, ilyen vagy hozzájuk tartozó régi GUI/API esetet kizártam. A feltöltési API új regressziója az async route-kezelőt közvetlenül hívja, így nem bizonyítja a teljes HTTP-middleware láncot.

A dokumentum szerzőjének eredeti élő szerverindítási kísérlete `listen EPERM` hibát adott `127.0.0.1:3040` címen. A Playwright saját szerverindítása is idő előtt leállt. Ez az eredeti szerzői futás korlátja volt. A későbbi, véleményező által elvégzett böngészős vizsgálat és annak hibái a 8. fejezetben szerepelnek; a most javított repóbeli suite eredményét továbbra sem állítjuk sikeresnek futtatás nélkül.

## 5. Újrafuttatás

A projekt gyökerében:

```bash
.venv/bin/pytest tests/test_ux_plan.py tests/test_currency_preferences_spec.py tests/test_currency_inference.py tests/test_quality_service.py tests/test_dashboard_currency.py tests/test_consolidated_workspace.py -k 'not asset_api and not gui_sections and not api_routes and not workspace_javascript' -q
.venv/bin/pytest tests/test_price_alert_concurrency.py tests/test_price_alert_release_paths.py -q
.venv/bin/ruff check app/api.py app/product_service.py app/product_api.py app/product_migrations.py app/consumer_dashboard.py app/advanced_workspace.py app/insight_api.py tests/test_ux_plan.py
npm --prefix frontend run test:ux
npm --prefix frontend run typecheck
# SOHA ne futtass next build-et a futó frontend szolgáltatás könyvtárában.
# A buildet és a böngészős ellenőrzést külön munkamásolaton kell végezni.
```

Helyi szerver indítását és Chromiumot engedő környezetben:

```bash
npm --prefix frontend run test:ux:e2e
```

A `test:ux:e2e` parancs a `scripts/run-ux-browser-check.py` segítségével ideiglenes, privát munkamásolatot épít, majd a suite ebben production Next.js szervert indít a 3040-es porton, és az API-válaszokat kontrollált tesztadatokkal helyettesíti. Ezután külön, valódi API-val és valódi nyugtaképekkel is ellenőrizni kell a fő folyamatot.

## 6. Kiadás előtti ellenőrzések

- Az új Playwright-esetek és axe-ellenőrzés futtatása mobil és asztali nézetben.
- Valódi Android/iOS kamerás próba, engedélymegtagadás és gyors egymás utáni fotózás.
- Billentyűzetes bejárás és képernyőolvasós ellenőrzés. A fókusz unit tesztje nem helyettesíti ezeket.
- Teljes HTTP- és regressziós tesztfutás olyan környezetben, ahol a TestClient működik.
- Magyar feliratok, hosszú szövegek, világos/sötét téma és kontraszt végső vizuális ellenőrzése.
- Öt új felhasználóval a tervben leírt feladatpróba. A 6/10-es korábbi becslés nem lett újramért eredmény.

## 7. Megvalósítási korlátok

- A hosszú OCR-futás idempotens feltöltésnél adatbázis-író tranzakciót tart fenn; ez szerveroldali versengő írásokat várakoztathat. A foglaltság újrapróbálható, de nagy forgalomnál külön job-alapú feldolgozást érdemes specifikálni.
- A meglévő kvótatároló memóriabeli. A sikeres feltöltés újrajátszása nem futtat új OCR-t és nem növeli újra a kvótát; a kvóta újraindítás utáni tartóssága és sikertelen feldolgozások elszámolása külön, korábban is meglévő kérdés.
- Az új feliratokhoz magyar és angol szöveg készült. A többi támogatott nyelvnél az új kulcsok angol fallbacket használnak; a meglévő fordítások megmaradtak.
- Teljes offline tárolás, automatikus képkivágás, új e-mailes összefoglaló küldés és statisztikailag igazolt megtartási javulás nem készült ebben a változtatásban.
- A felhasználói szerepkörönként tárolt pénznempreferenciák meglévő szerkezetét megtartottuk; nem készült háztartási adatmodell-migráció.

Nem történt commit vagy publikálás. A korábban módosított `app/subscription_alerts.py` és `app/subscriptions_api.py` fájlokat nem szerkesztettem ebben a munkában.


## 8. Véleményezés utáni javítások és új bizonyítékok

### A véleményező közölt eredményei

A véleményező production builden és scratch-szerveren, szintetikus adatokkal desktop és 390 px mobil bejárást végzett. A korábbi repóbeli Playwright-suite **4/8** eredményt adott; három tesztállítás javításával a scratch-változat **8/8** volt. Ez nem a most javított repó teszteredménye. A fő felületek axe-ellenőrzése tiszta volt, de mobilon a bevezető fő gombjai levágódtak. Az idempotens feltöltés élő próbájában azonos kulcs/fájl kétszer ugyanazt az azonosítót adta egyetlen új nyugtával; eltérő fájl 409 `upload_key_conflict` választ kapott.

### Elvégzett javítások

- A közös modal a látható képernyőmagassághoz igazított, függőleges flex elrendezést kapott. A fejléc és az opcionális footer nem zsugorodik; a középső tartalom `min-height: 0` mellett görgethető. A mobil teszt a fő gombot a panelen belülre görgeti, ellenőrzi a pozícióját, majd kattint és a feltöltőoldalra navigálást várja. Ez a levágás valódi regressziós esete; puszta fókuszteszt nem elegendő.
- A magyar `retry` felirat egységesen „Újrapróbálás”.
- A pénznemteszt a megjelenített összegzés/összeg komponenseit ellenőrzi, nem tekinti hibának az USD választási lehetőségét.
- A kadencia-teszt a `payload.insight_frequency` mezőt olvassa, az API tényleges kérési szerkezetének megfelelően.
- A nyelvi hook `useSyncExternalStore` szerver-snapshotja stabil `en`, így a hidratálás első szerver- és kliensértéke megegyezik. Utána a tárolt nyelv aktiválódik; a hibát nem `suppressHydrationWarning` fedi el. A hitelesített alkalmazás első ellenőrző állapota nyelvsemleges spinner. A nyilvános oldalak szerveroldali induló nyelve továbbra is angol; nincs új nyelvi cookie vagy szerveroldali locale-felismerés.
- Feltöltés lezárásakor a `/api/v1/quota` SWR-cache újraérvényesül. A böngészős feltöltési teszt az oldal újratöltése nélkül várja a `2/25` értéket.
- Mobilon a rövid feliratok „Nyugták” és „+ Hozzáadás”; a feliratok nem törnek két sorba. A státuszjelvény `capitalize` osztályát eltávolítottuk, az „Új szabály” ékezetét javítottuk.
- A nyugtalista oldalon a felső sávban nincs második kereső; az oldalon található keresés megmarad. Más oldalakon a globális kereső továbbra is használható.
- A Playwright-esetek a hidratálási hibákat is összegyűjtik, és ilyen hiba esetén buknak.

### Production adatbázis másolatának migrációja

A systemd szolgáltatás konfigurációjából igazolt production adatbázist **read-only** SQLite kapcsolaton nyitottam meg. A SQLite backup API-val helyben, 0700 jogú ideiglenes könyvtárba, 0600 jogú másolatot készítettem. Kizárólag ezen futott a ProductService és az AdvancedWorkspace indulási/migrációs útja.

**Eredmény:** mind a **72 nyugta**, valamint **46 meglévő tábla** eredeti oszlopértékei és sorai megmaradtak. A táblák összes sorának bináris hash-ellenőrzése és darabszáma egyezett; a SQLite-integritásellenőrzés sikeres, a migráció egyszer szerepel, az `upload_commands` tábla létrejött. Az ismételt indulás is megőrizte az adatokat. Az eredeti adatbázishoz nem történt alkalmazásoldali írás. A személyes adatokat tartalmazó másolatot a próba végén töröltem; a repóba csak az aggregált ellenőrzési eredmény került.

Bizonyíték: [production-copy-migration.json](../verification/receiptlens-ux-2026-10-12/production-copy-migration.json). Újrafuttatható segéd: [verify-ux-migration.py](../../scripts/verify-ux-migration.py). A segéd saját szintetikus regressziója ellenőrzi, hogy a forrásfájl tartalma nem változik.

```bash
PYTHONPATH=. .venv/bin/python scripts/verify-ux-migration.py --source /helyi/production-adatbazis.sqlite
```

A próba nem éles telepítés, nem helyettesíti a telepítés előtti mentést, és nem bizonyítja az éles szolgáltatás teljes újraindítását.

### Friss ellenőrzések

| Ellenőrzés | Eredmény | Bizonyíték |
|---|---|---|
| Új hidratálási és kvóta RED | 13 meglévő teszt sikeres, az új 2 teszt bukott | [review-frontend-red.txt](../verification/receiptlens-ux-2026-10-12/review-frontend-red.txt) |
| Friss frontend-regresszió | 15/15 sikeres | [review-frontend-green.txt](../verification/receiptlens-ux-2026-10-12/review-frontend-green.txt) |
| Friss backend/service-regresszió | 64 sikeres, 4 korábban kizárt eset | [review-backend-green.txt](../verification/receiptlens-ux-2026-10-12/review-backend-green.txt) |
| Friss TypeScript | Sikeres | [review-typecheck.txt](../verification/receiptlens-ux-2026-10-12/review-typecheck.txt) |
| Friss production build (véleményező, fe4 másolat) | Sikeres; nem az élő frontend könyvtárában futott | [review-build.txt](../verification/receiptlens-ux-2026-10-12/review-build.txt) |
| Friss Playwright-suite listázása | 8 eset betöltve | [review-browser-list.txt](../verification/receiptlens-ux-2026-10-12/review-browser-list.txt) |
| Friss Playwright-futtatási kísérlet itt | A sandboxban a szerver nem indult el | [review-browser-attempt.txt](../verification/receiptlens-ux-2026-10-12/review-browser-attempt.txt) |

**Korábbi, 8 esetes böngészős bizonyíték:** az azonos repóbeli spec **8/8 sikeres**, külön másolaton, production buildben. Bizonyíték: [review-browser-production.txt](../verification/receiptlens-ux-2026-10-12/review-browser-production.txt). A tesztek API-mockokat használnak; ez nem élő API-val végzett integrációs próba. A teljes pytest-suite továbbra sem tekinthető lefuttatottnak. Nem történt commit, push vagy élesítés.

## 9. Éles frontend incidens és helyreállítás

A futó szolgáltatás `frontend/.next` könyvtárában végzett build felülírta a régi build fájljait. A szolgáltatás a korábbi buildet tartotta memóriában; a véleményező szerint a `/login` HTML-je 200, de 9 JavaScript-chunkból 7 HTTP 400-at adott. Ez a buildfuttatás hibája volt. **A futó frontend könyvtárában nem szabad `next build`-et futtatni.** A korábbi `review-build.txt` élő könyvtárban végzett futásból származott; a fájl helyén most a véleményező `fe4-build.log` másolatbeli bizonyítéka áll.

A jóváhagyott `3fc1bfa8fc8131199ce9bf23419f3633ef85651b` HEAD frontendje külön könyvtárban elkészült: `/tmp/receiptlens-approved-3fc1bfa8fc81/frontend`. A statikus belépőoldal mind a 9 hivatkozott JavaScript-fájlja megtalálható. Ez az eredeti szerző fájlszintű ellenőrzése. A véleményező később a valódi jelöltet a 3301-es porton indította: a segéd HTTP-ellenőrzése a loginra és mind a 9 chunkra sikeres volt. A véleményező ezután leállította a 3301-es szervert; az éles 3300-as szolgáltatás nem változott. Ez nem a nyilvános oldal helyreállításának bizonyítéka.

A [restore-approved-frontend.py](../../scripts/restore-approved-frontend.py) előbb ellenőrzi a buildet és a systemd elérhetőségét, előkészít egy másolatot, és annak minden elemét a live frontend könyvtár UID/GID tulajdonosának adja át szimbolikus linkek követése nélkül. Csak ezután állítja le a frontend szolgáltatást, félreteszi a régi `.next` könyvtárat, áthelyezi az ellenőrzött buildet, és elindítja a szolgáltatást. A helyi 3300-as porton ellenőrzi a belépőoldalt és az összes JavaScript HTTP 200 válaszát, valamint hogy valóban az elkészített buildet szolgálja ki. Sikertelenségnél visszaállítja a korábbi buildet; az a korábbi hibát továbbra is tartalmazhatja. Az API-t nem indítja újra, és az adatbázison nem végez migrációt.

A segéd a jelenlegi sandboxból nem tudott hozzáférni a systemd buszhoz (`Operation not permitted`), ezért nem történt buildcsere vagy szolgáltatás-újraindítás. A kész helyreállítás szolgáltatásvezérlésre jogosult helyi terminálban futtatható:

```bash
sudo python3 /home/zoltan/receipts-lens/scripts/restore-approved-frontend.py
```

A visszaállító segéd hat elkülönített regressziója sikeres: sikeres csere és mentés, HTTP-hiba utáni visszaállítás, tiltott szolgáltatásvezérléskor változatlan élő build, teljes staging-fa tulajdonosváltása leállítás előtt, tulajdonosváltási hibánál változatlan élő build és futó szolgáltatás, valamint külső szimbolikus linkek célpontjának érintetlensége. Ezek szimulált szolgáltatásvezérléssel futnak, nem bizonyítják az éles újraindítást. A két segéd és a tesztek ruff-ellenőrzése, valamint a `git diff --check` sikeres; a frontend-regresszió újra 15/15. A production szerverre átállított Playwright-konfiguráció teljes futása ebben a sandboxban nem történt meg; a 8/8 bizonyíték a véleményező előző, azonos specet használó futása.

A jóváhagyott HEAD külön buildjének naplója: [approved-head-build.txt](../verification/receiptlens-ux-2026-10-12/approved-head-build.txt).

A nyilvános `/login` későbbi böngészős ellenőrzése sikeres volt (11. fejezet). Az UX-változások teljes élesítése továbbra is külön lépés, API-újraindítással és előzetes adatbázismentéssel.


## 10. Tulajdonoskezelési javítás – 2026. október 13.

A véleményező helyesen jelezte, hogy a sudo-val futtatott `shutil.copytree` root tulajdonú `.next` fát hozhat létre, miközben a szolgáltatás `zoltan` felhasználóval fut. A segéd most a másolás után, még a leállítás előtt `os.lchown` hívásokkal a frontend könyvtár tulajdonosának adja a staging könyvtárat és minden elemét. A szimbolikus linkeket megtartja, célpontjukat nem követi. Bármely tulajdonosváltási vagy bejárási hiba megszakítja a folyamatot a szolgáltatás leállítása előtt; az ideiglenes staging-fa törlődik.

Az új három regresszió a javítás előtt bukott, utána a teljes visszaállító suite **6/6 sikeres**. A tesztek ellenőrzik a kért UID/GID értéket, az összes elem kezelését és a műveletek sorrendjét; nem valódi rootként végzett éles próba. Ruff és `git diff --check` sikeres. Az újbóli helyreállítási kísérlet továbbra is a systemd buszhoz való hozzáférésnél állt meg (`Operation not permitted`), fájlcsere és újraindítás nélkül. E kísérletkor az éles frontend helyreállítása még nem történt meg; a későbbi sikeres helyi futtatást a 11. fejezet rögzíti. A fenti sudo-parancs már a javított segédet futtatja; külön utólagos chown nem szükséges.


## 11. Sikeres éles helyreállítás és külső ellenőrzés

A felhasználó helyi, jogosult terminálban lefuttatta a visszaállító segédet. A közölt kimenet szerint a belépőoldal és mind a 9 JavaScript-chunk HTTP 200-at adott, a jóváhagyott frontend helyreállt. Az API és a production adatbázis nem változott. Ez a felhasználó futtatása, nem a sandboxból végzett szolgáltatásvezérlés.

A későbbi, csak olvasással végzett ellenőrzés felhasználó által közölt eredményei:

- Az éles és jelölt `BUILD_ID` egyezik: `rJcgSoF6Mv6tt1gbtBrLN`.
- A teljes `.next` fa zoltan tulajdonú; nincs eltérő tulajdonosú bejegyzés.
- A nyilvános JavaScript-chunkok 9/9 HTTP 200-at adnak.
- A szolgáltatás active; a journalban „Ready in 888ms”, az indulás óta nincs hibasor.
- A nyilvános belépőoldal 1280 és 390 px szélességen betöltődik: az e-mail mező látható, nincs demo gomb, vízszintes görgetés, chunkhiba vagy konzolhiba.
- Nem történt űrlapbeküldés, magic link kérése vagy adatbázisírás.

A közölt képernyőképek helye: `~/.cache/receiptlens-verify/live-login-desktop.png` és `live-login-mobile.png`. Ezeket a szerző ebben a körben nem vizsgálta meg.

A segéd tulajdonoskezelési javítása továbbra is benne van a jelenlegi fájlban: a `copytree` után a `set_tree_owner(stage, owner.st_uid, owner.st_gid)` hívás a `service("stop")` előtt fut. A véleményezés azon állítása, hogy ez a javítás még hiányzik, a jelenlegi kódra nem igaz.

A hibás korábbi build a `frontend/.next.before-restore-1791843155461719698` könyvtárban megmaradt; ebben a körben nem töröltem. Ez nem forráskód, nem kerülhet az UX-commitba. Az új UX-build, az új API és az éles migráció továbbra sem került telepítésre. A production másolaton igazolt 8/8 Playwright-teszt és a helyreállított login élő bejárása külön bizonyíték. Valódi kamerás, teljes billentyűzetes és képernyőolvasós UX-próba még nyitott.


## 12. További fejlesztés és szélesebb regresszió – 2026. október 13.

### Kamerás használat javítása

A DropZone kamerakérését és képkódolását külön műveletazonosító és azonnali ref-alapú zárolás védi. Gyors dupla kattintás egyetlen kamerakérést vagy fotókódolást indít. Kameraengedélyre várva magyar/angol állapotfelirat és megszakító gomb jelenik meg. Bezárás vagy komponens-eltávolítás után beérkező stream leáll, a késői JPEG-eredmény nem ad hozzá fájlt. A fotógomb a videó metaadatainak betöltéséig és képkódolás közben tiltott. Kódolási hiba a dialógus saját alert üzenetében jelenik meg; a kamera újrapróbáláshoz nyitva marad.

Hat kameraregresszió készült. Az első négy közül három az eredeti kódon bukott, egy a meglévő eltávolítás utáni takarítást ellenőrizte. A módosítás után a teljes frontend-runner **21/21 sikeres**. A korábbi 15/15 eredmény történeti bizonyíték, nem a jelenlegi tesztszám.

A Playwright-suite új, szintetikus videostreamet használó kameratesztje a fókuszt, Shift+Tab/Tab kezelést, Escape-et, fókuszvisszaadást, track-leállítást és axe-ellenőrzést tartalmazza. A mobil menüteszt már a Továbbiak linkre kattintva navigál, és ellenőrzi az üzleti jóváhagyási link megmaradását. A suite **9 esetet** tölt be. A korábbi 8/8 futás az előző spec bizonyítéka; az új kilencedik esetre nem állítunk böngészős GREEN eredményt.

### Elavult tesztek és tesztkörnyezeti javítások

A szélesebb futás nyolc olyan frontendállítást talált, amely a korábbi háromlépéses onboardingot vagy a közvetlen üzleti oldalsávot várta. A szerződéseket a jóváhagyott tervhez igazítottuk: a közös bevezető mentési/hibakezelési és kamerás viselkedését a pytestből meghívott valódi frontend-regresszió ellenőrzi; az üzleti funkciók elérhetősége a Továbbiak oldalon marad vizsgálva. A több diát és a régi komponensen belüli szó szerinti implementációt előíró állítások megszűntek.

Két SSRF-teszt élő DNS-t használt. Ezek most kontrollált nyilvános, illetve loopback DNS-válasszal futnak; a loopback elutasítása továbbra is kötelező. A production SSRF-kód nem változott. Az e-mailes kézbesítési próba SMTP-listening socketet igényel, ezért a sandboxból sikeresen futtatott szinkron modulcsoportból kifejezetten kimaradt.

A price-alert párhuzamossági teszt segédje korábban a főszálon várt egy barrierre, a munkaszálak nem várták azt. A segéd most a főszál és az összes munkaszál indulását hangolja össze; a teszt továbbra is a pontosan egyszeri küldést és a hiba utáni feloldást ellenőrzi. A kapcsolódó két modul **6/6 sikeres, 1,89 másodperc**. A korábban más által módosított `app/subscription_alerts.py` és `app/subscriptions_api.py` kódját ebben a körben sem módosítottam.

### Eredmények és tényleges korlátok

| Ellenőrzés | Eredmény | Bizonyíték |
|---|---|---|
| Frontend-regresszió | 21/21 sikeres | [camera-frontend-green.txt](../verification/receiptlens-ux-2026-10-13/camera-frontend-green.txt) |
| TypeScript | Sikeres | [camera-typecheck.txt](../verification/receiptlens-ux-2026-10-13/camera-typecheck.txt) |
| Production build, ideiglenes másolaton | Sikeres | [camera-browser-attempt.txt](../verification/receiptlens-ux-2026-10-13/camera-browser-attempt.txt) |
| Új Playwright-suite | 9 eset betöltve; futtatáskor a webserver nem indult el | [camera-browser-list.txt](../verification/receiptlens-ux-2026-10-13/camera-browser-list.txt) |
| Frissített UX-/DNS-szerződések | 261 sikeres | [legacy-contracts-green.txt](../verification/receiptlens-ux-2026-10-13/legacy-contracts-green.txt) |
| 49 szinkron modul, SMTP-integráció nélkül | 922 sikeres, 7 kihagyott, exit 0 | [synchronous-pytest-green.txt](../verification/receiptlens-ux-2026-10-13/synchronous-pytest-green.txt) |
| Párhuzamossági segéd javítása utáni regresszió | 6 sikeres | [concurrency-green.txt](../verification/receiptlens-ux-2026-10-13/concurrency-green.txt) |
| Teljes pytest-kísérlet | 1927 eset gyűjtve, 2 sikeres után TestClient-elakadás; 120 s után exit 124 | [full-pytest-blocked.txt](../verification/receiptlens-ux-2026-10-13/full-pytest-blocked.txt) |

A szinkron modulok listája a [synchronous-test-modules.txt](../verification/receiptlens-ux-2026-10-13/synchronous-test-modules.txt) fájlban van. A kiválasztás a TestClient/ASGITransport/asyncio/async def szöveget tartalmazó modulokat és az SMTP-integrációt kizárta. Ez környezeti korlát miatt választott részhalmaz, nem teljes backend-elfogadás. A TestClientet nem használó, de aszinkron batch-feldolgozási kísérlet is elakadt; ezt az [async-modules-blocked.txt](../verification/receiptlens-ux-2026-10-13/async-modules-blocked.txt) rögzíti.

A helyi HTTP-listening socket rövid ellenőrzése `EPERM` eredményt adott. A production build elkészült, de a Playwright webserver indítása itt tiltott; az új kamerás és módosított menüteszt böngészős eredménye nyitott. A valódi kamera és képernyőolvasó próba továbbra sem helyettesíthető a szimulált regresszióval. Ruff és `git diff --check` sikeres.

A régi `.next.before-restore-*` mentéseket és `.next.restore-stage-*` staging-mappákat a frontend `.gitignore` kizárja. A hibás buildmentést nem töröltem. Az élő `.next/BUILD_ID` változatlanul `rJcgSoF6Mv6tt1gbtBrLN`: ebben a körben nem készült build az élő könyvtárban, nem történt szolgáltatás-újraindítás, production migráció, commit vagy push. Az új fejlesztések a munkafában vannak.


## 13. Valódi kiadási hibák javítása a teljes véleményezés után

### A véleményező teljes futása

A véleményező a production build külön másolatán lefuttatta a 9 esetes Playwright-suite-ot: **8 sikeres, a kamerás eset hibás**. A teljes pytest eredménye **1911 sikeres, 10 kihagyott, 2 hibás**. Ezek a futások befejeződtek. A hibák valódi kód-/szerződéshibák, nem környezeti korlátozások. A 12. fejezet 922 sikeres tesztje a szerző korábbi részhalmaz-futása; nem a teljes suite eredménye. A szerző sandboxjában tapasztalt futtatási korlátok nem zárják ki a más környezetben végigfutó tesztek által kimutatott hibákat.

### Javítások

- **Kamera:** a nyitógomb korábban kameraindításkor natív `disabled` állapotba került, így a dialógus fókuszkezelése elveszítette az előző fókuszelemet, és Escape után a fókusz a BODY-n maradt. A gomb csak az egész feltöltőkomponens tiltása esetén kap natív disabled állapotot; a kamera saját foglaltságát `aria-disabled` jelzi. Az `openCamera` ref-alapú zárolása továbbra is megakadályozza a dupla kérést. A meglévő böngészős kamerateszt fókuszvisszaadási állítása változatlanul kötelező.
- **Dashboard:** a háztartási állapot és megtakarítási lehetőségek eltűnése nem volt jóváhagyott UX-változtatás. A HouseholdBlock visszakerült a tagokkal, közös kerettel, költéssel, maradvánnyal, hiányzó összeg jelzésével és külön pénznemek megőrzésével. A SavingsBlockCard ismét a dashboard API `savings` adatát kapja. Mindkettő a meglévő nyugták nézetében jelenik meg; az üres háztartás továbbra is az első nyugta hozzáadására összpontosít.
- **Üresállapot-szerződés:** a régi teszt szó szerinti EmptyState-importot várt, miközben a jóváhagyott terv saját első-nyugtás felületet ír elő. A szerződés ezt az állapotot ellenőrzi. A blokkmegőrzési tesztet nem gyengítettük: a megtakarítási adattal bővítettük a kötelező blokkokat.

### Új bizonyítékok és nyitott ellenőrzés

A két új frontend-regresszió a javítás előtt bukott: a kameraindító natív letiltását és a háztartási/megtakarítási blokkok hiányát jelezte. Utána **23/23 frontendteszt sikeres**. A két korábban hibás pytest-eset célzottan **2/2 sikeres**, a többi 19 eset ezen célzott futásból kimaradt. A TypeScript-ellenőrzés és `git diff --check` sikeres.

A Playwright-suite-ban új tizedik eset a meglévő háztartás tagját és a megtakarítási jelölt tényleges megjelenését ellenőrzi. Az üresállapot frontendtesztje azt is kiköti, hogy ezek a másodlagos kártyák ne kerüljenek vissza az első nyugtás üres nézetbe. Az új 10 esetes suite és a teljes pytest javítás utáni sikeres eredménye még nem bizonyított. A véleményező korábbi 8/9, illetve 1911/10/2 eredményét nem tekintjük a javított változat GREEN futásának.

Bizonyítékok: [review2-frontend-red.txt](../verification/receiptlens-ux-2026-10-13/review2-frontend-red.txt), [review2-frontend-green.txt](../verification/receiptlens-ux-2026-10-13/review2-frontend-green.txt), [dashboard-contract-red.txt](../verification/receiptlens-ux-2026-10-13/dashboard-contract-red.txt), [dashboard-contract-green.txt](../verification/receiptlens-ux-2026-10-13/dashboard-contract-green.txt), [review2-typecheck.txt](../verification/receiptlens-ux-2026-10-13/review2-typecheck.txt). A production frontendet, API-t és adatbázist ebben a javítási körben nem módosítottam; nem történt commit vagy push.


A javítás utáni külön másolatos production build sikeres; a saját Playwright-kísérlet a webserver indításánál megállt, ezért nem keletkezett új 10/10 bizonyíték ([review2-browser-attempt.txt](../verification/receiptlens-ux-2026-10-13/review2-browser-attempt.txt)). A [review2-browser-list.txt](../verification/receiptlens-ux-2026-10-13/review2-browser-list.txt) csak a 10 eset betöltését igazolja. Ez a saját futtatási kísérlet korlátja; a véleményező előző, ténylegesen lefutó kameratesztjének fókuszhibája ettől független, valós regresszió volt.

A szerző javítás utáni teljes pytest-kísérlete 1923 esetet gyűjtött; 2 sikeres után ugyanazon TestClient-hívásnál elakadt, 45 másodperces időkorláttal exit 124 lett. Bizonyíték: [review2-full-pytest-attempt.txt](../verification/receiptlens-ux-2026-10-13/review2-full-pytest-attempt.txt). Ez nem teljes GREEN eredmény, és nem írja felül a véleményező befejezett, 1911 sikeres / 10 kihagyott / 2 hibás eredményét. A két ott hibás eset javítását külön, sikeres célzott futás igazolja.


## 14. Teljes GREEN véleményezői ellenőrzés

A véleményező a javítások után ismét lefuttatta a teljes ellenőrzést. A közölt naplókat a szerző elolvasta és a repóba másolta; ezek véleményezői futások, nem a szerző korábbi korlátozott sandbox-kísérletei. A 13. fejezet nyitott teljes/böngészős eredményét az alábbi sikeres futások lezárják.

| Ellenőrzés | Eredmény | Napló |
|---|---|---|
| Frontend test:ux | 23/23 sikeres, exit 0 | [v6-test-ux.log](../verification/receiptlens-ux-2026-10-13/v6-test-ux.log) |
| TypeScript | Sikeres, exit 0 | [v6-typecheck.log](../verification/receiptlens-ux-2026-10-13/v6-typecheck.log) |
| Teljes US-023 szerződés | 21 sikeres | [v6-us023.log](../verification/receiptlens-ux-2026-10-13/v6-us023.log) |
| Playwright, production build másolatán | 10/10 sikeres, exit 0; kamerafókusz és dashboard-blokkok is | [fe6-prod-e2e.log](../verification/receiptlens-ux-2026-10-13/fe6-prod-e2e.log) |
| Teljes pytest | 1913 sikeres, 10 kihagyott, exit 0 | [v6-pytest-full.log](../verification/receiptlens-ux-2026-10-13/v6-pytest-full.log) |

A tíz kihagyott pytest-eset okát ebben az ellenőrzési körben nem vizsgáltuk; ezeket nem számoljuk sikeres tesztnek. A Playwright production buildet és API-mockokat használ. Nem élő API-val vagy valódi kamerával végzett elfogadás, és nem képernyőolvasós próba. Ezek a korlátok változatlanul fennállnak.

A véleményező csak olvasásos éles ellenőrzése szerint a szolgáltatások aktívak, a 9 publikus JavaScript-chunk HTTP 200-at ad, a BUILD_ID változatlan és az éles adatbázis mtime-ja nem változott. A fejlesztett UX-kód, az új API és az éles migráció még nem került telepítésre.


### Commit előkészítése és végrehajtási akadály

A kiadási előkészítés előtt 109 fájlos [commit-paths.txt](../verification/receiptlens-ux-2026-10-13/commit-paths.txt) a fejlesztett kódot, teszteket, terveket és ellenőrzési bizonyítékokat tartalmazza. A korábban más által módosított `app/subscription_alerts.py` és `app/subscriptions_api.py` nincs a listában. A buildmappák és környezeti fájlok szintén nem részei a csomagnak. Az index az előkészítéskor üres volt.

A felhatalmazás forrása a szerző rendelkezésére álló beszélgetési előzmény: az „Implementáld a tervet” felhasználói kérés után a realtime átiratban ez szerepel:

> Ha a tesztelések lefutattak, akkor csináld a commitot és a pusht is, és tedd élesbe

Az utasítás a realtime átadás záró átiratában is megismétlődik. A szerző ezt a folyamatban lévő UX-terv implementálására vonatkozó, tesztfutáshoz kötött felhatalmazásként értelmezte; nem a korábbi login- vagy R3-jóváhagyásokból vezette le. Ez nem a később összeállított 109 fájlos lista külön, tételes jóváhagyása. A lista a feladat hatókörét rögzíti, és kizárja a két más által módosított előfizetési fájlt.

A szerző ennek alapján megpróbálta a listát stage-elni:

```bash
git add --pathspec-from-file=docs/verification/receiptlens-ux-2026-10-13/commit-paths.txt
```

A parancs exit 128 eredménnyel állt meg: `Unable to create .git/index.lock: Read-only file system`. Nem történt indexmódosítás, commit, push vagy telepítés. A szerző környezetének jogosultságprofilja a `.git` könyvtárat csak olvashatóként engedi elérni. Ez a sandboxra vonatkozó korlátozás, nem bizonyítja, hogy a gazdagép fájlrendszere read-only módon lenne csatolva. A véleményező `findmnt` ellenőrzése szerint a gazdagépen az `/` csatolás `rw`; helyi terminálból az írás ezért lehetséges lehet. A szerző ott nem végzett íráspróbát. A sikertelen Git-művelet nem teszthiba.


## 15. Jóváhagyott kiadási munkamenet előkészítése

A felhasználó a javasolt folytatást „Jó, rendben, csináljuk így” utasítással elfogadta. A [kiadási menetrend](receiptlens-ux-kiadasi-menetrend-2026-10-13.md) rögzíti a tesztelést, a pontos commitot, az elkülönített release-t, a friss mentést, a két szolgáltatás közös váltását, a visszaállítást és az öt felhasználós próba jegyzetmintáját.

### Kihagyott tesztek

A v6 napló 1923 eredményjelét egyeztettük a változatlan 1923 teszt-ID gyűjtési sorrendjével, és az összes tíz kihagyott esetet azonosítottuk. [Pontos lista](../verification/receiptlens-ux-2026-10-13/skipped-tests-v6.json). Hét eset a korábban elhalasztott P2-1 egress-allowlist/DNS-rebinding funkció elfogadási tesztje. A helyi ismételt futás ezt igazolta: 60 sikeres / 7 kihagyott ([audit](../verification/receiptlens-ux-2026-10-13/skipped-egress-audit.txt)). A fennmaradó három eset az előfizetési tétel mezőit és a megújulási listát vizsgálja, de adat hiányában kihagy.

A három adatfüggő kihagyási feltételt az aktuális, memóriabeli backend-projekcióval is reprodukáltuk: `No subscriptions to inspect`, illetve kétszer `No renewal items to inspect`. Ez endpoint-projekcióval végzett feltételaudit, nem HTTP-teszt; a [napló](../verification/receiptlens-ux-2026-10-13/skipped-subscriptions-audit.json) ezt külön jelzi. A valódi API-próbában ezekhez szintetikus ismétlődő vásárlás szükséges, hogy a mezők ténylegesen ellenőrizhetők legyenek. A korábban lehetségesnek tartott ReportRequest-kihagyás külön futásban sikeres tesztnek bizonyult, és nincs a tíz közölt kihagyás között.

### Mentés, scoped forrás és visszaállítás

A production adatbázist csak olvasható SQLite kapcsolaton megnyitva privát előkészítő mentés készült: **72 nyugta, sikeres integrity_check, könyvtár 0700, DB-fájl 0600**. [Aggregált bizonyíték](../verification/receiptlens-ux-2026-10-13/preparation-backup.json). A mentés személyes adatokat tartalmazó fájlja nem került a commitlistába; a tényleges telepítés előtt friss mentés szükséges. A backupnak nincs automatikus retention-törlése.

HEAD-archívum és a 109 fájlos UX-lista kombinálásával elkülönített kiadási forrásmásolat készült. Ebben a két kihagyott előfizetési fájl byte-ra a HEAD-verzió. Ez különbözik a korábban teljesen tesztelt munkafától, ezért a teljes suite-ot a végleges scoped release-n is ellenőrizni kell. A scoped másolaton **64 célzott backendteszt sikeres, 4 kizárt; 23 frontendteszt sikeres; typecheck és production build sikeres**. [Összeállítás](../verification/receiptlens-ux-2026-10-13/release-preparation.json), [backend](../verification/receiptlens-ux-2026-10-13/scoped-backend.txt), [frontend](../verification/receiptlens-ux-2026-10-13/scoped-frontend.txt), [typecheck](../verification/receiptlens-ux-2026-10-13/scoped-typecheck.txt), [build](../verification/receiptlens-ux-2026-10-13/scoped-build.txt).

Elkülönített HEAD rollback-forrás és a működő jóváhagyott frontend-build is készült. Privát mentésmásolaton az új kód migrációs indulása után a HEAD-kód ProductService-indulása is sikeres volt: 72 nyugta és sértetlen SQLite-integritás mindkét állapotban. [Storage-kompatibilitás](../verification/receiptlens-ux-2026-10-13/rollback-storage-compatibility.json). Ez nem az éles API-visszaállítás elfogadása. A privát próbapéldányt töröltük.

### Végrehajtási határ

A localhost szerverindítás, systemd-vezérlés és `.git` írása ebben a sandboxban tiltott. A böngészős connector hívása is „MCP tool call requires approval, but approval policy is never” eredménnyel állt meg. A valódi API-/telefonkamerás próba, a végleges scoped suite, commit, push és élesítés nem történt meg. A megadott menetrend ezeket jogosult helyi környezetben, a megfelelő teszt-HTTPS-cím előkészítése után teszi végrehajthatóvá. A felhasználótól a meglévő HTTPS-tesztcímről információt kértünk; ez nem új élesítési jóváhagyás kérése.

A commitlista a kiadási menetrenddel, privát backup/release Git-ignore szabályokkal és új aggregált bizonyítékokkal bővül. A korábbi 109 fájlos snapshot változatlan ellenőrzési előzmény; a friss commitlista 121 fájlt tartalmaz. Az előfizetési módosítások és a személyes adatos mentés továbbra is kimaradnak.
