"""ReceiptLens CLI — batch receipt processing from the command line.

Usage:
    receipts-lens batch --dir ./receipts --export quickbooks
    receipts-lens batch --dir ./receipts --lang deu --output results.csv
    receipts-lens batch --urls urls.txt --export xero --workers 4
    receipts-lens export --format quickbooks --date-from 2026-01-01
"""
from __future__ import annotations

import argparse
import os
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
        elif command == "forecast":
            return _cmd_forecast(args)
        elif command == "info":
            return _cmd_info(args)
        elif command == "subscription-alerts":
            return _cmd_subscription_alerts(args)
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

    # forecast subcommand
    forecast_parser = subparsers.add_parser("forecast", help="Forecast next-period spending")
    forecast_parser.add_argument(
        "--period",
        default="monthly",
        help="Forecast period (weekly, monthly, yearly; default: monthly)",
    )
    forecast_parser.add_argument(
        "--category",
        default=None,
        help="Category filter (default: all categories + overall)",
    )
    forecast_parser.add_argument(
        "--horizon",
        type=int,
        default=1,
        help="Number of periods ahead to forecast (default: 1)",
    )

    # subscription-alerts subcommand
    alerts_parser = subparsers.add_parser(
        "subscription-alerts",
        help="Run the daily subscription check (renewal + price-hike emails)",
    )
    alerts_parser.add_argument(
        "--tenant",
        default="demo",
        help="Accounting workspace tenant id (default: demo)",
    )
    alerts_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Suppress all outbound email (no send, no price_alert_sent row)",
    )
    alerts_parser.add_argument(
        "--today",
        default=None,
        help="ISO date anchor for a reproducible run (YYYY-MM-DD)",
    )

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


def _cmd_forecast(args: argparse.Namespace) -> int:
    """Execute the forecast command.

    Delegates to ``app.forecast.ForecastEngine`` and prints a per-category +
    overall next-period forecast summary to stdout.  Returns 0 on success,
    2 on failure.
    """
    from app.forecast import forecast_engine

    result = forecast_engine.forecast(
        date_from=None,
        date_to=None,
        period=args.period,
        category=args.category,
        horizon=args.horizon,
    )
    print(
        f"Forecast for period '{result.get('period', args.period)}' "
        f"(currency {result.get('currency', 'USD')}):",
        flush=True,
    )
    for entry in result.get("forecasts", []):
        print(
            f"  {entry.get('category', '?')}: "
            f"{entry.get('next_period_total', 0.0):.2f} "
            f"[{entry.get('confidence_low', 0.0):.2f} - "
            f"{entry.get('confidence_high', 0.0):.2f}]",
            flush=True,
        )
    return 0


def _cmd_subscription_alerts(args: argparse.Namespace) -> int:
    """Execute the subscription-alerts command.

    Builds the SMTP configuration from the environment (no ``to_addr`` — the
    trigger resolves the active owner itself) and delegates to
    ``app.subscription_alerts.daily_scheduler``, printing the run counters to
    stdout.  Returns 0 on success, 2 on failure.
    """
    import sys

    from app.subscription_alerts import daily_scheduler

    smtp_config = {
        "host": os.getenv("RECEIPTLENS_SMTP_HOST"),
        "port": os.getenv("RECEIPTLENS_SMTP_PORT"),
        "user": os.getenv("RECEIPTLENS_SMTP_USER"),
        "password": os.getenv("RECEIPTLENS_SMTP_PASSWORD"),
        # Both key spellings are accepted so an existing deployment that sets
        # only RECEIPTLENS_SMTP_FROM (or only ..._FROM_ADDR) still sends.
        "from_addr": (
            os.getenv("RECEIPTLENS_SMTP_FROM") or os.getenv("RECEIPTLENS_SMTP_FROM_ADDR")
        ),
    }
    if args.dry_run:
        # Intended: send_email_notification() bails out on its first line when
        # smtp_config is None, so nothing sends and no price_alert_sent row is
        # written — exactly what --dry-run's help text promises.
        smtp_config = None

    try:
        result = daily_scheduler(
            smtp_config=smtp_config,
            tenant=args.tenant,
            today=args.today,
        )
    except Exception:
        # Never echo the exception: it may carry SMTP credentials.
        print("Error: price-alert run failed", file=sys.stderr, flush=True)
        return 2

    for key in (
        "subscriptions_checked",
        "renewal_emails_sent",
        "price_emails_sent",
        "price_alerts_suppressed",
        "price_alerts_failed",
    ):
        print(f"{key}: {result.get(key, 0)}", flush=True)

    # Exit-code contract (main(), cli.py:15-19): 0 = success, 1 = partial
    # failure, 2 = fatal.
    #
    # The ONLY failure signal is ``price_alerts_failed``: a price hike that
    # was detected on this run and reached nobody.  Deriving the code from
    # anything else is a bug in both directions:
    #
    # * a healthy tenant whose renewal delivered and which has no price hike
    #   (renewal_emails_sent=1, price_emails_sent=0) would be reported as a
    #   failure — the most common real run;
    # * a real hike blocked by an SMTP gate would exit 0, because there was
    #   no prior row to suppress, so ``price_alerts_suppressed`` is 0 — the
    #   exact total failure this code exists to detect.
    #
    # A suppressed alert is a SUCCESS: it was delivered on an earlier run.
    # --dry-run sends nothing *by design*, so it is exempt and must never
    # exit 1.
    if not args.dry_run and result.get("price_alerts_failed"):
        print(
            f"Error: {result['price_alerts_failed']} price-hike alert(s) "
            "detected but not delivered",
            file=sys.stderr,
            flush=True,
        )
        return 1
    return 0


def _print_progress(job: object) -> None:
    """Print a progress bar to stderr."""
    import sys

    if hasattr(job, "progress"):
        pct = job.progress * 100  # type: ignore[union-attr]
        print(f"\r  Progress: {pct:.0f}%", file=sys.stderr, end="", flush=True)
