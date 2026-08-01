# Accounting Export Guide

ReceiptLens can export parsed receipts to CSV files formatted for
QuickBooks, Xero, or generic accounting workflows. Exports are available
via the API, the CLI, or direct Python library usage.

## Supported Formats

| Format     | Delimiter | Description                                      |
|------------|-----------|--------------------------------------------------|
| quickbooks | `,`       | QuickBooks-compatible journal entry format        |
| xero       | `,`       | Xero bill/bill-line format                       |
| generic    | `,`       | Universal format with merchant, category, amount  |

## Column Mappings

### QuickBooks

| CSV Column      | ReceiptLens field | Notes                          |
|-----------------|-------------------|--------------------------------|
| Date            | `date`            | ISO format `YYYY-MM-DD`       |
| Transaction Type | —                | Empty (set on import)          |
| Num             | —                 | Empty (set on import)          |
| Name            | `merchant`        | Vendor / store name            |
| Memo            | —                 | Empty                          |
| Account         | —                 | Empty (set on import)          |
| Debit           | `total`           | Receipt total amount           |
| Credit          | —                 | Empty                          |
| Currency        | `currency`        | ISO 4217 code (USD, EUR, ...)  |

### Xero

| CSV Column      | ReceiptLens field | Notes                          |
|-----------------|-------------------|--------------------------------|
| Date            | `date`            | ISO format `YYYY-MM-DD`       |
| Contact         | `merchant`        | Vendor / store name            |
| Description     | —                 | Empty                          |
| Quantity        | —                 | Empty                          |
| Unit Price      | —                 | Empty                          |
| Amount          | `total`           | Receipt total amount           |
| Tax Rate        | —                 | Empty                          |
| Tax Amount      | —                 | Empty                          |
| Account Code    | —                 | Empty (set on import)          |
| Currency Code   | `currency`        | ISO 4217 code (USD, EUR, ...)  |

### Generic

| CSV Column  | ReceiptLens field | Notes                          |
|-------------|-------------------|--------------------------------|
| Date        | `date`            | ISO format `YYYY-MM-DD`       |
| Merchant    | `merchant`        | Vendor / store name            |
| Category    | `category`        | AI-assigned category (if set)  |
| Description | —                 | Empty                          |
| Amount      | `total`           | Receipt total amount           |
| Currency    | `currency`        | ISO 4217 code (USD, EUR, ...)  |
| Tax         | `tax`             | Tax amount (if found)          |

## API Export Endpoint

### List available formats

```bash
curl http://localhost:8000/api/v1/receipts/export/formats
```

Response:

```json
{
  "formats": [
    {
      "name": "quickbooks",
      "columns": ["Date", "Transaction Type", "Num", "Name", "Memo", "Account", "Debit", "Credit", "Currency"],
      "delimiter": ","
    },
    {
      "name": "xero",
      "columns": ["Date", "Contact", "Description", "Quantity", "Unit Price", "Amount", "Tax Rate", "Tax Amount", "Account Code", "Currency Code"],
      "delimiter": ","
    },
    {
      "name": "generic",
      "columns": ["Date", "Merchant", "Category", "Description", "Amount", "Currency", "Tax"],
      "delimiter": ","
    }
  ]
}
```

### Export receipts as CSV

```bash
# QuickBooks format
curl http://localhost:8000/api/v1/receipts/export/quickbooks -o export.csv

# Xero format
curl http://localhost:8000/api/v1/receipts/export/xero -o export.csv

# Generic format
curl http://localhost:8000/api/v1/receipts/export/generic -o export.csv
```

The endpoint returns `text/csv` with appropriate headers.
Optional query parameters: `date_from`, `date_to`, `category`.

## CLI Export

```bash
# Export to QuickBooks CSV
receipts-lens export --format quickbooks > quickbooks_export.csv

# Export to Xero CSV
receipts-lens export --format xero > xero_export.csv

# Export with date filter
receipts-lens export --format generic --date-from 2026-01-01 --date-to 2026-06-30

# Export with category filter
receipts-lens export --format generic --category groceries
```

## Python Library Usage

```python
from app.export import ReceiptExporter, export_receipts
from app.normalization import NormalizedReceipt, NormalizedItem
from datetime import date

# Create sample receipts
receipts = [
    NormalizedReceipt(
        receipt_id="r001",
        merchant="Coffee Shop",
        date=date(2026, 3, 14),
        items=[NormalizedItem(name="Latte", quantity=1, unit_price=5.50, total_price=5.50)],
        subtotal=5.50,
        tax=0.50,
        tax_rate=10.0,
        total=6.00,
        currency="EUR",
        language="eng",
        raw_text="COFFEE SHOP\nLATTE 5.50\nTOTAL 6.00",
    )
]

# Export as CSV string (quickbooks format)
csv_output = export_receipts(receipts, format="quickbooks")
print(csv_output)

# Or use the exporter directly for more control
exporter = ReceiptExporter("xero")
rows = exporter.export_rows(receipts)  # list of dicts
csv_str = exporter.export_csv(receipts, include_header=True)
```

### Custom export profiles

You can define custom column mappings:

```python
from app.export import ExportProfile, ReceiptExporter

my_profile = ExportProfile(
    name="my_accounting",
    delimiter=",",
    columns=["Date", "Payee", "Amount", "Notes"],
    mapping={
        "date": "Date",
        "merchant": "Payee",
        "total": "Amount",
    },
)

exporter = ReceiptExporter(my_profile)
csv_str = exporter.export_csv(receipts)
```

## Import Instructions

### QuickBooks Desktop / Online

1. Open QuickBooks and go to **File > Utilities > Import > Excel/CSV**.
2. Select the exported CSV file.
3. Map columns:
   - `Date` → Transaction Date
   - `Name` → Payee
   - `Debit` → Amount (Debit)
   - `Currency` → Currency (QuickBooks Online auto-detects)
4. Set the **Account** column to the correct expense account.
5. Set `Transaction Type` to `Expense` or `Bill`.
6. Review and submit.

### Xero

1. Log in to Xero and go to **Business > Bills to Pay**.
2. Click **New Bill** or use **Import** for bulk upload.
3. Upload the exported CSV.
4. Map columns:
   - `Contact` → Supplier name (Xero matches existing contacts)
   - `Date` → Date
   - `Amount` → Total
   - `Account Code` → your expense account code (e.g. `400` for Office Supplies)
5. Review the preview and confirm.

### Generic CSV (Spreadsheet / Other Software)

1. Open the CSV in Excel, Google Sheets, or LibreOffice Calc.
2. All columns are self-describing: Date, Merchant, Category, Amount, Currency, Tax.
3. Use pivot tables, filters, or import into your accounting tool.

## CSV Injection Protection

All export formats prefix values starting with `=`, `+`, `-`, or `@`
with a single quote (`'`) to prevent CSV formula injection when
spreadsheets auto-execute formulas. This is handled transparently
by `ReceiptExporter` and `CsvAccountingConnector`.

## Formula Examples

The exported CSV for a QuickBooks import looks like:

```csv
Date,Transaction Type,Num,Name,Memo,Account,Debit,Credit,Currency
2026-03-14,,,,,,,12.50,EUR
```

The exported CSV for Xero looks like:

```csv
Date,Contact,Description,Quantity,Unit Price,Amount,Tax Rate,Tax Amount,Account Code,Currency Code
2026-03-14,Coffee Shop,,,,,12.50,,,,EUR
```

The exported CSV for generic format looks like:

```csv
Date,Merchant,Category,Description,Amount,Currency,Tax
2026-03-14,Coffee Shop,,,"",12.50,EUR,1.14
```

## File Reference

- Export profiles: `app/export.py:PROFILES`
- Exporter class: `app/export.py:ReceiptExporter`
- Normalization: `app/normalization.py:NormalizedReceipt`
- Accounting connector: `app/integrations.py:CsvAccountingConnector`
- Tests: `tests/test_export_profiles.py` (36 tests)
