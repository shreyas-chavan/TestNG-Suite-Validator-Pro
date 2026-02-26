#!/usr/bin/env python3
"""
Tutorial-style fix suggestion generator.
Uses a registry pattern instead of a giant if/elif chain.
Each error code maps to a handler that builds a FixSuggestion.
"""

import logging
from typing import List, Optional, Dict, Callable

from ..models import ValidationError, FixSuggestion

logger = logging.getLogger(__name__)

# Type alias for fix handler functions
FixHandler = Callable[[ValidationError, str, str, str], FixSuggestion]

# ─── Registry of fix handlers ─────────────────────────────
_FIX_HANDLERS: Dict[str, FixHandler] = {}


def _register(code: str):
    """Decorator to register a fix handler for an error code."""
    def decorator(func: FixHandler):
        _FIX_HANDLERS[code] = func
        return func
    return decorator


def _build_context_view(file_lines: List[str], error_line: Optional[int], radius: int = 3) -> str:
    """Build a context view showing lines around the error."""
    if not file_lines or not error_line or error_line < 1:
        return ""
    start = max(0, error_line - radius)
    end = min(len(file_lines), error_line + radius)
    context_lines = []
    for i in range(start, end):
        marker = "\u2192" if i == error_line - 1 else " "
        context_lines.append(f"{marker} {i+1:3d} | {file_lines[i].rstrip()}")
    return "\n".join(context_lines)


def generate_fix(error: ValidationError, file_lines: List[str] = None) -> FixSuggestion:
    """
    Generate a tutorial-style fix suggestion for a validation error.

    Args:
        error: The validation error to generate a fix for
        file_lines: Source file lines for context display

    Returns:
        FixSuggestion with title, steps, example code, and context
    """
    ctx = error.context_data or "Unknown"
    line_num = error.line or "?"
    bad_code = error.line_content.strip() if error.line_content else "..."
    context_view = _build_context_view(file_lines or [], error.line)

    # Look up registered handler
    handler = _FIX_HANDLERS.get(error.code)
    if handler:
        fix = handler(error, ctx, str(line_num), bad_code)
        fix.context = context_view
        return fix

    # Default fallback
    return FixSuggestion(
        title=f"\U0001f527 Fix: {error.message}",
        steps=[f"Error at Line {line_num}.", "Review XML structure."],
        code="",
        context=context_view,
    )


# ─── Registered Fix Handlers ──────────────────────────────

@_register("E170")
def _fix_spaces(err, ctx, line_num, bad_code):
    clean = ctx.replace(" ", "")
    return FixSuggestion(
        title="\u274c Fix: Forbidden Spaces",
        steps=[
            f"1. **The Issue:** You used spaces in the name '{ctx}'.",
            "2. **The Rule:** TestNG/Java forbids spaces in Class names and Method names.",
            "3. **Note:** Spaces are allowed in <test> names, but NOT in <class> or <include>.",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Delete the spaces.",
        ],
        code=f'name="{clean}"',
    )


@_register("E201")
def _fix_unclosed(err, ctx, line_num, bad_code):
    tag = err.context_data or "unknown"
    return FixSuggestion(
        title=f"\u274c Fix: Unclosed Tag <{tag}>",
        steps=[
            f"1. **The Issue:** You opened a <{tag}> tag at Line {line_num} but never closed it.",
            "2. **The Context:** The parser reached the end of the block, but this tag was still open.",
            f"3. **Action:** Add the closing tag `</{tag}>` before the parent block ends.",
        ],
        code=f"<{tag}>\n  ...\n</{tag}>",
    )


@_register("E104")
def _fix_dup_test(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Duplicate Test Name",
        steps=[
            f"1. **The Issue:** The test name '{ctx}' is used more than once.",
            "2. **The Rule:** Every <test> tag in a suite MUST have a unique name.",
            "3. **Action:** Rename this test to something unique.",
        ],
        code=f'<test name="{ctx}_Run2">',
    )


@_register("E110")
def _fix_classes_outside_test(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <classes>",
        steps=[
            "1. **The Issue:** You placed `<classes>` directly under `<suite>`.",
            "2. **The Rule:** `<classes>` must ALWAYS be inside a `<test>` container.",
            "3. **Hierarchy:** Suite \u2192 Test \u2192 Classes.",
            "4. **Action:** Wrap this block in a `<test>` tag.",
        ],
        code='<test name="MyTest">\n  <classes>\n    ...\n  </classes>\n</test>',
    )


@_register("E100")
def _fix_syntax(err, ctx, line_num, bad_code):
    msg = err.message
    if "Mismatched" in msg:
        steps = [
            "1. **The Issue:** Tag Mismatch.",
            f"2. **Detail:** {msg}",
            "3. **Meaning:** You opened one tag but tried to close a different one.",
            "4. **Action:** Ensure your closing tag matches the currently open tag.",
        ]
    elif "Unclosed" in msg:
        steps = [
            "1. **The Issue:** Unexpected End of File.",
            f"2. **Detail:** {msg}",
            "3. **Action:** Close the tag listed above before ending the file.",
        ]
    else:
        steps = [
            f"1. **Parser Error:** {msg}",
            '2. **Check For:** Missing quotes (`"`), missing brackets (`>`), or typos.',
        ]
    return FixSuggestion(title="\u274c Fix: XML Syntax Error", steps=steps)


@_register("E132")
def _fix_dup_param(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Duplicate Parameter",
        steps=[
            f"1. **The Issue:** The parameter '{ctx}' is defined twice in this block.",
            "2. **The Rule:** Parameter names must be unique within their scope (suite/test/class).",
            "3. **Action:** Delete one of the duplicates or rename one.",
        ],
    )


@_register("E160")
def _fix_dup_class(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Duplicate Class",
        steps=[
            f"1. **The Issue:** Class '{ctx}' appears twice in this test.",
            "2. **Action:** Merge them into a single <class> block.",
            "3. **Tip:** Move all <include> methods into the first block.",
        ],
    )


@_register("E107")
def _fix_empty_classes(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Empty <classes> Block",
        steps=[
            "1. **The Issue:** Your <classes> block has no <class> tags inside.",
            "2. **The Rule:** Every <classes> block must contain at least one <class> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add a <class> tag or remove the empty <classes> block.",
        ],
        code='<test name="MyTest">\n  <classes>\n    <class name="com.example.MyTestClass"/>\n  </classes>\n</test>',
    )


@_register("E108")
def _fix_empty_methods(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Empty <methods> Block",
        steps=[
            "1. **The Issue:** Your <methods> block has no <include> tags inside.",
            "2. **The Rule:** Every <methods> block must contain at least one <include> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add <include> tags or remove the <methods> block to run all methods.",
        ],
        code='<class name="com.example.MyClass">\n  <methods>\n    <include name="testMethod1"/>\n  </methods>\n</class>',
    )


@_register("E131")
def _fix_param_missing_value(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Parameter Missing Value",
        steps=[
            f"1. **The Issue:** Parameter '{ctx}' is missing the 'value' attribute.",
            "2. **The Rule:** Every <parameter> tag MUST have both 'name' and 'value' attributes.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add value="..." to your parameter tag.',
        ],
        code=f'<parameter name="{ctx}" value="yourValue"/>',
    )


@_register("E130")
def _fix_param_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Parameter Missing Name",
        steps=[
            "1. **The Issue:** Your <parameter> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <parameter> tag MUST have both 'name' and 'value' attributes.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="paramName" to your parameter tag.',
        ],
        code='<parameter name="paramName" value="paramValue"/>',
    )


@_register("E109")
def _fix_empty_packages(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Empty <packages> Block",
        steps=[
            "1. **The Issue:** Your <packages> block has no <package> tags inside.",
            "2. **The Rule:** Every <packages> block must contain at least one <package> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add <package> tags or remove the empty <packages> block.",
        ],
        code='<test name="MyTest">\n  <packages>\n    <package name="com.example.tests.*"/>\n  </packages>\n</test>',
    )


@_register("E113")
def _fix_packages_outside_test(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <packages>",
        steps=[
            "1. **The Issue:** You placed <packages> outside a <test> tag.",
            "2. **The Rule:** <packages> must ALWAYS be inside a <test> container.",
            "3. **Hierarchy:** <suite> \u2192 <test> \u2192 <packages>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <packages> block in a <test> tag.",
        ],
        code='<test name="MyTest">\n  <packages>\n    <package name="com.example.*"/>\n  </packages>\n</test>',
    )


@_register("E114")
def _fix_mix_classes_packages(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Cannot Mix <classes> and <packages>",
        steps=[
            "1. **The Issue:** You have both <classes> and <packages> in the same <test>.",
            "2. **The Rule:** TestNG allows EITHER <classes> OR <packages>, not both.",
            "3. **Action:** Choose one approach.",
            f"4. **Your Code:** `{bad_code}`",
        ],
        code='Option 1 - Classes:\n<test name="MyTest">\n  <classes>\n    <class name="com.example.Test1"/>\n  </classes>\n</test>\n\nOption 2 - Packages:\n<test name="MyTest">\n  <packages>\n    <package name="com.example.*"/>\n  </packages>\n</test>',
    )


@_register("E115")
def _fix_package_outside_packages(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <package>",
        steps=[
            "1. **The Issue:** You placed <package> outside a <packages> container.",
            "2. **The Rule:** <package> must be inside <packages>.",
            "3. **Hierarchy:** <test> \u2192 <packages> \u2192 <package>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <package> tags in a <packages> block.",
        ],
    )


@_register("E116")
def _fix_package_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Package Missing Name",
        steps=[
            "1. **The Issue:** Your <package> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <package> must have a name (e.g., com.example.*).",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="com.example.*" to your package tag.',
        ],
        code='<package name="com.example.tests.*"/>',
    )


@_register("E117")
def _fix_invalid_package_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Invalid Package Name Format",
        steps=[
            f"1. **The Issue:** Package name '{ctx}' has invalid format.",
            "2. **The Rule:** Package names must follow Java naming:",
            "   - Start with letter or underscore",
            "   - Use dots to separate parts (com.example.tests)",
            "   - Can end with .* for wildcard",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Examples:** com.example.*, org.tests, my_package.tests.*",
        ],
        code='<package name="com.example.tests.*"/>',
    )


@_register("E123")
def _fix_exclude_misplaced(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <exclude>",
        steps=[
            "1. **The Issue:** You placed <exclude> outside a <methods> block.",
            "2. **The Rule:** <exclude> must be inside <methods>, just like <include>.",
            "3. **Hierarchy:** <class> \u2192 <methods> \u2192 <exclude>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Move <exclude> inside the <methods> block.",
        ],
        code='<class name="com.example.MyClass">\n  <methods>\n    <include name="test1"/>\n    <exclude name="test2"/>\n  </methods>\n</class>',
    )


@_register("E124")
def _fix_exclude_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Exclude Missing Name",
        steps=[
            "1. **The Issue:** Your <exclude> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <exclude> must specify which method to exclude.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="methodName" to your exclude tag.',
        ],
        code='<exclude name="testMethodToSkip"/>',
    )


@_register("E101")
def _fix_suite_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Suite Missing Name",
        steps=[
            "1. **The Issue:** Your <suite> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every TestNG suite MUST have a name.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="MySuiteName" to your suite tag.',
        ],
        code='<suite name="TestSuite" verbose="1">',
    )


@_register("E102")
def _fix_multiple_suites(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Multiple <suite> Tags",
        steps=[
            "1. **The Issue:** You have more than one <suite> tag in the file.",
            "2. **The Rule:** A TestNG XML file can only have ONE root <suite> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Remove extra <suite> tags or split into separate files.",
        ],
        code='<suite name="MainSuite">\n  <test name="Test1">...</test>\n  <test name="Test2">...</test>\n</suite>',
    )


@_register("E103")
def _fix_test_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Test Missing Name",
        steps=[
            "1. **The Issue:** Your <test> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <test> tag MUST have a unique name.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="MyTestName" to your test tag.',
        ],
        code='<test name="RegressionTests">',
    )


@_register("E105")
def _fix_missing_suite(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Missing <suite> Tag",
        steps=[
            "1. **The Issue:** Your XML file doesn't have a <suite> root tag.",
            "2. **The Rule:** Every TestNG XML must start with <suite> and end with </suite>.",
            "3. **Action:** Wrap your entire configuration in a <suite> tag.",
        ],
        code='<suite name="TestSuite">\n  <test name="MyTest">\n    <classes>\n      <class name="com.example.TestClass"/>\n    </classes>\n  </test>\n</suite>',
    )


@_register("E106")
def _fix_empty_suite(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Empty Suite",
        steps=[
            "1. **The Issue:** Your <suite> tag has no <test> tags inside.",
            "2. **The Rule:** A suite must contain at least one <test> block.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add at least one <test> block with test classes.",
        ],
        code='<suite name="TestSuite">\n  <test name="SmokeTest">\n    <classes>\n      <class name="com.example.TestClass"/>\n    </classes>\n  </test>\n</suite>',
    )


@_register("E111")
def _fix_class_outside_classes(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <class>",
        steps=[
            "1. **The Issue:** You placed <class> outside a <classes> container.",
            "2. **The Rule:** <class> tags must be inside <classes>.",
            "3. **Hierarchy:** <test> \u2192 <classes> \u2192 <class>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <class> tags in a <classes> block.",
        ],
        code='<test name="MyTest">\n  <classes>\n    <class name="com.example.TestClass"/>\n  </classes>\n</test>',
    )


@_register("E112")
def _fix_class_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Class Missing Name",
        steps=[
            "1. **The Issue:** Your <class> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <class> must specify the fully qualified class name.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="com.example.YourTestClass" to your class tag.',
        ],
        code='<class name="com.example.tests.LoginTest"/>',
    )


@_register("E120")
def _fix_methods_outside_class(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <methods>",
        steps=[
            "1. **The Issue:** You placed <methods> outside a <class> tag.",
            "2. **The Rule:** <methods> must be inside a <class> block.",
            "3. **Hierarchy:** <class> \u2192 <methods> \u2192 <include>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Move <methods> inside the <class> tag.",
        ],
        code='<class name="com.example.TestClass">\n  <methods>\n    <include name="testMethod1"/>\n  </methods>\n</class>',
    )


@_register("E121")
def _fix_include_misplaced(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Misplaced <include>",
        steps=[
            "1. **The Issue:** You placed <include> outside a <methods> block.",
            "2. **The Rule:** <include> must be inside <methods>.",
            "3. **Hierarchy:** <class> \u2192 <methods> \u2192 <include>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <include> tags in a <methods> block.",
        ],
        code='<class name="com.example.TestClass">\n  <methods>\n    <include name="testLogin"/>\n  </methods>\n</class>',
    )


@_register("E122")
def _fix_include_missing_name(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Include Missing Name",
        steps=[
            "1. **The Issue:** Your <include> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <include> must specify which test method to run.",
            f"3. **Your Code:** `{bad_code}`",
            '4. **Action:** Add name="testMethodName" to your include tag.',
        ],
        code='<include name="testLogin"/>',
    )


@_register("E145")
def _fix_listeners_misplaced(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Misplaced <listeners>",
        steps=[
            "1. **The Issue:** <listeners> should be directly under <suite>.",
            "2. **Best Practice:** Place listeners at suite level for global scope.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Move <listeners> to be a direct child of <suite>.",
        ],
        code='<suite name="TestSuite">\n  <listeners>\n    <listener class-name="com.example.MyListener"/>\n  </listeners>\n  <test name="MyTest">...</test>\n</suite>',
    )


@_register("E161")
def _fix_dup_method(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u26a0\ufe0f Fix: Duplicate Method",
        steps=[
            f"1. **The Issue:** Method '{ctx}' is included multiple times in this class.",
            "2. **The Rule:** Each method should only be included once per <methods> block.",
            "3. **Action:** Remove the duplicate <include> tag.",
            "4. **Note:** TestNG will only run the method once anyway.",
        ],
    )


@_register("E200")
def _fix_structure_mismatch(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Structure Mismatch",
        steps=[
            f"1. **The Issue:** {err.message}",
            "2. **Common Causes:** Closing tag doesn't match opening tag, or tag in wrong location.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Check that opening and closing tags match exactly.",
        ],
    )


@_register("E180")
def _fix_invalid_parallel(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Invalid 'parallel' Value",
        steps=[
            f"1. **The Issue:** Invalid value '{ctx}' for 'parallel' attribute.",
            "2. **Valid Values:** methods, tests, classes, instances, false",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Use one of the valid parallel modes.",
        ],
        code='<suite name="TestSuite" parallel="methods" thread-count="5">',
    )


@_register("E181")
def _fix_invalid_thread_count(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Invalid 'thread-count' Value",
        steps=[
            f"1. **The Issue:** Invalid value '{ctx}' for 'thread-count' attribute.",
            "2. **The Rule:** thread-count must be a positive integer (1, 2, 3, ...).",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Set thread-count to a positive number.",
        ],
        code='<suite name="TestSuite" parallel="methods" thread-count="5">',
    )


@_register("E182")
def _fix_invalid_verbose(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Invalid 'verbose' Value",
        steps=[
            f"1. **The Issue:** Invalid value '{ctx}' for 'verbose' attribute.",
            "2. **Valid Values:** 0 (silent) to 10 (maximum detail).",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Use a number between 0 and 10.",
        ],
        code='<suite name="TestSuite" verbose="2">',
    )


@_register("E300")
def _fix_unknown_class(err, ctx, line_num, bad_code):
    steps = [
        f"1. **The Issue:** The class '{ctx}' is not in your project metadata.",
        "2. **Check:** Spelling, Case Sensitivity, and Package Name.",
    ]
    if err.suggestion:
        steps.append(f"3. **Suggestion:** {err.suggestion}")
    else:
        steps.append("3. **Action:** Check your Java source folder.")
    return FixSuggestion(title="\u2753 Fix: Unknown Class", steps=steps)


@_register("E301")
def _fix_unknown_method(err, ctx, line_num, bad_code):
    steps = [
        f"1. **The Issue:** Method '{ctx}' not found in the class.",
        "2. **Check:** Method name spelling and case sensitivity.",
    ]
    if err.suggestion:
        steps.append(f"3. **Suggestion:** {err.suggestion}")
    else:
        steps.append("3. **Action:** Verify the method exists in your test class.")
    return FixSuggestion(title="\u2753 Fix: Unknown Method", steps=steps)


@_register("E303")
def _fix_invalid_enum(err, ctx, line_num, bad_code):
    steps = [
        f"1. **The Issue:** Invalid value '{ctx}' for this parameter.",
        f"2. **Detail:** {err.message}",
    ]
    if err.suggestion:
        steps.append(f"3. **Suggestion:** {err.suggestion}")
    else:
        steps.append("3. **Action:** Use one of the allowed values.")
    return FixSuggestion(title="\u274c Fix: Invalid Enum Value", steps=steps)


@_register("E310")
def _fix_suite_file_not_found(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="\u274c Fix: Suite File Not Found",
        steps=[
            f"1. **The Issue:** The file '{ctx}' referenced in <suite-file> doesn't exist.",
            "2. **Check:** File path, spelling, and relative location.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Verify the file exists or correct the path.",
        ],
    )
