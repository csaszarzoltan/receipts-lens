#!/usr/bin/env python3
"""Seed demo receipts for two merchants and verify the subscription endpoints."""
import base64
from datetime import date, timedelta

import httpx

BASE = "http://localhost:8011"
TENANT = {"x-tenant-id": "docdemo", "x-role": "admin"}

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def seed(merchant: str, amounts: list[float], days_ago: list[int]) -> None:
    for amount, d in zip(amounts, days_ago):
        charge_date = (date.today() - timedelta(days=d)).isoformat()
        payload = {
            "image_url": f"data:image/png;base64,{base64.b64encode(PNG).decode()}",
            "vendor": merchant,
            "date": charge_date,
            "total": amount,
            "currency": "USD",
        }
        r = httpx.post(f"{BASE}/api/v1/receipts", json=payload, headers=TENANT, timeout=20)
        print(f"  seed {merchant} {amount} @ {charge_date}: {r.status_code}")


# Netflix: 6 charges, latest higher (price increase)
seed("Netflix", [15.49, 15.49, 15.49, 15.49, 15.49, 19.99], [180, 150, 120, 90, 60, 30])
# Spotify: 6 charges stable
seed("Spotify", [10.99, 10.99, 10.99, 10.99, 10.99, 10.99], [175, 145, 115, 85, 55, 25])

print("--- subscriptions ---")
r = httpx.get(f"{BASE}/api/v1/subscriptions", headers=TENANT, timeout=10)
print(r.status_code)
for s in r.json()["subscriptions"]:
    print(" ", s)
