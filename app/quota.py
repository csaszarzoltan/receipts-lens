"""Atomic tenant-month quota."""

import threading
from datetime import UTC, datetime


class QuotaStore:
    def __init__(self, limit=25, now=None):
        self.limit = limit
        self.now = now or (lambda: datetime.now(UTC))
        self.counts = {}
        self.lock = threading.Lock()

    def key(self, t):
        return f"{t}:{self.now().strftime('%Y-%m')}"

    def incr_and_check(self, t, pro=False):
        with self.lock:
            k = self.key(t)
            u = self.counts.get(k, 0) + 1
            self.counts[k] = u
        return {
            "used": u,
            "limit": None if pro else self.limit,
            "remaining": None if pro else max(0, self.limit - u),
            "allowed": pro or u <= self.limit,
            "period": k.rsplit(":", 1)[1],
        }

    def get_quota(self, t, pro=False):
        k = self.key(t)
        u = self.counts.get(k, 0)
        return {
            "used": u,
            "limit": None if pro else self.limit,
            "remaining": None if pro else max(0, self.limit - u),
            "allowed": True,
            "period": k.rsplit(":", 1)[1],
            "pro": pro,
        }

    def reset(self, t):
        with self.lock:
            self.counts.pop(self.key(t), None)


quota_store = QuotaStore()
