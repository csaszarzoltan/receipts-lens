#!/usr/bin/env python3
"""Create and list budgets using the ReceiptLens budget API.

Usage:
    python examples/budgets.py create "Meals & Entertainment" 500.0
    python examples/budgets.py create "Transportation" 300.0
    python examples/budgets.py list
    python examples/budgets.py analytics
"""

import sys

import httpx

API_BASE = "http://localhost:8000"


def create_budget(category: str, amount: float) -> dict:
    """Create a new monthly budget."""
    payload = {
        "category": category,
        "amount": amount,
        "currency": "USD",
        "period": "monthly",
        "alert_threshold": 0.8,
    }
    resp = httpx.post(f"{API_BASE}/api/v1/budgets", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def list_budgets() -> dict:
    """List all budgets with computed spend fields."""
    resp = httpx.get(f"{API_BASE}/api/v1/budgets", timeout=10)
    resp.raise_for_status()
    return resp.json()


def budget_analytics() -> dict:
    """Get budget vs actual overview."""
    resp = httpx.get(f"{API_BASE}/api/v1/analytics/budgets", timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <create|list|analytics> [args...]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]

    if action == "create":
        if len(sys.argv) < 4:
            print("Usage: budgets.py create <category> <amount>", file=sys.stderr)
            sys.exit(1)
        category = sys.argv[2]
        amount = float(sys.argv[3])
        result = create_budget(category, amount)
        print(f"Created budget: {result['category']} — ${result['amount']:.2f} ({result['budget_id']})")

    elif action == "list":
        result = list_budgets()
        print(f"\n{'Category':<30} {'Budgeted':<12} {'Spent':<12} {'Remaining':<12} {'Used%':<8}")
        print("-" * 74)
        for b in result.get("budgets", []):
            print(f"{b['category']:<30} ${b['amount']:<9.2f} ${b['spent']:<9.2f} ${b['remaining']:<9.2f} {b['pct_used']:<7.1f}")

    elif action == "analytics":
        result = budget_analytics()
        print(f"Period: {result['period']}")
        s = result["summary"]
        print(f"Total Budgeted: ${s['total_budgeted']:.2f}")
        print(f"Total Spent:    ${s['total_spent']:.2f}")
        print(f"Total Remaining: ${s['total_remaining']:.2f}")
        print(f"Overall:        {s['overall_pct']}%")
        print(f"On Track: {s['on_track']}  Warning: {s['warning']}  Over Budget: {s['over_budget']}")

    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
