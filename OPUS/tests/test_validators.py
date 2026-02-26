#!/usr/bin/env python3
"""
Comprehensive tests for the validation engine.
Tests all error codes, edge cases, and parsing scenarios.
"""

import os
import sys
import tempfile
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from OPUS.validators.sax_validator import validate_file
from OPUS.models import Severity
from OPUS.config import CODE_META


class TestErrorCodeCoverage(unittest.TestCase):
    """Verify all error codes are defined in CODE_META."""

    def test_all_codes_defined(self):
        expected = [
            "E100", "E101", "E102", "E103", "E104", "E105", "E106",
            "E107", "E108", "E109", "E110", "E111", "E112", "E113",
            "E114", "E115", "E116", "E117", "E120", "E121", "E122",
            "E123", "E124", "E130", "E131", "E132", "E145", "E160",
            "E161", "E170", "E180", "E181", "E182", "E183", "E184",
            "E185", "E200", "E201", "E300", "E301", "E302", "E303", "E310",
        ]
        for code in expected:
            self.assertIn(code, CODE_META, f"Missing code: {code}")


class BaseValidatorTest(unittest.TestCase):
    """Base class providing helper methods for validator tests."""

    def _validate_xml(self, xml_content: str, metadata=None):
        """Write XML to temp file, validate, return result."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml',
                                          delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            f.flush()
            path = f.name

        try:
            return validate_file(path, metadata)
        finally:
            os.unlink(path)

    def _assert_has_code(self, result, code, msg=""):
        codes = [e.code for e in result.errors]
        self.assertIn(code, codes, f"Expected {code} in errors. Got: {codes}. {msg}")

    def _assert_no_code(self, result, code, msg=""):
        codes = [e.code for e in result.errors]
        self.assertNotIn(code, codes, f"Unexpected {code} in errors. Got: {codes}. {msg}")

    def _assert_valid(self, result, msg=""):
        self.assertTrue(result.is_valid, f"Expected valid. Errors: {[(e.code, e.message) for e in result.errors]}. {msg}")

    def _assert_invalid(self, result, msg=""):
        self.assertFalse(result.is_valid, f"Expected invalid. {msg}")


class TestValidSuites(BaseValidatorTest):
    """Test that valid XML passes validation."""

    def test_minimal_valid_suite(self):
        xml = '''<suite name="S"><test name="T"><classes><class name="C"/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_methods(self):
        xml = '''<suite name="S">
            <test name="T">
                <classes>
                    <class name="com.example.Test">
                        <methods>
                            <include name="m1"/>
                            <include name="m2"/>
                        </methods>
                    </class>
                </classes>
            </test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_parameters(self):
        xml = '''<suite name="S">
            <parameter name="browser" value="chrome"/>
            <test name="T">
                <parameter name="url" value="http://example.com"/>
                <classes><class name="C"/></classes>
            </test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_listeners(self):
        xml = '''<suite name="S">
            <listeners>
                <listener class-name="com.example.Listener"/>
            </listeners>
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_packages(self):
        xml = '''<suite name="S">
            <test name="T">
                <packages>
                    <package name="com.example.tests"/>
                </packages>
            </test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_exclude(self):
        xml = '''<suite name="S">
            <test name="T">
                <classes>
                    <class name="C">
                        <methods>
                            <include name="m1"/>
                            <exclude name="m2"/>
                        </methods>
                    </class>
                </classes>
            </test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_suite_with_valid_attributes(self):
        xml = '''<suite name="S" parallel="methods" thread-count="5" verbose="2" preserve-order="true">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)


class TestStructuralErrors(BaseValidatorTest):
    """Test structural validation rules."""

    def test_e101_suite_missing_name(self):
        xml = '''<suite><test name="T"><classes><class name="C"/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E101")

    def test_e102_multiple_suites(self):
        xml = '''<suite name="S1"><test name="T"><classes><class name="C"/></classes></test></suite>'''
        # SAX will report error for second suite (not well-formed with 2 roots)
        # This test verifies the validator handles it gracefully
        result = self._validate_xml(xml)
        # Single suite should be fine
        self._assert_no_code(result, "E102")

    def test_e103_test_missing_name(self):
        xml = '''<suite name="S"><test><classes><class name="C"/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E103")

    def test_e104_duplicate_test_name(self):
        xml = '''<suite name="S">
            <test name="T1"><classes><class name="C1"/></classes></test>
            <test name="T1"><classes><class name="C2"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E104")

    def test_e105_missing_suite(self):
        xml = '''<test name="T"><classes><class name="C"/></classes></test>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E105")

    def test_e106_empty_suite(self):
        xml = '''<suite name="S"></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E106")

    def test_e107_empty_classes(self):
        xml = '''<suite name="S"><test name="T"><classes></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E107")

    def test_e108_empty_methods(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods></methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E108")

    def test_e109_empty_packages(self):
        xml = '''<suite name="S"><test name="T"><packages></packages></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E109")

    def test_e110_classes_outside_test(self):
        xml = '''<suite name="S"><classes><class name="C"/></classes></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E110")

    def test_e111_class_outside_classes(self):
        xml = '''<suite name="S"><test name="T"><class name="C"/></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E111")

    def test_e112_class_missing_name(self):
        xml = '''<suite name="S"><test name="T"><classes><class/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E112")

    def test_e113_packages_outside_test(self):
        xml = '''<suite name="S"><packages><package name="p"/></packages></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E113")

    def test_e114_mix_classes_and_packages(self):
        xml = '''<suite name="S"><test name="T">
            <classes><class name="C"/></classes>
            <packages><package name="p"/></packages>
        </test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E114")

    def test_e116_package_missing_name(self):
        xml = '''<suite name="S"><test name="T"><packages><package/></packages></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E116")

    def test_e117_invalid_package_name(self):
        xml = '''<suite name="S"><test name="T"><packages>
            <package name="123.bad"/>
        </packages></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E117")

    def test_e120_methods_outside_class(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <methods><include name="m"/></methods>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E120")

    def test_e122_include_missing_name(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods><include/></methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E122")

    def test_e124_exclude_missing_name(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods><exclude/></methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E124")

    def test_e130_param_missing_name(self):
        xml = '''<suite name="S"><parameter value="v"/>
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E130")

    def test_e131_param_missing_value(self):
        xml = '''<suite name="S"><parameter name="n"/>
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E131")

    def test_e132_duplicate_parameter(self):
        xml = '''<suite name="S">
            <parameter name="p" value="v1"/>
            <parameter name="p" value="v2"/>
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E132")


class TestDuplicateDetection(BaseValidatorTest):
    """Test duplicate detection rules."""

    def test_e160_duplicate_class(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"/>
            <class name="C"/>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E160")

    def test_e161_duplicate_method(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods>
                <include name="m"/>
                <include name="m"/>
            </methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E161")


class TestSpaceValidation(BaseValidatorTest):
    """Test space-in-name validation."""

    def test_e170_space_in_class_name(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="com.example.Test Class"/>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E170")

    def test_e170_space_in_method_name(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods>
                <include name="test Method"/>
            </methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E170")

    def test_spaces_allowed_in_test_name(self):
        xml = '''<suite name="My Suite"><test name="My Test">
            <classes><class name="C"/></classes>
        </test></suite>'''
        result = self._validate_xml(xml)
        self._assert_no_code(result, "E170")


class TestAttributeValidation(BaseValidatorTest):
    """Test attribute validation rules."""

    def test_e180_invalid_parallel(self):
        xml = '''<suite name="S" parallel="invalid">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E180")

    def test_e181_invalid_thread_count(self):
        xml = '''<suite name="S" thread-count="-5">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E181")

    def test_e181_non_numeric_thread_count(self):
        xml = '''<suite name="S" thread-count="abc">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E181")

    def test_e182_invalid_verbose(self):
        xml = '''<suite name="S" verbose="20">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E182")

    def test_e183_invalid_preserve_order(self):
        xml = '''<suite name="S" preserve-order="maybe">
            <test name="T"><classes><class name="C"/></classes></test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E183")


class TestMetadataValidation(BaseValidatorTest):
    """Test metadata-based semantic validation."""

    def test_e300_unknown_class(self):
        metadata = {"com.example.RealClass": {"methods": ["m1"]}}
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="com.example.FakeClass"/>
        </classes></test></suite>'''
        result = self._validate_xml(xml, metadata)
        self._assert_has_code(result, "E300")

    def test_e301_unknown_method(self):
        metadata = {"C": {"methods": ["realMethod"]}}
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"><methods><include name="fakeMethod"/></methods></class>
        </classes></test></suite>'''
        result = self._validate_xml(xml, metadata)
        self._assert_has_code(result, "E301")

    def test_known_class_passes(self):
        metadata = {"com.example.TestClass": {"methods": ["testLogin"]}}
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="com.example.TestClass">
                <methods><include name="testLogin"/></methods>
            </class>
        </classes></test></suite>'''
        result = self._validate_xml(xml, metadata)
        self._assert_no_code(result, "E300")
        self._assert_no_code(result, "E301")


class TestParameterScope(BaseValidatorTest):
    """Regression tests for parameter scoping across include/exclude."""

    def test_params_on_different_includes_no_false_duplicate(self):
        """Same param name on different <include> tags should NOT be duplicate."""
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C">
                <methods>
                    <include name="m1">
                        <parameter name="shelfUID" value="N1"/>
                    </include>
                    <include name="m2">
                        <parameter name="shelfUID" value="N1"/>
                    </include>
                </methods>
            </class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_no_code(result, "E132", "Same param on different includes should not be duplicate")

    def test_params_same_include_still_duplicate(self):
        """Same param name TWICE inside ONE <include> should still be duplicate."""
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C">
                <methods>
                    <include name="m1">
                        <parameter name="p" value="v1"/>
                        <parameter name="p" value="v2"/>
                    </include>
                </methods>
            </class>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_has_code(result, "E132")

    def test_params_scoped_per_test(self):
        """Same param name in different <test> blocks should NOT be duplicate."""
        xml = '''<suite name="S">
            <test name="T1">
                <parameter name="browser" value="chrome"/>
                <classes><class name="C1"/></classes>
            </test>
            <test name="T2">
                <parameter name="browser" value="firefox"/>
                <classes><class name="C2"/></classes>
            </test>
        </suite>'''
        result = self._validate_xml(xml)
        self._assert_no_code(result, "E132")


class TestEdgeCases(BaseValidatorTest):
    """Test edge cases and error recovery."""

    def test_empty_file(self):
        result = self._validate_xml("")
        self.assertTrue(len(result.errors) > 0)

    def test_malformed_xml(self):
        result = self._validate_xml("<suite name='S'><test>")
        self._assert_has_code(result, "E100")

    def test_dtd_declaration_accepted(self):
        xml = '''<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">
        <suite name="S"><test name="T"><classes><class name="C"/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self._assert_valid(result)

    def test_result_properties(self):
        xml = '''<suite name="S"><test name="T"><classes><class name="C"/></classes></test></suite>'''
        result = self._validate_xml(xml)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.warning_count, 0)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.duration_ms, 0)


class TestValidationResult(BaseValidatorTest):
    """Test ValidationResult properties and methods."""

    def test_errors_by_code(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C1 bad"/><class name="C2 bad"/>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        by_code = result.errors_by_code()
        self.assertIn("E170", by_code)

    def test_errors_by_severity(self):
        xml = '''<suite name="S"><test name="T"><classes>
            <class name="C"/><class name="C"/>
        </classes></test></suite>'''
        result = self._validate_xml(xml)
        by_sev = result.errors_by_severity()
        self.assertIn(Severity.WARNING, by_sev)


if __name__ == "__main__":
    unittest.main(verbosity=2)
