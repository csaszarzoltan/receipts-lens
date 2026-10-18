#!/usr/bin/env python3
"""Restore the approved frontend build, without restarting the API or migrating data."""
import argparse
import html
import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

APPROVED_COMMIT = "3fc1bfa8fc8131199ce9bf23419f3633ef85651b"
SERVICE = "receipts-lens-frontend.service"


def javascript_paths(page):
    return sorted({html.unescape(path).split("?")[0] for path in
                   re.findall(r'(?:src|href)="([^\"]+\.js(?:\?[^\"]*)?)"', page)
                   if path.startswith("/_next/")})


def validate_build(frontend):
    build = frontend / ".next"
    if not (build / "BUILD_ID").is_file():
        raise RuntimeError("Missing BUILD_ID")
    paths = javascript_paths((build / "server/app/login.html").read_text())
    if not paths or any(not (build / path.removeprefix("/_next/")).is_file()
                        for path in paths):
        raise RuntimeError("Missing login JavaScript chunks")
    return paths


def service(action):
    subprocess.run(["systemctl", action, SERVICE], check=True)


def set_tree_owner(root, uid, gid):
    """Set ownership of every staged entry without following symbolic links."""
    def traversal_failed(error):
        raise error

    os.lchown(root, uid, gid)
    for directory, directories, files in os.walk(root, followlinks=False,
                                               onerror=traversal_failed):
        for name in directories + files:
            os.lchown(Path(directory) / name, uid, gid)


def check_http(base_url, expected_build):
    last_error = None
    for _ in range(30):
        try:
            with urllib.request.urlopen(base_url + "/login", timeout=3) as response:
                if response.status != 200:
                    raise RuntimeError("Login HTTP status is not 200")
                page = response.read().decode()
            paths = javascript_paths(page)
            if not paths:
                raise RuntimeError("Login returned no JavaScript references")
            # Check against the candidate as well, to reject an old service/build.
            if paths != expected_build:
                raise RuntimeError("Service is not serving the approved build")
            for path in paths:
                with urllib.request.urlopen(base_url + path, timeout=3) as response:
                    if response.status != 200 or not response.read(1):
                        raise RuntimeError("JavaScript chunk health check failed")
            print(f"Login and all {len(paths)} JavaScript chunks return HTTP 200.")
            return
        except (OSError, RuntimeError) as error:
            last_error = error
            time.sleep(1)
    raise RuntimeError("Frontend HTTP verification failed") from last_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path,
                        default=Path("/tmp/receiptlens-approved-3fc1bfa8fc81/frontend"))
    parser.add_argument("--frontend", type=Path,
                        default=Path(__file__).resolve().parents[1] / "frontend")
    parser.add_argument("--base-url", default="http://127.0.0.1:3300")
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    frontend = args.frontend.resolve()
    if candidate == frontend:
        raise RuntimeError("Candidate must be outside the live frontend")
    if (candidate.parent / "approved-commit.txt").read_text().strip() != APPROVED_COMMIT:
        raise RuntimeError("Candidate is not the approved commit")
    expected = validate_build(candidate)
    # Fail before filesystem changes when service control is unavailable.
    subprocess.run(["systemctl", "show", SERVICE, "--property=ActiveState", "--value"],
                   check=True)
    stamp = str(time.time_ns())
    stage = frontend / (".next.restore-stage-" + stamp)
    backup = frontend / (".next.before-restore-" + stamp)
    live = frontend / ".next"
    if not live.is_dir():
        raise RuntimeError("Live .next directory is missing")
    owner = frontend.stat()
    swapped = False
    stopped = False
    try:
        shutil.copytree(candidate / ".next", stage, symlinks=True)
        set_tree_owner(stage, owner.st_uid, owner.st_gid)
        service("stop")
        stopped = True
        live.rename(backup)
        try:
            stage.rename(live)
        except BaseException:
            backup.rename(live)
            raise
        swapped = True
        service("start")
        check_http(args.base_url.rstrip("/"), expected)
        print(f"Approved frontend restored. Previous build preserved at: {backup}")
        print("API and production database were not modified.")
    except BaseException:
        if stopped:
            if swapped:
                service("stop")
                live.rename(stage)
                backup.rename(live)
            service("start")
            print("Previous build restored after failure; it may still have the original fault.")
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    main()
