# ReceiptLens

**Fotózd le a nyugtát, ellenőrizd az adatokat, és lásd át a kiadásaidat.**

A ReceiptLens nyugtákból készít kereshető vásárlási előzményeket. Háztartásoknak segít követni a költéseket, költségkereteket és előfizetéseket; kisvállalkozásoknak ellenőrzési és könyvelési exportot is kínál. Saját szerveren is futtatható.

**[Megnyitom az alkalmazást](https://receipts.allthezoo.com)** · [Helyi indítás](#helyi-indítás) · [Dokumentáció](#dokumentáció) · [Hibajelzés](https://github.com/csaszarzoltan/receipts-lens/issues)

## Mire használhatod?

| Feladat | Amit a ReceiptLens ad hozzá |
|---|---|
| Nyugták gyűjtése | Fotózás vagy képfeltöltés, eredeti kép és felismert adatok egy helyen. |
| Adatok ellenőrzése | Üzlet, dátum, tételek és végösszeg felismerése; a bizonytalan adatok javíthatók. |
| Kiadások áttekintése | Vásárlási előzmények, kategóriák, havi költés és költségkeretek. |
| Háztartási pénzügyek | Tagok, közös keret és megtakarítási lehetőségek áttekintése. |
| Előfizetések követése | Ismétlődő költések, megújulások, árváltozások és lemondási útmutatók. |
| Könyvelési előkészítés | Ellenőrzés, jóváhagyás, változástörténet és CSV-export. |

A felület magyarul is használható. A klasszikus képfelismeréshez **nem kell AI API-kulcs**: alapból Tesseract dolgozik. Az OCR tévedhet, ezért mentés és export előtt ellenőrizd a fontos összegeket.

## Az első nyugtád

1. Nyisd meg az [alkalmazást](https://receipts.allthezoo.com), és jelentkezz be e-mailes belépési linkkel. Google-belépés is elérhető, ha az üzemeltető beállította.
2. Fotózd le a nyugtát vagy válassz egy képet.
3. Ellenőrizd az üzletet, dátumot, pénznemet és végösszeget; javítsd, amit a felismerés elrontott.
4. Keresd vissza a vásárlást, és nézd meg a költési áttekintést.

Jó fényben, egyenesre igazított, éles képpel érdemes kezdeni. Az online alkalmazás és a fejlesztői ág funkciókészlete eltérhet.

## Helyi indítás

**Szükséges:** Python 3.11+, Node.js 22 és npm, valamint Tesseract 5 az angol nyelvi csomaggal. A következő lépések egy új Linux/macOS klónra vonatkoznak; Windowshoz van [külön útmutató](docs/WINDOWS_GUIDE_HU.md).

Ubuntu/Debian alatt az OCR telepítése:

```bash
sudo apt install tesseract-ocr tesseract-ocr-eng
```

**1. API indítása**

```bash
git clone https://github.com/csaszarzoltan/receipts-lens.git
cd receipts-lens
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

RECEIPTLENS_ENV=development \
RECEIPTLENS_SMTP_ENABLED=0 \
RECEIPTLENS_AUTH_BASE_URL=http://127.0.0.1:3000 \
RECEIPTLENS_PRODUCT_DB=./receiptlens-local.db \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**2. Felület indítása**, egy második terminálban, a klón gyökeréből:

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

- **Felület:** [http://127.0.0.1:3000](http://127.0.0.1:3000)
- **E-mailes belépés:** [http://127.0.0.1:3000/auth/magic-link](http://127.0.0.1:3000/auth/magic-link) — helyi fejlesztésben a belépési link a képernyőn is megjelenik, SMTP nélkül.
- **API-dokumentáció:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

A nyugtaadatok a `receiptlens-local.db` SQLite-fájlba kerülnek, így az API újraindítása után is megmaradnak.

## Beállítások és saját szerver

A backend **FastAPI + SQLite + Tesseract**, a felület **Next.js + React + TypeScript**.

| Beállítás | Mire szolgál? |
|---|---|
| `RECEIPTLENS_PRODUCT_DB` | Tartós adatbázis helye. Beállítás nélkül a repó gyökerében lévő `receiptlens-product.db` fájlba íródik, így újraindítás után is megmarad. Éles környezetben írható, perzisztens tárolóra állítsd. |
| `NEXT_PUBLIC_API_BASE_URL` | A frontend által használt API-cím. |
| `RECEIPTLENS_ALLOWED_ORIGINS` | A backendhez kapcsolódó engedélyezett frontend-címek. |
| `RECEIPTLENS_ENV=production` | Éles környezet; az e-mailes belépéshez SMTP-beállítás is kell. |

További minták: [.env.example](.env.example). A `.env` fájlt a fenti indítóparancs nem tölti be automatikusan.

Az e-mailes értesítések SMTP-t, a Google-belépés OAuth-beállítást igényel. A [Vision OCR](docs/ai-vision-ocr.md) külön engedélyezhető, külső szolgáltatót és API-kulcsot használhat; nincs alapból bekapcsolva. A [QuickBooks-integráció](docs/quickbooks-online.md) sandbox-központú; a CSV-export nem jelent automatikus éles könyvelési beküldést.

Telepítéshez: [infrastruktúra](infra/README.md) és [üzemeltetési terv](docs/plans/production-rollout-2026-08-13.md). **Buildet külön munkamásolatban készíts, ne a futó frontend könyvtárában.**

## Dokumentáció

- [Használati folyamatok](docs/product-workflows.md)
- [Költségkeretek és kimutatások](docs/budgets-and-analytics.md)
- [Előfizetések és értesítések](docs/subscription-alerts.md)
- [Könyvelési CSV-export](docs/accounting-export-guide.md)
- [API-referencia](docs/api.md) · [OCR működése](docs/ocr-pipeline.md)
- [Változások](CHANGELOG.md)

Fejlesztői ellenőrzés: `pytest`, `ruff check app tests`, illetve a `frontend/` könyvtárban `npm run typecheck`. A részletes API-, CLI- és telepítési információk a fenti útmutatókban találhatók.

## Visszajelzés és licenc

Hibát vagy ötletet az [Issues oldalon](https://github.com/csaszarzoltan/receipts-lens/issues) jelezhetsz. Írd le, mit szerettél volna elérni, mi történt, és milyen eszközt/böngészőt használtál.

[MIT-licenc](LICENSE).
