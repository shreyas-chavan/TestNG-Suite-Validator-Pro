#!/usr/bin/env python3
"""
Tests for fix generation and auto-fix engine.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from OPUS.models import ValidationError, Severity
from OPUS.fixes.fix_generator import generate_fix
from OPUS.fixes.auto_fixer import apply_auto_fix, batch_auto_fix
from OPUS.config import CODE_META


class TestFixGenerator(unittest.TestCase):
    """Test tutorial-style fix generation."""

    def _make_error(self, code, message="test", line=1, ctx=None, line_content=None):
        meta = CODE_META.get(code, (message, "ERROR"))
        return ValidationError(
            code=code, message=message, line=line,
            severity=Severity.ERROR if meta[1] == "ERROR" else Severity.WARNING,
            context_data=ctx, line_content=line_content,
        )

    def test_fix_for_every_registered_code(self):
        """Every code in CODE_META should produce a non-default fix."""
        test_codes = [
            "E100", "E101", "E102", "E103", "E104", "E105", "E106",
            "E107", "E108", "E109", "E110", "E111", "E112", "E113",
            "E114", "E115", "E116", "E117", "E120", "E121", "E122",
            "E123", "E124", "E130", "E131", "E132", "E145", "E160",
            "E161", "E170", "E180", "E181", "E182", "E200", "E201",
            "E300", "E301", "E303", "E310",
        ]
        for code in test_codes:
            err = self._make_error(code, ctx="test_ctx", line_content='<test name="x"/>')
            fix = generate_fix(err)
            self.assertIsNotNone(fix, f"No fix for {code}")
            self.assertTrue(len(fix.steps) > 0, f"Empty steps for {code}")
            self.assertTrue(len(fix.title) > 0, f"Empty title for {code}")

    def test_fix_e170_has_clean_name(self):
        err = self._make_error("E170", ctx="Test Class", line_content='<class name="Test Class"/>')
        fix = generate_fix(err)
        self.assertIn("TestClass", fix.code)

    def test_fix_context_view(self):
        lines = ["<suite>\n", "  <test>\n", "  </test>\n", "</suite>\n"]
        err = self._make_error("E103", line=2, line_content="  <test>")
        fix = generate_fix(err, lines)
        self.assertIn("2", fix.context)

    def test_fix_e100_mismatched(self):
        err = self._make_error("E100", message="Mismatched tag: expected </test>")
        fix = generate_fix(err)
        self.assertIn("Mismatch", fix.steps[0])

    def test_fix_e100_unclosed(self):
        err = self._make_error("E100", message="Unclosed tag at end of file")
        fix = generate_fix(err)
        self.assertIn("End of File", fix.steps[0])


class TestAutoFixer(unittest.TestCase):
    """Test the auto-fix engine."""

    def test_fix_e170_removes_spaces(self):
        lines = ['<class name="Test Class"/>\n']
        err = ValidationError(code="E170", message="Space", line=1,
                              severity=Severity.ERROR, context_data="Test Class")
        ok, msg = apply_auto_fix(err, lines)
        self.assertTrue(ok)
        self.assertIn("TestClass", lines[0])

    def test_fix_e101_adds_suite_name(self):
        lines = ['<suite>\n']
        err = ValidationError(code="E101", message="Missing name", line=1,
                              severity=Severity.ERROR)
        ok, msg = apply_auto_fix(err, lines)
        self.assertTrue(ok)
        self.assertIn('name="TestSuite"', lines[0])

    def test_fix_e103_adds_test_name(self):
        lines = ['<test>\n']
        err = ValidationError(code="E103", message="Missing name", line=1,
                              severity=Severity.ERROR)
        ok, msg = apply_auto_fix(err, lines)
        self.assertTrue(ok)
        self.assertIn('name="Test1"', lines[0])

    def test_fix_e112_adds_class_name(self):
        lines = ['<class/>\n']
        err = ValidationError(code="E112", message="Missing name", line=1,
                              severity=Severity.ERROR)
        ok, msg = apply_auto_fix(err, lines)
        self.assertTrue(ok)
        self.assertIn('name=', lines[0])

    def test_fix_invalid_line(self):
        lines = ['<test/>\n']
        err = ValidationError(code="E170", message="Space", line=99,
                              severity=Severity.ERROR)
        ok, msg = apply_auto_fix(err, lines)
        self.assertFalse(ok)

    def test_unfixable_code(self):
        lines = ['<suite name="S">\n']
        err = ValidationError(code="E200", message="Mismatch", line=1,
                              severity=Severity.ERROR)
        ok, msg = apply_auto_fix(err, lines)
        self.assertFalse(ok)


class TestBatchAutoFix(unittest.TestCase):
    """Test batch auto-fix functionality."""

    def test_batch_fix_creates_backup(self):
        content = '<suite>\n<test>\n<classes><class name="C"/></classes>\n</test>\n</suite>\n'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml',
                                          delete=False, encoding='utf-8') as f:
            f.write(content)
            path = f.name

        try:
            errors = [
                ValidationError(code="E101", message="Missing name", line=1,
                                severity=Severity.ERROR),
            ]
            fixed, total, msg = batch_auto_fix(path, errors, create_backup=True)
            self.assertGreaterEqual(fixed, 0)
            # Check backup was created
            self.assertTrue(os.path.exists(path + ".bak"))
        finally:
            os.unlink(path)
            if os.path.exists(path + ".bak"):
                os.unlink(path + ".bak")

    def test_batch_no_fixable(self):
        content = '<suite name="S"><test name="T"><classes><class name="C"/></classes></test></suite>'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml',
                                          delete=False, encoding='utf-8') as f:
            f.write(content)
            path = f.name

        try:
            errors = [
                ValidationError(code="E200", message="Mismatch", line=1,
                                severity=Severity.ERROR),
            ]
            fixed, total, msg = batch_auto_fix(path, errors)
            self.assertEqual(fixed, 0)
            self.assertEqual(total, 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
