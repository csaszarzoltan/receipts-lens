#!/usr/bin/env python3
"""List subscriptions and fetch cancellation guides from the ReceiptLens API.

Demonstrates the subscription intelligence endpoints:

    GET  /api/v1/subscriptions                          — renewals, cost, trend
    GET  /api/v1/subscriptions/{id}/cancel-guide        — cancellation steps

Usage:
    python examples/subscriptions.py
    python examples/subscriptions.py sub-001
    python examples/subscriptions.py --base http://localhost:8000

Requires a running server (uvicorn app.main:app). Subscriptions are derived
from at least two matching receipts for the same merchant, so the list is
empty until receipts have been uploaded.
"""

import argparse

import httpx

API_BASE = "http://localhost:8000"


def list_subscriptions(base: str) -> dict:
    """Return the subscription list with renewal dates and price trends."""
    resp = httpx.get(f"{base}/api/v1/subscriptions", timeout=10)
    resp.raise_for_status()
    return resp.json()


def cancel_guide(base: str, subscription_id: str) -> dict:
    """Return cancellation steps for a subscription's merchant."""
    resp = httpx.get(
        f"{base}/api/v1/subscriptions/{subscription_id}/cancel-guide",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subscription_id", nargs="?", help="e.g. sub-001")
    parser.add_argument("--base", default=API_BASE, help="server base URL")
    args = parser.parse_args()

    if args.subscription_id:
        guide = cancel_guide(args.base, args.subscription_id)
        print(f"Merchant:  {guide['merchant']}")
        print(f"Guide URL: {guide['url'] or '(none)'}")
        print("Steps:")
        for i, step in enumerate(guide["steps"], start=1):
            print(f"  {i}. {step}")
        return

    data = list_subscriptions(args.base)
    summary = data["summary"]
    print(f"Active subscriptions: {summary['total']}  "
          f"Monthly total: ${summary['monthly_total']:.2f}")
    print()
    print(f"{'ID':<9}{'Merchant':<22}{'Frequency':<10}{'Renewal':<12}"
          f"{'Monthly':<9}{'Trend':<7}")
    print("-" * 69)
    for sub in data["subscriptions"]:
        print(f"{sub['id']:<9}{sub['merchant']:<22}{sub['frequency']:<10}"
              f"{sub['renewal_date']:<12}${sub['monthly_cost']:<8.2f}"
              f"{sub['trend']:<7}")


if __name__ == "__main__":
    main()
