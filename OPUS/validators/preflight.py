#!/usr/bin/env python3
"""
Pre-flight regex scanner.
Performs fast, first-pass checks on raw XML text before SAX parsing.
Catches issues that are easier to detect with regex than SAX events.
"""

import re
import logging
from typing import List

from ..models import ValidationError, Severity

logger = logging.getLogger(__name__)


def preflight_scan(path: str, lines: List[str] = None) -> List[ValidationError]:
    """
    Run regex-based pre-flight checks on the XML file.

    Detects:
    - Duplicate test names (with line references for both original and duplicate)

    Args:
        path: File path (used for logging only if lines are provided)
        lines: Pre-read file lines. If None, reads from path.

    Returns:
        List of ValidationError objects found during pre-flight.
    """
    errors: List[ValidationError] = []

    if lines is None:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(path, encoding="latin-1") as f:
                    lines = f.readlines()
            except Exception as e:
                logger.warning("Pre-flight: cannot read %s: %s", path, e)
                return errors
        except Exception as e:
            logger.warning("Pre-flight: cannot read %s: %s", path, e)
            return errors

    test_name_map: dict = {}  # name -> first_line_number

    for i, line in enumerate(lines, 1):
        # Detect duplicate <test name="..."> declarations
        m_test = re.search(r'<test\b[^>]*\bname="([^"]+)"', line)
        if m_test:
            name = m_test.group(1)
            if name in test_name_map:
                errors.append(ValidationError(
                    code="E104",
                    message=f"Duplicate test: '{name}'",
                    line=i,
                    col=0,
                    severity=Severity.ERROR,
                    context_data=name,
                    line_content=line.strip(),
                ))
                # Also report original location (only once per name)
                orig_line = test_name_map[name]
                if orig_line > 0:
                    errors.append(ValidationError(
                        code="E104",
                        message=f"Original definition: '{name}'",
                        line=orig_line,
                        col=0,
                        severity=Severity.ERROR,
                        context_data=name,
                    ))
                    # Mark as already reported
                    test_name_map[name] = -1
            else:
                test_name_map[name] = i

    return errors
