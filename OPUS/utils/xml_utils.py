#!/usr/bin/env python3
"""
XML formatting and manipulation utilities.
"""

import re
import os
import shutil
import logging
from typing import Tuple, Optional
from xml.dom import minidom

logger = logging.getLogger(__name__)


def format_xml_content(content: str) -> Optional[str]:
    """
    Pretty-format XML content string.

    Args:
        content: Raw XML string

    Returns:
        Formatted XML string or None if content is not valid XML
    """
    try:
        clean = re.sub(r'>\s+<', '><', content.strip())
        dom = minidom.parseString(clean)
        lines = dom.toprettyxml(indent="  ").splitlines()
        return '\n'.join(line for line in lines if line.strip())
    except Exception as e:
        logger.debug("Cannot format XML: %s", e)
        return None


def format_xml_file(path: str, create_backup: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Pretty-format an XML file in place.

    Creates a .bak backup before modifying.

    Args:
        path: Path to the XML file
        create_backup: Whether to create a backup

    Returns:
        (success, error_message)
    """
    try:
        with open(path, encoding='utf-8') as f:
            original = f.read()
    except UnicodeDecodeError:
        try:
            with open(path, encoding='latin-1') as f:
                original = f.read()
        except Exception as e:
            return False, f"Cannot read file: {e}"
    except Exception as e:
        return False, f"Cannot read file: {e}"

    formatted = format_xml_content(original)
    if not formatted:
        return False, "XML syntax error — cannot format"

    if create_backup:
        try:
            shutil.copy2(path, path + ".bak")
        except Exception as e:
            logger.warning("Failed to create backup for %s: %s", path, e)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(formatted)
        return True, None
    except Exception as e:
        return False, f"Cannot write file: {e}"
