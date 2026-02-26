#!/usr/bin/env python3
"""
Hybrid SAX-based TestNG XML Validator.
Main validation engine using Python's xml.sax for streaming parse
with structural, hierarchy, attribute, and metadata validation.
"""

import os
import re
import logging
import difflib
import time
import xml.sax
from xml.sax.handler import ContentHandler
from typing import List, Optional, Dict, Set, Tuple

from ..models import ValidationError, ValidationResult, Severity
from ..config import (
    CODE_META, VALID_PARALLEL_VALUES, VALID_BOOLEAN_VALUES,
    VERBOSE_RANGE, JAVA_PACKAGE_PATTERN, AUTO_FIXABLE_CODES,
    ENCODING_FALLBACKS,
)
from .preflight import preflight_scan

logger = logging.getLogger(__name__)


class HybridValidator(ContentHandler):
    """
    SAX ContentHandler that validates TestNG XML structure.

    Validates:
    - Suite/test/class/methods hierarchy
    - Required attributes (name, etc.)
    - Attribute value constraints (parallel, thread-count, verbose, preserve-order)
    - Duplicate detection (test names, class refs, method includes, parameters)
    - Space-in-name rules
    - Empty container detection
    - Package name format
    - Packages/classes mutual exclusivity
    - Metadata-based class/method existence (optional)
    - Suite-file path existence
    """

    def __init__(self, filename: str, metadata: Optional[Dict] = None):
        super().__init__()
        self.filename = filename
        self.metadata = metadata
        self.base_path = os.path.dirname(os.path.abspath(filename))
        self.locator = None
        self.stack: List[Tuple[str, int]] = []
        self.errors: List[ValidationError] = []

        # Counters
        self.seen_suite = 0
        self.test_count = 0
        self.current_test: Optional[str] = None
        self.current_class: Optional[str] = None

        # Duplicate tracking
        self.test_names: Dict[str, int] = {}
        self.class_names: Dict[str, int] = {}
        self.method_names: Dict[str, int] = {}
        self.param_names: Set[str] = set()

        # Empty container tracking
        self.classes_has_children = False
        self.methods_has_children = False
        self.packages_has_children = False

        # Mutual exclusivity tracking
        self.test_has_classes = False
        self.test_has_packages = False

    def setDocumentLocator(self, locator):
        self.locator = locator

    def _pos(self) -> Tuple[int, int]:
        if self.locator:
            return (self.locator.getLineNumber(), self.locator.getColumnNumber())
        return (0, 0)

    def _err(self, code: str, msg: str, line: int, col: int,
             ctx: Optional[str] = None, sugg: Optional[str] = None):
        meta = CODE_META.get(code, (msg, "ERROR"))
        severity = Severity.WARNING if meta[1] == "WARNING" else Severity.ERROR
        auto_fixable = code in AUTO_FIXABLE_CODES
        self.errors.append(ValidationError(
            code=code, message=msg, line=line, col=col,
            severity=severity, context_data=ctx,
            auto_fixable=auto_fixable, suggestion=sugg,
        ))

    def _get_suggestion(self, name: str, valid) -> Optional[str]:
        matches = difflib.get_close_matches(name, valid, n=3, cutoff=0.6)
        return f"Did you mean: {', '.join(matches)}?" if matches else None

    def _check_space(self, name: str, entity_type: str, line: int, col: int):
        """Check for forbidden spaces in class/method names."""
        if not name:
            return
        if entity_type in ("class", "include", "exclude") and " " in name:
            self._err("E170", f"Space forbidden in {entity_type}: '{name}'", line, col, name)

    def _parent(self, expected: str) -> bool:
        """Check if the immediate parent tag matches expected."""
        return len(self.stack) >= 2 and self.stack[1][0] == expected

    # ─── SAX Events ────────────────────────────────────────

    def startElement(self, name: str, attrs):
        line, col = self._pos()
        self.stack.insert(0, (name, line))

        # Reset parameter tracking at scope boundaries
        # In TestNG, parameters can appear at suite, test, class, and include/exclude level.
        # Each scope has its own parameter namespace.
        if name in ("suite", "test", "class", "include", "exclude"):
            self.param_names = set()

        # ── <suite> ──
        if name == "suite":
            self.seen_suite += 1
            if self.seen_suite > 1:
                self._err("E102", "Multiple suites", line, col)
            if not attrs.get("name"):
                self._err("E101", "Suite missing name", line, col)

            # Validate suite attributes
            parallel = attrs.get("parallel")
            if parallel and parallel not in VALID_PARALLEL_VALUES:
                self._err("E180", f"Invalid parallel value: '{parallel}'", line, col, parallel)

            thread_count = attrs.get("thread-count")
            if thread_count:
                try:
                    tc = int(thread_count)
                    if tc < 1:
                        self._err("E181", f"thread-count must be positive: '{thread_count}'", line, col, thread_count)
                except ValueError:
                    self._err("E181", f"thread-count must be numeric: '{thread_count}'", line, col, thread_count)

            verbose = attrs.get("verbose")
            if verbose:
                try:
                    v = int(verbose)
                    if v not in VERBOSE_RANGE:
                        self._err("E182", f"verbose must be 0-10: '{verbose}'", line, col, verbose)
                except ValueError:
                    self._err("E182", f"verbose must be numeric: '{verbose}'", line, col, verbose)

            preserve_order = attrs.get("preserve-order")
            if preserve_order and preserve_order.lower() not in VALID_BOOLEAN_VALUES:
                self._err("E183", f"preserve-order must be true/false: '{preserve_order}'", line, col, preserve_order)

        # ── <suite-file> ──
        elif name == "suite-file":
            path = attrs.get("path")
            if path and not os.path.exists(os.path.join(self.base_path, path)):
                self._err("E310", f"File not found: {path}", line, col, path)

        # ── <test> ──
        elif name == "test":
            self.test_count += 1
            tname = attrs.get("name")
            self.current_test = tname
            self.class_names = {}
            self.test_has_classes = False
            self.test_has_packages = False
            if not tname:
                self._err("E103", "Test missing name", line, col)
            # Duplicate tests handled by pre-flight; spaces allowed in test names

        # ── <classes> ──
        elif name == "classes":
            if not self._parent("test"):
                self._err("E110", "<classes> must be inside <test>", line, col)
            if self.test_has_packages:
                self._err("E114", "Cannot mix <classes> and <packages> in same <test>", line, col)
            self.test_has_classes = True
            self.classes_has_children = False

        # ── <class> ──
        elif name == "class":
            if not self._parent("classes"):
                self._err("E111", "<class> must be inside <classes>", line, col)
            self.classes_has_children = True
            cname = attrs.get("name")
            self.current_class = cname
            self.method_names = {}
            if not cname:
                self._err("E112", "Class missing name", line, col)
            else:
                self._check_space(cname, "class", line, col)
                if cname in self.class_names:
                    self._err("E160", f"Duplicate class: '{cname}'", line, col, cname)
                else:
                    self.class_names[cname] = line

                if self.metadata and cname not in self.metadata:
                    sugg = self._get_suggestion(cname, self.metadata.keys())
                    self._err("E300", f"Class unknown: {cname}", line, col, cname, sugg)

        # ── <methods> ──
        elif name == "methods":
            if not self._parent("class"):
                self._err("E120", "<methods> must be inside <class>", line, col)
            self.methods_has_children = False

        # ── <include> ──
        elif name == "include":
            if not self._parent("methods"):
                self._err("E121", "<include> must be inside <methods>", line, col)
            self.methods_has_children = True
            mname = attrs.get("name")
            if not mname:
                self._err("E122", "Include missing name", line, col)
            else:
                self._check_space(mname, "include", line, col)
                if mname in self.method_names:
                    self._err("E161", f"Duplicate method: '{mname}'", line, col, mname)
                else:
                    self.method_names[mname] = line

                if self.metadata and self.current_class and self.current_class in self.metadata:
                    valid = self.metadata[self.current_class].get("methods", [])
                    if isinstance(valid, dict):
                        valid = list(valid.keys())
                    if mname not in valid:
                        sugg = self._get_suggestion(mname, valid)
                        self._err("E301", f"Method not in {self.current_class}: {mname}", line, col, mname, sugg)

        # ── <parameter> ──
        elif name == "parameter":
            pname = attrs.get("name")
            pval = attrs.get("value")
            if not pname:
                self._err("E130", "Parameter missing 'name' attribute", line, col)
            if not pval:
                self._err("E131", "Parameter missing 'value' attribute", line, col, pname or "unknown")
            if pname:
                if pname in self.param_names:
                    self._err("E132", f"Duplicate parameter: '{pname}'", line, col, pname)
                else:
                    self.param_names.add(pname)

            # Metadata enum validation
            if self.metadata and pname and pval and self.current_class and self.current_class in self.metadata:
                params = self.metadata[self.current_class].get("parameters", {})
                if pname in params:
                    allowed = params[pname]
                    if isinstance(allowed, list) and pval not in allowed:
                        self._err("E303", f"Invalid Enum '{pname}': {pval}", line, col, pval,
                                  f"Valid: {', '.join(allowed)}")

        # ── <packages> ──
        elif name == "packages":
            if not self._parent("test"):
                self._err("E113", "<packages> must be inside <test>", line, col)
            if self.test_has_classes:
                self._err("E114", "Cannot mix <packages> and <classes> in same <test>", line, col)
            self.test_has_packages = True
            self.packages_has_children = False

        # ── <package> ──
        elif name == "package":
            if not self._parent("packages"):
                self._err("E115", "<package> must be inside <packages>", line, col)
            self.packages_has_children = True
            pkg_name = attrs.get("name")
            if not pkg_name:
                self._err("E116", "Package missing name", line, col)
            else:
                if not re.match(JAVA_PACKAGE_PATTERN, pkg_name):
                    self._err("E117", f"Invalid package name format: '{pkg_name}'", line, col, pkg_name)

        # ── <exclude> ──
        elif name == "exclude":
            if not self._parent("methods"):
                self._err("E123", "<exclude> must be inside <methods>", line, col)
            self.methods_has_children = True
            mname = attrs.get("name")
            if not mname:
                self._err("E124", "Exclude missing name", line, col)
            else:
                self._check_space(mname, "exclude", line, col)

        # ── <listeners> ──
        elif name == "listeners":
            if not self._parent("suite"):
                self._err("E145", "<listeners> should be under <suite>", line, col)

    def endElement(self, name: str):
        line, col = self._pos()

        # Check for empty containers
        if name == "classes" and not self.classes_has_children:
            self._err("E107", "Empty <classes> block - no <class> tags found", line, col)
        elif name == "methods" and not self.methods_has_children:
            self._err("E108", "Empty <methods> block - no <include> tags found", line, col)
        elif name == "packages" and not self.packages_has_children:
            self._err("E109", "Empty <packages> block - no <package> tags found", line, col)

        # ── </suite> — master close ──
        if name == "suite":
            while self.stack:
                tag, ln = self.stack.pop(0)
                if tag == "suite":
                    return
                self._err("E201", f"Unclosed tag <{tag}> inside suite", line, col, tag)
            return

        # Find matching tag in stack
        tag_in_stack = False
        for i, (tag, _) in enumerate(self.stack):
            if tag == name:
                tag_in_stack = True
                break

        if not tag_in_stack:
            self._err("E200", f"Unexpected closing tag </{name}>", line, col, name)
            return

        # Pop tags until we find the match, reporting unclosed ones
        while self.stack:
            top_tag, top_line = self.stack[0]
            if top_tag == name:
                self.stack.pop(0)
                return
            else:
                self._err("E201", f"Unclosed tag <{top_tag}> (Opened L{top_line})", line, col, top_tag)
                self.stack.pop(0)

    def endDocument(self):
        for tag, ln in self.stack:
            self._err("E201", f"<{tag}> unclosed", ln, 0, tag)
        if self.test_count == 0 and self.seen_suite > 0:
            self._err("E106", "Empty suite", 0, 0)
        if self.seen_suite == 0:
            self._err("E105", "Missing <suite>", 0, 0)


def _read_file_lines(path: str) -> List[str]:
    """Read file lines with encoding fallback."""
    for enc in ENCODING_FALLBACKS:
        try:
            with open(path, encoding=enc) as f:
                return f.readlines()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            logger.error("Cannot read %s: %s", path, e)
            return []
    logger.error("Cannot decode %s with any known encoding", path)
    return []


def validate_file(path: str, metadata: dict = None) -> ValidationResult:
    """
    Validate a TestNG XML file using the hybrid approach.

    Combines:
    1. Pre-flight regex scan (duplicates)
    2. SAX parse (structure, hierarchy, attributes)
    3. Context injection (source line content on errors)
    4. Deduplication and sorting

    Args:
        path: Path to the XML file
        metadata: Optional dict of class->methods metadata for semantic validation

    Returns:
        ValidationResult with all findings
    """
    start_time = time.time()
    file_size = 0

    try:
        file_size = os.path.getsize(path)
    except OSError:
        pass

    # 1. Read file lines (for context injection and pre-flight)
    lines = _read_file_lines(path)

    # 2. Pre-flight scan
    pre_errors = preflight_scan(path, lines)

    # 3. SAX parse
    validator = HybridValidator(path, metadata)
    validator.errors.extend(pre_errors)

    try:
        parser = xml.sax.make_parser()
        parser.setContentHandler(validator)
        parser.parse(path)
    except xml.sax.SAXParseException as e:
        custom_msg = f"Syntax Error: {e.getMessage()}"
        # Try to provide a more helpful message for mismatched tags
        if "mismatched tag" in e.getMessage().lower() and validator.stack:
            expected = validator.stack[0][0]
            try:
                err_line_idx = e.getLineNumber() - 1
                if 0 <= err_line_idx < len(lines):
                    match = re.search(r"</(\w+)>", lines[err_line_idx])
                    if match:
                        found = match.group(1)
                        if found == "suite":
                            custom_msg = f"Unclosed Tag: <{expected}> was not closed before </suite>"
                        else:
                            custom_msg = f"Mismatched Tag: Expected </{expected}> but found </{found}>"
            except Exception:
                pass
        validator.errors.insert(0, ValidationError(
            code="E100", message=custom_msg,
            line=e.getLineNumber(), col=e.getColumnNumber(),
            severity=Severity.ERROR, context_data=custom_msg,
        ))
    except Exception as e:
        logger.error("Unexpected error parsing %s: %s", path, e)
        validator.errors.insert(0, ValidationError(
            code="E000", message=f"Parser crash: {str(e)}",
            line=0, col=0, severity=Severity.ERROR,
        ))

    # 4. Context injection — attach source line content to each error
    for err in validator.errors:
        if err.line and 0 < err.line <= len(lines):
            err.line_content = lines[err.line - 1].strip()

    # 5. Deduplicate and sort
    unique_errors: List[ValidationError] = []
    seen: set = set()
    for err in validator.errors:
        key = (err.line, err.code, err.message)
        if key not in seen:
            unique_errors.append(err)
            seen.add(key)
    unique_errors.sort(key=lambda x: (x.line or 0))

    duration_ms = (time.time() - start_time) * 1000

    return ValidationResult(
        file_path=path,
        errors=unique_errors,
        duration_ms=round(duration_ms, 2),
        file_size=file_size,
        metadata_used=metadata is not None,
    )
