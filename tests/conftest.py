"""Teszt-izolacio a FEAT-033B insight-tarolohoz.

Az insight-store folyamat-szintu singleton (app/insight_api.py), a 033B
acceptance-tesztek viszont mind onallo kiindulasi allapotot felteteleznek
(pl. ismetelt evaluate uj kartyat var, a dedup-teszt viszont tiszta
tarolot). Ezert minden teszt elott/utan uritjuk — ugyanaz a minta, mint
a tests/test_rate_limiting.py autouse _fresh_limiter fixture-je.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fresh_insight_store():
    from app import insight_api

    insight_api.store.reset()
    yield
    insight_api.store.reset()
