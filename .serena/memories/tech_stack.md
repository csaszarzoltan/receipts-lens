# Tech stack
- Python >=3.11, setuptools, deps in `pyproject.toml` (+ `uv.lock`); venv `.venv`.
- FastAPI, uvicorn, pydantic v2, pillow, pytesseract, httpx, reportlab, cryptography.
- Dev: pytest>=8.2, ruff>=0.4 (line-length 100, py311; ignores E401/E701/E702; per-file ignores for B008/BLE001 in API modules).
- Frontend: Next 14.2, React 18.3, TypeScript 5.9, Tailwind 3, Playwright + axe for UX checks.
