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
from typing import Any


class AlertType(str, Enum):
    BUDGET_THRESHOLD = "budget_threshold"
    UNUSUAL_SPENDING = "unusual_spending"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    PRICE_INCREASE = "price_increase"


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

    def schedule_renewal_alerts(
        self,
        subscriptions: list[dict[str, Any]],
        *,
        days_before: int = 3,
        today: str | None = None,
    ) -> list[Alert]:
        """Create ``SUBSCRIPTION_RENEWAL`` alerts for renewals due within *days_before*.

        Parameters
        ----------
        subscriptions:
            Subscription records; each is a dict with at least ``merchant``
            and ``renewal_date`` (ISO ``YYYY-MM-DD``) keys.
        days_before:
            How many days ahead of the renewal to fire the alert (default 3).
        today:
            Optional anchor date for deterministic tests; defaults to today.

        Returns
        -------
        list[Alert]
            The newly created renewal alerts.
        """
        from datetime import date as _date

        anchor = _date.fromisoformat(today) if today else _date.today()
        new_alerts: list[Alert] = []
        for sub in subscriptions:
            renewal = str(sub.get("renewal_date") or "")
            try:
                renewal_date = _date.fromisoformat(renewal)
            except ValueError:
                continue
            days_until = (renewal_date - anchor).days
            if 0 <= days_until <= days_before:
                merchant = str(sub.get("merchant") or "Unknown")
                alert = self.create_alert(
                    alert_type=AlertType.SUBSCRIPTION_RENEWAL,
                    severity=AlertSeverity.INFO,
                    category=merchant,
                    message=(
                        f"{merchant} renews on {renewal_date.isoformat()} "
                        f"({days_until} day{'s' if days_until != 1 else ''} from now)."
                    ),
                )
                new_alerts.append(alert)
        return new_alerts

    def create_price_increase_alert(
        self,
        merchant: str,
        current_amount: float,
        previous_amount: float,
    ) -> Alert:
        """Create a ``PRICE_INCREASE`` alert for a subscription price change.

        Parameters
        ----------
        merchant:
            Subscription merchant name.
        current_amount:
            The most recent (higher) amount charged.
        previous_amount:
            The previous amount the subscription charged.

        Returns
        -------
        Alert
            The newly created alert.
        """
        pct = (
            (current_amount / previous_amount - 1.0) * 100.0
            if previous_amount
            else 0.0
        )
        return self.create_alert(
            alert_type=AlertType.PRICE_INCREASE,
            severity=AlertSeverity.WARNING,
            category=merchant,
            message=(
                f"{merchant} subscription price increased by {pct:.1f}% "
                f"(from ${previous_amount:.2f} to ${current_amount:.2f})."
            ),
        )

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
