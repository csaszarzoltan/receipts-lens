# AI Vision OCR (AI Scan)

ReceiptLens can extract receipt data with an **LLM vision model** instead of
(classic) Tesseract OCR. The receipt image is sent as base64 to an
OpenAI-compatible vision-capable chat-completions endpoint, and the model
returns structured receipt JSON. When the vision path is unavailable or
fails, extraction **automatically falls back to the Tesseract pipeline**
(`app.ocr`), so an upload never fails just because the LLM is unreachable.

Implementation: `app/vision_ocr.py` (provider + fallback chain),
`app/api.py` (AI-mode fields on `POST /v1/parse-receipt`),
`app/product_api.py` (AI-mode fields on `POST /product/receipts/upload`),
`frontend/` (AI Scan toggle + result panel).

## How it works

The public entry point is `parse_receipt_with_vision(image_bytes)` in
`app/vision_ocr.py`. It returns the **same `ConfidenceReceipt` shape** as
`ocr.parse_receipt_with_confidence`; the producing path is marked in
`result.confidence["source"]`:

| Source | Meaning |
|---|---|
| `"vision"` | The LLM vision model produced the result |
| `"tesseract"` | The classic Tesseract pipeline produced it (fallback) |

Fallback chain (acceptance criterion #3):

1. **Provider disabled (config flag off) or no API key** → Tesseract immediately.
2. **Vision call succeeds** → vision result (source `vision`).
3. **Timeout / API error / non-JSON response** → one retry for transient
   failures (timeout, connection error, HTTP 5xx), then Tesseract (source
   `tesseract`).

The vision request posts the image as a base64 data URL
(`data:<mime>;base64,...`; MIME sniffed from magic bytes — PNG/JPEG/GIF/WebP)
to `{LLM_BASE_URL}/chat/completions` with `temperature: 0.0` and
`max_tokens: 600`. Non-transient failures (HTTP 4xx, malformed model output)
fall back immediately without retry.

## Setup

The vision path is **off by default** — it is a paid LLM call, so the cost
guard must be explicitly lifted.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | for vision | *(empty)* | API key for the OpenAI-compatible endpoint |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | Base URL of the OpenAI-compatible API |
| `LLM_MODEL` | No | `gpt-4o-mini` | Vision-capable model name |
| `VISION_OCR_ENABLED` | No | *(off)* | Cost guard — set to `1`/`true`/`yes`/`on` to enable the vision path |
| `VISION_OCR_TIMEOUT` | No | `30.0` | Request timeout in seconds (float) |

> `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` are shared with the AI
> categorization feature (`app/categorizer.py`) — same names, same values.

### Quick start (OpenAI)

```bash
export LLM_API_KEY="sk-..."
export LLM_BASE_URL="https://api.openai.com/v1"   # default
export LLM_MODEL="gpt-4o-mini"                    # default
export VISION_OCR_ENABLED=1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Any OpenAI-compatible vision endpoint works (Azure OpenAI, Together,
OpenRouter, local vLLM/llama.cpp servers, ...) — point `LLM_BASE_URL` at its
`/v1` root and set `LLM_MODEL` to a vision-capable model.

### Without configuration

With no `VISION_OCR_ENABLED` / `LLM_API_KEY`, everything still works exactly
as before: `ai_scan=true` requests simply resolve to
`"source": "tesseract"` with a `tesseract_result` payload. This is the
documented, verified fallback behavior — no API key is required to use
AI-mode requests, only to get vision results.

## API usage

### `POST /v1/parse-receipt` with `ai_scan=true`

Add the form field `ai_scan=true` to the existing endpoint. The response
gains a top-level `source` field plus `ai_result` / `tesseract_result`
payloads (both carrying the same receipt/confidence shape as the regular
response).

```bash
curl -X POST "http://localhost:8000/v1/parse-receipt" \
  -F "file=@/path/to/receipt.jpg" \
  -F "ai_scan=true"
```

**Vision disabled / unavailable (real fallback response)** — the common case
when `VISION_OCR_ENABLED` is not set:

```json
{
  "source": "tesseract",
  "tesseract_result": {
    "vendor": "STORE NAME",
    "total": 42.50,
    "date": "2025-03-14",
    "tax": 3.40,
    "currency": "USD",
    "line_items": [
      { "name": "ITEM", "price": 9.99 }
    ],
    "confidence": {
      "vendor": 0.88,
      "total": 0.95,
      "date": 0.80,
      "tax": 0.70,
      "currency": 0.99,
      "line_items": 0.85
    }
  }
}
```

**Vision success** — when the vision path produced the result, `source` is
`"vision"` and the response also exposes `ai_result` (the vision extraction)
alongside `tesseract_result` (the classic pipeline on the same image), so
clients can compare the two. Field values are model output; this is the
contract shape (verified against the renderer):

```json
{
  "source": "vision",
  "ai_result": {
    "vendor": "STARBUCKS COFFEE",
    "total": 12.34,
    "date": "2026-08-01",
    "tax": 1.11,
    "currency": "USD",
    "line_items": [],
    "confidence": { "vendor": 0.99, "total": 0.98 }
  },
  "tesseract_result": {
    "vendor": "STARBUCKS COFFEE",
    "total": 12.34,
    "date": "2026-08-01",
    "tax": 1.11,
    "currency": "USD",
    "line_items": [],
    "confidence": { "vendor": 0.88 }
  }
}
```

> The regular flow (no `ai_scan`) is unchanged: it never leaks `source` /
> `ai_result` / `tesseract_result`, so existing clients are unaffected.

### `POST /product/receipts/upload` with `ai_scan=true`

The product upload endpoint accepts the same `ai_scan` form field. On
success (`201`) the response adds `source` and, in AI mode, `ai_result` /
`tesseract_result` payloads. Note the product endpoint's extraction payload
keys the merchant as `merchant` (the `AiExtraction` contract in
`frontend/lib/types.ts`), whereas `/v1/parse-receipt` uses `vendor`:

```bash
curl -X POST "http://localhost:8000/product/receipts/upload" \
  -F "file=@/path/to/receipt.jpg" \
  -F "ai_scan=true"
```

```json
{
  "receipt_id": "…",
  "source": "vision",
  "ai_result": {
    "merchant": "STARBUCKS COFFEE",
    "date": "2026-08-01",
    "total": 12.34,
    "tax": 1.11,
    "currency": "USD",
    "line_items": [],
    "confidence": { "vendor": 0.99, "source": "vision" }
  },
  "tesseract_result": {
    "merchant": "STARBUCKS COFFEE",
    "date": "2026-08-01",
    "total": 12.34,
    "tax": 1.11,
    "currency": "USD",
    "line_items": [],
    "confidence": { "vendor": 0.88 }
  }
}
```

When the vision path falls back, only `tesseract_result` is present and
`source` is `"tesseract"` (the frontend shows a friendly fallback notice).

## Python library usage

`app.vision_ocr` works standalone, no server required — same pattern as
`app.ocr`:

```bash
# from the repo root, using the repo virtualenv
.venv/bin/python - <<'EOF'
from app.vision_ocr import parse_receipt_with_vision, SOURCE_VISION, SOURCE_TESSERACT

with open("receipt.jpg", "rb") as f:
    result = parse_receipt_with_vision(f.read())

source = (result.confidence or {}).get("source")
print("source:", source)
assert source in (SOURCE_VISION, SOURCE_TESSERACT)
print("merchant:", result.merchant)
print("total   :", result.total)
print("date    :", result.date)
EOF
```

The provider class is directly configurable and inspectable:

```bash
.venv/bin/python - <<'EOF'
import os
from app.vision_ocr import VisionOcrProvider

p = VisionOcrProvider()
print("enabled :", p.enabled)    # VISION_OCR_ENABLED flag (cost guard)
print("available:", p.available) # enabled AND LLM_API_KEY set
print("model   :", p._model)     # LLM_MODEL (default gpt-4o-mini)

os.environ["VISION_OCR_ENABLED"] = "1"
os.environ["LLM_API_KEY"] = "sk-..."
print("available with config:", VisionOcrProvider().available)
EOF
```

## Frontend

- **AI Scan toggle** (`frontend/components/AiScanToggle.tsx`) — accessible
  switch (`role="switch"`, keyboard-togglable) in the upload flow. When on,
  files are uploaded with `ai_scan=true`.
- **Result panel** (`frontend/components/AiResultPanel.tsx`) — renders the
  extraction source badge (vision vs tesseract), per-field confidence, a
  friendly notice when Tesseract was used, and a compact AI-vs-OCR
  comparison when both pipelines ran.
- **API client** (`frontend/lib/api.ts`) — `uploadReceiptWithAi(file)` posts
  to `/product/receipts/upload` with `ai_scan=true`.
- **Dev mock** (`frontend/lib/aiScanMock.ts`) — contract-shaped mock for
  local UI development, enabled with
  `NEXT_PUBLIC_USE_MOCK_AI=1 npm run dev`. When unset, the UI calls the real
  backend and surfaces real errors (the mock never silently replaces a live
  API failure). File names containing `blur`, `ocr`, `fallback`,
  `handwritten`, or `dark` resolve to the Tesseract-fallback mock so the
  fallback notice can be demoed.

## Behavior notes

- **Cost guard.** The vision path makes a paid LLM call per receipt; it only
  runs when `VISION_OCR_ENABLED` is truthy **and** `LLM_API_KEY` is set
  (`VisionOcrProvider.available`).
- **One retry.** Timeout, connection error, or HTTP 5xx triggers exactly one
  retry; a second failure falls back to Tesseract. HTTP 4xx and malformed
  model output fall back immediately.
- **Language hint.** `lang` (e.g. `"deu"`) is prepended to the extraction
  prompt as `The receipt is written in language code '<lang>'.` The API
  endpoints currently call without an explicit `lang`.
- **Confidence.** Per-field confidence is derived from the vision JSON: 1.0
  when the model extracted the field, 0.0 when absent — the API contract
  only requires the keys to exist. It is not a calibrated probability.
- **Dependency.** The vision path's only external dependency is `httpx`
  (already a project dependency, pinned `httpx>=0.27` in `pyproject.toml`).
- **Not used by batch/v2 endpoints.** The batch and export endpoints
  (`app/api_v2.py`) intentionally keep the classic Tesseract path so their
  response schemas stay stable.
