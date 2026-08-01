# Multi-Language OCR Guide

ReceiptLens supports receipt parsing in 6 languages via Tesseract OCR language packs.
Each language is handled with locale-aware decimal separators, date formats, and currency defaults.

## Supported Languages

| Code | Language   | Decimal separator | Default currency | Date formats tried (priority order)          |
|------|------------|-------------------|------------------|----------------------------------------------|
| eng  | English    | `.` (dot)         | USD              | `YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, `MM-DD-YYYY` |
| deu  | German     | `,` (comma)       | EUR              | `DD.MM.YYYY`, `DD.MM.YY`, `YYYY-MM-DD`     |
| fra  | French     | `,` (comma)       | EUR              | `DD/MM/YYYY`, `DD.MM.YYYY`, `YYYY-MM-DD`   |
| ita  | Italian    | `,` (comma)       | EUR              | `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`   |
| spa  | Spanish    | `.` (dot)         | EUR              | `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`   |
| por  | Portuguese | `,` (comma)       | EUR              | `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`   |

## Tesseract Language Pack Installation

Each language requires its Tesseract training data to be installed on the system.

### Debian / Ubuntu

```bash
# English (required)
sudo apt install tesseract-ocr tesseract-ocr-eng

# German
sudo apt install tesseract-ocr-deu

# French
sudo apt install tesseract-ocr-fra

# Spanish
sudo apt install tesseract-ocr-spa

# Italian
sudo apt install tesseract-ocr-ita

# Portuguese
sudo apt install tesseract-ocr-por

# All at once
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-fra \
  tesseract-ocr-spa tesseract-ocr-ita tesseract-ocr-por
```

### macOS (Homebrew)

```bash
# Homebrew installs English by default
brew install tesseract

# Additional language packs — download from GitHub and place in tessdata directory:
# https://github.com/tesseract-ocr/tessdata_best
# Place .traineddata files in $(brew --prefix tesseract)/share/tessdata/
```

### Windows

Download `.traineddata` files from https://github.com/tesseract-ocr/tessdata_best
and place them in the Tesseract `tessdata` directory (typically `C:\Program Files\Tesseract-OCR\tessdata`).

### Docker (infra/Dockerfile)

The production Dockerfile includes English by default. To add languages:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-ita \
    tesseract-ocr-por
```

## Usage

### API: specify language on parse

Pass the `lang` form field to the batch endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/receipts/batch" \
  -F "files=@receipt_de.jpg" \
  -F "lang=deu"
```

Without `lang`, the parser defaults to `eng`.

### Library: `parse_receipt` with lang

```python
from app.ocr import parse_receipt

with open("receipt_de.jpg", "rb") as f:
    result = parse_receipt(f.read(), lang="deu")

print(result.merchant)  # German store name
print(result.currency)  # EUR
```

### Library: auto-detect language

```python
from app.ocr import detect_language

with open("receipt_unknown.jpg", "rb") as f:
    lang = detect_language(f.read())

print(lang)  # e.g. "deu", "fra", "eng"
```

`detect_language` runs OCR with each supported language and picks the one
with the highest average character confidence from Tesseract `image_to_data`.

### CLI: batch with language

```bash
receipts-lens batch --dir ./receipts-de --lang deu --output results.csv
```

### Multi-language mixing (Tesseract `+` syntax)

Tesseract supports language combining via `+` (e.g. `eng+deu` for mixed
German-English receipts). ReceiptLens validates each component against
the supported set:

```python
from app.ocr import extract_text

# Will raise ValueError if either code is not in SUPPORTED_LANGUAGES
text = extract_text(image_bytes, lang="eng+deu")
```

## Accuracy Tips per Language

### English (eng)
- Highest accuracy overall; Tesseract's default language.
- Works well with printed receipts in US/UK formats.

### German (deu)
- Receipts use comma as decimal separator (`12,50` not `12.50`).
- Amounts with thousand separators like `1.234,56` are parsed correctly.
- Umlauts (ä, ö, ü, ß) are recognized if the `deu` training data is installed.

### French (fra)
- Same decimal convention as German (comma).
- Accented characters (é, è, ê, ç) require the `fra` training data.
- French receipts often use `TTC` (tax included) — tax extraction may
  find `TVA` or `TTC` instead of `TAX`.

### Spanish (spa)
- Uses dot as decimal separator (like English).
- Receipts from Spain often show `IVA` for tax — the parser recognizes
  this as a tax marker.

### Italian (ita)
- Comma decimal separator.
- Italian receipts may show `IVA` as the tax label.
- Receipts printed on thermal paper often have lower OCR confidence.

### Portuguese (por)
- Comma decimal separator.
- Brazilian and European Portuguese receipts are both supported.
- Portuguese receipts may show `IVA` or `IMPOSTO` for tax.

### General tips
- **Image quality matters more than language.** Ensure the receipt photo
  is well-lit, flat, and in focus. The preprocessing pipeline handles
  rotation, deskew, and contrast, but extreme blur cannot be recovered.
- **High-resolution images help.** Upscale happens automatically (1.5x),
  but a low-res phone photo still loses detail.
- **Mixed-language receipts** (e.g. import receipts with brand names in
  English and body text in German) work best with `lang="eng+deu"`.
- **Check confidence scores.** Low confidence on specific fields (vendor,
  total) indicates the OCR may have misread that part of the image.

## How Locale Affects Parsing

ReceiptLens uses locale awareness in three ways:

1. **Decimal separator** — `_parse_float_locale` uses the locale's decimal
   separator to correctly parse amounts like `1.234,56` (German) vs
   `1,234.56` (English).

2. **Date parsing** — `_DATE_FORMATS[lang]` defines the order of date
   format patterns tried. German receipts use `DD.MM.YYYY` first; English
   receipts try `YYYY-MM-DD` first.

3. **Currency default** — if no explicit currency symbol or code is found
   on the receipt, the locale default is used (`USD` for English, `EUR`
   for all others).

## File Reference

- Supported languages: `app/ocr.py:SUPPORTED_LANGUAGES`
- Locale decimal map: `app/ocr.py:_LOCALE_DECIMAL_MAP`
- Currency locale hints: `app/ocr.py:_CURRENCY_LOCALE_HINTS`
- Date format patterns: `app/normalization.py:_DATE_FORMATS`
- Auto-detection: `app/ocr.py:detect_language()`
- Tests: `tests/test_multilang_ocr.py` (43 tests)
