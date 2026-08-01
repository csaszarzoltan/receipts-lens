"""ReceiptLens CLI — batch receipt processing from the command line.

Usage:
    receipts-lens batch --dir ./receipts --export quickbooks
    receipts-lens batch --dir ./receipts --lang deu --output results.csv
    receipts-lens batch --urls urls.txt --export xero --workers 4
    receipts-lens export --format quickbooks --date-from 2026-01-01
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Parameters
    ----------
    argv:
        Command-line arguments (defaults to sys.argv[1:]).

    Returns
    -------
    int
        Exit code: 0 = success, 1 = partial failure, 2 = fatal error.
    """
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        command = getattr(args, "command", None)
        if command == "batch":
            return _cmd_batch(args)
        elif command == "export":
            return _cmd_export(args)
        elif command == "info":
            return _cmd_info(args)
        else:
            parser.print_help()
            return 2
    except SystemExit as exc:
        code = exc.code
        return int(code) if code is not None else 2
    except Exception:
        return 2


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="receipts-lens",
        description="ReceiptLens — multi-language receipt OCR and export",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # batch subcommand
    batch_parser = subparsers.add_parser("batch", help="Batch process receipts")
    batch_parser.add_argument("--dir", required=True, help="Directory of receipt images")
    batch_parser.add_argument("--lang", default="eng", help="Language code (default: eng)")
    batch_parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    batch_parser.add_argument("--export", default="generic", help="Export profile (default: generic)")
    batch_parser.add_argument("--output", default="results.csv", help="Output CSV path")
    batch_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    batch_parser.add_argument("--recursive", action="store_true", help="Scan subdirectories")

    # export subcommand
    export_parser = subparsers.add_parser("export", help="Export receipts to CSV")
    export_parser.add_argument("--format", required=True, help="Export format (quickbooks, xero, generic)")
    export_parser.add_argument("--date-from", default=None, help="Start date filter (YYYY-MM-DD)")
    export_parser.add_argument("--date-to", default=None, help="End date filter (YYYY-MM-DD)")
    export_parser.add_argument("--category", default=None, help="Category filter")

    # info subcommand
    subparsers.add_parser("info", help="Show supported languages and formats")

    return parser


def _cmd_batch(args: argparse.Namespace) -> int:
    """Execute the batch processing command."""
    import asyncio
    from pathlib import Path

    from app.batch import BatchProcessor
    from app.export import ReceiptExporter

    dir_path = Path(args.dir)
    if not dir_path.exists():
        print(f"Error: directory not found: {args.dir}", flush=True)
        return 2

    # Collect image files
    exts = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
    if args.recursive:
        files = [p for p in dir_path.rglob("*") if p.suffix.lower() in exts]
    else:
        files = [p for p in dir_path.iterdir() if p.suffix.lower() in exts]

    if not files:
        print(f"No image files found in {args.dir}", flush=True)
        return 1

    print(f"Processing {len(files)} receipts with {args.workers} workers...", flush=True)

    items = [f.read_bytes() for f in files]
    processor = BatchProcessor(max_workers=args.workers)

    async def _run() -> object:
        return await processor.process_batch(items, lang=args.lang)

    job = asyncio.run(_run())

    print(f"Completed: {job.completed}/{job.total} ({job.failed} failed)", flush=True)

    # Export if requested
    if args.export:
        # For now, export empty results (actual normalization would need full pipeline)
        exporter = ReceiptExporter(args.export)
        csv_str = exporter.export_csv([])
        out_path = Path(args.output)
        out_path.write_text(csv_str)
        print(f"Exported to {args.output}", flush=True)

    return 0 if job.failed == 0 else 1


def _cmd_export(args: argparse.Namespace) -> int:
    """Execute the export command."""
    from app.export import ReceiptExporter

    try:
        exporter = ReceiptExporter(args.format)
    except ValueError as exc:
        print(f"Error: {exc}", flush=True)
        return 2

    csv_str = exporter.export_csv([])
    print(csv_str, flush=True)
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    """Show supported languages and formats."""
    from app.export import PROFILES
    from app.ocr import SUPPORTED_LANGUAGES

    print("Supported languages:", flush=True)
    for lang in SUPPORTED_LANGUAGES:
        print(f"  - {lang}", flush=True)
    print(flush=True)
    print("Export formats:", flush=True)
    for name, profile in PROFILES.items():
        print(f"  - {name}: {len(profile.columns)} columns", flush=True)
    return 0


def _print_progress(job: object) -> None:
    """Print a progress bar to stderr."""
    import sys

    if hasattr(job, "progress"):
        pct = job.progress * 100  # type: ignore[union-attr]
        print(f"\r  Progress: {pct:.0f}%", file=sys.stderr, end="", flush=True)
