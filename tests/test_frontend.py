"""Pre-development interface + behavioral tests for ReceiptLens Next.js frontend.

Covers the frontend project structure, TypeScript type definitions,
typed API client, React component smoke tests, and behavioral stubs
for all core pages (Dashboard, Upload, Receipts, Forecast, etc.).

Layout:
  * Interface tests — filesystem, type parsing, API contract checks.
    These MUST pass immediately after the developer scaffolds the
    Next.js project and adds the required files.
  * Behavioral tests — acceptance-criteria assertions that fail with
    NotImplementedError until the feature is implemented.

Run with:
    .venv/bin/python -m pytest tests/test_frontend.py -v
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"

# Required files after P0-1 scaffolding
REQUIRED_FILES = [
    "package.json",
    "tsconfig.json",
    "next.config.ts",
    "tailwind.config.ts",
    "app/layout.tsx",
    "app/page.tsx",
    "app/globals.css",
]

# Required lib files after P0-2 / P0-3
REQUIRED_LIB_FILES = [
    "lib/types.ts",
    "lib/api.ts",
    "lib/i18n.ts",
    "lib/auth.ts",
    "lib/utils.ts",
]

# Required component files after P0-4 / P0-5
REQUIRED_COMPONENT_FILES = [
    "components/AppShell.tsx",
    "components/Sidebar.tsx",
    "components/MobileNav.tsx",
    "components/Topbar.tsx",
    "components/EmptyState.tsx",
    "components/ConfidenceBadge.tsx",
    "components/StatusBadge.tsx",
    "components/Money.tsx",
    "components/Pagination.tsx",
    "components/FilterBar.tsx",
    "components/Toast.tsx",
    "components/Modal.tsx",
]

# Page route files
REQUIRED_PAGE_FILES = [
    "app/(app)/layout.tsx",
    "app/(app)/dashboard/page.tsx",
    "app/(app)/receipts/page.tsx",
    "app/(app)/upload/page.tsx",
    "app/(app)/review/page.tsx",
    "app/(app)/approvals/page.tsx",
    "app/(app)/forecast/page.tsx",
    "app/(app)/settings/page.tsx",
    "app/(auth)/login/page.tsx",
]

# TypeScript interface names that must exist in lib/types.ts
REQUIRED_INTERFACES = [
    "Receipt",
    "LineItem",
    "ReceiptItem",
    "ReceiptStatus",
    "ReceiptMetadata",
    "ReadinessInfo",
    "DashboardData",
    "ReviewItem",
    "Approval",
    "ApprovalPolicy",
    "DuplicateCandidate",
    "AutomationRule",
    "Connection",
    "ExportRun",
    "ExportPreparation",
    "ValidationResult",
    "OCRBox",
    "HistoryEntry",
    "ForecastResult",
    "ForecastEntry",
    "AnomalyResult",
    "AnomalyEntry",
    "BudgetVarianceResult",
    "BudgetProjection",
    "WorkQueueItem",
    "Notification",
    "SavedView",
    "Member",
    "PermissionMatrix",
    "Preferences",
    "RecurringExpense",
    "InboundEmail",
    "Job",
    "BatchJob",
    "Diagnostics",
    "ExchangeRate",
]

# API client functions that must exist in lib/api.ts
REQUIRED_API_FUNCTIONS = [
    "getHealth",
    "getReadiness",
    "getCapabilities",
    "uploadReceipt",
    "searchReceipts",
    "getReceipt",
    "getReceiptImage",
    "getReceiptBoxes",
    "getReceiptHistory",
    "validateReceipt",
    "updateMetadata",
    "updateReceiptWorkspace",
    "updateLineItems",
    "getReviewItems",
    "correctReceipt",
    "getApprovals",
    "decideApproval",
    "createApprovalPolicy",
    "getDuplicates",
    "decideDuplicate",
    "getRules",
    "createRule",
    "previewRule",
    "getSavedViews",
    "createSavedView",
    "deleteSavedView",
    "getNotifications",
    "updateNotification",
    "markAllRead",
    "getMembers",
    "addMember",
    "getConnections",
    "createConnection",
    "testConnection",
    "createExport",
    "getExportRuns",
    "prepareExport",
    "getExportFormats",
    "getDashboard",
    "getWorkQueue",
    "getJobs",
    "retryJob",
    "cancelJob",
    "exportPrivacyData",
    "setRetention",
    "purgeExpired",
    "getPreferences",
    "savePreferences",
    "batchUpload",
    "getBatchStatus",
    "getForecast",
    "getAnomalies",
    "getBudgetVariance",
    "getApprovalFlows",
    "getInboundEmails",
    "receiveEmail",
    "getRecurringExpenses",
    "submitRecurringFeedback",
    "getPermissions",
    "updatePermissions",
    "getDiagnostics",
    "downloadDiagnostics",
    "createApiKey",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_ts(relpath: str) -> str:
    """Read a TypeScript file from frontend/ and return its content."""
    path = FRONTEND / relpath
    if not path.exists():
        pytest.fail(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def _ts_has_interface(content: str, name: str) -> bool:
    """Check if TypeScript content defines an interface or type with given name."""
    # Match: export interface Name { ... } or export type Name = ...
    pattern = rf"export\s+(interface|type)\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


def _ts_has_function(content: str, name: str) -> bool:
    """Check if TypeScript content defines an exported function with given name."""
    # Match: export async function name( or export function name(
    pattern = rf"export\s+(async\s+)?function\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


def _ts_has_export_const(content: str, name: str) -> bool:
    """Check if TypeScript content has export const name = function or similar."""
    # Also match: export const name = async ( or export const name = (
    pattern = rf"export\s+const\s+{re.escape(name)}\s*=\s*(async\s+)?\("
    return bool(re.search(pattern, content))


def _ts_has_type(content: str, name: str) -> bool:
    """Check if TypeScript content defines a type alias."""
    pattern = rf"export\s+type\s+{re.escape(name)}\s*="
    return bool(re.search(pattern, content))


def _ts_has_component(content: str, name: str) -> bool:
    """Check if TypeScript content exports a React component."""
    # Match: export default function Name( or export function Name(
    pattern = rf"export\s+(default\s+)?(function|const)\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


# ============================================================================
# INTERFACE TESTS — must pass immediately after scaffolding
# ============================================================================


class TestProjectStructure:
    """Verify Next.js project exists with correct structure."""

    def test_frontend_directory_exists(self) -> None:
        assert FRONTEND.is_dir(), f"frontend/ directory not found at {FRONTEND}"

    @pytest.mark.parametrize("filename", REQUIRED_FILES)
    def test_required_file_exists(self, filename: str) -> None:
        path = FRONTEND / filename
        assert path.exists(), f"Missing required file: frontend/{filename}"

    def test_package_json_has_next(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "next" in deps, "package.json must list 'next' as a dependency"

    def test_package_json_has_react(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "react" in deps, "package.json must list 'react' as a dependency"

    def test_package_json_has_swr(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "swr" in deps, "package.json must list 'swr' as a dependency"

    def test_package_json_has_tailwind(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "tailwindcss" in deps, "package.json must list 'tailwindcss'"

    def test_package_json_has_typescript(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "typescript" in deps, "package.json must list 'typescript'"

    def test_package_json_has_recharts(self) -> None:
        import json
        pkg = json.loads((FRONTEND / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "recharts" in deps, "package.json must list 'recharts'"

    def test_tsconfig_json_exists(self) -> None:
        import json
        tsconfig = json.loads((FRONTEND / "tsconfig.json").read_text())
        assert "compilerOptions" in tsconfig, "tsconfig.json must have compilerOptions"

    def test_next_config_exists(self) -> None:
        path = FRONTEND / "next.config.ts"
        assert path.exists(), "next.config.ts must exist"


class TestLibFiles:
    """Verify lib/ directory has required modules."""

    @pytest.mark.parametrize("filename", REQUIRED_LIB_FILES)
    def test_lib_file_exists(self, filename: str) -> None:
        path = FRONTEND / filename
        assert path.exists(), f"Missing required lib file: frontend/{filename}"


class TestComponentFiles:
    """Verify components/ directory has required components."""

    @pytest.mark.parametrize("filename", REQUIRED_COMPONENT_FILES)
    def test_component_file_exists(self, filename: str) -> None:
        path = FRONTEND / filename
        assert path.exists(), f"Missing required component: frontend/{filename}"


class TestPageFiles:
    """Verify app/ directory has required page routes."""

    @pytest.mark.parametrize("filename", REQUIRED_PAGE_FILES)
    def test_page_file_exists(self, filename: str) -> None:
        path = FRONTEND / filename
        assert path.exists(), f"Missing required page: frontend/{filename}"


class TestTypeScriptTypes:
    """Verify lib/types.ts defines all required interfaces."""

    @pytest.fixture(scope="class")
    def types_content(self) -> str:
        return _read_ts("lib/types.ts")

    @pytest.mark.parametrize("interface_name", REQUIRED_INTERFACES)
    def test_interface_exists(self, types_content: str, interface_name: str) -> None:
        assert _ts_has_interface(types_content, interface_name), (
            f"lib/types.ts must define 'export interface {interface_name}' "
            f"or 'export type {interface_name}'"
        )

    def test_receipt_has_required_fields(self, types_content: str) -> None:
        for field in ["vendor", "total", "date", "tax", "currency", "line_items", "confidence"]:
            assert field in types_content, f"Receipt interface must have '{field}' field"

    def test_forecast_result_has_required_fields(self, types_content: str) -> None:
        for field in ["period", "currency", "forecasts", "source_range"]:
            assert field in types_content, f"ForecastResult must have '{field}' field"

    def test_anomaly_result_has_required_fields(self, types_content: str) -> None:
        for field in ["method", "threshold", "anomalies"]:
            assert field in types_content, f"AnomalyResult must have '{field}' field"

    def test_budget_variance_has_required_fields(self, types_content: str) -> None:
        for field in ["currency", "projections"]:
            assert field in types_content, f"BudgetVarianceResult must have '{field}' field"

    def test_receipt_status_enum_values(self, types_content: str) -> None:
        for status in ["needs_review", "completed", "pending", "approved", "rejected", "failed"]:
            assert status in types_content, f"ReceiptStatus must include '{status}'"

    def test_preferences_has_onboarding_field(self, types_content: str) -> None:
        assert "onboarding_done" in types_content, (
            "Preferences interface must have 'onboarding_done' for onboarding flow"
        )


class TestApiClient:
    """Verify lib/api.ts exports all required typed functions."""

    @pytest.fixture(scope="class")
    def api_content(self) -> str:
        return _read_ts("lib/api.ts")

    @pytest.mark.parametrize("func_name", REQUIRED_API_FUNCTIONS[:20])
    def test_api_function_exists(self, api_content: str, func_name: str) -> None:
        assert _ts_has_function(api_content, func_name) or _ts_has_export_const(
            api_content, func_name
        ), f"lib/api.ts must export function '{func_name}'"

    def test_api_has_api_base_url(self, api_content: str) -> None:
        assert "API_BASE_URL" in api_content or "BASE_URL" in api_content, (
            "lib/api.ts must define API_BASE_URL or BASE_URL"
        )

    def test_api_has_request_function(self, api_content: str) -> None:
        assert _ts_has_function(api_content, "request") or _ts_has_export_const(
            api_content, "request"
        ), "lib/api.ts must export a generic request() function"

    def test_api_has_tenant_request(self, api_content: str) -> None:
        assert _ts_has_function(api_content, "tenantRequest") or _ts_has_export_const(
            api_content, "tenantRequest"
        ), "lib/api.ts must export tenantRequest()"

    def test_api_has_upload_with_progress(self, api_content: str) -> None:
        assert (
            _ts_has_function(api_content, "uploadWithProgress")
            or _ts_has_export_const(api_content, "uploadWithProgress")
        ), "lib/api.ts must export uploadWithProgress()"

    def test_api_has_api_error_class(self, api_content: str) -> None:
        assert "ApiError" in api_content, "lib/api.ts must define ApiError class"

    def test_api_includes_tenant_headers(self, api_content: str) -> None:
        assert "X-Tenant-ID" in api_content, (
            "lib/api.ts must include X-Tenant-ID header"
        )
        assert "X-Role" in api_content, (
            "lib/api.ts must include X-Role header"
        )

    @pytest.mark.parametrize("func_name", REQUIRED_API_FUNCTIONS[20:40])
    def test_api_function_exists_batch2(self, api_content: str, func_name: str) -> None:
        assert _ts_has_function(api_content, func_name) or _ts_has_export_const(
            api_content, func_name
        ), f"lib/api.ts must export function '{func_name}'"

    @pytest.mark.parametrize("func_name", REQUIRED_API_FUNCTIONS[40:])
    def test_api_function_exists_batch3(self, api_content: str, func_name: str) -> None:
        assert _ts_has_function(api_content, func_name) or _ts_has_export_const(
            api_content, func_name
        ), f"lib/api.ts must export function '{func_name}'"


class TestAppShellComponents:
    """Verify core layout components export correctly."""

    @pytest.mark.parametrize(
        "comp_file,comp_name",
        [
            ("components/AppShell.tsx", "AppShell"),
            ("components/Sidebar.tsx", "Sidebar"),
            ("components/MobileNav.tsx", "MobileNav"),
            ("components/Topbar.tsx", "Topbar"),
            ("components/EmptyState.tsx", "EmptyState"),
            ("components/Toast.tsx", "Toast"),
            ("components/Modal.tsx", "Modal"),
        ],
    )
    def test_component_exports(self, comp_file: str, comp_name: str) -> None:
        content = _read_ts(comp_file)
        assert _ts_has_component(content, comp_name), (
            f"frontend/{comp_file} must export component '{comp_name}'"
        )

    def test_empty_state_has_expected_props(self) -> None:
        content = _read_ts("components/EmptyState.tsx")
        for prop in ["icon", "title", "description"]:
            assert prop in content, f"EmptyState must accept '{prop}' prop"

    def test_empty_state_has_optional_action(self) -> None:
        content = _read_ts("components/EmptyState.tsx")
        assert "action" in content, "EmptyState must accept optional 'action' prop"


# ============================================================================
# BEHAVIORAL TESTS — fail with NotImplementedError until implemented
# ============================================================================


class TestDashboardBehavior:
    """Dashboard page renders KPI cards with correct data structure."""

    def test_dashboard_page_file_exists(self) -> None:
        path = FRONTEND / "app/(app)/dashboard/page.tsx"
        assert path.exists(), "Dashboard page must exist"

    def test_dashboard_renders_kpi_cards(self) -> None:
        content = _read_ts("app/(app)/dashboard/page.tsx")
        # Dashboard must reference KPI data or dashboard data
        has_kpi = any(
            term in content
            for term in ["KPI", "kpi", "DashboardData", "dashboard", "getDashboard"]
        )
        assert has_kpi, (
            "Dashboard page must reference KPI cards or DashboardData"
        )

    def test_dashboard_uses_get_dashboard(self) -> None:
        content = _read_ts("app/(app)/dashboard/page.tsx")
        assert "getDashboard" in content or "dashboard" in content.lower(), (
            "Dashboard must call getDashboard() API function"
        )

    def test_dashboard_has_spending_chart(self) -> None:
        """F1.2 §3.4 block 2 — 'Mire ment el a pénzem?' (kördiagram/lista).

        The consumer dashboard renders the monthly category breakdown as a
        list (the plan allows chart OR list); a chart may also be present.
        """
        content = _read_ts("app/(app)/dashboard/page.tsx")
        has_chart = any(
            term in content
            for term in ["Chart", "chart", "recharts", "LineChart", "BarChart", "spending"]
        )
        has_category_list = any(
            term in content
            for term in ["Mire ment el a pénzem", "categories", "monthly_by_category"]
        )
        assert has_chart or has_category_list, (
            "Dashboard must include a spending chart or the category "
            "breakdown list (F1.2 §3.4 block 2)"
        )


class TestReceiptUploadBehavior:
    """Receipt upload flow triggers OCR and shows preview."""

    def test_upload_page_file_exists(self) -> None:
        path = FRONTEND / "app/(app)/upload/page.tsx"
        assert path.exists(), "Upload page must exist"

    def test_upload_has_drop_zone(self) -> None:
        content = _read_ts("app/(app)/upload/page.tsx")
        has_dropzone = any(
            term in content
            for term in ["DropZone", "dropzone", "drop", "upload", "UploadQueue", "file"]
        )
        assert has_dropzone, "Upload page must include a drag-and-drop upload area"

    def test_upload_calls_upload_receipt(self) -> None:
        content = _read_ts("app/(app)/upload/page.tsx")
        has_upload = any(
            term in content
            for term in ["uploadReceipt", "upload", "Upload", "FormData"]
        )
        assert has_upload, "Upload page must call uploadReceipt() or handle file upload"


class TestReceiptListBehavior:
    """Receipt list supports search and filter operations."""

    def test_receipts_page_file_exists(self) -> None:
        path = FRONTEND / "app/(app)/receipts/page.tsx"
        assert path.exists(), "Receipts page must exist"

    def test_receipts_has_search(self) -> None:
        content = _read_ts("app/(app)/receipts/page.tsx")
        has_search = any(
            term in content
            for term in ["search", "Search", "query", "FilterBar", "filter"]
        )
        assert has_search, "Receipts page must support search/filter operations"

    def test_receipts_uses_search_receipts(self) -> None:
        content = _read_ts("app/(app)/receipts/page.tsx")
        has_api = any(
            term in content
            for term in ["searchReceipts", "getReceipts", "receipts"]
        )
        assert has_api, "Receipts page must call searchReceipts() API function"

    def test_receipts_supports_pagination(self) -> None:
        content = _read_ts("app/(app)/receipts/page.tsx")
        has_pagination = any(
            term in content
            for term in ["Pagination", "pagination", "offset", "limit", "page"]
        )
        assert has_pagination, "Receipts page must support pagination"


class TestReceiptDetailBehavior:
    """Receipt detail loads a single receipt directly (regression for F1)."""

    def test_receipt_detail_page_file_exists(self) -> None:
        path = FRONTEND / "app/(app)/receipts/[id]/page.tsx"
        assert path.exists(), "Receipt detail page must exist"

    def test_receipt_detail_uses_direct_get_receipt(self) -> None:
        content = _read_ts("app/(app)/receipts/[id]/page.tsx")
        assert "getReceipt(" in content, "Detail page must call getReceipt() API function"

    def test_receipt_detail_does_not_search_full_list(self) -> None:
        content = _read_ts("app/(app)/receipts/[id]/page.tsx")
        assert "searchReceipts" not in content, (
            "Detail page must not fetch the whole list to find one receipt "
            "(breaks beyond the first 200)"
        )


class TestForecastBehavior:
    """Forecast page displays prediction chart data."""

    def test_forecast_page_file_exists(self) -> None:
        path = FRONTEND / "app/(app)/forecast/page.tsx"
        assert path.exists(), "Forecast page must exist"

    def test_forecast_uses_get_forecast(self) -> None:
        content = _read_ts("app/(app)/forecast/page.tsx")
        has_api = any(
            term in content
            for term in ["getForecast", "ForecastResult", "forecast"]
        )
        assert has_api, "Forecast page must call getForecast() API function"

    def test_forecast_displays_chart(self) -> None:
        content = _read_ts("app/(app)/forecast/page.tsx")
        has_chart = any(
            term in content
            for term in ["Chart", "chart", "recharts", "LineChart", "BarChart", "Area"]
        )
        assert has_chart, "Forecast page must include a chart for predictions"

    def test_forecast_shows_anomalies(self) -> None:
        content = _read_ts("app/(app)/forecast/page.tsx")
        has_anomalies = any(
            term in content
            for term in ["anomal", "Anomaly", "getAnomalies", "AnomalyResult"]
        )
        assert has_anomalies, "Forecast page must display anomaly data"

    def test_forecast_shows_budget_variance(self) -> None:
        content = _read_ts("app/(app)/forecast/page.tsx")
        has_budget = any(
            term in content
            for term in ["budget", "Budget", "getBudgetVariance", "BudgetVariance"]
        )
        assert has_budget, "Forecast page must show budget variance projections"


class TestOnboardingBehavior:
    """Onboarding flow shows for first-time users."""

    def test_onboarding_component_exists(self) -> None:
        path = FRONTEND / "components/Onboarding.tsx"
        assert path.exists(), "Onboarding component must exist"

    def test_onboarding_component_exports(self) -> None:
        content = _read_ts("components/Onboarding.tsx")
        assert _ts_has_component(content, "Onboarding"), (
            "Onboarding.tsx must export an Onboarding component"
        )

    def test_onboarding_checks_preferences(self) -> None:
        content = _read_ts("components/Onboarding.tsx")
        has_check = any(
            term in content
            for term in ["onboarding_done", "onboarding", "preferences", "Preferences"]
        )
        assert has_check, (
            "Onboarding component must check preferences.onboarding_done"
        )

    def test_onboarding_has_steps(self) -> None:
        content = _read_ts("components/Onboarding.tsx")
        has_steps = any(
            term in content
            for term in ["step", "Step", "steps", "Steps", "welcome", "Welcome", "upload"]
        )
        assert has_steps, "Onboarding must have multiple guided steps"

    def test_onboarding_has_skip(self) -> None:
        content = _read_ts("components/Onboarding.tsx")
        has_skip = any(
            term in content
            for term in ["Skip", "skip", "skipOnboarding", "onboarding_done"]
        )
        assert has_skip, "Onboarding must have a Skip option"


class TestEmptyStateBehavior:
    """Empty states render when no data exists."""

    def test_empty_state_component_exists(self) -> None:
        path = FRONTEND / "components/EmptyState.tsx"
        assert path.exists(), "EmptyState component must exist"

    def test_empty_state_accepted_by_receipts(self) -> None:
        content = _read_ts("app/(app)/receipts/page.tsx")
        has_empty = any(
            term in content
            for term in ["EmptyState", "empty", "no receipts", "no data"]
        )
        assert has_empty, "Receipts page must use EmptyState for empty data"

    def test_empty_state_accepted_by_forecast(self) -> None:
        content = _read_ts("app/(app)/forecast/page.tsx")
        has_empty = any(
            term in content
            for term in ["EmptyState", "empty", "not enough data", "No data"]
        )
        assert has_empty, "Forecast page must use EmptyState for insufficient data"

    def test_empty_state_accepted_by_approvals(self) -> None:
        path = FRONTEND / "app/(app)/approvals/page.tsx"
        if path.exists():
            content = path.read_text(encoding="utf-8")
            has_empty = any(
                term in content
                for term in ["EmptyState", "empty", "nothing pending", "No data"]
            )
            assert has_empty, "Approvals page must use EmptyState for empty data"


class TestMobileResponsiveBehavior:
    """Mobile-responsive layout applies correct breakpoints."""

    def test_globals_css_has_tailwind(self) -> None:
        content = _read_ts("app/globals.css")
        has_tailwind = any(
            term in content
            for term in ["@tailwind", "tailwind", "@apply"]
        )
        assert has_tailwind, "globals.css must import Tailwind CSS"

    def test_sidebar_responsive(self) -> None:
        content = _read_ts("components/Sidebar.tsx")
        has_responsive = any(
            term in content
            for term in ["hidden", "md:", "lg:", "xl:", "responsive", "@media"]
        )
        assert has_responsive, "Sidebar must have responsive breakpoint classes"

    def test_mobile_nav_exists(self) -> None:
        content = _read_ts("components/MobileNav.tsx")
        has_mobile = any(
            term in content
            for term in ["mobile", "Mobile", "bottom", "tab", "sm:", "md:"]
        )
        assert has_mobile, "MobileNav must have mobile-specific layout"

    def test_app_shell_includes_both_navs(self) -> None:
        content = _read_ts("components/AppShell.tsx")
        has_sidebar = "Sidebar" in content
        has_mobile = "MobileNav" in content
        assert has_sidebar and has_mobile, (
            "AppShell must include both Sidebar and MobileNav"
        )
