#!/usr/bin/env python3
"""
Safe file I/O utilities with encoding detection and error handling.
"""

import os
import logging
from typing import List, Optional, Tuple
from pathlib import Path

from ..config import ENCODING_FALLBACKS, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


def read_file_safe(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Read a file with encoding fallback.

    Tries multiple encodings and returns the content and detected encoding.

    Args:
        path: File path to read

    Returns:
        (content, encoding) or (None, error_message) on failure
    """
    if not os.path.isfile(path):
        return None, f"File not found: {path}"

    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return None, f"File too large ({file_size_mb:.1f} MB > {MAX_FILE_SIZE_MB} MB limit)"

    for enc in ENCODING_FALLBACKS:
        try:
            with open(path, encoding=enc) as f:
                content = f.read()
            return content, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
        except PermissionError:
            return None, f"Permission denied: {path}"
        except Exception as e:
            return None, f"Read error: {e}"

    return None, f"Cannot decode file with any supported encoding"


def read_file_lines(path: str) -> List[str]:
    """
    Read file lines with encoding fallback.

    Args:
        path: File path to read

    Returns:
        List of lines (empty on failure)
    """
    content, enc = read_file_safe(path)
    if content is None:
        logger.warning("Cannot read %s: %s", path, enc)
        return []
    return content.splitlines(keepends=True)


def validate_file_path(path: str) -> Tuple[bool, str]:
    """
    Validate that a path points to a readable XML file.

    Returns:
        (is_valid, error_message)
    """
    if not path:
        return False, "Empty path"

    if not os.path.exists(path):
        return False, f"File not found: {path}"

    if not os.path.isfile(path):
        return False, f"Not a file: {path}"

    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}"

    if not os.access(path, os.R_OK):
        return False, f"File not readable: {path}"

    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large: {file_size_mb:.1f} MB"

    return True, ""


def find_xml_files(folder: str) -> List[str]:
    """
    Recursively find all XML files in a folder.

    Args:
        folder: Root folder to search

    Returns:
        List of absolute XML file paths
    """
    xml_files = []
    try:
        for root, _, files in os.walk(folder):
            for f in files:
                if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS:
                    xml_files.append(os.path.join(root, f))
    except Exception as e:
        logger.error("Error scanning folder %s: %s", folder, e)
    return xml_files
