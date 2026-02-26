#!/usr/bin/env python3
"""
JSON report exporter.
"""

import json
import os
import logging
from datetime import datetime
from typing import List

from ..models import ValidationResult
from ..config import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


def export_json(results: List[ValidationResult], output_path: str) -> bool:
    """
    Export validation results as a structured JSON file.

    Args:
        results: List of ValidationResult objects
        output_path: Output JSON file path

    Returns:
        True on success
    """
    try:
        report = {
            "generator": f"{APP_NAME} v{APP_VERSION}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_files": len(results),
                "passed": sum(1 for r in results if r.status == "PASS"),
                "failed": sum(1 for r in results if r.status == "FAIL"),
                "warnings_only": sum(1 for r in results if r.status == "WARN"),
                "total_errors": sum(r.error_count for r in results),
                "total_warnings": sum(r.warning_count for r in results),
            },
            "files": [],
        }

        for r in results:
            file_entry = {
                "file": os.path.basename(r.file_path),
                "path": r.file_path,
                "status": r.status,
                "error_count": r.error_count,
                "warning_count": r.warning_count,
                "duration_ms": r.duration_ms,
                "errors": [
                    {
                        "code": e.code,
                        "message": e.message,
                        "line": e.line,
                        "col": e.col,
                        "severity": str(e.severity),
                        "context": e.context_data,
                        "suggestion": e.suggestion,
                        "auto_fixable": e.auto_fixable,
                    }
                    for e in r.errors
                ],
            }
            report["files"].append(file_entry)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("JSON report exported to %s", output_path)
        return True

    except Exception as e:
        logger.error("Failed to export JSON report: %s", e)
        return False
