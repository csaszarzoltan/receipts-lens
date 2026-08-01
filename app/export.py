"""Accounting export — QuickBooks, Xero, Generic CSV formats."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.normalization import NormalizedReceipt

# ---------------------------------------------------------------------------
# Export profile definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExportProfile:
    """Defines column mapping for an accounting export format."""
    name: str
    delimiter: str
    columns: list[str]              # CSV header columns
    mapping: dict[str, str]         # NormalizedReceipt field -> CSV column name


# Pre-defined profiles
PROFILES: dict[str, ExportProfile] = {
    "quickbooks": ExportProfile(
        name="quickbooks",
        delimiter=",",
        columns=[
            "Date", "Transaction Type", "Num", "Name", "Memo",
            "Account", "Debit", "Credit", "Currency",
        ],
        mapping={
            "date": "Date",
            "merchant": "Name",
            "total": "Debit",
            "currency": "Currency",
        },
    ),
    "xero": ExportProfile(
        name="xero",
        delimiter=",",
        columns=[
            "Date", "Contact", "Description", "Quantity",
            "Unit Price", "Amount", "Tax Rate", "Tax Amount",
            "Account Code", "Currency Code",
        ],
        mapping={
            "date": "Date",
            "merchant": "Contact",
            "total": "Amount",
            "currency": "Currency Code",
        },
    ),
    "generic": ExportProfile(
        name="generic",
        delimiter=",",
        columns=[
            "Date", "Merchant", "Category", "Description",
            "Amount", "Currency", "Tax",
        ],
        mapping={
            "date": "Date",
            "merchant": "Merchant",
            "category": "Category",
            "total": "Amount",
            "currency": "Currency",
            "tax": "Tax",
        },
    ),
}


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------

class ReceiptExporter:
    """Export normalized receipts to accounting-compatible CSV formats."""

    def __init__(self, profile: ExportProfile | str = "generic") -> None:
        """
        Parameters
        ----------
        profile:
            Export profile name ("quickbooks", "xero", "generic")
            or a custom ExportProfile instance.
        """
        if isinstance(profile, str):
            if profile not in PROFILES:
                raise ValueError(f"Unknown profile: {profile!r}. Available: {list(PROFILES.keys())}")
            self._profile = PROFILES[profile]
        else:
            self._profile = profile

    def export_csv(
        self,
        receipts: list[NormalizedReceipt],
        *,
        include_header: bool = True,
    ) -> str:
        """Generate CSV string for the configured profile.

        Returns
        -------
        str
            Complete CSV content with headers and data rows.
        """
        import csv
        import io

        rows = self.export_rows(receipts)
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=self._profile.columns,
            delimiter=self._profile.delimiter,
            extrasaction="ignore",
        )
        if include_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buf.getvalue()

    def export_rows(
        self,
        receipts: list[NormalizedReceipt],
    ) -> list[dict[str, Any]]:
        """Export receipts as list of dicts (for programmatic use)."""
        rows: list[dict[str, Any]] = []
        for receipt in receipts:
            row: dict[str, Any] = {}
            for field_name, col_name in self._profile.mapping.items():
                value = getattr(receipt, field_name, None)
                if isinstance(value, date):
                    value = value.isoformat()
                # Formula injection prevention
                if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@"):
                    value = "'" + value
                row[col_name] = value
            # Fill unmapped columns with empty string
            for col in self._profile.columns:
                if col not in row:
                    row[col] = ""
            rows.append(row)
        return rows

    @staticmethod
    def list_profiles() -> list[str]:
        """Return available export profile names."""
        return list(PROFILES.keys())

    @staticmethod
    def get_profile(name: str) -> ExportProfile:
        """Get an export profile by name.

        Raises ValueError if profile not found.
        """
        if name not in PROFILES:
            raise ValueError(f"Unknown profile: {name!r}. Available: {list(PROFILES.keys())}")
        return PROFILES[name]


def export_receipts(
    receipts: list[NormalizedReceipt],
    format: str = "generic",
) -> str:
    """Convenience function: export receipts to CSV string."""
    exporter = ReceiptExporter(format)
    return exporter.export_csv(receipts)
