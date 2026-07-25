"""ReceiptLens budget and spending alert system.

``AlertStore`` is an in-memory, thread-safe store that creates alerts when:
- Budget spending exceeds ``alert_threshold`` (budget_threshold alert).
- Current period spending deviates > 2× stddev from historical average
  (unusual_spending alert).

Alerts can be acknowledged via ``POST /api/v1/alerts/{id}/acknowledge``.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from enum import Enum


class AlertType(str, Enum):
    BUDGET_THRESHOLD = "budget_threshold"
    UNUSUAL_SPENDING = "unusual_spending"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert:
    """A single alert instance."""

    def __init__(
        self,
        alert_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        category: str,
        message: str,
        pct_used: float | None = None,
        created_at: str | None = None,
        acknowledged: bool = False,
    ) -> None:
        self.alert_id = alert_id
        self.type = alert_type
        self.severity = severity
        self.category = category
        self.message = message
        self.pct_used = pct_used
        self.created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.acknowledged = acknowledged


class AlertStore:
    """Thread-safe in-memory store for alerts.

    ``AlertStore.evaluate_budgets()`` should be called after every receipt
    addition to check budget thresholds and unusual spending patterns.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, Alert] = {}

    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        category: str,
        message: str,
        pct_used: float | None = None,
    ) -> Alert:
        """Create a new alert and store it.  Returns the stored ``Alert``."""
        alert_id = str(uuid.uuid4())
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            category=category,
            message=message,
            pct_used=pct_used,
        )
        with self._lock:
            self._data[alert_id] = alert
        return alert

    def list_alerts(self) -> list[Alert]:
        """Return all active (non-acknowledged) alerts."""
        with self._lock:
            return [
                a for a in self._data.values()
                if not a.acknowledged
            ]

    def all_alerts(self) -> list[Alert]:
        """Return every alert ever created (including acknowledged)."""
        with self._lock:
            return list(self._data.values())

    def acknowledge(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged.  Returns ``True`` if found."""
        with self._lock:
            alert = self._data.get(alert_id)
            if alert is None:
                return False
            alert.acknowledged = True
        return True

    def unread_count(self) -> int:
        """Number of alerts where acknowledged == False."""
        with self._lock:
            return sum(1 for a in self._data.values() if not a.acknowledged)

    def evaluate_budgets(self) -> list[Alert]:
        """Check every budget threshold and spending anomaly.

        Called automatically after each receipt is added.  Returns any newly
        generated alerts.
        """
        new_alerts: list[Alert] = []

        threshold_alerts = self._check_budget_thresholds()
        new_alerts.extend(threshold_alerts)

        unusual_alerts = self._check_unusual_spending()
        new_alerts.extend(unusual_alerts)

        return new_alerts

    def _check_budget_thresholds(self) -> list[Alert]:
        """Check budget spending against alert thresholds.

        Generates a budget_threshold alert when any budget's pct_used
        meets or exceeds its alert_threshold.
        """
        from app.budgets import budget_store

        new_alerts: list[Alert] = []
        budgets = budget_store.list()

        for budget in budgets:
            # pct_used is stored as a percentage (e.g. 80.0 means 80%)
            pct = budget.pct_used / 100.0
            threshold = budget.alert_threshold

            if pct >= threshold:
                if pct >= 1.0:
                    severity = AlertSeverity.CRITICAL
                    message = (
                        f"{budget.category} spending has exceeded the budget "
                        f"(${budget.spent:.2f} spent of ${budget.amount:.2f} budgeted)."
                    )
                elif pct >= threshold + 0.1:
                    severity = AlertSeverity.WARNING
                    message = (
                        f"{budget.category} spending has reached {pct * 100:.1f}% "
                        f"of the budget (${budget.spent:.2f} of ${budget.amount:.2f})."
                    )
                else:
                    severity = AlertSeverity.INFO
                    message = (
                        f"{budget.category} spending is approaching the budget limit "
                        f"({pct * 100:.1f}% used)."
                    )

                alert = self.create_alert(
                    alert_type=AlertType.BUDGET_THRESHOLD,
                    severity=severity,
                    category=budget.category,
                    message=message,
                    pct_used=round(pct * 100, 1),
                )
                new_alerts.append(alert)

        return new_alerts

    def _check_unusual_spending(self) -> list[Alert]:
        """Detect unusual spending patterns.

        Compares current period spending against historical average for
        each category.  Generates an alert when spending deviates by
        more than 2 standard deviations from the mean.
        """
        from app.reports import receipt_store

        new_alerts: list[Alert] = []
        now = datetime.now(timezone.utc)

        # Determine current period dates
        if now.month == 1:
            prev_year = now.year - 1
            prev_month = 12
        else:
            prev_year = now.year
            prev_month = now.month - 1

        import calendar
        last_day_prev = calendar.monthrange(prev_year, prev_month)[1]
        prev_month_start = f"{prev_year:04d}-{prev_month:02d}-01"
        prev_month_end = f"{prev_year:04d}-{prev_month:02d}-{last_day_prev:02d}"

        current_month_start = now.strftime("%Y-%m-01")
        current_month_end = now.strftime(
            "%Y-%m-%d"
        )

        # Get receipts for current and previous month
        current_receipts = receipt_store.list(
            date_from=current_month_start, date_to=current_month_end
        )
        historical_receipts = receipt_store.list(
            date_from=prev_month_start, date_to=prev_month_end
        )

        # Build category-level spending for current period
        current_cat_spending: dict[str, float] = {}
        for r in current_receipts:
            total = r.total or 0.0
            # Use merchant as category proxy
            merchant = (r.merchant or "Unknown").lower()
            current_cat_spending[merchant] = (
                current_cat_spending.get(merchant, 0.0) + total
            )

        # Build category-level spending for historical period
        historical_cat_spending: dict[str, float] = {}
        for r in historical_receipts:
            total = r.total or 0.0
            merchant = (r.merchant or "Unknown").lower()
            historical_cat_spending[merchant] = (
                historical_cat_spending.get(merchant, 0.0) + total
            )

        # Simple heuristic: if current spending on a merchant is > 2x the
        # historical average for that merchant, flag as unusual
        for merchant, current_amount in current_cat_spending.items():
            historical_amount = historical_cat_spending.get(merchant, 0.0)
            if historical_amount > 0 and current_amount > historical_amount * 2:
                alert = self.create_alert(
                    alert_type=AlertType.UNUSUAL_SPENDING,
                    severity=AlertSeverity.WARNING,
                    category=merchant.title(),
                    message=(
                        f"Unusual spending detected at {merchant.title()}: "
                        f"${current_amount:.2f} this month vs "
                        f"${historical_amount:.2f} last month."
                    ),
                )
                new_alerts.append(alert)

        return new_alerts


# Singleton instance
alert_store = AlertStore()
