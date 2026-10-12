"""The login page signs a visitor in as themselves; the shared demo household is an opt-in dev build only."""

from __future__ import annotations

from pathlib import Path

import pytest

LOGIN = Path(__file__).resolve().parent.parent / "frontend" / "app" / "(auth)" / "login" / "page.tsx"
PRODUCTION_ENV = Path(__file__).resolve().parent.parent / "frontend" / ".env.production"


@pytest.mark.test_id("TEST-RL-V02-275")
@pytest.mark.requirements("FEAT-RL-V02-REQ-067")
@pytest.mark.scenario("AC-RL-V02-59")
def test_login_asks_for_the_visitors_own_email() -> None:
    source = LOGIN.read_text(encoding="utf-8")
    assert 'id="login-email"' in source and 'type="email"' in source
    assert "requestMagicLink({ email: email.trim() })" in source


@pytest.mark.test_id("TEST-RL-V02-276")
@pytest.mark.requirements("FEAT-RL-V02-REQ-067")
@pytest.mark.scenario("AC-RL-V02-59")
def test_demo_address_is_reachable_only_behind_the_dev_flag() -> None:
    source = LOGIN.read_text(encoding="utf-8")
    assert source.count("demo-admin@receiptlens.local") == 1
    # The one use sits in the demo handler, and the button that calls it renders only when the flag is on.
    assert 'process.env.NEXT_PUBLIC_DEMO_LOGIN === "1"' in source
    assert "{demoEnabled && (" in source
    handler = source[source.index("async function signInAsDemo"):]
    assert handler.index("demo-admin@receiptlens.local") < handler.index("return (")
    if PRODUCTION_ENV.exists():  # untracked in CI checkouts
        assert "NEXT_PUBLIC_DEMO_LOGIN" not in PRODUCTION_ENV.read_text(encoding="utf-8")
