"""Pre-development interface + behavioral tests for CLI Batch Mode.

Module 6: app/cli.py — argparse-based CLI with batch/export/info subcommands.

Run: PYTHONPATH=src .venv/bin/python -m pytest tests/test_cli.py -v
"""
from __future__ import annotations

import argparse
import inspect
from typing import get_type_hints

import pytest

from app.cli import _build_parser, _cmd_batch, _cmd_export, _cmd_info, main

# ===========================================================================
# INTERFACE TESTS — must pass immediately
# ===========================================================================

class TestCLIInterface:
    """Verify CLI functions exist with correct signatures."""

    def test_main_exists(self):
        assert callable(main)

    def test_main_signature(self):
        sig = inspect.signature(main)
        params = list(sig.parameters)
        assert "argv" in params

    def test_main_returns_int(self):
        hints = get_type_hints(main) if hasattr(main, '__annotations__') else {}
        # Return type should be int
        ret = hints.get("return")
        assert ret is int or ret == "int" or ret is None  # None if no annotation

    def test_build_parser_exists(self):
        assert callable(_build_parser)

    def test_build_parser_returns_parser(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(parser, argparse.ArgumentParser)

    def test_cmd_batch_exists(self):
        assert callable(_cmd_batch)

    def test_cmd_export_exists(self):
        assert callable(_cmd_export)

    def test_cmd_info_exists(self):
        assert callable(_cmd_info)

    def test_cmd_batch_signature(self):
        sig = inspect.signature(_cmd_batch)
        params = list(sig.parameters)
        assert "args" in params

    def test_cmd_export_signature(self):
        sig = inspect.signature(_cmd_export)
        params = list(sig.parameters)
        assert "args" in params

    def test_cmd_info_signature(self):
        sig = inspect.signature(_cmd_info)
        params = list(sig.parameters)
        assert "args" in params


class TestBuildParserBehavior:
    """Behavioral: parser construction and subcommand registration."""

    def test_parser_has_batch_subcommand(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        # Parse with --help should not raise; batch should be recognized
        args, _ = parser.parse_known_args(["batch", "--dir", "."])
        assert args.command == "batch"

    def test_parser_has_export_subcommand(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["export", "--format", "generic"])
        assert args.command == "export"

    def test_parser_has_info_subcommand(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["info"])
        assert args.command == "info"

    def test_batch_requires_dir(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        with pytest.raises(SystemExit):
            parser.parse_args(["batch"])

    def test_batch_has_lang_option(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--lang", "deu"])
        assert args.lang == "deu"

    def test_batch_has_workers_option(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--workers", "8"])
        assert args.workers == 8

    def test_batch_has_export_option(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--export", "quickbooks"])
        assert args.export == "quickbooks"

    def test_batch_has_output_option(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--output", "out.csv"])
        assert str(args.output) == "out.csv"

    def test_batch_has_verbose_flag(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--verbose"])
        assert args.verbose is True

    def test_batch_has_recursive_flag(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["batch", "--dir", ".", "--recursive"])
        assert args.recursive is True

    def test_export_requires_format(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        with pytest.raises(SystemExit):
            parser.parse_args(["export"])

    def test_export_has_date_from(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["export", "--format", "xero", "--date-from", "2026-01-01"])
        assert args.date_from == "2026-01-01"

    def test_export_has_date_to(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["export", "--format", "xero", "--date-to", "2026-12-31"])
        assert args.date_to == "2026-12-31"

    def test_export_has_category(self):
        try:
            parser = _build_parser()
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        args, _ = parser.parse_known_args(["export", "--format", "xero", "--category", "food"])
        assert args.category == "food"


class TestMainBehavior:
    """Behavioral: CLI entry point execution."""

    def test_main_returns_int(self):
        try:
            result = main(["info"])
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert isinstance(result, int)

    def test_main_invalid_command_returns_error(self):
        try:
            result = main(["nonexistent"])
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == 2  # fatal error exit code

    def test_main_info_returns_zero(self):
        try:
            result = main(["info"])
        except NotImplementedError:
            pytest.skip("Not implemented yet — RED phase")
        assert result == 0
