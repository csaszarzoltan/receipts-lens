"""Exercise frontend build replacement and rollback without real service control."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def restore(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/restore-approved-frontend.py"
    spec = importlib.util.spec_from_file_location("frontend_restore", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidate = tmp_path / "approved/frontend"
    (candidate / ".next/server/app").mkdir(parents=True)
    (candidate / ".next/static/chunks").mkdir(parents=True)
    (candidate / ".next/BUILD_ID").write_text("approved")
    (candidate / ".next/server/app/login.html").write_text(
        '<script src="/_next/static/chunks/login.js"></script>')
    (candidate / ".next/static/chunks/login.js").write_text("approved javascript")
    (candidate.parent / "approved-commit.txt").write_text(module.APPROVED_COMMIT)
    frontend = tmp_path / "live"
    (frontend / ".next").mkdir(parents=True)
    (frontend / ".next/BUILD_ID").write_text("old")
    monkeypatch.setattr(sys, "argv", [str(script), "--candidate", str(candidate),
                                     "--frontend", str(frontend)])
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: None)
    actions = []
    monkeypatch.setattr(module, "service", actions.append)
    return module, frontend, actions


def test_success_replaces_build_only_after_stop_and_preserves_previous(restore, monkeypatch):
    module, frontend, actions = restore

    def verify(base_url, paths):
        assert actions == ["stop", "start"]
        assert (frontend / ".next/BUILD_ID").read_text() == "approved"
        assert paths == ["/_next/static/chunks/login.js"]

    monkeypatch.setattr(module, "check_http", verify)
    module.main()
    backups = list(frontend.glob(".next.before-restore-*"))
    assert len(backups) == 1
    assert (backups[0] / "BUILD_ID").read_text() == "old"
    assert not list(frontend.glob(".next.restore-stage-*"))


def test_failed_health_check_rolls_back_build_and_restarts(restore, monkeypatch):
    module, frontend, actions = restore

    def failure(*args):
        raise RuntimeError("HTTP verification failed")

    monkeypatch.setattr(module, "check_http", failure)
    with pytest.raises(RuntimeError, match="HTTP verification failed"):
        module.main()
    assert (frontend / ".next/BUILD_ID").read_text() == "old"
    assert actions == ["stop", "start", "stop", "start"]
    assert not list(frontend.glob(".next.restore-stage-*"))


def test_denied_service_access_leaves_live_build_untouched(restore, monkeypatch):
    module, frontend, actions = restore

    def denied(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "systemctl")

    monkeypatch.setattr(module.subprocess, "run", denied)
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert (frontend / ".next/BUILD_ID").read_text() == "old"
    assert actions == []
    assert sorted(path.name for path in frontend.iterdir()) == [".next"]


def test_entire_staging_tree_gets_frontend_owner_before_stop(restore, monkeypatch):
    module, frontend, actions = restore
    owner = frontend.stat()
    changed = set()

    def chown(path, uid, gid):
        path = Path(path)
        assert (uid, gid) == (owner.st_uid, owner.st_gid)
        assert actions == []
        assert (frontend / ".next/BUILD_ID").read_text() == "old"
        assert path.is_relative_to(frontend)
        assert path.parts[len(frontend.parts)].startswith(".next.restore-stage-")
        changed.add(path)

    def service(action):
        if action == "stop":
            stage, = frontend.glob(".next.restore-stage-*")
            assert changed == {stage, *stage.rglob("*")}
        actions.append(action)

    monkeypatch.setattr(os, "lchown", chown)
    monkeypatch.setattr(module, "service", service)
    monkeypatch.setattr(module, "check_http", lambda *args: None)
    module.main()
    assert actions == ["stop", "start"]


def test_owner_change_failure_keeps_service_and_live_build_untouched(restore, monkeypatch):
    module, frontend, actions = restore

    def denied(*args):
        raise PermissionError("ownership denied")

    monkeypatch.setattr(os, "lchown", denied)
    monkeypatch.setattr(module, "check_http", lambda *args: None)
    with pytest.raises(PermissionError, match="ownership denied"):
        module.main()
    assert actions == []
    assert (frontend / ".next/BUILD_ID").read_text() == "old"
    assert sorted(path.name for path in frontend.iterdir()) == [".next"]


def test_tree_owner_does_not_follow_external_symlinks(restore, tmp_path, monkeypatch):
    module, _, _ = restore
    tree = tmp_path / "stage"
    tree.mkdir()
    external = tmp_path / "outside"
    external.mkdir()
    (external / "untouched").write_text("external")
    link = tree / "link"
    link.symlink_to(external, target_is_directory=True)
    changed = []
    monkeypatch.setattr(os, "lchown", lambda path, uid, gid:
                        changed.append((Path(path), uid, gid)))
    module.set_tree_owner(tree, 1234, 5678)
    assert set(changed) == {(tree, 1234, 5678), (link, 1234, 5678)}
