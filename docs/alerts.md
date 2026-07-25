# Alert System

ReceiptLens v0.6.0 includes an alert system that notifies you when spending approaches or exceeds budget limits.

## How It Works

The `AlertStore` in `app/alerts.py` automatically generates two types of alerts:

1. **Budget Threshold Alerts** — fires when a budget's spending reaches its `alert_threshold` (default 80%). Severity escalates from INFO (approaching) → WARNING (near limit) → CRITICAL (exceeded).

2. **Unusual Spending Alerts** — compares current month spending against the previous month. Flags merchants with spending > 2x the historical average as potentially unusual.

Alerts are evaluated automatically via `AlertStore.evaluate_budgets()`, which should be called after each receipt addition.

## Endpoints

### `GET /api/v1/alerts`

List all active (non-acknowledged) alerts.

```bash
curl http://localhost:8000/api/v1/alerts
```

Response:
```json
{
  "alerts": [
    {
      "alert_id": "uuid",
      "type": "budget_threshold",
      "severity": "warning",
      "category": "Meals & Entertainment",
      "message": "Meals & Entertainment spending has reached 85.0% of the budget ($425.00 of $500.00).",
      "pct_used": 85.0,
      "created_at": "2026-07-25T00:00:00Z",
      "acknowledged": false
    }
  ],
  "unread_count": 1
}
```

### `POST /api/v1/alerts/{alert_id}/acknowledge`

Mark an alert as acknowledged (dismisses it from the active list).

```bash
curl -X POST http://localhost:8000/api/v1/alerts/{alert_id}/acknowledge
```

## Integration

Call `alert_store.evaluate_budgets()` after each receipt is parsed:

```python
from app.alerts import alert_store

# After saving a receipt:
new_alerts = alert_store.evaluate_budgets()
for alert in new_alerts:
    print(f"Alert: {alert.message}")
```
