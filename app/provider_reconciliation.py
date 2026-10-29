"""Compare a local purchase with the copy the provider (for example a bookkeeping
integration) holds for it.

Used by provider integrations. It is separate from the FEAT-038 transaction matching
workflow in app/feature_specs.py.
"""
from __future__ import annotations

from decimal import Decimal

# Amounts within this tolerance count as the same total.
TOTAL_TOLERANCE = Decimal(".01")


class ProviderReconciliation:
    def __init__(self, service, provider):
        self.db, self.provider = service._db, provider

    def verify(self, actor, item, source):
        try:
            remote = self.provider.get_purchase(item["provider_id"])
        except KeyError:
            return {"status": "missing_remote", "differences": ["remote"]}
        differences = []
        for field in ("date", "currency"):
            if str(remote.get(field)) != str(source.get(field)):
                differences.append(field)
        if abs(Decimal(str(remote.get("total"))) - Decimal(str(source.get("total")))) > TOTAL_TOLERANCE:
            differences.append("total")
        return {
            "status": "needs_reconciliation" if differences else "verified",
            "differences": differences,
            "provider_id": item["provider_id"],
        }
