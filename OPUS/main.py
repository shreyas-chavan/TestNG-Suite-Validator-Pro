#!/usr/bin/env python3
"""
TestNG Validator Pro - Entry Point.
Supports both GUI mode (default) and CLI mode (--cli).

Usage:
    GUI Mode:   python -m OPUS.main
    CLI Mode:   python -m OPUS.main --cli file1.xml file2.xml
    CLI Help:   python -m OPUS.main --help
"""

import sys
import os
import argparse
import logging

# Ensure the parent directory is on the path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from OPUS.config import APP_TITLE, APP_VERSION
from OPUS.utils.logging_config import setup_logging


def run_gui():
    """Launch the graphical user interface."""
    import tkinter as tk
    from OPUS.ui.app import ValidatorApp

    # Try TkinterDnD for native drag & drop support
    root = None
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except (ImportError, Exception):
        root = tk.Tk()

    app = ValidatorApp(root)
    root.mainloop()


def run_cli(args):
    """Run validation in CLI mode."""
    from OPUS.validators import validate_file
    from OPUS.exporters import export_html, export_csv, export_json
    from OPUS.utils.file_utils import find_xml_files

    logger = logging.getLogger("testng_validator")

    # Collect files
    all_files = []
    for path in args.files:
        if os.path.isdir(path):
            all_files.extend(find_xml_files(path))
        elif os.path.isfile(path):
            all_files.append(path)
        else:
            logger.warning("Path not found: %s", path)

    if not all_files:
        logger.error("No XML files found.")
        sys.exit(1)

    # Load metadata if provided
    metadata = None
    if args.metadata:
        import json
        try:
            with open(args.metadata, encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info("Loaded metadata: %d classes", len(metadata))
        except Exception as e:
            logger.error("Failed to load metadata: %s", e)

    # Validate each file
    results = []
    total_errors = 0
    total_warnings = 0

    print(f"\n{APP_TITLE} - CLI Mode")
    print("=" * 60)
    print(f"Files to validate: {len(all_files)}")
    print("=" * 60)

    for filepath in all_files:
        result = validate_file(filepath, metadata)
        results.append(result)

        icon = "\u2705" if result.is_valid else ("\u26a0\ufe0f" if result.error_count == 0 else "\u274c")
        print(f"\n{icon} {os.path.basename(filepath)}")
        print(f"   Status: {result.status} | Errors: {result.error_count} | Warnings: {result.warning_count} | Time: {result.duration_ms:.1f}ms")

        if args.verbose and result.errors:
            for e in result.errors:
                sev_icon = "\u274c" if e.is_error else "\u26a0\ufe0f"
                print(f"   {sev_icon} L{e.line or '?'} [{e.code}] {e.message}")

        total_errors += result.error_count
        total_warnings += result.warning_count

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r.is_valid)
    print(f"  Total files:    {len(results)}")
    print(f"  Passed:         {passed}")
    print(f"  Failed:         {len(results) - passed}")
    print(f"  Total errors:   {total_errors}")
    print(f"  Total warnings: {total_warnings}")
    print("=" * 60)

    # Export if requested
    if args.output:
        ext = os.path.splitext(args.output)[1].lower()
        success = False
        if ext == ".html":
            success = export_html(results, args.output)
        elif ext == ".csv":
            success = export_csv(results, args.output)
        elif ext == ".json":
            success = export_json(results, args.output)
        else:
            logger.error("Unsupported output format: %s (use .html, .csv, or .json)", ext)

        if success:
            print(f"\nReport saved to: {args.output}")

    # Exit code: 0 if all passed, 1 if any errors
    sys.exit(0 if total_errors == 0 else 1)


def main():
    parser = argparse.ArgumentParser(
        prog="testng-validator",
        description=f"{APP_TITLE} - TestNG XML Suite Validator",
    )
    parser.add_argument("--version", action="version", version=f"{APP_TITLE}")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed error output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--metadata", "-m", type=str, help="Path to metadata JSON file")
    parser.add_argument("--output", "-o", type=str, help="Export report (supports .html, .csv, .json)")
    parser.add_argument("files", nargs="*", help="XML files or directories to validate")

    args = parser.parse_args()

    # Setup logging
    setup_logging(debug=args.debug)

    if args.cli or args.files:
        if not args.files:
            parser.error("CLI mode requires at least one file or directory")
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
