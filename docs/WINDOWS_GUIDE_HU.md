# ReceiptLens használata Windows rendszeren

## 1. Előfeltételek

Telepítsd a következőket:

1. **Python 3.11 vagy újabb** a python.org oldalról. A telepítőben jelöld be az **Add python.exe to PATH** lehetőséget.
2. **Tesseract OCR 5.x for Windows**. A telepítés után a `tesseract.exe` könyvtára legyen a `PATH` része. Gyakori helye:
   `C:\Program Files\Tesseract-OCR`.
3. Opcionálisan Git, ha repositoryból dolgozol.

Ellenőrzés új PowerShell-ablakban:

```powershell
py --version
tesseract --version
```

Ha a Tesseract nincs a PATH-ban, csak az aktuális PowerShell-munkamenethez:

```powershell
$env:Path += ";C:\Program Files\Tesseract-OCR"
tesseract --version
```

## 2. Virtuális környezet és telepítés

A projekt gyökerében:

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

A `Set-ExecutionPolicy` csak az aktuális PowerShell-folyamatra érvényes. Command Prompt használatakor az aktiválás:

```cmd
.venv\Scripts\activate.bat
```

## 3. Tesztelés

```powershell
$env:PYTHONPATH = "."
python -m pytest -ra
python -m ruff check .
python -m compileall -q app tests
```

A `PYTHONPATH` beállítása azért szerepel explicit módon, hogy a helyi `app` csomag biztosan importálható legyen telepítés nélküli vagy eltérő pytest-indítás esetén is.

## 4. A szerver indítása

```powershell
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Nyisd meg:

- API dokumentáció: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

A szervert `Ctrl+C` billentyűvel állíthatod le.

## 5. Nyugta feldolgozása PowerShellből

A `curl` PowerShellben alias lehet, ezért használd a `curl.exe` programot:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/v1/parse-receipt" `
  -F "file=@C:\Receipts\receipt.jpg"
```

Vagy futtasd a mellékelt parancssori példát:

```powershell
python examples\parse_receipt.py "C:\Receipts\receipt.jpg"
```

## 6. Receipt tárolási API

Publikus kép URL-jének feldolgozása és ideiglenes memóriatárba helyezése:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/receipts" `
  -H "Content-Type: application/json" `
  -d '{"image_url":"https://example.com/receipt.png"}'
```

Lista és lekérés:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/receipts"
curl.exe "http://127.0.0.1:8000/api/v1/receipts/RECEIPT_ID"
```

A jelenlegi store folyamatmemóriában működik. A szerver újraindításakor a futás közben hozzáadott rekordok elvesznek. Ez fejlesztési/demo működés, nem tartós production adattár.

## 7. Gyakori hibák

### `tesseract is not installed or it's not in your PATH`

Add hozzá a `C:\Program Files\Tesseract-OCR` könyvtárat a Windows PATH környezeti változóhoz, majd nyiss új terminált.

### PowerShell nem engedi a virtuális környezet aktiválását

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### `ModuleNotFoundError: No module named 'app'`

A projekt gyökeréből futtasd a parancsot, aktiváld a virtuális környezetet, és szükség esetén:

```powershell
$env:PYTHONPATH = "."
```

### Portütközés

Válassz másik portot:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

### Az OCR pontatlan

Használj éles, egyenletesen megvilágított, lehetőleg 300 DPI körüli képet. A confidence score-ok alapján kezeld ellenőrzendőként a bizonytalan mezőket.
