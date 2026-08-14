"""
BDD regression contract for US-019 — consumer-pivot navigation & role naming
(F1.1 of docs/plans/consumer-pivot-2026-08-13.md).

Scope: frontend-only. The story verifies the *mapping layer* the UI is built
on: lib/nav.ts (household navigation + hidden Business section) and
lib/roles.ts (wire role -> household label). These are the source-of-truth
constants every page and component render from, so asserting them here
protects the acceptance criteria:

  1. Main navigation contains zero business jargon
     (approval / export / accounting / cost-center / tenant / api-key / webhook).
  2. Business features are hidden behind a separate "Business" entry point
     (not deleted).
  3. Role surfaces display household names (Háztartás tulajdonosa, Felnőtt tag,
     Könyvelő / tanácsadó).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"

# Business terms that must never appear in the consumer navigation labels.
BUSINESS_TERMS = ("approval", "export", "accounting", "cost.center", "tenant", "api.key", "webhook")

# Wire role -> expected household label (plan §3.2).
EXPECTED_ROLE_LABELS = {
    "admin": "Háztartás tulajdonosa",
    "reviewer": "Felnőtt tag",
    "integrator": "Könyvelő / tanácsadó (Business mód)",
}

# Consumer navigation: href -> expected label (plan §3.3).
EXPECTED_CONSUMER_NAV = {
    "/dashboard": "Áttekintés",
    "/receipts": "Vásárlások",
    "/upload": "Nyugta hozzáadása",
    "/review": "Ellenőrzés",
    "/duplicates": "Ismétlődések",
    "/inbox": "Családi postafiók",
    "/subscriptions": "Előfizetések",
    "/forecast": "Előrejelzés",
    "/budget": "Háztartási keret",
    "/reports": "Összesítés",
    "/settings": "Beállítások",
}

# Business features that must be hidden behind the Business entry point.
BUSINESS_HREFS = {"/approvals", "/exports", "/accounting", "/integrations", "/automations"}


def _read(rel: str) -> str:
    path = FRONTEND / rel
    assert path.exists(), f"{rel} missing — consumer nav contract depends on it"
    return path.read_text(encoding="utf-8")


def _extract_items(src: str, const_name: str) -> list[tuple[str, str]]:
    """Parse `{ href: "...", label: "...", icon: "..." }` entries of a const array."""
    block = re.search(rf"export const {const_name}[^=]*= \[\n(.*?)\n\];", src, re.DOTALL)
    assert block, f"export const {const_name} not found"
    return re.findall(r'href:\s*"([^"]+)",\s*label:\s*"([^"]+)"', block.group(1))


def test_us_019_consumer_nav_labels_match_plan() -> None:
    src = _read("lib/nav.ts")
    items = dict(_extract_items(src, "NAV_ITEMS"))
    assert items == EXPECTED_CONSUMER_NAV, (
        f"lib/nav.ts NAV_ITEMS diverged from plan §3.3:\n"
        f"  missing: {sorted(set(EXPECTED_CONSUMER_NAV) - set(items))}\n"
        f"  extra:   {sorted(set(items) - set(EXPECTED_CONSUMER_NAV))}\n"
        f"  label diffs: {[(k, items.get(k), EXPECTED_CONSUMER_NAV[k]) for k in EXPECTED_CONSUMER_NAV if items.get(k) != EXPECTED_CONSUMER_NAV[k]]}"
    )


def test_us_019_consumer_nav_has_no_business_terms() -> None:
    src = _read("lib/nav.ts")
    items = dict(_extract_items(src, "NAV_ITEMS"))
    for href, label in items.items():
        lowered = label.lower()
        for term in BUSINESS_TERMS:
            assert re.search(term, lowered) is None, (
                f"consumer nav item '{label}' ({href}) contains business term '{term}'"
            )


def test_us_019_business_features_hidden_in_separate_section() -> None:
    src = _read("lib/nav.ts")
    business = dict(_extract_items(src, "BUSINESS_NAV_ITEMS"))
    consumer = dict(_extract_items(src, "NAV_ITEMS"))
    # Every business feature must exist in BUSINESS_NAV_ITEMS (not deleted)…
    assert BUSINESS_HREFS <= set(business), (
        f"missing business features in BUSINESS_NAV_ITEMS: {sorted(BUSINESS_HREFS - set(business))}"
    )
    # …and must NOT appear in the consumer navigation.
    overlap = set(business) & set(consumer)
    assert not overlap, f"business features leaked into consumer nav: {sorted(overlap)}"


def test_us_019_role_labels_are_household_names() -> None:
    src = _read("lib/roles.ts")
    for role, label in EXPECTED_ROLE_LABELS.items():
        assert f"{role}: \"{label}\"" in src, (
            f"lib/roles.ts ROLE_LABELS missing '{role}' -> '{label}'"
        )


def test_us_019_sidebars_render_business_section_entry_point() -> None:
    sidebar = _read("components/Sidebar.tsx")
    mobile = _read("components/MobileNav.tsx")
    assert "BUSINESS_NAV_ITEMS" in sidebar and "Business" in sidebar, (
        "Sidebar must render a Business section entry point"
    )
    assert "BUSINESS_NAV_ITEMS" in mobile and "Business" in mobile, (
        "MobileNav must render a Business section entry point"
    )
