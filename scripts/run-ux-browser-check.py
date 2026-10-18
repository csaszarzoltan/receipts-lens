#!/usr/bin/env python3
"""Build and test a private copy; never overwrite a running frontend build."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    source = Path(__file__).resolve().parents[1] / "frontend"
    dependencies = source / "node_modules"
    if not dependencies.is_dir():
        raise RuntimeError("Install frontend dependencies before running browser tests")
    with tempfile.TemporaryDirectory(prefix="receiptlens-ux-browser-") as temporary:
        work = Path(temporary) / "frontend"
        shutil.copytree(source, work, ignore=shutil.ignore_patterns(
            "node_modules", ".next", ".next.*", ".env*", "*.tsbuildinfo",
            "test-results", "playwright-report"))
        (work / "node_modules").symlink_to(dependencies, target_is_directory=True)
        env = {**os.environ, "NEXT_PUBLIC_API_BASE_URL": "http://127.0.0.1:8140"}
        print("Building an isolated frontend copy; live .next is untouched.", flush=True)
        subprocess.run(["npm", "run", "build"], cwd=work, env=env, check=True)
        subprocess.run(["node", "node_modules/@playwright/test/cli.js", "test",
                        "--config", "playwright.ux.config.ts"],
                       cwd=work, env=env, check=True)


if __name__ == "__main__":
    main()
