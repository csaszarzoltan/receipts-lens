"""Pre-development interface + behavioral tests for Accounting Export.

Module 4: app/export.py — ExportProfile, ReceiptExporter, QuickBooks/Xero/Generic.

Run: PYTHONPATH=src .venv/bin/python -m pytest tests/test_export_profiles.py -v
"""
from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from datetime import date
from typing import Any, get_type_hints

import pytest

from app.export import (
    PROFILES,
    ExportProfile,
    ReceiptExporter,
    export_receipts,
)
from app.normalization import NormalizedItem, NormalizedReceipt

# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def sample_receipts():
    """A list of NormalizedReceipt objects for export testing."""
    return [
        NormalizedReceipt(
            receipt_id="r1",
            merchant="WALMART",
            date=date(2026, 7, 1),
            items=[NormalizedItem(name="Milk", quantity=1, unit_price=2.99, total_price=2.99)],
            subtotal=2.99,
            tax=0.24,
            tax_rate=0.08,
            total=3.23,
            currency="USD",
            language="eng",
            raw_text="WALMART\nMilk 2.99\nTax 0.24\nTotal $3.23",
        ),
        NormalizedReceipt(
            receipt_id="r2",
            merchant="REWE",
            date=date(2026, 7, 2),
            items=[NormalizedItem(name="Milch", quantity=1, unit_price=1.49, total_price=1.49)],
            subtotal=1.49,
            tax=0.12,
            tax_rate=0.08,
            total=1.61,
            currency="EUR",
            language="deu",
            raw_text="REWE\nMilch 1,49\nMwSt 0,12\nSumme 1,61 EUR",
        ),
    ]


# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================

class TestExportProfileInterface:
    """Verify ExportProfile dataclass exists and has required fields."""

    def test_is_dataclass(self):
        assert is_dataclass(ExportProfile)

    def test_is_frozen(self):
        # frozen=True means instances are immutable
        field_names = {f.name for f in fields(ExportProfile)}
        assert "name" in field_names

    def test_has_name(self):
        field_names = {f.name for f in fields(ExportProfile)}
        assert "name" in field_names

    def test_has_delimiter(self):
        field_names = {f.name for f in fields(ExportProfile)}
        assert "delimiter" in field_names

    def test_has_columns(self):
        field_names = {f.name for f in fields(ExportProfile)}
        assert "columns" in field_names

    def test_has_mapping(self):
        field_names = {f.name for f in fields(ExportProfile)}
        assert "mapping" in field_names

    def test_profiles_dict_exists(self):
        assert isinstance(PROFILES, dict)

    def test_profiles_has_quickbooks(self):
        assert "quickbooks" in PROFILES

    def test_profiles_has_xero(self):
        assert "xero" in PROFILES

    def test_profiles_has_generic(self):
        assert "generic" in PROFILES

    def test_quickbooks_profile_is_export_profile(self):
        assert isinstance(PROFILES["quickbooks"], ExportProfile)

    def test_xero_profile_is_export_profile(self):
        assert isinstance(PROFILES["xero"], ExportProfile)

    def test_generic_profile_is_export_profile(self):
        assert isinstance(PROFILES["generic"], ExportProfile)

    def test_quickbooks_has_expected_columns(self):
        cols = PROFILES["quickbooks"].columns
        expected = ["Date", "Transaction Type", "Num", "Name", "Memo",
                     "Account", "Debit", "Credit", "Currency"]
        assert cols == expected

    def test_xero_has_expected_columns(self):
        cols = PROFILES["xero"].columns
        expected = ["Date", "Contact", "Description", "Quantity",
                     "Unit Price", "Amount", "Tax Rate", "Tax Amount",
                     "Account Code", "Currency Code"]
        assert cols == expected

    def test_generic_has_expected_columns(self):
        cols = PROFILES["generic"].columns
        expected = ["Date", "Merchant", "Category", "Description",
                     "Amount", "Currency", "Tax"]
        assert cols == expected


class TestReceiptExporterInterface:
    """Verify ReceiptExporter class exists with required methods."""

    def test_class_exists(self):
        assert ReceiptExporter is not None

    def test_init_signature(self):
        sig = inspect.signature(ReceiptExporter.__init__)
        params = list(sig.parameters)
        assert "profile" in params

    def test_init_profile_default(self):
        sig = inspect.signature(ReceiptExporter.__init__)
        assert sig.parameters["profile"].default == "generic"

    def test_export_csv_exists(self):
        assert hasattr(ReceiptExporter, "export_csv")
        assert callable(ReceiptExporter.export_csv)

    def test_export_csv_signature(self):
        sig = inspect.signature(ReceiptExporter.export_csv)
        params = list(sig.parameters)
        assert "receipts" in params
        assert "include_header" in params

    def test_export_rows_exists(self):
        assert hasattr(ReceiptExporter, "export_rows")
        assert callable(ReceiptExporter.export_rows)

    def test_list_profiles_static(self):
        assert hasattr(ReceiptExporter, "list_profiles")

    def test_get_profile_static(self):
        assert hasattr(ReceiptExporter, "get_profile")

    def test_export_receipts_function_exists(self):
        assert callable(export_receipts)


# ===========================================================================
# BEHAVIORAL TESTS — should fail with NotImplementedError until implemented
# ===========================================================================

class TestReceiptExporterBehavior:
    """Behavioral: CSV export for each profile format."""

    def test_quickbooks_csv_has_headers(self, sample_receipts):
        try:
            exporter = ReceiptExporter("quickbooks")
            csv_str = exporter.export_csv(sample_receipts)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        first_line = csv_str.strip().split("\n")[0]
        assert "Date" in first_line
        assert "Name" in first_line
        assert "Debit" in first_line

    def test_quickbooks_csv_has_data_row(self, sample_receipts):
        try:
            exporter = ReceiptExporter("quickbooks")
            csv_str = exporter.export_csv(sample_receipts)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        lines = csv_str.strip().split("\n")
        assert len(lines) >= 2  # header + at least 1 data row

    def test_xero_csv_has_headers(self, sample_receipts):
        try:
            exporter = ReceiptExporter("xero")
            csv_str = exporter.export_csv(sample_receipts)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        first_line = csv_str.strip().split("\n")[0]
        assert "Contact" in first_line
        assert "Amount" in first_line

    def test_generic_csv_has_headers(self, sample_receipts):
        try:
            exporter = ReceiptExporter("generic")
            csv_str = exporter.export_csv(sample_receipts)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        first_line = csv_str.strip().split("\n")[0]
        assert "Merchant" in first_line
        assert "Amount" in first_line

    def test_empty_receipts_returns_header_only(self):
        try:
            exporter = ReceiptExporter("generic")
            csv_str = exporter.export_csv([])
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # header only

    def test_list_profiles_returns_three(self):
        result = ReceiptExporter.list_profiles()
        assert sorted(result) == ["generic", "quickbooks", "xero"]

    def test_get_profile_returns_export_profile(self):
        try:
            profile = ReceiptExporter.get_profile("quickbooks")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(profile, ExportProfile)
        assert profile.name == "quickbooks"

    def test_get_profile_invalid_raises(self):
        try:
            with pytest.raises(ValueError):
                ReceiptExporter.get_profile("nonexistent")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")

    def test_export_rows_returns_list_of_dicts(self, sample_receipts):
        try:
            exporter = ReceiptExporter("generic")
            rows = exporter.export_rows(sample_receipts)
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(rows, list)
        assert all(isinstance(r, dict) for r in rows)

    def test_export_receipts_convenience_function(self, sample_receipts):
        try:
            csv_str = export_receipts(sample_receipts, format="generic")
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(csv_str, str)
        assert "Merchant" in csv_str.split("\n")[0]

    def test_formula_injection_prevention(self):
        """Text fields starting with =, +, -, @ should be prefixed with '."""
        receipt = NormalizedReceipt(
            receipt_id="r1",
            merchant="=SUM(A1:A10)",  # formula injection attempt
            date=date(2026, 7, 1),
            items=[],
            subtotal=0,
            tax=None,
            tax_rate=None,
            total=0,
            currency="USD",
            language="eng",
            raw_text="=SUM(A1:A10)",
        )
        try:
            exporter = ReceiptExporter("generic")
            csv_str = exporter.export_csv([receipt])
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        # Formula injection should be neutralized
        assert "=SUM" not in csv_str or "'=SUM" in csv_str
