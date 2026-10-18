# ReceiptLens UX – kiadás és visszaállítás

## Előkészített állapot

A felhasználó a kiadási munkamenetet a „Jó, rendben, csináljuk így” utasítással elfogadta. A munkasorrend: kihagyott tesztek áttekintése → valódi API- és kamerás próba → mentés → scoped commit/push → frontend és API együtt történő telepítése → öt felhasználós próba.

- A teljes munkafás ellenőrzés: 1913 pytest sikeres, 10 kihagyott; 23 frontend-regresszió; 10 Playwright-eset API-mockokkal, production build másolatán.
- A kihagyott esetek listája: [skipped-tests-v6.json](../verification/receiptlens-ux-2026-10-13/skipped-tests-v6.json). A v6 napló 1923 eredményjelének pozícióját a változatlan 1923 tesztből álló gyűjtési sorrenddel egyeztettük; így a konkrét test ID-k azonosíthatók. Hét elhalasztott P2-1 egress-allowlist/DNS-rebinding teszt, három üres előfizetési adathalmazon kihagyott tétel-/megújulásmező-ellenőrzés. Az utóbbiakhoz a valódi API-próbában szintetikus ismétlődő vásárlást is kell rögzíteni. A biztonsági P2-funkció nem része ennek az UX-kiadásnak.
- Privát előkészítő mentés: `backups/ux-release-1791907390708456130/receiptlens-product.db`, 72 nyugta, sikeres integrity_check, könyvtár 0700, fájl 0600. A személyes adatokat tartalmazó DB nincs a commitban. [Aggregált bizonyíték](../verification/receiptlens-ux-2026-10-13/preparation-backup.json).
- Elkülönített forrás/build: `/home/zoltan/receipts-lens/releases/ux-prep-1791907771421899193/source`. HEAD-archívum és a korábbi 109 fájlos UX-lista ráhelyezésével készült. A két kihagyott előfizetési fájl itt byte-ra a HEAD-változat. Nem Git-commit, nem éles kiadás. [Összeállítási bizonyíték](../verification/receiptlens-ux-2026-10-13/release-preparation.json).
- Ezen a scoped másolaton 64 célzott backendteszt és 23 frontendteszt sikeres, typecheck és production build rendben. A teljes v6 suite a munkafán futott, ezért a végleges scoped release teljes ellenőrzése még szükséges.

## 1. Valódi API és kamera – kiadás előtt

A candidate API külön, üres tesztadatbázist kapjon. A production DB-t ne használjuk a feltöltési próbához. A szerver csak loopbacken induljon; a telefonos próbához külön HTTPS tesztcím kell. A következő parancs jogosult helyi terminálból futtatható, az előkészített forrás könyvtárában:

```bash
RECEIPTLENS_ENV=development RECEIPTLENS_SMTP_ENABLED=0 \
RECEIPTLENS_PRODUCT_DB=/tmp/receiptlens-ux-probe.db \
/home/zoltan/receipts-lens/.venv/bin/uvicorn app.main:app \
  --app-dir /home/zoltan/receipts-lens/releases/ux-prep-1791907771421899193/source \
  --host 127.0.0.1 --port 8131
```

Ez a tesztszerver nem a production szolgáltatás. A hozzá tartozó tesztfrontend külön buildje a teszt API-címét használja; az előkészített production build már az éles API-címet tartalmazza, ezért azt nem szabad a teszt API-próba bizonyítékának tekinteni. A production `.next` mappában nem futtatunk buildet.

Ellenőrizendő, feljegyzendő eredmények:

1. `/health` és `/ready` HTTP 200; új tesztháztartás saját, szintetikus adatokkal.
2. Két azonos nevű kép külön nyugtát hoz létre. Azonos fájl és Idempotency-Key ismétlése ugyanazt az azonosítót adja, a nyugtaszám csak egyszer nő. Azonos kulcs más fájllal 409. Az API tesztpéldányának újraindítása után is ugyanaz az eredmény jár vissza.
3. Kategória- és dátumszűrés 50-nél több szintetikus nyugtán; a találatszám és lapozás a teljes háztartási adathalmazon helyes.
4. Telefonon: engedélyezett kamera, engedélymegtagadás/fájlválasztás, megszakítás, két egymás utáni fotó, feltöltés után friss kvóta, ellenőrzés és mentés. Billentyűzettel: bevezető, kamera és értesítési dialógus Tab/Shift+Tab, Escape, fókuszvisszaadás. Képernyőolvasóval legalább a fájlválasztás, feltöltési állapot és hiba bejárása.
5. Nem üres háztartásban tagok, keret, költés és megtakarítás látható. Eltérő pénznemek nem adódnak össze. Ismétlődő szintetikus vásárlásokkal ellenőrizendők az előfizetési mezők és megújulási napok; a három adat nélküli kihagyás nem helyettesíti ezt.

A valódi kamera és képernyőolvasó tesztjét ebben a sandboxban nem végeztük el. A böngészős connector itt jóváhagyást igényelt, amelyet a környezet nem enged meg; a szerverindítás és szolgáltatásvezérlés is tiltott. Ezek végrehajtási akadályok, nem a v6 tesztek hibái.

## 2. Pontos commit és végleges release

A frissített [commit-paths.txt](../verification/receiptlens-ux-2026-10-13/commit-paths.txt) kizárja a külön előfizetési módosításokat, mentéseket, környezeti fájlokat és buildmappákat. Írható helyi Git-környezetben az index tartalmát a listával egyeztetni kell; a commitba csak ez a csomag kerülhet. A meglévő munkafa két külön fájlját nem állítjuk vissza és nem commitoljuk.

```bash
git add --pathspec-from-file=docs/verification/receiptlens-ux-2026-10-13/commit-paths.txt
git diff --cached --stat
git diff --cached --check
git commit -m "feat: implement household UX plan and durable receipt uploads"
git push origin fix/ocr-webhook-currency
```

Ezeket a szerző nem tudta végrehajtani a sandbox `.git` írási tiltása miatt. A végleges commitból készülő release külön könyvtárban épül, és azon kell lefuttatni a teljes pytestet `-rs` opcióval, a frontend-regressziót és a production Playwright-próbát. A 109 fájlos előkészítő snapshot után csak kiadási dokumentáció és Git-ignore változott; ettől még az előkészítő másolat nem a végleges commit.

## 3. Mentés és két szolgáltatás együtt történő váltása

A telepítéshez systemd-konfigurációt írni képes helyi végrehajtás kell. A tényleges váltás közvetlenül előtti mentés friss legyen; a korábban elkészült előkészítő mentés nem helyettesíti. SQLite backup API-val készüljön, integritásellenőrzéssel és privát hozzáféréssel. A forrásra csak olvasható kapcsolatot használjunk. A jelenlegi szolgáltatáskonfigurációkat és a korábbi release útvonalát is őrizzük meg.

A szolgáltatásoknak azonos kiadási forrásra kell váltaniuk. A futó repo munkafáján végzett sima API-újraindítás a két kizárt előfizetési módosítást is betöltené, ezért nem ez a telepítési módszer.

A végleges release frontendje `zoltan` tulajdonú legyen. A frontend systemd override a `WorkingDirectory` értéket a release `frontend/` könyvtárára állítja. Az API eredeti munkakönyvtára és EnvironmentFile-ja megmarad, hogy a meglévő relatív adat-/logútvonalak ne változzanak; az API ExecStart az új forrást `uvicorn --app-dir <release-forrás>` argumentummal tölti be. Az API meglévő 8130-as és a frontend 3300-as portja marad.

A megfelelő override-ok pontos sablonjai, a `<release-forrás>` tényleges, végleges commitból épített útvonalával:

```ini
# receipts-lens-api.service.d/90-ux-release.conf
[Service]
ExecStart=
ExecStart=/home/zoltan/receipts-lens/.venv/bin/uvicorn app.main:app --app-dir <release-forrás> --host 127.0.0.1 --port 8130 --log-level info
```

```ini
# receipts-lens-frontend.service.d/90-ux-release.conf
[Service]
WorkingDirectory=<release-forrás>/frontend
```

A sablonok nincsenek telepítve. A migráció az új API indulásakor történik; a privát production-másolaton korábban már ellenőrzött migráció létrehozza az `upload_commands` és `product_migrations` táblákat. A frontend indítása előtt a helyi API health/ready, adatbázis-integritás, nyugtaszám és migrációs marker ellenőrizendő. Ezután indul az azonos release frontendje, és ellenőrizendő a helyi/nyilvános login, minden JS-chunk, session-folyamat és egy jóváhagyott próbaháztartás fő útja. A felhasználói forgalom váltásához rövid karbantartási ablakot kell választani.

## 4. Visszaállítás

Sikertelen váltáskor mindkét korábbi forrást/buildet kell visszatenni, majd a két szolgáltatást ellenőrizni. Az előkészített HEAD-visszaállítási forrás: `/home/zoltan/receipts-lens/releases/ux-prep-1791907771421899193/rollback-head`; frontend BUILD_ID: `rJcgSoF6Mv6tt1gbtBrLN`. A visszaállításnál az API `--app-dir` argumentuma ezt a könyvtárat, a frontend WorkingDirectory pedig ennek `frontend/` alkönyvtárát kapja. Az override-ok egyszerű eltávolítása az aktuális, fejlesztett repo-forrást töltené be az API-ba, ezért önmagában nem elegendő. A már megőrzött jóváhagyott HEAD-frontend rendelkezésre áll. A régi hibás 17:02-es build nem a visszaállítási cél.

Az adatbázist nem állítjuk vissza automatikusan: a migráció új táblákat hoz létre, a meglévő sorokat megőrzi. Elsődlegesen a korábbi kódot állítjuk vissza a megmaradó DB-vel, és ellenőrizzük a kompatibilitást. DB-mentés visszatöltése csak leállított szolgáltatásokkal és annak ellenőrzése után végezhető, hogy nem veszne el azóta rögzített felhasználói adat. WAL/SHM fájlokat futó szolgáltatás alatt nem cserélünk.

## 5. Öt felhasználós próba a kiadás után

Résztvevőnként 15–20 perc: első nyugta lefotózása, összeg ellenőrzése/javítása, mentés, visszakeresés, egy dátum-/kategóriaszűrő, megtakarítási vagy háztartási állapot értelmezése. F1–F5 azonosítóval rögzítjük a készüléket, feladatbefejezést, segítségigényt, elakadást és a résztvevő saját megfogalmazását. Nem tekintjük statisztikailag igazolt megtartási eredménynek. A következő fejlesztési sorrend az ismétlődő megfigyelt akadályokból készül.

| Résztvevő | Készülék | Feladat | Befejezte | Segítség | Megfigyelt akadály |
|---|---|---|---|---|---|
| F1 | | | | | |
| F2 | | | | | |
| F3 | | | | | |
| F4 | | | | | |
| F5 | | | | | |


A [rollback-storage-compatibility.json](../verification/receiptlens-ux-2026-10-13/rollback-storage-compatibility.json) privát mentésmásolaton igazolja az új ProductService migrációs indulását, majd ugyanazon másolaton a HEAD ProductService indulását: mindkettőnél 72 nyugta, sikeres SQLite-integritás és egyetlen migrációs marker. Ez storage/startup ellenőrzés, nem teljes HTTP- vagy éles rollback-próba. Az ellenőrzéshez használt személyes adatos másolat törlődött.
