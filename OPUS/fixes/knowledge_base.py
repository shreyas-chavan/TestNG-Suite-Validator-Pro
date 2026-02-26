#!/usr/bin/env python3
"""
Knowledge Base for TestNG Validator Pro.
Provides detailed explanations, sample usage, and reference data
for every error code. Used by the enhanced fix window tabs.
"""

from typing import Dict, Optional


# ─── Knowledge Base Entry Structure ──────────────────────────
# Each entry has:
#   explain  - Plain-English explanation of the error (novice-friendly)
#   sample   - Correct XML sample demonstrating the right way
#   mistakes - Common mistakes that cause this error

KNOWLEDGE_BASE: Dict[str, dict] = {

    # ══════════════════════════════════════════════════════════
    # STRUCTURAL ERRORS
    # ══════════════════════════════════════════════════════════

    "E100": {
        "explain": (
            "XML Syntax Error means your file has a fundamental formatting problem "
            "that prevents it from being read at all.\n\n"
            "Think of XML like parentheses in math — every opening tag <tag> needs "
            "a matching closing tag </tag>, every quote must be paired, and special "
            "characters like & must be written as &amp;.\n\n"
            "The XML parser stopped reading your file at this point because it "
            "encountered something it couldn't understand."
        ),
        "sample": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">\n'
            '<suite name="MySuite">\n'
            '  <test name="MyTest">\n'
            '    <classes>\n'
            '      <class name="com.example.TestClass"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            'Missing closing quote: name="MySuite  (missing the second ")',
            "Missing closing bracket: <suite name='MySuite'  (missing >)",
            "Mismatched tags: <suite>...</test> (opened suite, closed test)",
            "Special characters: Using & instead of &amp; in attribute values",
            "Unclosed tags: Forgetting </suite> at the end of the file",
        ],
    },

    "E101": {
        "explain": (
            "Every TestNG suite MUST have a name attribute. The name is used in "
            "test reports, logging, and to identify your test suite.\n\n"
            "Without a name, TestNG cannot properly generate reports or identify "
            "which suite produced which results."
        ),
        "sample": (
            '<suite name="RegressionSuite" verbose="1">\n'
            '  <test name="SmokeTests">\n'
            '    <classes>\n'
            '      <class name="com.example.SmokeTest"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            '<suite> without any name attribute',
            '<suite name=""> with empty name',
            'Typo in attribute: <suite nme="MySuite">',
        ],
    },

    "E102": {
        "explain": (
            "A TestNG XML file can only have ONE root <suite> element. "
            "If you need multiple suites, create separate XML files for each.\n\n"
            "Think of the <suite> tag as the container for your entire test "
            "configuration — you can have many <test> blocks inside one suite, "
            "but only one suite per file."
        ),
        "sample": (
            '<!-- ONE suite with MULTIPLE tests -->\n'
            '<suite name="AllTests">\n'
            '  <test name="UnitTests">...</test>\n'
            '  <test name="IntegrationTests">...</test>\n'
            '  <test name="E2ETests">...</test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Having two <suite> tags in one file",
            "Copy-pasting another suite XML without removing the outer <suite>",
        ],
    },

    "E103": {
        "explain": (
            "Every <test> element MUST have a name attribute. Test names appear "
            "in reports and logs, making it easy to identify which test group "
            "passed or failed.\n\n"
            "Choose descriptive names like 'LoginTests' or 'PaymentFlow' rather "
            "than generic names like 'Test1'."
        ),
        "sample": (
            '<test name="LoginTests" preserve-order="true">\n'
            '  <classes>\n'
            '    <class name="com.example.LoginTest"/>\n'
            '  </classes>\n'
            '</test>'
        ),
        "mistakes": [
            '<test> without name attribute',
            '<test name=""> with empty name',
        ],
    },

    "E104": {
        "explain": (
            "Each <test> in a suite must have a UNIQUE name. Duplicate names "
            "cause confusion in reports — you won't know which 'Test1' passed "
            "and which failed.\n\n"
            "TestNG uses the test name as an identifier, so duplicates can "
            "cause unexpected behavior in parallel execution and reporting."
        ),
        "sample": (
            '<suite name="MySuite">\n'
            '  <test name="LoginTests">...</test>\n'
            '  <test name="PaymentTests">...</test>\n'
            '  <test name="ProfileTests">...</test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Copy-pasting a <test> block without changing the name",
            "Using generic names like 'Test' for multiple blocks",
        ],
    },

    "E105": {
        "explain": (
            "Your XML file doesn't have a <suite> root element. Every TestNG "
            "XML file MUST start with <suite> as the root tag.\n\n"
            "The <suite> tag is the top-level container that holds all your "
            "test configurations. Without it, TestNG doesn't know how to "
            "interpret the file."
        ),
        "sample": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE suite SYSTEM "https://testng.org/testng-1.0.dtd">\n'
            '<suite name="MySuite">\n'
            '  <test name="MyTest">\n'
            '    <classes>\n'
            '      <class name="com.example.TestClass"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Starting the file with <test> instead of <suite>",
            "Missing the <suite> wrapper entirely",
            "Using a different root element like <configuration>",
        ],
    },

    "E106": {
        "explain": (
            "Your <suite> tag has no <test> elements inside it. An empty suite "
            "won't run any tests.\n\n"
            "You need at least one <test> block containing either <classes> or "
            "<packages> to define what TestNG should execute."
        ),
        "sample": (
            '<suite name="MySuite">\n'
            '  <test name="SmokeTest">\n'
            '    <classes>\n'
            '      <class name="com.example.SmokeTest"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Creating a suite with only listeners but no tests",
            "Accidentally deleting all <test> blocks",
        ],
    },

    "E107": {
        "explain": (
            "Your <classes> block is empty — it has no <class> tags inside. "
            "TestNG needs at least one class to know which test classes to run.\n\n"
            "Each <class> tag points to a Java test class by its fully-qualified "
            "name (package + class name)."
        ),
        "sample": (
            '<classes>\n'
            '  <class name="com.example.tests.LoginTest"/>\n'
            '  <class name="com.example.tests.SignupTest"/>\n'
            '</classes>'
        ),
        "mistakes": [
            "Empty <classes></classes> block",
            "Putting class names as text instead of <class> tags",
        ],
    },

    "E108": {
        "explain": (
            "Your <methods> block is empty — it has no <include> or <exclude> "
            "tags inside. If you don't specify methods, TestNG runs ALL methods "
            "in the class.\n\n"
            "Use <include> to run specific methods, or <exclude> to skip "
            "specific methods. If you want all methods, remove the <methods> block entirely."
        ),
        "sample": (
            '<class name="com.example.LoginTest">\n'
            '  <methods>\n'
            '    <include name="testValidLogin"/>\n'
            '    <include name="testInvalidPassword"/>\n'
            '    <exclude name="testSlowLogin"/>\n'
            '  </methods>\n'
            '</class>'
        ),
        "mistakes": [
            "Empty <methods></methods> block",
            "Wanting to run all methods but still having an empty <methods> tag",
        ],
    },

    "E109": {
        "explain": (
            "Your <packages> block is empty — it has no <package> tags inside. "
            "TestNG needs at least one package to scan for test classes.\n\n"
            "Package scanning lets you include all test classes in a package "
            "without listing them individually."
        ),
        "sample": (
            '<packages>\n'
            '  <package name="com.example.tests.*"/>\n'
            '  <package name="com.example.integration"/>\n'
            '</packages>'
        ),
        "mistakes": [
            "Empty <packages></packages> block",
            "Forgetting to add the .* wildcard for sub-packages",
        ],
    },

    "E110": {
        "explain": (
            "You placed <classes> directly under <suite>. The correct hierarchy is:\n\n"
            "  <suite> → <test> → <classes> → <class>\n\n"
            "<classes> MUST be inside a <test> block. The <test> groups related "
            "classes together and controls execution settings like parallel mode."
        ),
        "sample": (
            '<suite name="MySuite">\n'
            '  <test name="MyTest">\n'
            '    <classes>\n'
            '      <class name="com.example.TestClass"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Putting <classes> directly under <suite> without a <test> wrapper",
        ],
    },

    "E111": {
        "explain": (
            "You placed a <class> tag outside of a <classes> container. "
            "The correct hierarchy is:\n\n"
            "  <test> → <classes> → <class>\n\n"
            "Every <class> tag must be wrapped in a <classes> block."
        ),
        "sample": (
            '<test name="MyTest">\n'
            '  <classes>\n'
            '    <class name="com.example.TestClass"/>\n'
            '  </classes>\n'
            '</test>'
        ),
        "mistakes": [
            "Putting <class> directly under <test> without <classes> wrapper",
        ],
    },

    "E112": {
        "explain": (
            "Your <class> tag is missing the 'name' attribute. The name must be "
            "the fully-qualified Java class name (package + class).\n\n"
            "Example: com.example.tests.LoginTest\n"
            "This tells TestNG exactly which Java class contains your test methods."
        ),
        "sample": '<class name="com.example.tests.LoginTest"/>',
        "mistakes": [
            "<class/> without any attributes",
            '<class className="..."/> (wrong attribute name)',
        ],
    },

    "E113": {
        "explain": (
            "You placed <packages> outside a <test> block. The correct hierarchy is:\n\n"
            "  <suite> → <test> → <packages> → <package>\n\n"
            "<packages> MUST be inside a <test> element."
        ),
        "sample": (
            '<test name="PackageTest">\n'
            '  <packages>\n'
            '    <package name="com.example.tests.*"/>\n'
            '  </packages>\n'
            '</test>'
        ),
        "mistakes": [
            "Putting <packages> directly under <suite>",
        ],
    },

    "E114": {
        "explain": (
            "You have both <classes> and <packages> inside the same <test> block. "
            "TestNG allows EITHER <classes> OR <packages> in a single <test>, not both.\n\n"
            "Choose one approach:\n"
            "  • <classes> — List specific test classes by name\n"
            "  • <packages> — Scan entire packages for test classes\n\n"
            "If you need both, create separate <test> blocks."
        ),
        "sample": (
            '<!-- Approach 1: Separate test blocks -->\n'
            '<suite name="MySuite">\n'
            '  <test name="SpecificTests">\n'
            '    <classes>\n'
            '      <class name="com.example.LoginTest"/>\n'
            '    </classes>\n'
            '  </test>\n'
            '  <test name="PackageTests">\n'
            '    <packages>\n'
            '      <package name="com.example.integration.*"/>\n'
            '    </packages>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Mixing <classes> and <packages> in the same <test>",
        ],
    },

    "E115": {
        "explain": (
            "You placed a <package> tag outside of a <packages> container. "
            "The correct hierarchy is:\n\n"
            "  <test> → <packages> → <package>\n\n"
            "Every <package> tag must be wrapped in a <packages> block, "
            "which itself must be inside a <test> block."
        ),
        "sample": (
            '<test name="PackageTest">\n'
            '  <packages>\n'
            '    <package name="com.example.tests.*"/>\n'
            '  </packages>\n'
            '</test>'
        ),
        "mistakes": [
            "Putting <package> directly under <test> without <packages> wrapper",
            "Putting <package> under <suite> instead of inside <test> → <packages>",
        ],
    },

    "E116": {
        "explain": (
            "Your <package> tag is missing the 'name' attribute. The name should "
            "be a Java package path, optionally ending with .* for wildcard.\n\n"
            "Example: com.example.tests.* (includes all classes in that package)"
        ),
        "sample": '<package name="com.example.tests.*"/>',
        "mistakes": [
            "<package/> without name attribute",
            "Using class name instead of package name",
        ],
    },

    "E117": {
        "explain": (
            "The package name doesn't follow Java naming conventions. "
            "Valid package names:\n"
            "  • Use lowercase letters, digits, underscores\n"
            "  • Separate segments with dots (.)\n"
            "  • Each segment starts with a letter or underscore\n"
            "  • Can end with .* for wildcard scanning"
        ),
        "sample": (
            '<!-- Valid package names -->\n'
            '<package name="com.example.tests"/>\n'
            '<package name="com.example.tests.*"/>\n'
            '<package name="org.myproject.integration"/>'
        ),
        "mistakes": [
            "Starting with a number: 1com.example",
            "Using spaces: com. example.tests",
            "Using hyphens: com.my-project.tests",
        ],
    },

    "E121": {
        "explain": (
            "You placed an <include> tag in the wrong location. <include> tags "
            "are used to specify which test methods to run and must be inside "
            "a <methods> block.\n\n"
            "The correct hierarchy is:\n"
            "  <class> → <methods> → <include>"
        ),
        "sample": (
            '<class name="com.example.LoginTest">\n'
            '  <methods>\n'
            '    <include name="testValidLogin"/>\n'
            '    <include name="testInvalidLogin"/>\n'
            '  </methods>\n'
            '</class>'
        ),
        "mistakes": [
            "Putting <include> directly under <class> without <methods> wrapper",
            "Putting <include> outside of any <class> block",
        ],
    },

    "E123": {
        "explain": (
            "You placed an <exclude> tag in the wrong location. <exclude> tags "
            "are used to skip specific test methods and must be inside "
            "a <methods> block.\n\n"
            "The correct hierarchy is:\n"
            "  <class> → <methods> → <exclude>"
        ),
        "sample": (
            '<class name="com.example.LoginTest">\n'
            '  <methods>\n'
            '    <exclude name="testSlowMethod"/>\n'
            '  </methods>\n'
            '</class>'
        ),
        "mistakes": [
            "Putting <exclude> directly under <class> without <methods> wrapper",
        ],
    },

    "E120": {
        "explain": (
            "You placed <methods> outside a <class> block. The correct hierarchy is:\n\n"
            "  <class> → <methods> → <include>/<exclude>\n\n"
            "<methods> defines which specific methods to run (or skip) in a class."
        ),
        "sample": (
            '<class name="com.example.LoginTest">\n'
            '  <methods>\n'
            '    <include name="testValidLogin"/>\n'
            '  </methods>\n'
            '</class>'
        ),
        "mistakes": [
            "Putting <methods> directly under <test> or <classes>",
        ],
    },

    "E122": {
        "explain": (
            "Your <include> tag is missing the 'name' attribute. The name must be "
            "the exact method name from your Java test class.\n\n"
            "Note: Method names are case-sensitive! 'testLogin' ≠ 'TestLogin'"
        ),
        "sample": '<include name="testValidLogin"/>',
        "mistakes": [
            "<include/> without name",
            "Typo in the method name",
        ],
    },

    "E124": {
        "explain": (
            "Your <exclude> tag is missing the 'name' attribute. <exclude> is used "
            "to skip specific test methods.\n\n"
            "Tip: Use <exclude> when you want to run most methods but skip a few."
        ),
        "sample": '<exclude name="testSlowMethod"/>',
        "mistakes": [
            "<exclude/> without name",
        ],
    },

    "E130": {
        "explain": (
            "Your <parameter> tag is missing the 'name' attribute. Parameters are "
            "key-value pairs that pass data to your test methods.\n\n"
            "In your Java code, you use @Parameters({\"paramName\"}) to receive "
            "these values. The 'name' here must match what your Java code expects."
        ),
        "sample": '<parameter name="browser" value="chrome"/>',
        "mistakes": [
            "<parameter value='chrome'/> (missing name)",
            "<parameter> without any attributes",
        ],
    },

    "E131": {
        "explain": (
            "Your <parameter> tag is missing the 'value' attribute. Every parameter "
            "needs both a name AND a value.\n\n"
            "The value is what gets passed to your test method at runtime."
        ),
        "sample": '<parameter name="browser" value="chrome"/>',
        "mistakes": [
            '<parameter name="browser"/> (missing value)',
        ],
    },

    "E132": {
        "explain": (
            "The same parameter name appears more than once in the same scope. "
            "Parameter names must be unique within their parent element.\n\n"
            "If you need different values for the same parameter, define them at "
            "different levels (suite vs test vs class)."
        ),
        "sample": (
            '<!-- Parameters at different levels -->\n'
            '<suite name="MySuite">\n'
            '  <parameter name="env" value="staging"/>  <!-- suite level -->\n'
            '  <test name="Test1">\n'
            '    <parameter name="browser" value="chrome"/>  <!-- test level -->\n'
            '    ...\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Defining the same parameter twice in one <test> block",
            "Copy-pasting parameters without removing duplicates",
        ],
    },

    "E160": {
        "explain": (
            "The same class appears more than once in a <test> block. This means "
            "the class's tests would run twice, which is usually unintentional.\n\n"
            "If you need to run the same class with different configurations, "
            "put them in separate <test> blocks with different parameters."
        ),
        "sample": (
            '<test name="MyTest">\n'
            '  <classes>\n'
            '    <class name="com.example.LoginTest"/>  <!-- only once! -->\n'
            '    <class name="com.example.SignupTest"/>\n'
            '  </classes>\n'
            '</test>'
        ),
        "mistakes": [
            "Listing the same class twice in <classes>",
            "Copy-paste without cleanup",
        ],
    },

    "E161": {
        "explain": (
            "The same method is included more than once in the <methods> block. "
            "TestNG will only run it once anyway, so the duplicate is unnecessary.\n\n"
            "Remove the extra <include> to keep your XML clean."
        ),
        "sample": (
            '<methods>\n'
            '  <include name="testLogin"/>  <!-- only once! -->\n'
            '  <include name="testLogout"/>\n'
            '</methods>'
        ),
        "mistakes": [
            "Including the same method twice",
        ],
    },

    "E170": {
        "explain": (
            "Spaces are NOT allowed in Java class names or method names. "
            "If you see spaces, it's likely a copy-paste error or accidental keypress.\n\n"
            "Note: Spaces ARE allowed in <test> and <suite> names — just not in "
            "<class> names or <include>/<exclude> method names."
        ),
        "sample": (
            '<!-- CORRECT: No spaces in class/method names -->\n'
            '<class name="com.example.tests.LoginTest"/>\n'
            '<include name="testValidLogin"/>\n\n'
            '<!-- Spaces OK in test/suite names -->\n'
            '<test name="Login Tests - Chrome">'
        ),
        "mistakes": [
            "Accidental spaces in class name: 'com.example. LoginTest'",
            "Trailing/leading spaces: ' testLogin '",
            "Spaces in method name from copy-paste",
        ],
    },

    "E145": {
        "explain": (
            "You placed <listeners> in an invalid location. The <listeners> block "
            "must be a direct child of <suite>.\n\n"
            "Listeners are classes that receive TestNG events (like test start, "
            "test pass/fail) and can perform actions like taking screenshots, "
            "logging, or generating custom reports."
        ),
        "sample": (
            '<suite name="MySuite">\n'
            '  <listeners>\n'
            '    <listener class-name="com.example.TestListener"/>\n'
            '    <listener class-name="com.example.ReportListener"/>\n'
            '  </listeners>\n'
            '  <test name="MyTest">...</test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Putting <listeners> inside a <test> block instead of directly under <suite>",
            "Putting <listeners> inside <classes> or <methods>",
        ],
    },

    "E184": {
        "explain": (
            "A boolean attribute has an invalid value. Boolean attributes in TestNG "
            "XML only accept 'true' or 'false' (lowercase).\n\n"
            "Common boolean attributes: allow-return-values, group-by-instances, "
            "skip-failed-invocation-counts."
        ),
        "sample": (
            '<!-- Boolean attributes use true/false -->\n'
            '<suite name="MySuite" allow-return-values="true">\n'
            '<test name="MyTest" group-by-instances="false">'
        ),
        "mistakes": [
            'Using "yes"/"no" instead of "true"/"false"',
            'Using "1"/"0" instead of "true"/"false"',
            'Using uppercase: "TRUE" or "False"',
        ],
    },

    "E185": {
        "explain": (
            "A numeric attribute has an invalid value. This attribute expects "
            "a number (integer), but you provided something that isn't a valid number."
        ),
        "sample": (
            '<!-- Numeric attributes need integer values -->\n'
            '<suite name="MySuite" thread-count="5" verbose="2">\n'
            '<test name="MyTest" invocation-count="3">'
        ),
        "mistakes": [
            'Using text: thread-count="five"',
            'Using decimal: thread-count="2.5" (must be integer)',
            'Using negative: thread-count="-1"',
        ],
    },

    "E200": {
        "explain": (
            "The XML structure doesn't match what TestNG expects. This usually "
            "means a tag was found in the wrong place.\n\n"
            "TestNG has a specific tag hierarchy:\n"
            "  suite → test → classes → class → methods → include/exclude\n\n"
            "Make sure each tag is nested correctly inside its parent."
        ),
        "sample": (
            '<suite name="MySuite">\n'
            '  <test name="MyTest">\n'
            '    <classes>\n'
            '      <class name="com.example.Test">\n'
            '        <methods>\n'
            '          <include name="testMethod"/>\n'
            '        </methods>\n'
            '      </class>\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Nesting tags in the wrong order",
            "Missing an intermediate container tag",
        ],
    },

    "E201": {
        "explain": (
            "A tag was opened but never properly closed. Every opening tag "
            "needs a matching closing tag.\n\n"
            "Examples of matching pairs:\n"
            "  <suite>...</suite>\n"
            "  <test>...</test>\n"
            "  <classes>...</classes>\n\n"
            "Self-closing tags like <class name='...'/> don't need a separate closing tag."
        ),
        "sample": (
            '<!-- All tags properly closed -->\n'
            '<suite name="MySuite">\n'
            '  <test name="MyTest">\n'
            '    <classes>\n'
            '      <class name="com.example.Test"/>  <!-- self-closing -->\n'
            '    </classes>\n'
            '  </test>\n'
            '</suite>'
        ),
        "mistakes": [
            "Forgetting </suite> at the end of the file",
            "Forgetting </test> after a test block",
            "Forgetting </classes> or </methods>",
        ],
    },

    "E400": {
        "explain": (
            "The <groups> configuration is invalid. Groups in TestNG allow you to "
            "categorize test methods and run specific categories.\n\n"
            "A valid <groups> block goes inside <test> and contains <run> with "
            "<include> and/or <exclude> for group names."
        ),
        "sample": (
            '<test name="GroupedTests">\n'
            '  <groups>\n'
            '    <run>\n'
            '      <include name="smoke"/>\n'
            '      <exclude name="slow"/>\n'
            '    </run>\n'
            '  </groups>\n'
            '  <classes>\n'
            '    <class name="com.example.AllTests"/>\n'
            '  </classes>\n'
            '</test>'
        ),
        "mistakes": [
            "Missing the <run> element inside <groups>",
            "Putting <groups> outside of a <test> block",
            "Using invalid group configuration syntax",
        ],
    },

    "E401": {
        "explain": (
            "Your <groups> block is empty — it has no configuration inside. "
            "An empty <groups> block has no effect.\n\n"
            "Either add group include/exclude rules, or remove the empty "
            "<groups> block entirely."
        ),
        "sample": (
            '<groups>\n'
            '  <run>\n'
            '    <include name="regression"/>\n'
            '  </run>\n'
            '</groups>'
        ),
        "mistakes": [
            "Empty <groups></groups> block",
            "Forgetting to add <run> with <include>/<exclude>",
        ],
    },

    # ══════════════════════════════════════════════════════════
    # ATTRIBUTE VALIDATION
    # ══════════════════════════════════════════════════════════

    "E180": {
        "explain": (
            "The 'parallel' attribute controls how TestNG runs tests concurrently. "
            "Only specific values are allowed:\n\n"
            "  • false/none — No parallel execution (default)\n"
            "  • methods — Run test methods in parallel\n"
            "  • tests — Run <test> blocks in parallel\n"
            "  • classes — Run test classes in parallel\n"
            "  • instances — Run test instances in parallel"
        ),
        "sample": (
            '<!-- Run methods in parallel with 5 threads -->\n'
            '<suite name="MySuite" parallel="methods" thread-count="5">\n'
            '  ...\n'
            '</suite>'
        ),
        "mistakes": [
            'parallel="true" (not a valid value, use "methods" etc.)',
            'parallel="parallel" (not a valid value)',
        ],
    },

    "E181": {
        "explain": (
            "The 'thread-count' attribute must be a positive integer. It controls "
            "how many threads TestNG uses for parallel execution.\n\n"
            "Typical values: 2-10 for most projects. Higher values use more CPU."
        ),
        "sample": '<suite name="MySuite" parallel="methods" thread-count="5">',
        "mistakes": [
            'thread-count="abc" (not a number)',
            'thread-count="-1" (must be positive)',
            'thread-count="0" (must be at least 1)',
        ],
    },

    "E182": {
        "explain": (
            "The 'verbose' attribute controls log detail level. "
            "Valid range: 0 (silent) to 10 (maximum detail).\n\n"
            "  • 0 = No output\n"
            "  • 1 = Minimal (default)\n"
            "  • 2-3 = Normal detail\n"
            "  • 10 = Full debug output"
        ),
        "sample": '<suite name="MySuite" verbose="2">',
        "mistakes": [
            'verbose="high" (must be a number)',
            'verbose="99" (max is 10)',
        ],
    },

    "E183": {
        "explain": (
            "The 'preserve-order' attribute must be 'true' or 'false'. "
            "When true, TestNG runs tests in the order they appear in the XML file."
        ),
        "sample": '<test name="OrderedTest" preserve-order="true">',
        "mistakes": [
            'preserve-order="yes" (must be true/false)',
        ],
    },

    # ══════════════════════════════════════════════════════════
    # METADATA / MAVEN ERRORS
    # ══════════════════════════════════════════════════════════

    "E300": {
        "explain": (
            "The class name in your XML was not found in the loaded Maven/JAR metadata. "
            "This means either:\n\n"
            "  1. The class name has a typo (check spelling carefully)\n"
            "  2. The class is in a different package (check the package path)\n"
            "  3. The class exists in a JAR that hasn't been scanned yet\n"
            "  4. The class was removed or renamed in a newer version\n\n"
            "Tip: Check the 'Reference' tab for similar class names from "
            "the scanned JARs."
        ),
        "sample": (
            '<!-- Ensure the FULL package path is correct -->\n'
            '<class name="com.example.api.operation.MyTestClass"/>\n\n'
            '<!-- Common mistake: missing a package segment -->\n'
            '<!-- WRONG: com.example.MyTestClass -->\n'
            '<!-- RIGHT: com.example.api.operation.MyTestClass -->'
        ),
        "mistakes": [
            "Missing intermediate package: com.example.MyClass vs com.example.sub.MyClass",
            "Case mismatch: com.example.myclass vs com.example.MyClass",
            "Old class name after refactoring",
        ],
    },

    "E301": {
        "explain": (
            "The method name was not found in the specified class. This means "
            "the method doesn't exist in the JAR metadata for that class.\n\n"
            "Possible causes:\n"
            "  1. Typo in the method name (check spelling and case)\n"
            "  2. The method was renamed or removed\n"
            "  3. The method is in a parent/superclass (not always detected)\n\n"
            "Tip: Check the 'Reference' tab to see all available methods in the class."
        ),
        "sample": (
            '<class name="com.example.LoginTest">\n'
            '  <methods>\n'
            '    <include name="testValidLogin"/>  <!-- must match exactly -->\n'
            '  </methods>\n'
            '</class>'
        ),
        "mistakes": [
            "Case mismatch: testlogin vs testLogin",
            "Extra/missing prefix: test_login vs testLogin",
            "Method was removed in latest JAR version",
        ],
    },

    "E302": {
        "explain": (
            "The number of <parameter> tags doesn't match what the method expects "
            "based on its Java signature.\n\n"
            "This is a WARNING because:\n"
            "  • Some parameters may have default values in the Java code\n"
            "  • Parameters can be inherited from the parent <test> or <suite> level\n"
            "  • The method may use @Optional annotations for some parameters\n"
            "  • TestNG can inject certain values automatically\n\n"
            "This warning is safe to ignore if your tests run correctly.\n\n"
            "Check the 'Reference' tab to see the method's full parameter list "
            "and determine which parameters might be missing or extra."
        ),
        "sample": (
            '<!-- If method expects 3 params: routerId, vrf, detailed -->\n'
            '<include name="getBgpNeighborTable">\n'
            '  <parameter name="routerId" value="10.0.0.1"/>\n'
            '  <parameter name="vrf" value="0"/>\n'
            '  <parameter name="detailed" value="true"/>\n'
            '</include>'
        ),
        "mistakes": [
            "Forgetting optional parameters",
            "Adding extra parameters not in the method signature",
            "Parameters defined at suite/test level being counted separately",
        ],
    },

    "E303": {
        "explain": (
            "The parameter value doesn't match any of the allowed enum values "
            "from the Java code.\n\n"
            "Java enums are a fixed set of allowed values. Using anything else "
            "will cause a runtime error in your tests.\n\n"
            "Check the 'Reference' tab for the complete list of valid values."
        ),
        "sample": (
            '<!-- Use exactly one of the valid enum values -->\n'
            '<parameter name="protocol" value="BGP"/>  <!-- must match enum -->'
        ),
        "mistakes": [
            "Case mismatch: 'bgp' vs 'BGP'",
            "Typo in enum value",
            "Using a value from a different enum type",
        ],
    },

    "E310": {
        "explain": (
            "A <suite-file> reference points to a file that doesn't exist. "
            "Suite files let you compose multiple suite XMLs together.\n\n"
            "Check that the file path is correct and the file exists relative "
            "to your project directory."
        ),
        "sample": (
            '<suite name="MasterSuite">\n'
            '  <suite-files>\n'
            '    <suite-file path="smoke-tests.xml"/>\n'
            '    <suite-file path="regression-tests.xml"/>\n'
            '  </suite-files>\n'
            '</suite>'
        ),
        "mistakes": [
            "Wrong file path or spelling",
            "File was moved or renamed",
            "Using absolute path when relative is needed",
        ],
    },
}

# Fill in defaults for codes not yet in the knowledge base
_DEFAULT_ENTRY = {
    "explain": "This error indicates an issue with your TestNG XML configuration. "
               "Review the Quick Fix tab for specific guidance.",
    "sample": "",
    "mistakes": [],
}


def get_knowledge(code: str) -> dict:
    """Get knowledge base entry for an error code."""
    return KNOWLEDGE_BASE.get(code, _DEFAULT_ENTRY)


def _safe_type(raw_type: str) -> str:
    """Ensure a type string is human-readable. Strips any JVM artifacts."""
    if not raw_type or raw_type == 'unknown':
        return 'text'
    # If it still contains JVMType or L...;, clean it
    s = raw_type
    if 'JVMType' in s or (s.startswith('L') and s.endswith(';')):
        import re
        m = re.search(r"name='([^']*)'", s)
        if m:
            s = m.group(1).replace('/', '.')
        elif s.startswith('L') and s.endswith(';'):
            s = s[1:-1].replace('/', '.')
    # Simplify well-known types
    simple = {
        'java.lang.String': 'String', 'java.lang.Integer': 'int',
        'java.lang.Long': 'long', 'java.lang.Double': 'double',
        'java.lang.Float': 'float', 'java.lang.Boolean': 'boolean',
        'I': 'int', 'J': 'long', 'D': 'double', 'F': 'float',
        'Z': 'boolean', 'B': 'byte', 'C': 'char', 'S': 'short', 'V': 'void',
    }
    if s in simple:
        return simple[s]
    if '.' in s:
        return s.rsplit('.', 1)[-1]
    return s


def _default_for_type(java_type: str) -> str:
    """Return a sensible default value string for a Java type."""
    t = _safe_type(java_type).lower()
    if 'string' in t:
        return "value"
    elif t in ('int', 'integer', 'short', 'byte'):
        return "0"
    elif t in ('long',):
        return "0"
    elif t in ('boolean',):
        return "true"
    elif t in ('double', 'float'):
        return "0.0"
    elif t in ('char',):
        return "a"
    else:
        return "value"


def get_class_reference(class_name: str, metadata: Optional[dict]) -> Optional[str]:
    """
    Build a beginner-friendly class reference from metadata.
    Shows available methods with clean parameter info — no JVM types.
    """
    if not metadata or class_name not in metadata:
        return None

    cls_meta = metadata[class_name]
    methods = cls_meta.get("methods", {})
    source_jar = cls_meta.get("source_jar", "unknown")

    # Separate test methods from utility methods
    test_methods = {}
    other_methods = {}
    for mname, minfo in sorted(methods.items()):
        # Skip compiler-generated / internal methods
        if mname.startswith('$') or mname.startswith('ajc$') or mname.startswith('lambda$'):
            continue
        if minfo.get("is_test", False):
            test_methods[mname] = minfo
        else:
            other_methods[mname] = minfo

    short_class = class_name.rsplit('.', 1)[-1] if '.' in class_name else class_name
    lines = []
    lines.append(f"Class: {short_class}")
    lines.append(f"Full path: {class_name}")
    lines.append(f"Source JAR: {source_jar}")
    lines.append(f"Total methods: {len(test_methods) + len(other_methods)}")
    lines.append("")

    def _format_method_list(method_dict, header):
        if not method_dict:
            return
        lines.append(header)
        lines.append("-" * 50)
        for mname, minfo in method_dict.items():
            params = minfo.get("parameters", [])
            annotations = minfo.get("annotations", [])
            ann_str = ""
            if annotations:
                ann_str = " ".join(f"@{a}" for a in annotations if a)
                ann_str = f"  [{ann_str}]"
            if params:
                param_parts = []
                for i, p in enumerate(params):
                    ptype = _safe_type(p.get("type", "text"))
                    pname = p.get("name", f"arg{i}")
                    param_parts.append(f"{pname} ({ptype})")
                lines.append(f"  {mname}")
                lines.append(f"    Parameters: {', '.join(param_parts)}{ann_str}")
            else:
                lines.append(f"  {mname}  (no parameters){ann_str}")
            lines.append("")

    _format_method_list(test_methods, "Test Methods (usable in <include>):")
    _format_method_list(other_methods, "Other Methods:")

    return "\n".join(lines)


def get_method_reference(class_name: str, method_name: str,
                         metadata: Optional[dict]) -> Optional[str]:
    """
    Build a beginner-friendly method reference.
    Shows parameters in plain language and suggested XML — no JVM types.
    """
    if not metadata or class_name not in metadata:
        return None

    cls_meta = metadata[class_name]
    methods = cls_meta.get("methods", {})

    if method_name not in methods:
        return None

    minfo = methods[method_name]
    params = minfo.get("parameters", [])
    annotations = minfo.get("annotations", [])
    is_test = minfo.get("is_test", False)

    lines = []
    lines.append(f"Method: {method_name}")
    short_class = class_name.rsplit('.', 1)[-1] if '.' in class_name else class_name
    lines.append(f"Class:  {short_class} ({class_name})")
    if annotations:
        lines.append(f"Tags:   {', '.join('@' + a for a in annotations if a)}")
    if is_test:
        lines.append("Type:   Test method (can be used in <include>)")
    lines.append(f"Accepts {len(params)} parameter(s)")
    lines.append("")

    if params:
        lines.append("Parameters this method expects:")
        lines.append("-" * 50)
        for i, p in enumerate(params):
            ptype = _safe_type(p.get("type", "text"))
            pname = p.get("name", f"param{i+1}")
            example = _default_for_type(ptype)
            lines.append(f"  {i+1}. {pname}")
            lines.append(f"     Type: {ptype}    Example value: \"{example}\"")
        lines.append("")

    lines.append("Suggested XML:")
    lines.append("-" * 50)
    lines.append(f'<include name="{method_name}">')
    for i, p in enumerate(params):
        pname = p.get("name", f"param{i+1}")
        ptype = p.get("type", "String")
        default = _default_for_type(ptype)
        lines.append(f'  <parameter name="{pname}" value="{default}"/>')
    lines.append("</include>")

    return "\n".join(lines)


def get_missing_params_info(class_name: str, method_name: str,
                            provided_count: int,
                            metadata: Optional[dict]) -> Optional[str]:
    """
    For E302: show which parameters are present vs missing, beginner-friendly.
    """
    if not metadata or class_name not in metadata:
        return None

    cls_meta = metadata[class_name]
    methods = cls_meta.get("methods", {})

    if method_name not in methods:
        return None

    minfo = methods[method_name]
    params = minfo.get("parameters", [])
    expected = len(params)

    lines = []
    lines.append(f"Method: {method_name}")
    lines.append(f"Parameters expected: {expected}")
    lines.append(f"Parameters in XML:   {provided_count}")
    lines.append("")

    if provided_count < expected:
        missing = expected - provided_count
        lines.append(f"You may be missing {missing} parameter(s).")
        lines.append("")
        lines.append("Parameter checklist:")
        lines.append("-" * 50)
        for i, p in enumerate(params):
            pname = p.get("name", f"param{i+1}")
            ptype = _safe_type(p.get("type", "text"))
            if i < provided_count:
                lines.append(f"  \u2705 {pname} ({ptype}) — provided")
            else:
                example = _default_for_type(ptype)
                lines.append(f"  \u274c {pname} ({ptype}) — MISSING  (example: \"{example}\")")

        lines.append("")
        lines.append("Add these to your XML:")
        lines.append("-" * 50)
        for i in range(provided_count, expected):
            p = params[i]
            pname = p.get("name", f"param{i+1}")
            ptype = p.get("type", "String")
            default = _default_for_type(ptype)
            lines.append(f'<parameter name="{pname}" value="{default}"/>')

        lines.append("")
        lines.append("Note: Some parameters may be optional (@Optional in Java).")
        lines.append("If the tests run fine without them, this warning is safe to ignore.")
    else:
        extra = provided_count - expected
        lines.append(f"You have {extra} extra parameter(s) beyond what the method expects.")
        lines.append("")
        lines.append("The method only accepts these parameters:")
        lines.append("-" * 50)
        for i, p in enumerate(params):
            pname = p.get("name", f"param{i+1}")
            ptype = _safe_type(p.get("type", "text"))
            lines.append(f"  {i+1}. {pname} ({ptype})")
        lines.append("")
        lines.append("Remove the extra <parameter> tags, or check if they belong")
        lines.append("at the <test> or <suite> level instead.")

    return "\n".join(lines)
