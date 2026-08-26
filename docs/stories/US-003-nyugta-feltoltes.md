# US-003: Nyugta feltöltés — drag-and-drop / camera

- Epic: Core / Upload + OCR
- Priority: P0
- Source: docs/plans/production-rollout-2026-08-13.md §3.2, receipt upload flow
- Prototípus: élő https://receipts.allthezoo.com/upload — státusz: production

## Story (As a … I want … So that …)

**Happy:** As a háztartás tagja I want that nyugtaképet dobok a dropzone-ba, azonnal OCR-t kapok és az eredmény megjelenik a várakozási sorban So that percről percre látom milyen adatokat talált a rendszer.

**Error:** As a háztartás tagja I want that ha a kép túl nagy, nem támogatott formátumú, vagy a szerver nem elérhető, egyérthető hibaüzenetet látok az adott fájlnál So that nem veszett el a teljes batch.

**Edge:** As a háztartás tagja I want that ha több képet dobok egyszerre, mindet feldolgozza párhuzamosan és külön kártyaként jelenik meg So that nem kell egymás után feltöltenem.

**Gui:** As a háztartás tagja I want that a feltöltés során progress bar látható, az AI Scan toggle élesben jelen van de „coming soon" szöveggel, és az eredmény panel source-badge-et mutat (tesseract / ai) So that tudom melyik módszer dolgozta fel.

## Acceptance Criteria (Gherkin — given/when/then)

### AC1: Happy — dropzone single file upload
- **given** a felhasználó session-nel a /upload oldalon van
- **when** drag-and-drop-val (vagy kamera capture) egy `image/jpeg` képet ad a dropzone-hoz
- **then** az upload indításra kerül (POST /product/receipts/upload multipart)
- **then** az UploadQueue-ban egy kártya jelenik meg progress bar-al
- **then** feltöltés után az eredmény panelben megjelenik a nyugta összege, dátuma, OCR source badge

### AC2: Error — túl nagy fájl + szerver 500
- **given** a felhasználó 5MB-nál nagyobb képet próbál feltölteni
- **when** a beküldés megtörténik
- **then** az adott fájl kártyáján hibaüzenet jelenik meg (nem az összes)
- **then** a többi fájl továbbra is feldolgozásra kerül

### AC3: Edge — batch upload (3 fájl egyszerre)
- **given** a felhasználó 3 db `image/jpeg` képet ad a dropzone-hoz
- **when** a feltöltés elindul
- **then** 3 külön kártya jelenik meg az UploadQueue-ban
- **then** mindegyiknek saját progress bar-a van
- **then** mindegyik feldolgozás után eredményt mutat

### AC4: GUI — AI Scan toggle + source badge
- **given** a felhasználó a /upload oldalon van
- **when** az oldal betölt
- **then** az AI Scan toggle nem aktív (élesben gated — "coming soon" szöveg)
- **then** ha van korábbi feltöltés, az eredmény panel source-badge-et mutat (`tesseract` vagy `ai`)

## gui_flow (UI kontraktus)

### Happy flow:
1. Open `/upload` → látom: h1 „Nyugta hozzáadása" + DropZone area + AI Scan „coming soon"
2. Drop image → DropZone visszajelz (fájlnév, méret)
3. UploadQueue: kártya progress bar-al (→ uploading → processing → done)
4. Utolsó kártya: eredmény panel (összeg, dátum, tesseract badge)

### Error flow:
1. Drop túl nagy fájl → kártyán piros hibaüzenet, nem az összesnél
2. /upload üres tartalom → EmptyState „Ready when you are"

### Edge flow:
1. Drop 3 fájl egyszerre → 3 UploadQueue kártya, párhuzamos feldolgozás
2. AI Scan: /upload-en toggle jelen van, de nincs active (production gated)

## Megjegyzés
- E2E: `frontend/e2e/us_003_upload.spec.ts`
- API: `tests/test_us_003_upload.py`
