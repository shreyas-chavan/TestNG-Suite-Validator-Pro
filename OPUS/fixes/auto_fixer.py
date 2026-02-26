#!/usr/bin/env python3
"""
Auto-fix engine for TestNG XML validation errors.
Applies safe, reversible fixes to XML files based on error codes.
"""

import os
import shutil
import logging
from typing import List, Tuple

from ..models import ValidationError
from ..config import AUTO_FIXABLE_CODES

logger = logging.getLogger(__name__)


def apply_auto_fix(error: ValidationError, file_lines: List[str]) -> Tuple[bool, str]:
    """
    Attempt to automatically fix a single error in-memory.

    Modifies file_lines in place if successful.

    Args:
        error: The validation error to fix
        file_lines: Mutable list of file lines (modified in place)

    Returns:
        (success, message) tuple
    """
    if not error.line or error.line < 1 or error.line > len(file_lines):
        return False, "Invalid line number"

    line_idx = error.line - 1
    original_line = file_lines[line_idx]

    # E170: Remove spaces from names
    if error.code == "E170" and error.context_data:
        clean_name = error.context_data.replace(" ", "")
        fixed_line = original_line.replace(
            f'name="{error.context_data}"', f'name="{clean_name}"'
        )
        if fixed_line != original_line:
            file_lines[line_idx] = fixed_line
            return True, f"Removed spaces from '{error.context_data}' \u2192 '{clean_name}'"

    # E101: Add missing suite name
    elif error.code == "E101":
        if '<suite' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace('<suite', '<suite name="TestSuite"')
            return True, "Added default suite name 'TestSuite'"

    # E103: Add missing test name
    elif error.code == "E103":
        if '<test' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace('<test', '<test name="Test1"')
            return True, "Added default test name 'Test1'"

    # E112: Add missing class name
    elif error.code == "E112":
        if '<class' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace(
                '<class', '<class name="com.example.TestClass"'
            )
            return True, "Added placeholder class name (update with your actual class)"

    # E122: Add missing include name
    elif error.code == "E122":
        if '<include' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace('<include', '<include name="testMethod"')
            return True, "Added placeholder method name (update with your actual method)"

    # E124: Add missing exclude name
    elif error.code == "E124":
        if '<exclude' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace('<exclude', '<exclude name="testMethod"')
            return True, "Added placeholder method name (update with your actual method)"

    # E116: Add missing package name
    elif error.code == "E116":
        if '<package' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace('<package', '<package name="com.example.*"')
            return True, "Added placeholder package name (update with your actual package)"

    # E130: Add missing parameter name
    elif error.code == "E130":
        if '<parameter' in original_line and 'name=' not in original_line:
            file_lines[line_idx] = original_line.replace(
                '<parameter', '<parameter name="paramName"'
            )
            return True, "Added placeholder parameter name"

    # E131: Add missing parameter value
    elif error.code == "E131":
        if '<parameter' in original_line and 'value=' not in original_line:
            fixed = original_line.replace('/>', ' value="paramValue"/>')
            if fixed == original_line:
                fixed = original_line.replace('>', ' value="paramValue">')
            file_lines[line_idx] = fixed
            return True, "Added placeholder parameter value"

    # E104: Rename duplicate test
    elif error.code == "E104" and error.context_data:
        if f'name="{error.context_data}"' in original_line:
            new_name = f"{error.context_data}_Copy"
            file_lines[line_idx] = original_line.replace(
                f'name="{error.context_data}"', f'name="{new_name}"'
            )
            return True, f"Renamed duplicate test to '{new_name}'"

    # E107: Remove empty <classes> block
    elif error.code == "E107":
        return _remove_empty_block(file_lines, line_idx, "classes")

    # E108: Remove empty <methods> block
    elif error.code == "E108":
        return _remove_empty_block(file_lines, line_idx, "methods")

    # E109: Remove empty <packages> block
    elif error.code == "E109":
        return _remove_empty_block(file_lines, line_idx, "packages")

    # E132: Remove duplicate parameter
    elif error.code == "E132" and error.context_data:
        if '<parameter' in original_line and f'name="{error.context_data}"' in original_line:
            file_lines[line_idx] = ""
            return True, f"Removed duplicate parameter '{error.context_data}'"

    # E160: Remove duplicate class
    elif error.code == "E160" and error.context_data:
        if '<class' in original_line and f'name="{error.context_data}"' in original_line:
            file_lines[line_idx] = ""
            return True, f"Removed duplicate class '{error.context_data}'"

    # E161: Remove duplicate method
    elif error.code == "E161" and error.context_data:
        if '<include' in original_line and f'name="{error.context_data}"' in original_line:
            file_lines[line_idx] = ""
            return True, f"Removed duplicate method '{error.context_data}'"

    return False, "This error cannot be auto-fixed"


def _remove_empty_block(file_lines: List[str], start_idx: int, tag_name: str) -> Tuple[bool, str]:
    """Remove an empty XML block (opening + closing tag with nothing between)."""
    line = file_lines[start_idx]
    if f'<{tag_name}>' in line or f'<{tag_name}/>' in line:
        for i in range(start_idx, min(start_idx + 5, len(file_lines))):
            if f'</{tag_name}>' in file_lines[i]:
                file_lines[start_idx] = ""
                file_lines[i] = ""
                return True, f"Removed empty <{tag_name}> block"
    return False, f"Could not find closing </{tag_name}>"


def batch_auto_fix(
    file_path: str,
    errors: List[ValidationError],
    create_backup: bool = True,
) -> Tuple[int, int, str]:
    """
    Attempt to auto-fix all fixable errors in a file.

    Creates a backup before modifying. Sorts errors by line number
    descending to prevent line-shift issues.

    Args:
        file_path: Path to the XML file
        errors: List of validation errors
        create_backup: Whether to create a .bak backup file

    Returns:
        (fixed_count, total_fixable, result_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            file_lines = f.readlines()
    except Exception as e:
        return 0, 0, f"Cannot read file: {e}"

    fixable_errors = [e for e in errors if e.code in AUTO_FIXABLE_CODES]

    if not fixable_errors:
        return 0, 0, "No auto-fixable errors found"

    # Create backup before modifying
    if create_backup:
        try:
            backup_path = file_path + ".bak"
            shutil.copy2(file_path, backup_path)
            logger.info("Backup created: %s", backup_path)
        except Exception as e:
            logger.warning("Failed to create backup: %s", e)

    # Sort by line number descending to avoid shifts
    fixable_errors.sort(key=lambda e: e.line or 0, reverse=True)

    fixed_count = 0
    messages = []

    for error in fixable_errors:
        success, msg = apply_auto_fix(error, file_lines)
        if success:
            fixed_count += 1
            messages.append(f"Line {error.line}: {msg}")

    if fixed_count > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(file_lines)
            result = f"\u2705 Fixed {fixed_count}/{len(fixable_errors)} errors:\n" + "\n".join(messages)
            return fixed_count, len(fixable_errors), result
        except Exception as e:
            return 0, len(fixable_errors), f"Error writing file: {e}"

    return 0, len(fixable_errors), "No errors could be auto-fixed"
