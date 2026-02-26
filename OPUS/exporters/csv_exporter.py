#!/usr/bin/env python3
"""
CSV report exporter.
"""

import csv
import os
import logging
from typing import List

from ..models import ValidationResult

logger = logging.getLogger(__name__)


def export_csv(results: List[ValidationResult], output_path: str) -> bool:
    """
    Export validation results as a CSV file.

    Args:
        results: List of ValidationResult objects
        output_path: Output CSV file path

    Returns:
        True on success
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["File", "Line", "Code", "Severity", "Message", "Context"])

            for r in results:
                for e in r.errors:
                    writer.writerow([
                        os.path.basename(r.file_path),
                        e.line or "",
                        e.code,
                        str(e.severity),
                        e.message,
                        e.context_data or "",
                    ])

        logger.info("CSV report exported to %s", output_path)
        return True

    except Exception as e:
        logger.error("Failed to export CSV report: %s", e)
        return False
