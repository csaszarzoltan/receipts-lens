"""Feature specs for FEAT-038 .. FEAT-048: statuses, transitions, inputs, roles and checks.

Every action lists the statuses it may start from (sources) and the statuses it can end in
(targets). tests/test_feature_specs.py checks that each status is reachable and that
every target is declared.
"""
from __future__ import annotations

import re
from decimal import ROUND_DOWN, Decimal
from typing import Any

from app.feature_core import REVIEWER_ROLES, Action, FeatureSpec, Hub

Data = dict[str, Any]
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ---------------------------------------------------------------------------
# Reusable checks
# ---------------------------------------------------------------------------

def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def require(*keys: str):
    def check(_hub: Hub, _tenant: str, data: Data) -> list[str]:
        return [f"{k} is required" for k in keys if _blank(data.get(k))]
    return check


def positive(key: str):
    def check(_hub: Hub, _tenant: str, data: Data) -> list[str]:
        value = data.get(key)
        if value is None:
            return [f"{key} is required"]
        return [] if float(value) > 0 else [f"{key} must be greater than zero"]
    return check


def receipt_exists(key: str):
    def check(hub: Hub, tenant: str, data: Data) -> list[str]:
        if _blank(data.get(key)):
            return [f"{key} is required"]
        return [] if hub.receipt(tenant, str(data[key])) else [f"{key}: receipt not found"]
    return check


def receipt_optional_exists(key: str):
    def check(hub: Hub, tenant: str, data: Data) -> list[str]:
        if _blank(data.get(key)):
            return []
        return [] if hub.receipt(tenant, str(data[key])) else [f"{key}: receipt not found"]
    return check


def refund_within_receipt(partial: bool):
    """A refund cannot exceed the original receipt total; a partial refund must stay below it."""
    def check(hub: Hub, tenant: str, data: Data) -> list[str]:
        receipt = hub.receipt(tenant, str(data.get("original_receipt") or ""))
        if receipt is None:
            return ["original_receipt: receipt not found"]
        total = receipt.get("total")
        if total is None:
            return []  # the receipt total is unconfirmed, so it cannot be compared
        amount = float(data.get("amount") or 0)
        if partial and amount >= total:
            return ["amount must be below the receipt total for a partial refund"]
        if not partial and amount > total:
            return ["amount is larger than the receipt total"]
        return []
    return check


def period_format(_hub: Hub, _tenant: str, data: Data) -> list[str]:
    period = data.get("period")
    if _blank(period):
        return ["period is required"]
    return [] if PERIOD_RE.match(str(period)) else ["period must look like YYYY-MM"]


def open_tasks_are_zero(hub: Hub, tenant: str, data: Data) -> list[str]:
    count = hub.open_quality_tasks(tenant, str(data.get("period") or ""))
    return [f"{count} open quality task(s) block this period"] if count else []


def enrich_open_tasks(hub: Hub, tenant: str, data: Data) -> None:
    data["open_quality_tasks"] = hub.open_quality_tasks(tenant, str(data.get("period") or ""))


def precheck_target(hub: Hub, tenant: str, data: Data) -> str:
    return "READY_TO_CLOSE" if data.get("open_quality_tasks", 0) == 0 else "BLOCKED"


def _participants(value: Any) -> list[str]:
    seen: dict[str, None] = {}
    for part in str(value or "").split(","):
        name = part.strip()
        if name and name.lower() not in {k.lower() for k in seen}:
            seen[name] = None
    return list(seen)


def _cost_split_errors(data: Data) -> list[str]:
    errors = []
    if data.get("total") is None or float(data["total"]) <= 0:
        errors.append("total must be greater than zero")
    if len(_participants(data.get("participants"))) < 2:
        errors.append("at least two participants are required")
    return errors


def split_shares(data: Data) -> list[dict[str, Any]]:
    """Equal split in cents; the remainder cents go to the first participants."""
    names = _participants(data.get("participants"))
    if _cost_split_errors(data) or not names:
        return []
    cents = int((Decimal(str(data["total"])) * 100).to_integral_value(rounding=ROUND_DOWN))
    base, remainder = divmod(cents, len(names))
    return [
        {"name": name, "amount": (base + (1 if i < remainder else 0)) / 100}
        for i, name in enumerate(names)
    ]


def _cost_split_derive(data: Data) -> Data:
    names = _participants(data.get("participants"))
    return {"shares": split_shares(data), "participant_count": len(names)}


def _savings_derive(data: Data) -> Data:
    target = float(data.get("target_amount") or 0)
    saved = float(data.get("saved_amount") or 0)
    progress = min(saved / target, 1.0) if target > 0 else 0.0
    return {"progress": round(progress, 4), "remaining": round(max(target - saved, 0.0), 2)}


def _price_derive(data: Data) -> Data:
    last = data.get("last_price")
    watch = data.get("watch_price")
    below = last is not None and watch is not None and float(last) <= float(watch)
    return {"below_watch": bool(below)}


# ---------------------------------------------------------------------------
# Targets that depend on the merged data
# ---------------------------------------------------------------------------

def _to_receipt_status(hub: Hub, tenant: str, data: Data) -> str:
    receipt = hub.receipt(tenant, str(data.get("receipt") or "")) or {}
    status = receipt.get("status")
    if status in ("completed", "approved"):
        return "APPROVED"
    if status == "needs_review":
        return "NEEDS_REVIEW"
    if status in ("rejected", "failed"):
        return "FAILED"
    return "PROCESSING"


def _savings_target(_hub: Hub, _tenant: str, data: Data) -> str:
    saved = float(data.get("saved_amount") or 0)
    target = float(data.get("target_amount") or 0)
    return "ACHIEVED" if saved >= target else "ON_TRACK"


def _price_target(_hub: Hub, _tenant: str, data: Data) -> str:
    return "NEEDS_REVIEW" if data.get("below_watch_price") else "TRACKED"


def _enrich_price(_hub: Hub, _tenant: str, data: Data) -> None:
    observed = data.pop("observed_price", None)
    if observed is None:
        return
    data["last_price"] = observed
    data["below_watch_price"] = float(observed) <= float(data.get("watch_price") or 0)


def _enrich_contribution(_hub: Hub, _tenant: str, data: Data) -> None:
    amount = data.pop("amount", None)
    if amount is None:
        return
    data["saved_amount"] = round(float(data.get("saved_amount") or 0) + float(amount), 2)


def _enrich_sync(_hub: Hub, _tenant: str, data: Data) -> None:
    base = data.pop("base_revision", None)
    server = float(data.get("server_revision") or 0)
    ok = base is not None and float(base) == server
    data["sync_ok"] = ok
    if ok:
        data["server_revision"] = server + 1


def _sync_target(_hub: Hub, _tenant: str, data: Data) -> str:
    return "SYNCED" if data.get("sync_ok") else "CONFLICT"


def _positive_amount(key: str):
    def check(_hub: Hub, _tenant: str, data: Data) -> list[str]:
        value = data.get(key)
        return [] if value is not None and float(value) > 0 else [f"{key} must be greater than zero"]
    return check


def _merchant_and_amount(_hub: Hub, _tenant: str, data: Data) -> list[str]:
    errors = require("merchant")(_hub, _tenant, data)
    if data.get("amount") is None or float(data["amount"]) <= 0:
        errors.append("amount must be greater than zero")
    return errors


# ---------------------------------------------------------------------------
# FEAT-038 reconciliation: bank and card transactions matched to each other
# ---------------------------------------------------------------------------

RECONCILIATION = FeatureSpec(
    key="reconciliation",
    prefix="/api/v2/reconciliation/matches",
    feat="FEAT-038",
    statuses=("UNMATCHED", "SUGGESTED", "CONFIRMED", "REJECTED", "REVERSED"),
    initial="UNMATCHED",
    fields=("bank_reference", "card_reference", "amount", "currency"),
    numbers=("amount",),
    create_check=lambda h, t, d: (
        [] if not _blank(d.get("bank_reference")) or not _blank(d.get("card_reference"))
        else ["bank_reference or card_reference is required"]
    ),
    actions=(
        Action("suggest", ("UNMATCHED",), ("SUGGESTED",), "SUGGESTED",
               requires=("bank_reference", "card_reference")),
        Action("confirm", ("UNMATCHED", "SUGGESTED"), ("CONFIRMED",), "CONFIRMED",
               requires=("bank_reference", "card_reference")),
        Action("reject", ("SUGGESTED", "CONFIRMED"), ("REJECTED",), "REJECTED",
               input="reason", input_required=True, requires=("reason",)),
        Action("reverse", ("CONFIRMED",), ("REVERSED",), "REVERSED",
               input="reason", input_required=True, requires=("reason",)),
        Action("reopen", ("REJECTED", "REVERSED"), ("UNMATCHED",), "UNMATCHED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-039 missing receipts: transactions with no receipt yet
# ---------------------------------------------------------------------------

MISSING_RECEIPTS = FeatureSpec(
    key="missing_receipts",
    prefix="/api/v2/missing-receipts",
    feat="FEAT-039",
    statuses=("OPEN", "ASSIGNED", "SNOOZED", "EXEMPTED", "RESOLVED", "REOPENED"),
    initial="OPEN",
    fields=("merchant", "amount", "date"),
    numbers=("amount",),
    create_check=_merchant_and_amount,
    actions=(
        Action("assign", ("OPEN", "REOPENED", "SNOOZED"), ("ASSIGNED",), "ASSIGNED",
               input="assignee", input_required=True, requires=("assignee",)),
        Action("snooze", ("OPEN", "ASSIGNED"), ("SNOOZED",), "SNOOZED",
               input="snooze_until", input_type="date", input_required=True, requires=("snooze_until",)),
        Action("exempt", ("OPEN", "ASSIGNED", "SNOOZED", "REOPENED"), ("EXEMPTED",), "EXEMPTED",
               input="reason", input_required=True, requires=("reason",)),
        Action("resolve", ("OPEN", "ASSIGNED", "SNOOZED", "REOPENED"), ("RESOLVED",), "RESOLVED",
               input="receipt", input_required=True, requires=("receipt",),
               check=receipt_exists("receipt")),
        Action("reopen", ("RESOLVED", "EXEMPTED", "SNOOZED"), ("REOPENED",), "REOPENED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-042 refunds and reversals matched to the original receipt
# ---------------------------------------------------------------------------

REFUNDS = FeatureSpec(
    key="refunds",
    prefix="/api/v2/refunds",
    feat="FEAT-042",
    statuses=("DETECTED", "SUGGESTED", "PARTIALLY_MATCHED", "MATCHED", "REVERSED", "DISPUTED"),
    initial="DETECTED",
    fields=("merchant", "amount", "original_receipt"),
    numbers=("amount",),
    create_check=_merchant_and_amount,
    actions=(
        Action("suggest", ("DETECTED",), ("SUGGESTED",), "SUGGESTED",
               input="original_receipt", input_required=True, requires=("original_receipt",),
               check=receipt_exists("original_receipt")),
        Action("partial", ("DETECTED", "SUGGESTED"), ("PARTIALLY_MATCHED",), "PARTIALLY_MATCHED",
               input="original_receipt", input_required=True, requires=("original_receipt", "amount"),
               check=refund_within_receipt(partial=True)),
        Action("match", ("DETECTED", "SUGGESTED", "PARTIALLY_MATCHED"), ("MATCHED",), "MATCHED",
               input="original_receipt", input_required=True, requires=("original_receipt", "amount"),
               check=refund_within_receipt(partial=False)),
        Action("reverse", ("MATCHED", "PARTIALLY_MATCHED"), ("REVERSED",), "REVERSED"),
        Action("dispute", ("DETECTED", "SUGGESTED", "PARTIALLY_MATCHED", "MATCHED"), ("DISPUTED",), "DISPUTED",
               input="reason", input_required=True, requires=("reason",)),
        Action("reopen", ("DISPUTED",), ("DETECTED",), "DETECTED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-043 shared purchases and cost splits
# ---------------------------------------------------------------------------

COST_SPLITS = FeatureSpec(
    key="cost_splits",
    prefix="/api/v2/cost-splits",
    feat="FEAT-043",
    statuses=("DRAFT", "PENDING_APPROVAL", "APPROVED", "DISPUTED", "CANCELLED"),
    initial="DRAFT",
    fields=("receipt", "total", "participants", "currency"),
    numbers=("total",),
    create_check=lambda h, t, d: _cost_split_errors(d) + receipt_optional_exists("receipt")(h, t, d),
    derive=_cost_split_derive,
    actions=(
        Action("submit", ("DRAFT", "DISPUTED"), ("PENDING_APPROVAL",), "PENDING_APPROVAL",
               requires=("total", "participants"), check=lambda h, t, d: _cost_split_errors(d)),
        Action("approve", ("PENDING_APPROVAL",), ("APPROVED",), "APPROVED",
               roles=REVIEWER_ROLES),
        Action("dispute", ("PENDING_APPROVAL", "APPROVED"), ("DISPUTED",), "DISPUTED",
               input="reason", input_required=True, requires=("reason",)),
        Action("cancel", ("DRAFT", "PENDING_APPROVAL", "DISPUTED"), ("CANCELLED",), "CANCELLED"),
        Action("reopen", ("DISPUTED", "CANCELLED"), ("DRAFT",), "DRAFT"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-044 spending goals and savings: progress is derived from contributions
# ---------------------------------------------------------------------------

SAVINGS_GOALS = FeatureSpec(
    key="savings_goals",
    prefix="/api/v2/savings-goals",
    feat="FEAT-044",
    statuses=("DRAFT", "ACTIVE", "ON_TRACK", "AT_RISK", "ACHIEVED", "PAUSED", "ARCHIVED"),
    initial="DRAFT",
    fields=("target_amount", "currency", "deadline", "saved_amount"),
    numbers=("target_amount", "amount", "saved_amount"),
    create_check=lambda h, t, d: (
        [] if d.get("target_amount") is not None and float(d["target_amount"]) > 0
        else ["target_amount must be greater than zero"]
    ) + ([] if len(str(d.get("currency") or "")) == 3 else ["currency must be a 3-letter code"]),
    derive=_savings_derive,
    actions=(
        Action("activate", ("DRAFT", "PAUSED"), ("ACTIVE",), "ACTIVE",
               requires=("target_amount",), check=positive("target_amount")),
        Action("contribute", ("ACTIVE", "ON_TRACK", "AT_RISK"), ("ON_TRACK", "ACHIEVED"), _savings_target,
               input="amount", input_type="number", input_required=True, requires=("amount",),
               check=_positive_amount("amount"), enrich=_enrich_contribution),
        Action("flag_risk", ("ACTIVE", "ON_TRACK"), ("AT_RISK",), "AT_RISK",
               input="reason", input_required=True, requires=("reason",)),
        Action("pause", ("ACTIVE", "ON_TRACK", "AT_RISK"), ("PAUSED",), "PAUSED"),
        Action("archive", ("DRAFT", "ACTIVE", "ON_TRACK", "AT_RISK", "ACHIEVED", "PAUSED"), ("ARCHIVED",), "ARCHIVED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-041 household price watch: a candidate becomes tracked; prices below the watch need review
# ---------------------------------------------------------------------------

PRICE_TRACKING = FeatureSpec(
    key="price_tracking",
    prefix="/api/v2/price-tracking",
    feat="FEAT-041",
    statuses=("CANDIDATE", "TRACKED", "NEEDS_REVIEW", "PAUSED", "ARCHIVED"),
    initial="CANDIDATE",
    fields=("product", "merchant", "watch_price"),
    numbers=("watch_price", "observed_price"),
    create_check=lambda h, t, d: require("product")(h, t, d) + positive("watch_price")(h, t, d),
    derive=_price_derive,
    actions=(
        Action("track", ("CANDIDATE", "PAUSED", "NEEDS_REVIEW"), ("TRACKED",), "TRACKED",
               requires=("watch_price",), check=positive("watch_price")),
        Action("observe", ("TRACKED", "NEEDS_REVIEW"), ("TRACKED", "NEEDS_REVIEW"), _price_target,
               input="observed_price", input_type="number", input_required=True,
               requires=("observed_price",), check=_positive_amount("observed_price"), enrich=_enrich_price),
        Action("pause", ("TRACKED", "NEEDS_REVIEW"), ("PAUSED",), "PAUSED"),
        Action("archive", ("CANDIDATE", "TRACKED", "NEEDS_REVIEW", "PAUSED"), ("ARCHIVED",), "ARCHIVED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-046 data-quality tasks: must be resolved before a period can close
# ---------------------------------------------------------------------------

QUALITY_TASKS = FeatureSpec(
    key="data_quality",
    prefix="/api/v2/quality-tasks",
    feat="FEAT-046",
    statuses=("OPEN", "ASSIGNED", "IN_PROGRESS", "SNOOZED", "EXEMPTED", "RESOLVED", "REOPENED"),
    initial="OPEN",
    fields=("issue_type", "receipt", "period"),
    create_check=lambda h, t, d: require("issue_type")(h, t, d) + receipt_optional_exists("receipt")(h, t, d),
    actions=(
        Action("assign", ("OPEN", "REOPENED", "SNOOZED"), ("ASSIGNED",), "ASSIGNED",
               input="assignee", input_required=True, requires=("assignee",)),
        Action("start", ("OPEN", "ASSIGNED", "REOPENED"), ("IN_PROGRESS",), "IN_PROGRESS"),
        Action("snooze", ("OPEN", "ASSIGNED", "IN_PROGRESS"), ("SNOOZED",), "SNOOZED",
               input="reason", input_required=True, requires=("reason",)),
        Action("exempt", ("OPEN", "ASSIGNED", "IN_PROGRESS", "SNOOZED"), ("EXEMPTED",), "EXEMPTED",
               input="reason", input_required=True, requires=("reason",)),
        Action("resolve", ("OPEN", "ASSIGNED", "IN_PROGRESS", "REOPENED"), ("RESOLVED",), "RESOLVED",
               input="note", input_required=True, requires=("note",)),
        Action("reopen", ("RESOLVED", "EXEMPTED"), ("REOPENED",), "REOPENED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-047 accounting periods: close requires no open quality tasks; closed periods are locked
# ---------------------------------------------------------------------------

PERIOD_CLOSE = FeatureSpec(
    key="period_close",
    prefix="/api/v2/accounting-periods",
    feat="FEAT-047",
    statuses=("OPEN", "BLOCKED", "READY_TO_CLOSE", "CLOSED", "REOPEN_PENDING", "REOPENED"),
    initial="OPEN",
    fields=("period", "note"),
    create_check=period_format,
    actions=(
        Action("precheck", ("OPEN", "BLOCKED", "READY_TO_CLOSE", "REOPENED"), ("READY_TO_CLOSE", "BLOCKED"),
               precheck_target, requires=("period",), enrich=enrich_open_tasks),
        Action("close", ("READY_TO_CLOSE",), ("CLOSED",), "CLOSED",
               roles=REVIEWER_ROLES, check=open_tasks_are_zero),
        Action("request_reopen", ("CLOSED",), ("REOPEN_PENDING",), "REOPEN_PENDING",
               input="reason", input_required=True, requires=("reason",)),
        Action("approve_reopen", ("REOPEN_PENDING",), ("REOPENED",), "REOPENED", roles=REVIEWER_ROLES),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-045 offline captures waiting to sync; base_revision detects a conflicting server change
# ---------------------------------------------------------------------------

OFFLINE_SYNC = FeatureSpec(
    key="offline_sync",
    prefix="/api/v2/offline-sync",
    feat="FEAT-045",
    statuses=("LOCAL_ONLY", "QUEUED", "UPLOADING", "PROCESSING", "CONFLICT", "SYNCED", "FAILED", "DISCARDED"),
    initial="LOCAL_ONLY",
    fields=("device", "receipt"),
    numbers=("base_revision",),
    create_check=lambda h, t, d: require("device")(h, t, d) + receipt_optional_exists("receipt")(h, t, d),
    actions=(
        Action("queue", ("LOCAL_ONLY", "FAILED"), ("QUEUED",), "QUEUED"),
        Action("start_upload", ("QUEUED",), ("UPLOADING",), "UPLOADING"),
        Action("process", ("UPLOADING",), ("PROCESSING",), "PROCESSING"),
        Action("sync", ("PROCESSING",), ("SYNCED", "CONFLICT"), _sync_target,
               input="base_revision", input_type="number", input_required=True, requires=("base_revision",),
               enrich=_enrich_sync),
        Action("retry", ("CONFLICT", "FAILED"), ("QUEUED",), "QUEUED"),
        Action("fail", ("QUEUED", "UPLOADING", "PROCESSING"), ("FAILED",), "FAILED",
               input="reason", input_required=True, requires=("reason",)),
        Action("discard", ("LOCAL_ONLY", "QUEUED", "FAILED", "CONFLICT"), ("DISCARDED",), "DISCARDED"),
    ),
)

# ---------------------------------------------------------------------------
# FEAT-048 mobile capture: a capture links to an uploaded receipt and follows its processing
# ---------------------------------------------------------------------------

MOBILE_RECEIPTS = FeatureSpec(
    key="mobile_receipts",
    prefix="/api/v2/mobile-receipts",
    feat="FEAT-048",
    statuses=("CAPTURING", "PREVIEW", "DRAFT", "PROCESSING", "NEEDS_REVIEW", "APPROVED", "FAILED"),
    initial="CAPTURING",
    fields=("receipt", "merchant", "amount"),
    numbers=("amount",),
    actions=(
        Action("attach", ("CAPTURING",), ("PREVIEW",), "PREVIEW",
               input="receipt", input_required=True, requires=("receipt",),
               check=receipt_exists("receipt")),
        Action("save_draft", ("PREVIEW",), ("DRAFT",), "DRAFT", requires=("receipt",)),
        Action("sync", ("PREVIEW", "DRAFT", "PROCESSING", "NEEDS_REVIEW", "FAILED"),
               ("PROCESSING", "NEEDS_REVIEW", "APPROVED", "FAILED"), _to_receipt_status,
               requires=("receipt",), check=receipt_exists("receipt")),
        Action("approve", ("PREVIEW", "DRAFT", "NEEDS_REVIEW"), ("APPROVED",), "APPROVED",
               roles=REVIEWER_ROLES, requires=("receipt",), check=receipt_exists("receipt")),
        Action("fail", ("PREVIEW", "DRAFT", "PROCESSING", "NEEDS_REVIEW"), ("FAILED",), "FAILED",
               input="reason", input_required=True, requires=("reason",)),
        Action("retry", ("FAILED",), ("CAPTURING",), "CAPTURING"),
    ),
)

SPECS: dict[str, FeatureSpec] = {
    spec.key: spec
    for spec in (
        RECONCILIATION, MISSING_RECEIPTS, REFUNDS, COST_SPLITS, SAVINGS_GOALS,
        PRICE_TRACKING, QUALITY_TASKS, PERIOD_CLOSE, OFFLINE_SYNC, MOBILE_RECEIPTS,
    )
}

__all__ = ["SPECS", "split_shares"]
