# AI Receipt Categorization

ReceiptLens v0.6.0 adds ML-based receipt categorization that automatically classifies receipts into categories like Food, Transport, Office Supplies, Software, etc.

## How It Works

The `Categorizer` class in `app/categorizer.py` uses a two-tier approach:

1. **Keyword/Regex Fast Path** (offline, always available) — matches vendor names against a built-in rule list of 50+ known merchants. Returns `confidence: "high"` on match.

2. **Optional LLM Enrichment** — when `LLM_API_KEY` is set, uncategorized receipts are sent to an OpenAI-compatible API for intelligent classification. Returns `confidence: "medium"` on LLM match.

3. **Fallback** — if neither rule nor LLM matches, the receipt is classified as `"Uncategorized"` with `confidence: "low"`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | (empty) | API key for LLM enrichment. Leave empty for offline-only mode |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for OpenAI-compatible endpoint |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |

## Endpoint

### `POST /api/v1/categorize`

Categorize a receipt by vendor name.

```bash
curl -X POST http://localhost:8000/api/v1/categorize \
  -H "Content-Type: application/json" \
  -d '{"vendor": "Starbucks Coffee", "total": 5.75}'
```

Response:
```json
{
  "category": "Meals & Entertainment",
  "confidence": "high",
  "matched_rule": "starbucks",
  "subcategory": "Coffee Shops"
}
```

## Supported Categories

- Meals & Entertainment (Coffee Shops, Fast Food)
- Transportation (Fuel, Rideshare, Rail, Air Travel)
- Shopping (Online Retail, Retail, Wholesale, Home Goods, Electronics, Home Improvement)
- Groceries (Supermarket)
- Healthcare (Pharmacy)
- Utilities (Internet, Telecom, Electric)
- Office Supplies (Stationery)
- Housing (Lodging)
- Uncategorized (fallback)
