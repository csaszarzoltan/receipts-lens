# Budget Management & Spending Analytics

ReceiptLens v0.6.0 adds per-category budget tracking and spending analytics to help manage expenses.

## Budget Management

Set monthly, weekly, or yearly budgets per category and track spending in real time.

### Endpoints

#### `POST /api/v1/budgets`

Create a new budget definition.

```bash
curl -X POST http://localhost:8000/api/v1/budgets \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Meals & Entertainment",
    "amount": 500.00,
    "currency": "USD",
    "period": "monthly",
    "alert_threshold": 0.8
  }'
```

#### `GET /api/v1/budgets`

List all budget definitions with computed spend fields.

```bash
curl http://localhost:8000/api/v1/budgets
```

#### `GET /api/v1/budgets/{id}`

Get a single budget by ID.

#### `PUT /api/v1/budgets/{id}`

Update fields on an existing budget.

```bash
curl -X PUT http://localhost:8000/api/v1/budgets/{id} \
  -H "Content-Type: application/json" \
  -d '{"amount": 600.00}'
```

#### `DELETE /api/v1/budgets/{id}`

Delete a budget definition.

### Response Format

```json
{
  "budget_id": "uuid",
  "category": "Meals & Entertainment",
  "amount": 500.0,
  "currency": "USD",
  "period": "monthly",
  "alert_threshold": 0.8,
  "created_at": "2026-07-25T00:00:00Z",
  "updated_at": "2026-07-25T00:00:00Z",
  "spent": 342.50,
  "remaining": 157.50,
  "pct_used": 68.5
}
```

## Spending Analytics

Aggregate spending data by category, merchant, day, or month.

### `GET /api/v1/analytics/spending`

```bash
curl "http://localhost:8000/api/v1/analytics/spending?date_from=2026-07-01&date_to=2026-07-31&group_by=category"
```

Parameters:
- `date_from` (required) — start date in YYYY-MM-DD format
- `date_to` (required) — end date in YYYY-MM-DD format
- `group_by` (optional, default: `category`) — `category`, `merchant`, `day`, or `month`
- `category` (optional) — filter to a specific category

### `GET /api/v1/analytics/budgets`

Compare budget definitions against current spending.

```bash
curl "http://localhost:8000/api/v1/analytics/budgets?period=monthly"
```

Parameters:
- `period` (optional) — filter to a specific period type (`weekly`, `monthly`, `yearly`)

Response includes a summary with total budgeted, total spent, total remaining, overall percentage, and counts of budgets on track / warning / over-budget.
