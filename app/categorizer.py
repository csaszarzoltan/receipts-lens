"""ReceiptLens keyword/regex categorizer with optional LLM fallback.

``Categorizer`` uses a rule list of (regex, category, subcategory) tuples.
If no rule matches and ``LLM_API_KEY`` is set, an HTTP call is made to an
OpenAI-compatible endpoint.  Both paths return a ``CategorizationResult``.
"""
from __future__ import annotations

import json
import os
from typing import Any

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


class CategorizationResult:
    """Result of a categorization attempt."""

    def __init__(
        self,
        category: str,
        confidence: str,
        matched_rule: str | None = None,
        subcategory: str | None = None,
    ) -> None:
        self.category = category
        self.confidence = confidence  # "high" | "medium" | "low"
        self.matched_rule = matched_rule
        self.subcategory = subcategory


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

# (vendor_substring, category, subcategory)
_DEFAULT_RULES: list[tuple[str, str, str]] = [
    ("starbucks", "Meals & Entertainment", "Coffee Shops"),
    ("shell", "Transportation", "Fuel"),
    ("exxon", "Transportation", "Fuel"),
    ("bp", "Transportation", "Fuel"),
    ("esso", "Transportation", "Fuel"),
    ("chevron", "Transportation", "Fuel"),
    ("uber", "Transportation", "Rideshare"),
    ("lyft", "Transportation", "Rideshare"),
    ("amtrak", "Transportation", "Rail"),
    ("delta air", "Transportation", "Air Travel"),
    ("united", "Transportation", "Air Travel"),
    ("amazon", "Shopping", "Online Retail"),
    ("walmart", "Shopping", "Retail"),
    ("costco", "Shopping", "Wholesale"),
    ("target", "Shopping", "Retail"),
    ("ikea", "Shopping", "Home Goods"),
    ("mcdonald", "Meals & Entertainment", "Fast Food"),
    ("burger king", "Meals & Entertainment", "Fast Food"),
    ("subway", "Meals & Entertainment", "Fast Food"),
    ("pizza hut", "Meals & Entertainment", "Fast Food"),
    ("kfc", "Meals & Entertainment", "Fast Food"),
    ("wendy", "Meals & Entertainment", "Fast Food"),
    ("taco bell", "Meals & Entertainment", "Fast Food"),
    ("chipotle", "Meals & Entertainment", "Fast Food"),
    ("panera", "Meals & Entertainment", "Fast Food"),
    ("whole foods", "Groceries", "Supermarket"),
    ("kroger", "Groceries", "Supermarket"),
    ("safeway", "Groceries", "Supermarket"),
    ("trader joe", "Groceries", "Supermarket"),
    ("aldi", "Groceries", "Supermarket"),
    ("lidl", "Groceries", "Supermarket"),
    ("cvs", "Healthcare", "Pharmacy"),
    ("walgreens", "Healthcare", "Pharmacy"),
    ("rite aid", "Healthcare", "Pharmacy"),
    ("comcast", "Utilities", "Internet"),
    ("verizon", "Utilities", "Telecom"),
    ("att", "Utilities", "Telecom"),
    ("t-mobile", "Utilities", "Telecom"),
    ("pg&e", "Utilities", "Electric"),
    ("duke energy", "Utilities", "Electric"),
    ("national grid", "Utilities", "Electric"),
    ("office depot", "Office Supplies", "Stationery"),
    ("staples", "Office Supplies", "Stationery"),
    ("best buy", "Shopping", "Electronics"),
    ("home depot", "Shopping", "Home Improvement"),
    ("lowe", "Shopping", "Home Improvement"),
    ("marriott", "Housing", "Lodging"),
    ("hilton", "Housing", "Lodging"),
    ("airbnb", "Housing", "Lodging"),
]


class Categorizer:
    """Keyword/regex receipt categorizer with optional LLM fallback.

    Usage::

        cat = Categorizer()
        result = cat.categorize(vendor="STARBUCKS COFFEE", total=5.75)
        assert result.category == "Meals & Entertainment"
    """

    def __init__(self, rules: list[tuple[str, str, str]] | None = None) -> None:
        self._rules = rules or _DEFAULT_RULES
        self._llm_api_key = os.environ.get("LLM_API_KEY", "")
        self._llm_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self._llm_base_url = os.environ.get(
            "LLM_BASE_URL", "https://api.openai.com/v1"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def categorize(
        self,
        vendor: str,
        total: float | None = None,
        line_items: list[dict[str, Any]] | None = None,
    ) -> CategorizationResult:
        """Categorize a receipt vendor/items into a predefined category.

        * Fast path: keyword/regex match against **vendor** name.
        * Fallback LLM path: if no rule matches and ``LLM_API_KEY`` is set,
          an HTTP POST is made to the configured LLM endpoint.
        * Final fallback: returns ``"Uncategorized"`` with ``confidence="low"``.
        """
        # Fast path: match against known rules
        result = self._match_rules(vendor)
        if result is not None:
            return result

        # LLM fallback if key is available
        if self._llm_api_key:
            llm_result = self._llm_fallback(vendor, total, line_items)
            if llm_result is not None:
                return llm_result

        # Final fallback
        return CategorizationResult(
            category="Uncategorized",
            confidence="low",
        )

    def categorize_batch(
        self,
        receipts: list[dict[str, Any]],
    ) -> list[CategorizationResult]:
        """Batch-categorize multiple receipts (no LLM fallback per item)."""
        results: list[CategorizationResult] = []
        for receipt in receipts:
            vendor = receipt.get("vendor", "")
            result = self._match_rules(vendor)
            if result is not None:
                results.append(result)
            else:
                results.append(
                    CategorizationResult(
                        category="Uncategorized",
                        confidence="low",
                    )
                )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_rules(self, vendor: str) -> CategorizationResult | None:
        """Case-insensitive substring match against rule list."""
        vendor_lower = vendor.lower()
        for substring, category, subcategory in self._rules:
            if substring in vendor_lower:
                return CategorizationResult(
                    category=category,
                    confidence="high",
                    matched_rule=substring,
                    subcategory=subcategory,
                )
        return None

    def _llm_fallback(
        self,
        vendor: str,
        total: float | None,
        line_items: list[dict[str, Any]] | None,
    ) -> CategorizationResult | None:
        """Call an OpenAI-compatible LLM to categorize an unknown vendor.

        Returns ``None`` on any error (timeout, network, parse) so the
        caller can fall back to ``"Uncategorized"``.
        """
        try:
            import httpx

            prompt = (
                f"Categorize this merchant into exactly one of these categories: "
                f"Meals & Entertainment, Transportation, Shopping, Groceries, "
                f"Healthcare, Utilities, Office Supplies, Housing, "
                f"Uncategorized.\n"
                f"Merchant: {vendor}\n"
            )
            if total is not None:
                prompt += f"Total: {total}\n"
            if line_items:
                prompt += f"Items: {json.dumps(line_items)}\n"
            prompt += (
                "\nRespond ONLY with a JSON object: "
                '{"category": "...", "subcategory": "...", "confidence": "high|medium|low"}'
            )

            headers = {
                "Authorization": f"Bearer {self._llm_api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": self._llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 100,
            }

            with httpx.Client(timeout=httpx.Timeout(connect=5.0, read=15.0)) as client:
                resp = client.post(
                    f"{self._llm_base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

            category = parsed.get("category", "Uncategorized")
            subcategory = parsed.get("subcategory")
            confidence = parsed.get("confidence", "medium")

            # Validate confidence is one of the expected values
            if confidence not in ("high", "medium", "low"):
                confidence = "medium"

            return CategorizationResult(
                category=category,
                confidence=confidence,
                subcategory=subcategory,
            )
        except Exception:
            # Any failure (httpx, json, key error) -> no LLM result
            return None
