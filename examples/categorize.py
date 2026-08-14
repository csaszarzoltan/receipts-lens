#!/usr/bin/env python3
"""Categorize a receipt using the ReceiptLens AI categorization API.

Usage:
    python examples/categorize.py Starbucks 5.75
    python examples/categorize.py "Shell Gas" 45.00
"""

import sys

import httpx

API_BASE = "http://localhost:8000"


def categorize(vendor: str, total: float | None = None) -> dict:
    """Send a vendor name to the categorization endpoint."""
    payload: dict = {"vendor": vendor}
    if total is not None:
        payload["total"] = total

    resp = httpx.post(f"{API_BASE}/api/v1/categorize", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <vendor> [total]", file=sys.stderr)
        sys.exit(1)

    vendor = sys.argv[1]
    total = float(sys.argv[2]) if len(sys.argv) > 2 else None

    result = categorize(vendor, total)
    print(f"Vendor:       {vendor}")
    print(f"Category:     {result['category']}")
    print(f"Confidence:   {result['confidence']}")
    if result.get("matched_rule"):
        print(f"Matched Rule: {result['matched_rule']}")
    if result.get("subcategory"):
        print(f"Subcategory:  {result['subcategory']}")


if __name__ == "__main__":
    main()
