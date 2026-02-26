#!/usr/bin/env python3
"""
TestNG Validator Pro v9.5 - "Tutorial Edition"
Base: v9.0 (Stable)
Changes:
✓ UPGRADE: "Tutorial-Style" Fixes (Detailed, step-by-step instructions).
✓ UPGRADE: Error objects now capture the actual 'line_content' for better context.
✓ UI: Fix panel uses rich formatting (Headers, Steps, Code).
✓ RETAINED: All core logic (Pre-Flight, Safe Suite, Whitespace Rules) matches v9.0.
"""

import os, re, threading, json, difflib, csv
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple
from datetime import datetime
import xml.sax
from xml.sax.handler import ContentHandler
from xml.dom import minidom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Modern UI imports
try:
    import customtkinter as ctk
    from PIL import Image, ImageTk
    import darkdetect
    HAS_MODERN_UI = True
    # Set appearance mode
    ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
except ImportError:
    HAS_MODERN_UI = False
    print("⚠️ Modern UI not available. Install: pip install customtkinter Pillow darkdetect")

# Syntax highlighting
try:
    from pygments import lex
    from pygments.lexers import XmlLexer
    from pygments.token import Token
    HAS_SYNTAX_HIGHLIGHT = True
except ImportError:
    HAS_SYNTAX_HIGHLIGHT = False

# ==================== DATA STRUCTURES ====================

@dataclass
class ValidationError:
    code: str
    message: str
    line: Optional[int]
    col: Optional[int]
    severity: str = "ERROR"
    context_data: Optional[str] = None
    line_content: Optional[str] = None # Added to show user's bad code
    auto_fixable: bool = False
    suggestion: Optional[str] = None
    fix_action: Optional[str] = None  # Describes what the auto-fix will do

CODE_META = {
    # Structural
    "E100": ("XML Syntax Error", "ERROR"), 
    "E101": ("Suite missing name", "ERROR"),
    "E102": ("Multiple <suite> tags", "ERROR"), 
    "E103": ("Test missing name", "ERROR"),
    "E104": ("Duplicate test name", "ERROR"), 
    "E105": ("Missing <suite>", "ERROR"),
    "E106": ("Empty suite", "WARNING"),
    "E107": ("Empty <classes> block", "WARNING"),
    "E108": ("Empty <methods> block", "WARNING"),
    "E109": ("Empty <packages> block", "WARNING"),
    "E110": ("<classes> outside <test>", "ERROR"),
    "E111": ("<class> outside <classes>", "ERROR"), 
    "E112": ("Class missing name", "ERROR"),
    "E113": ("<packages> outside <test>", "ERROR"),
    "E114": ("Cannot mix <packages> and <classes>", "ERROR"),
    "E115": ("<package> outside <packages>", "ERROR"),
    "E116": ("Package missing name", "ERROR"),
    "E117": ("Invalid package name format", "ERROR"),
    "E120": ("<methods> outside <class>", "ERROR"), 
    "E121": ("<include> misplaced", "ERROR"),
    "E122": ("Include missing name", "ERROR"),
    "E123": ("<exclude> misplaced", "ERROR"),
    "E124": ("Exclude missing name", "ERROR"), 
    "E130": ("Parameter missing 'name' attr", "ERROR"),
    "E131": ("Parameter missing 'value' attr", "ERROR"),
    "E132": ("Duplicate Parameter", "ERROR"),
    "E145": ("<listeners> misplaced", "ERROR"),
    "E160": ("Duplicate class", "WARNING"), 
    "E161": ("Duplicate method", "WARNING"),
    "E170": ("Invalid Space in Name", "ERROR"),
    # Attribute Validation
    "E180": ("Invalid 'parallel' value", "ERROR"),
    "E181": ("Invalid 'thread-count' value", "ERROR"),
    "E182": ("Invalid 'verbose' value", "ERROR"),
    "E183": ("Invalid 'preserve-order' value", "ERROR"),
    "E184": ("Invalid boolean attribute", "ERROR"),
    "E185": ("Invalid numeric attribute", "ERROR"),
    # Structure
    "E200": ("Structure Mismatch", "ERROR"), 
    "E201": ("Unclosed tag", "ERROR"),
    # Metadata
    "E300": ("Class not found in Project", "ERROR"),
    "E301": ("Method not found in Class", "ERROR"),
    "E303": ("Invalid Enum Value", "ERROR"),
    "E310": ("Suite file not found", "ERROR"),
}

# ==================== TUTORIAL FIX GENERATOR ====================

def generate_fix(error: ValidationError, file_lines: List[str] = None) -> Dict:
    ctx = error.context_data or "Unknown"
    line_num = error.line or "?"
    bad_code = error.line_content.strip() if error.line_content else "..."
    msg = error.message
    
    # Build context view (3 lines before/after the error)
    context_view = ""
    if file_lines and error.line and error.line > 0:
        start_line = max(0, error.line - 3)
        end_line = min(len(file_lines), error.line + 3)
        context_lines = []
        for i in range(start_line, end_line):
            line_marker = "→" if i == error.line - 1 else " "
            context_lines.append(f"{line_marker} {i+1:3d} | {file_lines[i].rstrip()}")
        context_view = "\n".join(context_lines)
    
    # Default Template
    fix = {
        "title": f"🔧 Fix: {error.message}",
        "steps": [f"Error at Line {line_num}.", "Review XML structure."],
        "code": "",
        "context": context_view  # Add context to all fixes
    }

    # --- 1. SPACES IN NAMES (E170) ---
    if error.code == "E170":
        fix["title"] = "❌ Fix: Forbidden Spaces"
        fix["steps"] = [
            f"1. **The Issue:** You used spaces in the name '{ctx}'.",
            "2. **The Rule:** TestNG/Java forbids spaces in Class names and Method names.",
            "3. **Note:** Spaces are allowed in <test> names, but NOT in <class> or <include>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Delete the spaces."
        ]
        clean = ctx.replace(" ", "")
        fix["code"] = f'name="{clean}"'

    # --- 2. UNCLOSED TAGS (E201) ---
    elif error.code == "E201":
        tag = error.context_data
        fix["title"] = f"❌ Fix: Unclosed Tag <{tag}>"
        fix["steps"] = [
            f"1. **The Issue:** You opened a <{tag}> tag at Line {line_num} but never closed it.",
            "2. **The Context:** The parser reached the end of the block (or </suite>), but this tag was still open.",
            f"3. **Action:** Add the closing tag `</{tag}>` before the parent block ends."
        ]
        fix["code"] = f"<{tag}>\n  ...\n</{tag}> "

    # --- 3. DUPLICATE TEST NAME (E104) ---
    elif error.code == "E104":
        fix["title"] = "⚠️ Fix: Duplicate Test Name"
        fix["steps"] = [
            f"1. **The Issue:** The test name '{ctx}' is used more than once.",
            "2. **The Rule:** Every <test> tag in a suite MUST have a unique name.",
            "3. **Action:** Rename this test to something unique."
        ]
        fix["code"] = f'<test name="{ctx}_Run2">'

    # --- 4. MISPLACED CLASSES (E110) ---
    elif error.code == "E110":
        fix["title"] = "❌ Fix: Misplaced <classes>"
        fix["steps"] = [
            "1. **The Issue:** You placed `<classes>` directly under `<suite>`.",
            "2. **The Rule:** `<classes>` must ALWAYS be inside a `<test>` container.",
            "3. **Hierarchy:** Suite -> Test -> Classes.",
            "4. **Action:** Wrap this block in a `<test>` tag."
        ]
        fix["code"] = '<test name="MyTest">\n  <classes>\n    ...\n  </classes>\n</test>'

    # --- 5. SYNTAX ERRORS (E100) ---
    elif error.code == "E100":
        fix["title"] = "❌ Fix: XML Syntax Error"
        if "Mismatched" in msg:
            fix["steps"] = [
                "1. **The Issue:** Tag Mismatch.",
                f"2. **Detail:** {msg}",
                "3. **Meaning:** You opened one tag (e.g. <test>) but tried to close a different one (e.g. </suite>).",
                "4. **Action:** Ensure your closing tag matches the currently open tag."
            ]
        elif "Unclosed" in msg:
            fix["steps"] = [
                "1. **The Issue:** Unexpected End of File.",
                f"2. **Detail:** {msg}",
                "3. **Action:** You must close the tag listed above before ending the file."
            ]
        else:
            fix["steps"] = [
                f"1. **Parser Error:** {msg}",
                "2. **Check For:** Missing quotes (`\"`), missing brackets (`>`), or typos."
            ]

    # --- 6. DUPLICATE PARAMETER (E132) ---
    elif error.code == "E132":
        fix["title"] = "⚠️ Fix: Duplicate Parameter"
        fix["steps"] = [
            f"1. **The Issue:** The parameter '{ctx}' is defined twice in this block.",
            "2. **The Rule:** Parameter names must be unique within their scope (suite/test/class).",
            "3. **Action:** Delete one of the duplicates or rename one if they serve different purposes."
        ]

    # --- 7. DUPLICATE CLASS (E160) ---
    elif error.code == "E160":
        fix["title"] = "⚠️ Fix: Duplicate Class"
        fix["steps"] = [
            f"1. **The Issue:** Class '{ctx}' appears twice in this test.",
            "2. **Action:** Merge them into a single <class> block.",
            "3. **Tip:** Move all <include> methods into the first block."
        ]

    # --- 8. EMPTY CLASSES BLOCK (E107) ---
    elif error.code == "E107":
        fix["title"] = "⚠️ Fix: Empty <classes> Block"
        fix["steps"] = [
            "1. **The Issue:** Your <classes> block has no <class> tags inside.",
            "2. **The Rule:** Every <classes> block must contain at least one <class> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add a <class> tag or remove the empty <classes> block."
        ]
        fix["code"] = """<test name="MyTest">
  <classes>
    <class name="com.example.MyTestClass"/>
  </classes>
</test>"""

    # --- 9. EMPTY METHODS BLOCK (E108) ---
    elif error.code == "E108":
        fix["title"] = "⚠️ Fix: Empty <methods> Block"
        fix["steps"] = [
            "1. **The Issue:** Your <methods> block has no <include> tags inside.",
            "2. **The Rule:** Every <methods> block must contain at least one <include> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add <include> tags or remove the <methods> block to run all methods."
        ]
        fix["code"] = """<class name="com.example.MyClass">
  <methods>
    <include name="testMethod1"/>
    <include name="testMethod2"/>
  </methods>
</class>"""

    # --- 10. PARAMETER MISSING VALUE (E131) ---
    elif error.code == "E131":
        fix["title"] = "❌ Fix: Parameter Missing Value"
        fix["steps"] = [
            f"1. **The Issue:** Parameter '{ctx}' is missing the 'value' attribute.",
            "2. **The Rule:** Every <parameter> tag MUST have both 'name' and 'value' attributes.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add value=\"...\" to your parameter tag."
        ]
        fix["code"] = f'<parameter name="{ctx}" value="yourValue"/>'

    # --- 11. PARAMETER MISSING NAME (E130) ---
    elif error.code == "E130":
        fix["title"] = "❌ Fix: Parameter Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <parameter> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <parameter> tag MUST have both 'name' and 'value' attributes.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"paramName\" to your parameter tag."
        ]
        fix["code"] = '<parameter name="paramName" value="paramValue"/>'

    # --- 12. EMPTY PACKAGES BLOCK (E109) ---
    elif error.code == "E109":
        fix["title"] = "⚠️ Fix: Empty <packages> Block"
        fix["steps"] = [
            "1. **The Issue:** Your <packages> block has no <package> tags inside.",
            "2. **The Rule:** Every <packages> block must contain at least one <package> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Either add <package> tags or remove the empty <packages> block."
        ]
        fix["code"] = """<test name="MyTest">
  <packages>
    <package name="com.example.tests.*"/>
  </packages>
</test>"""

    # --- 13. PACKAGES OUTSIDE TEST (E113) ---
    elif error.code == "E113":
        fix["title"] = "❌ Fix: Misplaced <packages>"
        fix["steps"] = [
            "1. **The Issue:** You placed <packages> outside a <test> tag.",
            "2. **The Rule:** <packages> must ALWAYS be inside a <test> container.",
            "3. **Hierarchy:** <suite> → <test> → <packages>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <packages> block in a <test> tag."
        ]
        fix["code"] = """<test name="MyTest">
  <packages>
    <package name="com.example.*"/>
  </packages>
</test>"""

    # --- 14. MIXING CLASSES AND PACKAGES (E114) ---
    elif error.code == "E114":
        fix["title"] = "❌ Fix: Cannot Mix <classes> and <packages>"
        fix["steps"] = [
            "1. **The Issue:** You have both <classes> and <packages> in the same <test>.",
            "2. **The Rule:** TestNG allows EITHER <classes> OR <packages>, not both.",
            "3. **Action:** Choose one approach:",
            "   - Use <classes> to specify individual test classes",
            "   - Use <packages> to run all classes in a package",
            f"4. **Your Code:** `{bad_code}`"
        ]
        fix["code"] = """Option 1 - Use classes:
<test name="MyTest">
  <classes>
    <class name="com.example.Test1"/>
  </classes>
</test>

Option 2 - Use packages:
<test name="MyTest">
  <packages>
    <package name="com.example.*"/>
  </packages>
</test>"""

    # --- 15. PACKAGE OUTSIDE PACKAGES (E115) ---
    elif error.code == "E115":
        fix["title"] = "❌ Fix: Misplaced <package>"
        fix["steps"] = [
            "1. **The Issue:** You placed <package> outside a <packages> container.",
            "2. **The Rule:** <package> must be inside <packages>.",
            "3. **Hierarchy:** <test> → <packages> → <package>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <package> tags in a <packages> block."
        ]

    # --- 16. PACKAGE MISSING NAME (E116) ---
    elif error.code == "E116":
        fix["title"] = "❌ Fix: Package Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <package> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <package> must have a name (e.g., com.example.*).",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"com.example.*\" to your package tag."
        ]
        fix["code"] = '<package name="com.example.tests.*"/>'

    # --- 17. INVALID PACKAGE NAME (E117) ---
    elif error.code == "E117":
        fix["title"] = "❌ Fix: Invalid Package Name Format"
        fix["steps"] = [
            f"1. **The Issue:** Package name '{ctx}' has invalid format.",
            "2. **The Rule:** Package names must follow Java naming:",
            "   - Start with letter or underscore",
            "   - Use dots to separate parts (com.example.tests)",
            "   - Can end with .* for wildcard",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Examples:** com.example.*, org.tests, my_package.tests.*"
        ]
        fix["code"] = '<package name="com.example.tests.*"/>'

    # --- 18. EXCLUDE MISPLACED (E123) ---
    elif error.code == "E123":
        fix["title"] = "❌ Fix: Misplaced <exclude>"
        fix["steps"] = [
            "1. **The Issue:** You placed <exclude> outside a <methods> block.",
            "2. **The Rule:** <exclude> must be inside <methods>, just like <include>.",
            "3. **Hierarchy:** <class> → <methods> → <exclude>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Move <exclude> inside the <methods> block."
        ]
        fix["code"] = """<class name="com.example.MyClass">
  <methods>
    <include name="test1"/>
    <exclude name="test2"/>
  </methods>
</class>"""

    # --- 19. EXCLUDE MISSING NAME (E124) ---
    elif error.code == "E124":
        fix["title"] = "❌ Fix: Exclude Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <exclude> tag is missing the 'name' attribute.",
            "2. **The Rule:** Every <exclude> must specify which method to exclude.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"methodName\" to your exclude tag."
        ]
        fix["code"] = '<exclude name="testMethodToSkip"/>'

    # --- 20. SUITE MISSING NAME (E101) ---
    elif error.code == "E101":
        fix["title"] = "❌ Fix: Suite Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <suite> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every TestNG suite MUST have a name.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"MySuiteName\" to your suite tag."
        ]
        fix["code"] = '<suite name="TestSuite" verbose="1">'

    # --- 21. MULTIPLE SUITES (E102) ---
    elif error.code == "E102":
        fix["title"] = "❌ Fix: Multiple <suite> Tags"
        fix["steps"] = [
            "1. **The Issue:** You have more than one <suite> tag in the file.",
            "2. **The Rule:** A TestNG XML file can only have ONE root <suite> tag.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Remove extra <suite> tags or split into separate files."
        ]
        fix["code"] = """<!-- Correct: Single suite -->
<suite name="MainSuite">
  <test name="Test1">...</test>
  <test name="Test2">...</test>
</suite>"""

    # --- 22. TEST MISSING NAME (E103) ---
    elif error.code == "E103":
        fix["title"] = "❌ Fix: Test Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <test> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <test> tag MUST have a unique name.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"MyTestName\" to your test tag."
        ]
        fix["code"] = '<test name="RegressionTests">'

    # --- 23. MISSING SUITE (E105) ---
    elif error.code == "E105":
        fix["title"] = "❌ Fix: Missing <suite> Tag"
        fix["steps"] = [
            "1. **The Issue:** Your XML file doesn't have a <suite> root tag.",
            "2. **The Rule:** Every TestNG XML must start with <suite> and end with </suite>.",
            "3. **Action:** Wrap your entire configuration in a <suite> tag."
        ]
        fix["code"] = """<suite name="TestSuite">
  <test name="MyTest">
    <classes>
      <class name="com.example.TestClass"/>
    </classes>
  </test>
</suite>"""

    # --- 24. EMPTY SUITE (E106) ---
    elif error.code == "E106":
        fix["title"] = "⚠️ Fix: Empty Suite"
        fix["steps"] = [
            "1. **The Issue:** Your <suite> tag has no <test> tags inside.",
            "2. **The Rule:** A suite must contain at least one <test> block.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add at least one <test> block with test classes."
        ]
        fix["code"] = """<suite name="TestSuite">
  <test name="SmokeTest">
    <classes>
      <class name="com.example.TestClass"/>
    </classes>
  </test>
</suite>"""

    # --- 25. CLASS OUTSIDE CLASSES (E111) ---
    elif error.code == "E111":
        fix["title"] = "❌ Fix: Misplaced <class>"
        fix["steps"] = [
            "1. **The Issue:** You placed <class> outside a <classes> container.",
            "2. **The Rule:** <class> tags must be inside <classes>.",
            "3. **Hierarchy:** <test> → <classes> → <class>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <class> tags in a <classes> block."
        ]
        fix["code"] = """<test name="MyTest">
  <classes>
    <class name="com.example.TestClass"/>
  </classes>
</test>"""

    # --- 26. CLASS MISSING NAME (E112) ---
    elif error.code == "E112":
        fix["title"] = "❌ Fix: Class Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <class> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <class> must specify the fully qualified class name.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"com.example.YourTestClass\" to your class tag."
        ]
        fix["code"] = '<class name="com.example.tests.LoginTest"/>'

    # --- 27. METHODS OUTSIDE CLASS (E120) ---
    elif error.code == "E120":
        fix["title"] = "❌ Fix: Misplaced <methods>"
        fix["steps"] = [
            "1. **The Issue:** You placed <methods> outside a <class> tag.",
            "2. **The Rule:** <methods> must be inside a <class> block.",
            "3. **Hierarchy:** <class> → <methods> → <include>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Move <methods> inside the <class> tag."
        ]
        fix["code"] = """<class name="com.example.TestClass">
  <methods>
    <include name="testMethod1"/>
  </methods>
</class>"""

    # --- 28. INCLUDE MISPLACED (E121) ---
    elif error.code == "E121":
        fix["title"] = "❌ Fix: Misplaced <include>"
        fix["steps"] = [
            "1. **The Issue:** You placed <include> outside a <methods> block.",
            "2. **The Rule:** <include> must be inside <methods>.",
            "3. **Hierarchy:** <class> → <methods> → <include>",
            f"4. **Your Code:** `{bad_code}`",
            "5. **Action:** Wrap your <include> tags in a <methods> block."
        ]
        fix["code"] = """<class name="com.example.TestClass">
  <methods>
    <include name="testLogin"/>
    <include name="testLogout"/>
  </methods>
</class>"""

    # --- 29. INCLUDE MISSING NAME (E122) ---
    elif error.code == "E122":
        fix["title"] = "❌ Fix: Include Missing Name"
        fix["steps"] = [
            "1. **The Issue:** Your <include> tag doesn't have a 'name' attribute.",
            "2. **The Rule:** Every <include> must specify which test method to run.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Add name=\"testMethodName\" to your include tag."
        ]
        fix["code"] = '<include name="testLogin"/>'

    # --- 30. LISTENERS MISPLACED (E145) ---
    elif error.code == "E145":
        fix["title"] = "⚠️ Fix: Misplaced <listeners>"
        fix["steps"] = [
            "1. **The Issue:** <listeners> should be directly under <suite>.",
            "2. **Best Practice:** Place listeners at suite level for global scope.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Move <listeners> to be a direct child of <suite>."
        ]
        fix["code"] = """<suite name="TestSuite">
  <listeners>
    <listener class-name="com.example.MyListener"/>
  </listeners>
  <test name="MyTest">...</test>
</suite>"""

    # --- 31. DUPLICATE METHOD (E161) ---
    elif error.code == "E161":
        fix["title"] = "⚠️ Fix: Duplicate Method"
        fix["steps"] = [
            f"1. **The Issue:** Method '{ctx}' is included multiple times in this class.",
            "2. **The Rule:** Each method should only be included once per <methods> block.",
            "3. **Action:** Remove the duplicate <include> tag.",
            "4. **Note:** TestNG will only run the method once anyway."
        ]

    # --- 32. STRUCTURE MISMATCH (E200) ---
    elif error.code == "E200":
        fix["title"] = "❌ Fix: Structure Mismatch"
        fix["steps"] = [
            f"1. **The Issue:** {msg}",
            "2. **Common Causes:** Closing tag doesn't match opening tag, or tag in wrong location.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Check that opening and closing tags match exactly."
        ]

    # --- 33. INVALID PARALLEL (E180) ---
    elif error.code == "E180":
        fix["title"] = "❌ Fix: Invalid 'parallel' Value"
        fix["steps"] = [
            f"1. **The Issue:** Invalid value '{ctx}' for 'parallel' attribute.",
            "2. **Valid Values:** methods, tests, classes, instances, false",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Use one of the valid parallel modes."
        ]
        fix["code"] = '<suite name="TestSuite" parallel="methods" thread-count="5">'

    # --- 34. INVALID THREAD-COUNT (E181) ---
    elif error.code == "E181":
        fix["title"] = "❌ Fix: Invalid 'thread-count' Value"
        fix["steps"] = [
            f"1. **The Issue:** Invalid value '{ctx}' for 'thread-count' attribute.",
            "2. **The Rule:** thread-count must be a positive integer (1, 2, 3, ...).",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Set thread-count to a positive number."
        ]
        fix["code"] = '<suite name="TestSuite" parallel="methods" thread-count="5">'

    # --- 35. INVALID VERBOSE (E182) ---
    elif error.code == "E182":
        fix["title"] = "❌ Fix: Invalid 'verbose' Value"
        fix["steps"] = [
            f"1. **The Issue:** Invalid value '{ctx}' for 'verbose' attribute.",
            "2. **Valid Values:** 0 (silent) to 10 (maximum detail).",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Use a number between 0 and 10."
        ]
        fix["code"] = '<suite name="TestSuite" verbose="2">'

    # --- 36. METADATA ERRORS ---
    elif error.code == "E300":
        fix["title"] = "❓ Fix: Unknown Class"
        fix["steps"] = [
            f"1. **The Issue:** The class '{ctx}' is not in your project metadata.",
            "2. **Check:** Spelling, Case Sensitivity, and Package Name.",
            f"3. **Suggestion:** {error.suggestion}" if error.suggestion else "3. **Action:** Check your Java source folder."
        ]

    elif error.code == "E301":
        fix["title"] = "❓ Fix: Unknown Method"
        fix["steps"] = [
            f"1. **The Issue:** Method '{ctx}' not found in the class.",
            "2. **Check:** Method name spelling and case sensitivity.",
            f"3. **Suggestion:** {error.suggestion}" if error.suggestion else "3. **Action:** Verify the method exists in your test class."
        ]

    elif error.code == "E303":
        fix["title"] = "❌ Fix: Invalid Enum Value"
        fix["steps"] = [
            f"1. **The Issue:** Invalid value '{ctx}' for this parameter.",
            f"2. **Detail:** {msg}",
            f"3. **Suggestion:** {error.suggestion}" if error.suggestion else "3. **Action:** Use one of the allowed values."
        ]

    elif error.code == "E310":
        fix["title"] = "❌ Fix: Suite File Not Found"
        fix["steps"] = [
            f"1. **The Issue:** The file '{ctx}' referenced in <suite-file> doesn't exist.",
            "2. **Check:** File path, spelling, and relative location.",
            f"3. **Your Code:** `{bad_code}`",
            "4. **Action:** Verify the file exists or correct the path."
        ]

    return fix

# ==================== AUTO-FIX ENGINE ====================

def apply_auto_fix(file_path: str, error: ValidationError, file_lines: List[str]) -> Tuple[bool, str]:
    """
    Attempts to automatically fix the error in the file.
    Returns (success: bool, message: str)
    """
    if not error.line or error.line < 1 or error.line > len(file_lines):
        return False, "Invalid line number"
    
    line_idx = error.line - 1
    original_line = file_lines[line_idx]
    fixed_line = original_line
    
    # E170: Remove spaces from names
    if error.code == "E170" and error.context_data:
        clean_name = error.context_data.replace(" ", "")
        fixed_line = original_line.replace(f'name="{error.context_data}"', f'name="{clean_name}"')
        if fixed_line != original_line:
            file_lines[line_idx] = fixed_line
            return True, f"Removed spaces from '{error.context_data}' → '{clean_name}'"
    
    # E101: Add missing suite name
    elif error.code == "E101":
        if '<suite' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<suite', '<suite name="TestSuite"')
            file_lines[line_idx] = fixed_line
            return True, "Added default suite name 'TestSuite'"
    
    # E103: Add missing test name
    elif error.code == "E103":
        if '<test' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<test', '<test name="Test1"')
            file_lines[line_idx] = fixed_line
            return True, "Added default test name 'Test1'"
    
    # E112: Add missing class name
    elif error.code == "E112":
        if '<class' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<class', '<class name="com.example.TestClass"')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder class name (update with your actual class)"
    
    # E122: Add missing include name
    elif error.code == "E122":
        if '<include' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<include', '<include name="testMethod"')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder method name (update with your actual method)"
    
    # E124: Add missing exclude name
    elif error.code == "E124":
        if '<exclude' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<exclude', '<exclude name="testMethod"')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder method name (update with your actual method)"
    
    # E116: Add missing package name
    elif error.code == "E116":
        if '<package' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<package', '<package name="com.example.*"')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder package name (update with your actual package)"
    
    # E130: Add missing parameter name
    elif error.code == "E130":
        if '<parameter' in original_line and 'name=' not in original_line:
            fixed_line = original_line.replace('<parameter', '<parameter name="paramName"')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder parameter name"
    
    # E131: Add missing parameter value
    elif error.code == "E131":
        if '<parameter' in original_line and 'value=' not in original_line:
            fixed_line = original_line.replace('/>', ' value="paramValue"/>')
            if fixed_line == original_line:
                fixed_line = original_line.replace('>', ' value="paramValue">')
            file_lines[line_idx] = fixed_line
            return True, "Added placeholder parameter value"
    
    # E104: Rename duplicate test
    elif error.code == "E104" and error.context_data:
        if f'name="{error.context_data}"' in original_line:
            new_name = f"{error.context_data}_Copy"
            fixed_line = original_line.replace(f'name="{error.context_data}"', f'name="{new_name}"')
            file_lines[line_idx] = fixed_line
            return True, f"Renamed duplicate test to '{new_name}'"
    
    # E107: Remove empty <classes> block
    elif error.code == "E107":
        if '<classes>' in original_line or '<classes/>' in original_line:
            # Look for closing tag
            for i in range(line_idx, min(line_idx + 5, len(file_lines))):
                if '</classes>' in file_lines[i]:
                    # Remove both opening and closing tags
                    file_lines[line_idx] = ""
                    file_lines[i] = ""
                    return True, "Removed empty <classes> block"
    
    # E108: Remove empty <methods> block
    elif error.code == "E108":
        if '<methods>' in original_line or '<methods/>' in original_line:
            for i in range(line_idx, min(line_idx + 5, len(file_lines))):
                if '</methods>' in file_lines[i]:
                    file_lines[line_idx] = ""
                    file_lines[i] = ""
                    return True, "Removed empty <methods> block"
    
    # E109: Remove empty <packages> block
    elif error.code == "E109":
        if '<packages>' in original_line or '<packages/>' in original_line:
            for i in range(line_idx, min(line_idx + 5, len(file_lines))):
                if '</packages>' in file_lines[i]:
                    file_lines[line_idx] = ""
                    file_lines[i] = ""
                    return True, "Removed empty <packages> block"
    
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

def batch_auto_fix(file_path: str, errors: List[ValidationError]) -> Tuple[int, int, str]:
    """
    Attempts to auto-fix all fixable errors in the file.
    Returns (fixed_count, total_fixable, result_message)
    """
    try:
        with open(file_path, 'r') as f:
            file_lines = f.readlines()
        
        fixable_errors = [e for e in errors if e.code in [
            "E170", "E101", "E103", "E112", "E122", "E124", "E116", 
            "E130", "E131", "E104", "E107", "E108", "E109", 
            "E132", "E160", "E161"
        ]]
        
        if not fixable_errors:
            return 0, 0, "No auto-fixable errors found"
        
        fixed_count = 0
        messages = []
        
        # Sort errors by line number (descending) to avoid line number shifts
        fixable_errors.sort(key=lambda e: e.line or 0, reverse=True)
        
        for error in fixable_errors:
            success, msg = apply_auto_fix(file_path, error, file_lines)
            if success:
                fixed_count += 1
                messages.append(f"Line {error.line}: {msg}")
        
        if fixed_count > 0:
            # Write back to file
            with open(file_path, 'w') as f:
                f.writelines(file_lines)
            
            result = f"✅ Fixed {fixed_count}/{len(fixable_errors)} errors:\n" + "\n".join(messages)
            return fixed_count, len(fixable_errors), result
        else:
            return 0, len(fixable_errors), "No errors could be auto-fixed"
    
    except Exception as e:
        return 0, 0, f"Error during auto-fix: {str(e)}"

# ==================== PRE-FLIGHT SCANNER (REGEX) ====================

def preflight_scan(path: str) -> List[ValidationError]:
    errors = []
    try:
        with open(path) as f:
            lines = f.readlines()
        
        test_map = {}
        for i, line in enumerate(lines, 1):
            # Check Duplicate Test Names
            m_test = re.search(r'<test[^>]+name="([^"]+)"', line)
            if m_test:
                name = m_test.group(1)
                if name in test_map:
                    errors.append(ValidationError("E104", f"Duplicate test: '{name}'", i, 0, "ERROR", name))
                    errors.append(ValidationError("E104", f"Original definition: '{name}'", test_map[name], 0, "ERROR", name))
                else:
                    test_map[name] = i
            
            # Note: Space checks removed from here (handled by Main Parser only) to avoid duplicates
    except:
        pass 
    return errors

# ==================== HYBRID VALIDATOR (MAIN ENGINE) ====================

class HybridValidator(ContentHandler):
    def __init__(self, filename: str, metadata: Optional[Dict] = None):
        super().__init__()
        self.filename = filename
        self.metadata = metadata
        self.base_path = os.path.dirname(os.path.abspath(filename))
        self.locator = None
        self.stack: List[Tuple[str, int]] = []
        self.errors: List[ValidationError] = []
        
        self.seen_suite = 0
        self.test_count = 0
        self.current_test = None
        self.current_class = None
        
        self.test_names: Dict[str, int] = {}
        self.class_names: Dict[str, int] = {} 
        self.method_names: Dict[str, int] = {}
        self.param_names: Set[str] = set()
        
        # Track empty containers for validation
        self.classes_has_children = False
        self.methods_has_children = False
        self.packages_has_children = False
        
        # Track if test has classes or packages (mutually exclusive)
        self.test_has_classes = False
        self.test_has_packages = False

    def setDocumentLocator(self, locator): self.locator = locator
    def _pos(self): return (self.locator.getLineNumber(), self.locator.getColumnNumber()) if self.locator else (0, 0)
    
    def _err(self, code, msg, line, col, ctx=None, sugg=None):
        meta = CODE_META.get(code, (msg, "ERROR"))
        self.errors.append(ValidationError(code, msg, line, col, meta[1], ctx, False, sugg))

    def _get_suggestion(self, name: str, valid) -> Optional[str]:
        matches = difflib.get_close_matches(name, valid, n=3, cutoff=0.6)
        return f"Did you mean: {', '.join(matches)}?" if matches else None

    # Helper: Check spaces (Only for Class/Include)
    def _check_space(self, name, entity_type, line, col):
        if not name: return
        if entity_type in ["class", "include"] and " " in name:
            self._err("E170", f"Space forbidden in {entity_type}: '{name}'", line, col, name)

    def startElement(self, name, attrs):
        line, col = self._pos()
        self.stack.insert(0, (name, line))
        
        # Reset parameter tracking at appropriate scope boundaries
        if name == "suite":
            self.param_names = set()  # Suite-level params
        elif name == "test":
            self.param_names = set()  # Test-level params (new scope)
        elif name == "class":
            self.param_names = set()  # Class-level params (new scope)
        # Note: Do NOT reset on 'include' - params are scoped to class, not include

        if name == "suite":
            self.seen_suite += 1
            if self.seen_suite > 1: self._err("E102", "Multiple suites", line, col)
            if not attrs.get("name"): self._err("E101", "Suite missing name", line, col)
            
            # Validate suite attributes
            parallel = attrs.get("parallel")
            if parallel and parallel not in ["methods", "tests", "classes", "instances", "false", "none"]:
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
                    if v < 0 or v > 10:
                        self._err("E182", f"verbose must be 0-10: '{verbose}'", line, col, verbose)
                except ValueError:
                    self._err("E182", f"verbose must be numeric: '{verbose}'", line, col, verbose)
            
            preserve_order = attrs.get("preserve-order")
            if preserve_order and preserve_order.lower() not in ["true", "false"]:
                self._err("E183", f"preserve-order must be true/false: '{preserve_order}'", line, col, preserve_order)
        
        elif name == "suite-file":
            path = attrs.get("path")
            if path and not os.path.exists(os.path.join(self.base_path, path)):
                self._err("E310", f"File not found: {path}", line, col, path)

        elif name == "test":
            self.test_count += 1
            tname = attrs.get("name")
            self.current_test = tname
            self.class_names = {}
            # Reset test-level tracking
            self.test_has_classes = False
            self.test_has_packages = False
            if not tname:
                self._err("E103", "Test missing name", line, col)
            # Duplicate tests handled by Pre-Flight. Spaces Allowed.

        elif name == "classes":
            if not self._parent("test"): self._err("E110", "<classes> must be inside <test>", line, col)
            # Check for mutual exclusivity with packages
            if self.test_has_packages:
                self._err("E114", "Cannot mix <classes> and <packages> in same <test>", line, col)
            self.test_has_classes = True
            self.classes_has_children = False  # Track if classes block has children

        elif name == "class":
            if not self._parent("classes"): self._err("E111", "<class> must be inside <classes>", line, col)
            self.classes_has_children = True  # Mark that classes has at least one child
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

        elif name == "methods":
            if not self._parent("class"): self._err("E120", "<methods> must be inside <class>", line, col)
            self.methods_has_children = False  # Track if methods block has children

        elif name == "include":
            if not self._parent("methods"): self._err("E121", "<include> must be inside <methods>", line, col)
            self.methods_has_children = True  # Mark that methods has at least one child
            mname = attrs.get("name")
            if not mname:
                self._err("E122", "Include missing name", line, col)
            else:
                self._check_space(mname, "include", line, col)
                if mname in self.method_names:
                    self._err("E161", f"Duplicate method: '{mname}'", line, col, mname)
                else:
                    self.method_names[mname] = line
                
                if self.metadata and self.current_class in self.metadata:
                    valid = self.metadata[self.current_class].get("methods", [])
                    if mname not in valid:
                        sugg = self._get_suggestion(mname, valid)
                        self._err("E301", f"Method not in {self.current_class}: {mname}", line, col, mname, sugg)

        elif name == "parameter":
            pname = attrs.get("name")
            pval = attrs.get("value")
            
            # Validate required attributes
            if not pname:
                self._err("E130", "Parameter missing 'name' attribute", line, col)
            if not pval:
                self._err("E131", "Parameter missing 'value' attribute", line, col, pname or "unknown")
            
            if pname:
                self._check_space(pname, "parameter", line, col)
                if pname in self.param_names:
                     self._err("E132", f"Duplicate parameter: '{pname}'", line, col, pname)
                else:
                    self.param_names.add(pname)

            if self.metadata and pname and pval and self.current_class in self.metadata:
                params = self.metadata[self.current_class].get("parameters", {})
                if pname in params:
                    allowed = params[pname]
                    if isinstance(allowed, list) and pval not in allowed:
                        self._err("E303", f"Invalid Enum '{pname}': {pval}", line, col, pval, f"Valid: {', '.join(allowed)}")

        elif name == "packages":
            if not self._parent("test"): self._err("E113", "<packages> must be inside <test>", line, col)
            # Check for mutual exclusivity with classes
            if self.test_has_classes:
                self._err("E114", "Cannot mix <packages> and <classes> in same <test>", line, col)
            self.test_has_packages = True
            self.packages_has_children = False  # Track if packages block has children
        
        elif name == "package":
            if not self._parent("packages"): self._err("E115", "<package> must be inside <packages>", line, col)
            self.packages_has_children = True  # Mark that packages has at least one child
            pkg_name = attrs.get("name")
            if not pkg_name:
                self._err("E116", "Package missing name", line, col)
            else:
                # Validate package name format (e.g., com.example.* or com.example.tests)
                if not re.match(r'^[a-zA-Z_][\w.]*(\.\*)?$', pkg_name):
                    self._err("E117", f"Invalid package name format: '{pkg_name}'", line, col, pkg_name)
        
        elif name == "exclude":
            if not self._parent("methods"): self._err("E123", "<exclude> must be inside <methods>", line, col)
            self.methods_has_children = True  # Mark that methods has at least one child
            mname = attrs.get("name")
            if not mname:
                self._err("E124", "Exclude missing name", line, col)
            else:
                self._check_space(mname, "exclude", line, col)
        
        elif name == "listeners":
            if not self._parent("suite"): self._err("E145", "<listeners> should be under <suite>", line, col)

    def endElement(self, name):
        line, col = self._pos()
        
        # Check for empty containers before processing closing tag
        if name == "classes":
            if not self.classes_has_children:
                self._err("E107", "Empty <classes> block - no <class> tags found", line, col)
        elif name == "methods":
            if not self.methods_has_children:
                self._err("E108", "Empty <methods> block - no <include> tags found", line, col)
        elif name == "packages":
            if not self.packages_has_children:
                self._err("E109", "Empty <packages> block - no <package> tags found", line, col)
        
        # === MASTER KEY: </suite> ===
        if name == "suite":
            while self.stack:
                tag, ln = self.stack.pop(0)
                if tag == "suite": return 
                self._err("E201", f"Unclosed tag <{tag}> inside suite", line, col, tag)
            return

        tag_in_stack = False
        for i, (tag, _) in enumerate(self.stack):
            if tag == name:
                tag_in_stack = True
                break
        
        if not tag_in_stack:
            self._err("E200", f"Unexpected closing tag </{name}>", line, col, name)
            return

        while self.stack:
            top_tag, top_line = self.stack[0]
            if top_tag == name:
                self.stack.pop(0) 
                return
            else:
                self._err("E201", f"Unclosed tag <{top_tag}> (Opened L{top_line})", line, col, top_tag)
                self.stack.pop(0)

    def endDocument(self):
        for tag, ln in self.stack: self._err("E201", f"<{tag}> unclosed", ln, 0, tag)
        if self.test_count == 0 and self.seen_suite > 0: self._err("E106", "Empty suite", 0, 0)
        if self.seen_suite == 0: self._err("E105", "Missing <suite>", 0, 0)

    def _parent(self, exp): return len(self.stack) >= 2 and self.stack[1][0] == exp

def validate_file_hybrid(path: str, metadata: dict = None) -> List[ValidationError]:
    # 1. Read File Lines (For Context Injection)
    lines = []
    try:
        with open(path) as f: lines = f.readlines()
    except: pass

    # 2. PRE-FLIGHT SCAN (Regex)
    pre_errors = preflight_scan(path)
    
    # 3. MAIN PARSER (SAX)
    v = HybridValidator(path, metadata)
    v.errors.extend(pre_errors)
    
    try:
        parser = xml.sax.make_parser()
        parser.setContentHandler(v)
        parser.parse(path)
    except xml.sax.SAXParseException as e:
        custom_msg = f"Syntax Error: {e.getMessage()}"
        if "mismatched tag" in e.getMessage() and v.stack:
            expected = v.stack[0][0]
            try:
                if e.getLineNumber()-1 < len(lines):
                    match = re.search(r"</(\w+)>", lines[e.getLineNumber()-1])
                    if match:
                        found = match.group(1)
                        if found == "suite":
                            custom_msg = f"Unclosed Tag: <{expected}> was not closed before </suite>"
                        else:
                            custom_msg = f"Mismatched Tag: Expected </{expected}> but found </{found}>"
            except: pass
        v.errors.insert(0, ValidationError("E100", custom_msg, e.getLineNumber(), e.getColumnNumber(), "ERROR", context_data=custom_msg))
    except Exception as e:
        v.errors.insert(0, ValidationError("E000", str(e), 0, 0, "ERROR"))
    
    # 4. Context Injection (Add user's code to error objects)
    for e in v.errors:
        if e.line and e.line > 0 and e.line <= len(lines):
            e.line_content = lines[e.line - 1].strip()

    # Dedup and Sort
    unique_errors = []
    seen = set()
    for e in v.errors:
        key = (e.line, e.code, e.message)
        if key not in seen:
            unique_errors.append(e)
            seen.add(key)
            
    unique_errors.sort(key=lambda x: (x.line or 0))
    return unique_errors

def format_xml_content(content: str) -> str:
    try:
        clean = re.sub(r'>\s+<', '><', content.strip())
        dom = minidom.parseString(clean)
        return '\n'.join([l for l in dom.toprettyxml(indent="  ").splitlines() if l.strip()])
    except Exception:
        return None

def format_xml_file(path):
    try:
        with open(path) as f: orig = f.read()
        formatted = format_xml_content(orig)
        if not formatted: return False, "Syntax Error"
        with open(path + ".bak", 'w') as f: f.write(orig)
        with open(path, 'w') as f: f.write(formatted)
        return True, None
    except Exception as e: return False, str(e)

# ==================== GUI ====================

class ValidatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔍 TestNG Validator Pro v10.0 - Modern Edition")
        try: self.root.state('zoomed')
        except: self.root.attributes('-fullscreen', True)
        
        self.files = {}
        self.metadata = None
        self.maven_metadata = None  # Separate Maven metadata
        self.current_theme = "System"  # Track current theme
        self.colors = {'err': '#d32f2f', 'warn': '#f57c00', 'ok': '#388e3c'}
        self.check_icon = {"on": "☑", "off": "☐"} 
        self._setup_ui()
    
    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=30, font=('Segoe UI', 9))
        
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        file_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_m)
        file_m.add_command(label="Add Files", command=self.add_files)
        file_m.add_command(label="Add Folder", command=self.add_folder)
        file_m.add_separator()
        file_m.add_command(label="Load Metadata (JSON)", command=self.load_metadata)
        file_m.add_separator()
        
        # Theme submenu
        theme_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Theme", menu=theme_m)
        theme_m.add_command(label="☀️ Light Mode", command=lambda: self.change_theme("Light"))
        theme_m.add_command(label="🌙 Dark Mode", command=lambda: self.change_theme("Dark"))
        theme_m.add_command(label="💻 System Default", command=lambda: self.change_theme("System"))
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self.root.quit)
        
        tb = ttk.Frame(self.root)
        tb.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(tb, text="➕ Add", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="📋 Metadata", command=self.load_metadata).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="🔍 Scan Maven JARs", command=self.scan_maven_jars).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="▶️ Validate Selected", command=self.run_validation).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="✨ Format Selected", command=self.format_file_ui).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="📊 Report Selected", command=self.generate_report).pack(side=tk.LEFT, padx=2)
        
        # Theme toggle button
        self.theme_btn = ttk.Button(tb, text="🌓 Theme", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=2)
        ttk.Button(tb, text="🗑️ Clear All", command=self.clear_all).pack(side=tk.RIGHT)
        
        self.meta_lbl = tk.Label(tb, text="⚠️ No Metadata", bg="#ffebee", fg="#c62828", padx=10, relief=tk.RIDGE)
        self.meta_lbl.pack(side=tk.RIGHT, padx=10)
        
        pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left = ttk.Frame(pane)
        pane.add(left, weight=3)
        
        cols = ("check", "file", "status", "errors", "warnings")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        self.tree.heading("check", text="☑", command=self.toggle_all_checks)
        self.tree.heading("file", text="File Name")
        self.tree.heading("status", text="Status")
        self.tree.heading("errors", text="Errors")
        self.tree.heading("warnings", text="Warnings")
        self.tree.column("check", width=40, anchor="center")
        self.tree.column("file", width=350)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("errors", width=70, anchor="center")
        self.tree.column("warnings", width=70, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<<TreeviewSelect>>", self.update_summary)
        
        right = ttk.LabelFrame(pane, text="📋 Summary")
        pane.add(right, weight=1)
        self.summary = scrolledtext.ScrolledText(right, width=35, bg="#f9f9f9", font=('Consolas', 9), wrap="word", state="disabled")
        self.summary.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor="w").pack(fill=tk.X, side=tk.BOTTOM)

    def toggle_theme(self):
        """Toggle between Light, Dark, and System themes"""
        if not HAS_MODERN_UI:
            messagebox.showinfo("Theme Toggle", "Modern UI not available.\nInstall: pip install customtkinter")
            return
        
        themes = ["Light", "Dark", "System"]
        current_idx = themes.index(self.current_theme)
        next_theme = themes[(current_idx + 1) % len(themes)]
        self.change_theme(next_theme)
    
    def change_theme(self, theme):
        """Change the application theme"""
        if not HAS_MODERN_UI:
            return
        
        self.current_theme = theme
        ctk.set_appearance_mode(theme)
        
        # Update theme button text
        theme_icons = {"Light": "☀️", "Dark": "🌙", "System": "💻"}
        self.theme_btn.config(text=f"{theme_icons.get(theme, '🌓')} {theme}")
        
        # Update colors based on theme
        if theme == "Dark":
            self.root.configure(bg="#1e1e1e")
        elif theme == "Light":
            self.root.configure(bg="#ffffff")
        
        self.status.set(f"Theme changed to {theme} mode")
    
    def scan_maven_jars(self):
        """Scan Maven JARs or browse for JAR files/folders"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔍 Maven JAR Scanner")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        # Instructions
        ttk.Label(dialog, text="Scan Maven JARs for Metadata", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        ttk.Label(dialog, text="Choose one of the following options:", font=('Segoe UI', 10)).pack(pady=5)
        
        # Option 1: Browse for JAR file
        frame1 = ttk.LabelFrame(dialog, text="Option 1: Select JAR File", padding=10)
        frame1.pack(fill=tk.X, padx=20, pady=10)
        
        jar_path_var = tk.StringVar()
        ttk.Entry(frame1, textvariable=jar_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame1, text="Browse JAR", command=lambda: self._browse_jar(jar_path_var)).pack(side=tk.LEFT)
        
        # Option 2: Browse for folder containing JARs
        frame2 = ttk.LabelFrame(dialog, text="Option 2: Select Folder with JARs", padding=10)
        frame2.pack(fill=tk.X, padx=20, pady=10)
        
        folder_path_var = tk.StringVar()
        ttk.Entry(frame2, textvariable=folder_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame2, text="Browse Folder", command=lambda: self._browse_folder(folder_path_var)).pack(side=tk.LEFT)
        
        # Option 3: Maven repository (group/artifact)
        frame3 = ttk.LabelFrame(dialog, text="Option 3: Maven Repository (Advanced)", padding=10)
        frame3.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(frame3, text="Group ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        group_id_var = tk.StringVar()
        ttk.Entry(frame3, textvariable=group_id_var, width=40).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(frame3, text="Artifact ID:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        artifact_id_var = tk.StringVar()
        ttk.Entry(frame3, textvariable=artifact_id_var, width=40).grid(row=1, column=1, padx=5, pady=2)
        
        # Scan button
        def start_scan():
            jar_path = jar_path_var.get()
            folder_path = folder_path_var.get()
            group_id = group_id_var.get()
            artifact_id = artifact_id_var.get()
            
            if jar_path:
                self._scan_single_jar(jar_path, dialog)
            elif folder_path:
                self._scan_jar_folder(folder_path, dialog)
            elif group_id and artifact_id:
                self._scan_maven_repo(group_id, artifact_id, dialog)
            else:
                messagebox.showwarning("No Selection", "Please select a JAR, folder, or enter Maven coordinates.")
        
        ttk.Button(dialog, text="🔍 Start Scan", command=start_scan, width=20).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy, width=20).pack()
    
    def _browse_jar(self, var):
        """Browse for a single JAR file"""
        path = filedialog.askopenfilename(
            title="Select JAR File",
            filetypes=[("JAR Files", "*.jar"), ("All Files", "*.*")]
        )
        if path:
            var.set(path)
    
    def _browse_folder(self, var):
        """Browse for a folder containing JARs"""
        path = filedialog.askdirectory(title="Select Folder with JAR Files")
        if path:
            var.set(path)
    
    def _scan_single_jar(self, jar_path, parent_dialog):
        """Scan a single JAR file"""
        if not os.path.exists(jar_path):
            messagebox.showerror("Error", f"JAR file not found: {jar_path}")
            return
        
        try:
            from maven_extractor import MavenMetadataExtractor
            
            self.status.set("Scanning JAR file...")
            parent_dialog.destroy()
            
            extractor = MavenMetadataExtractor()
            metadata = extractor.extract_from_jar(jar_path)
            
            if metadata:
                self.maven_metadata = metadata
                self.meta_lbl.config(
                    text=f"✅ Maven: {len(metadata)} classes from JAR",
                    bg="#e3f2fd", fg="#1565c0"
                )
                messagebox.showinfo("Success", f"Extracted {len(metadata)} classes from JAR")
            else:
                messagebox.showwarning("No Data", "No classes found in JAR")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan JAR:\n{str(e)}")
        finally:
            self.status.set("Ready")
    
    def _scan_jar_folder(self, folder_path, parent_dialog):
        """Scan all JARs in a folder"""
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", f"Folder not found: {folder_path}")
            return
        
        try:
            from maven_extractor import MavenMetadataExtractor
            import glob
            
            jar_files = glob.glob(os.path.join(folder_path, "*.jar"))
            if not jar_files:
                messagebox.showwarning("No JARs", f"No JAR files found in: {folder_path}")
                return
            
            self.status.set(f"Scanning {len(jar_files)} JAR files...")
            parent_dialog.destroy()
            
            extractor = MavenMetadataExtractor()
            all_metadata = {}
            
            for jar in jar_files:
                metadata = extractor.extract_from_jar(jar)
                all_metadata.update(metadata)
            
            if all_metadata:
                self.maven_metadata = all_metadata
                self.meta_lbl.config(
                    text=f"✅ Maven: {len(all_metadata)} classes from {len(jar_files)} JARs",
                    bg="#e3f2fd", fg="#1565c0"
                )
                messagebox.showinfo("Success", f"Extracted {len(all_metadata)} classes from {len(jar_files)} JARs")
            else:
                messagebox.showwarning("No Data", "No classes found in JARs")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan folder:\n{str(e)}")
        finally:
            self.status.set("Ready")
    
    def _scan_maven_repo(self, group_id, artifact_id, parent_dialog):
        """Scan Maven repository for specific artifact"""
        try:
            from maven_extractor import MavenMetadataExtractor
            
            self.status.set(f"Scanning Maven repo for {group_id}:{artifact_id}...")
            parent_dialog.destroy()
            
            extractor = MavenMetadataExtractor()
            metadata = extractor.scan_project_jars([group_id], [artifact_id])
            
            if metadata:
                self.maven_metadata = metadata
                self.meta_lbl.config(
                    text=f"✅ Maven: {len(metadata)} classes",
                    bg="#e3f2fd", fg="#1565c0"
                )
                
                # Save to file
                output_file = "maven_metadata.json"
                extractor.save_metadata(output_file)
                
                messagebox.showinfo("Success", 
                    f"Extracted {len(metadata)} classes\nSaved to: {output_file}")
            else:
                messagebox.showwarning("No Data", 
                    f"No JARs found for {group_id}:{artifact_id}\n\n"
                    "Check that the artifact exists in ~/.m2/repository")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan Maven repo:\n{str(e)}")
        finally:
            self.status.set("Ready")

    def load_metadata(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            with open(path) as f: self.metadata = json.load(f)
            self.meta_lbl.config(text=f"✅ Meta: {len(self.metadata)} classes", bg="#e8f5e9", fg="#2e7d32")
        except Exception as e: messagebox.showerror("Error", str(e))

    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("XML", "*.xml"), ("All", "*.*")])
        for p in paths:
            if p not in self.files:
                self.files[p] = {"status": "Pending", "errors": [], "err_cnt": 0, "warn_cnt": 0, "checked": True}
                self.tree.insert("", "end", iid=p, values=(self.check_icon["on"], os.path.basename(p), "⏳ Pending", "-", "-"))

    def add_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        cnt = 0
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith('.xml'):
                    p = os.path.join(root, f)
                    if p not in self.files:
                        self.files[p] = {"status": "Pending", "errors": [], "err_cnt": 0, "warn_cnt": 0, "checked": True}
                        self.tree.insert("", "end", iid=p, values=(self.check_icon["on"], os.path.basename(p), "⏳ Pending", "-", "-"))
                        cnt += 1
        if cnt: self.status.set(f"Added {cnt} files.")

    def on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) == "#1":
            row_id = self.tree.identify_row(event.y)
            self.toggle_check(row_id)
            return "break"

    def toggle_check(self, item_id):
        current = self.tree.item(item_id, "values")
        new_val = self.check_icon["off"] if current[0] == self.check_icon["on"] else self.check_icon["on"]
        self.tree.item(item_id, values=(new_val, *current[1:]))
        self.files[item_id]["checked"] = (new_val == self.check_icon["on"])

    def toggle_all_checks(self):
        if not self.files: return
        first_id = self.tree.get_children()[0]
        target = not self.files[first_id]["checked"]
        icon = self.check_icon["on"] if target else self.check_icon["off"]
        for item_id in self.tree.get_children():
            self.files[item_id]["checked"] = target
            vals = self.tree.item(item_id, "values")
            self.tree.item(item_id, values=(icon, *vals[1:]))

    def get_target_files(self): return [p for p, d in self.files.items() if d["checked"]]

    def run_validation(self):
        targets = self.get_target_files()
        if not targets: return messagebox.showwarning("Warning", "No files selected.")
        self.status.set(f"Validating {len(targets)} files...")
        threading.Thread(target=self._validate_task, args=(targets,), daemon=True).start()

    def _validate_task(self, targets):
        for path in targets:
            try:
                errs = validate_file_hybrid(path, self.metadata)
                e_cnt = sum(1 for e in errs if e.severity == "ERROR")
                w_cnt = sum(1 for e in errs if e.severity == "WARNING")
                stat = "✅ PASS" if not errs else ("⚠️ WARN" if e_cnt == 0 else "❌ FAIL")
            except Exception as e:
                errs = [ValidationError("E000", f"Crash: {str(e)}", 0, 0)]
                e_cnt, w_cnt = 1, 0
                stat = "❌ CRASH"
            
            self.files[path].update({"status": stat, "errors": errs, "err_cnt": e_cnt, "warn_cnt": w_cnt})
            self.root.after(0, lambda p=path, s=stat, e=e_cnt, w=w_cnt: self._update_tree_row(p, s, e, w))
        self.root.after(0, self.status.set, "Done.")

    def _update_tree_row(self, path, stat, errs, warns):
        if self.tree.exists(path):
            current = self.tree.item(path, "values")
            self.tree.item(path, values=(current[0], current[1], stat, errs or "-", warns or "-"))
            sel = self.tree.selection()
            if sel and sel[0] == path: self.update_summary(None)

    def format_file_ui(self):
        targets = self.get_target_files()
        if not targets: return messagebox.showwarning("Warning", "No files selected.")
        count = 0
        for p in targets:
            ok, _ = format_xml_file(p)
            if ok: count += 1
        messagebox.showinfo("Done", f"Formatted {count} files.")

    def generate_report(self):
        targets = self.get_target_files()
        if not targets: return messagebox.showwarning("Warning", "No files selected.")
        path = filedialog.asksaveasfilename(defaultextension=".html")
        if not path: return
        html = "<html><head><style>body{font-family:sans-serif} .fail{color:red} .pass{color:green}</style></head><body><h1>TestNG Report</h1><table border='1' cellpadding='5'><tr><th>File</th><th>Status</th><th>Errors</th></tr>"
        for fp in targets:
            d = self.files[fp]
            cls = "fail" if "FAIL" in d['status'] else "pass"
            html += f"<tr><td>{os.path.basename(fp)}</td><td class='{cls}'>{d['status']}</td><td>{d['err_cnt']}</td></tr>"
        html += "</table></body></html>"
        with open(path, 'w') as f: f.write(html)
        messagebox.showinfo("Success", "Report Generated")

    def export_csv(self):
        targets = self.get_target_files()
        if not targets: return
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["File", "Line", "Code", "Severity", "Message"])
            for fp in targets:
                for e in self.files[fp]['errors']: writer.writerow([os.path.basename(fp), e.line, e.code, e.severity, e.message])
        messagebox.showinfo("Success", "Exported CSV")

    def update_summary(self, event):
        sel = self.tree.selection()
        if not sel: return
        data = self.files[sel[0]]
        self.summary.config(state="normal")
        self.summary.delete("1.0", tk.END)
        txt = f"{os.path.basename(sel[0])}\nStatus: {data['status']}\n\n"
        if data['errors']:
            for e in data['errors'][:10]:
                meta = CODE_META.get(e.code, (e.message, ""))[0]
                txt += f"[{e.code}] {meta} (L{e.line})\n"
        self.summary.insert("1.0", txt)
        self.summary.config(state="disabled")

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) != "#1":
            sel = self.tree.selection()
            if sel: self.open_details(sel[0])

    def open_details(self, path):
        win = tk.Toplevel(self.root)
        win.title(f"Edit: {os.path.basename(path)}")
        try: win.state('zoomed')
        except: win.attributes('-fullscreen', True)
        
        pane = ttk.PanedWindow(win, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True)
        upper = ttk.PanedWindow(pane, orient=tk.HORIZONTAL)
        pane.add(upper, weight=3)
        
        err_fr = ttk.LabelFrame(upper, text="Issues")
        upper.add(err_fr, weight=1)
        err_list = tk.Listbox(err_fr, font=('Consolas', 9))
        err_list.pack(fill=tk.BOTH, expand=True)
        
        code_fr = ttk.LabelFrame(upper, text="Editor")
        upper.add(code_fr, weight=2)
        tb = ttk.Frame(code_fr)
        tb.pack(fill=tk.X)
        stat_lbl = tk.Label(tb, text="Unsaved", fg="gray")
        stat_lbl.pack(side=tk.RIGHT, padx=5)
        ttk.Button(tb, text="💾 Save, Format & Validate", 
                   command=lambda: self.save_and_revalidate(path, code_txt, err_list, stat_lbl)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="🔧 Auto-Fix This Error", 
                   command=lambda: self.auto_fix_single(path, err_list, code_txt, stat_lbl)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="✨ Auto-Fix All", 
                   command=lambda: self.auto_fix_batch(path, err_list, code_txt, stat_lbl)).pack(side=tk.LEFT, padx=2)
        
        code_cont = ttk.Frame(code_fr)
        code_cont.pack(fill=tk.BOTH, expand=True)
        gutter = tk.Text(code_cont, width=4, bg="#eee", state="disabled", font=('Consolas', 9))
        gutter.pack(side=tk.LEFT, fill=tk.Y)
        code_txt = tk.Text(code_cont, wrap="none", font=('Consolas', 9), undo=True)
        code_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vs = ttk.Scrollbar(code_cont, command=lambda *a: (code_txt.yview(*a), gutter.yview(*a)))
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        code_txt.config(yscrollcommand=lambda *a: (vs.set(*a), gutter.yview_moveto(a[0])))
        
        # Read file lines for context-aware fixes
        file_lines = []
        try:
            with open(path) as f: 
                content = f.read()
                file_lines = content.splitlines()
            code_txt.insert("1.0", content)
            self._update_gutter(code_txt, gutter)
        except: pass
        
        code_txt.tag_config("err_line", background="#ffe0e0")
        fix_fr = ttk.LabelFrame(pane, text="Detailed Fix Suggestions")
        pane.add(fix_fr, weight=1)
        fix_txt = scrolledtext.ScrolledText(fix_fr, bg="#f5f5f5", font=('Segoe UI', 10))
        fix_txt.pack(fill=tk.BOTH, expand=True)

        self._populate_errors(err_list, self.files[path]["errors"])

        def on_select(evt):
            sel_idx = err_list.curselection()
            if not sel_idx: return
            err = self.files[path]["errors"][sel_idx[0]]
            code_txt.tag_remove("err_line", "1.0", "end")
            if err.line:
                code_txt.tag_add("err_line", f"{err.line}.0", f"{err.line}.end")
                code_txt.see(f"{err.line}.0")
            
            # --- RENDER RICH TEXT TUTORIAL WITH CONTEXT ---
            fix = generate_fix(err, file_lines)
            fix_txt.config(state="normal")
            fix_txt.delete("1.0", "end")
            
            # Title
            fix_txt.insert("end", f"{fix['title']}\n\n", "header")
            fix_txt.tag_config("header", font=('Segoe UI', 11, 'bold'), foreground="#333")
            
            # Context (show user's actual code with surrounding lines)
            if fix.get('context'):
                fix_txt.insert("end", "📍 Your Code (Line Context):\n", "bold")
                fix_txt.tag_config("bold", font=('Segoe UI', 9, 'bold'))
                fix_txt.insert("end", fix['context'] + "\n\n", "context")
                fix_txt.tag_config("context", font=('Consolas', 9), background="#fff9e6", lmargin1=10)
            
            # Steps
            for step in fix['steps']:
                fix_txt.insert("end", f"{step}\n")
            
            # Code Snippet
            if fix['code']:
                fix_txt.insert("end", "\n💡 Example Fix:\n", "bold")
                fix_txt.insert("end", fix['code'], "code")
                fix_txt.tag_config("code", font=('Consolas', 10), background="#e0f7fa", lmargin1=10)
            
            fix_txt.config(state="disabled")

        err_list.bind("<<ListboxSelect>>", on_select)
        code_txt.bind("<Key>", lambda e: stat_lbl.config(text="• Modified", fg="blue"))

    def _update_gutter(self, txt, gutter):
        lines = int(txt.index("end-1c").split('.')[0])
        gutter.config(state="normal")
        gutter.delete("1.0", tk.END)
        gutter.insert("1.0", "\n".join(str(i) for i in range(1, lines+1)))
        gutter.config(state="disabled")

    def _populate_errors(self, listbox, errors):
        listbox.delete(0, tk.END)
        for e in errors:
            icon = "❌" if e.severity == "ERROR" else "⚠️"
            listbox.insert(tk.END, f"{icon} L{e.line} [{e.code}] {e.message}")
            listbox.itemconfig(tk.END, fg=self.colors['err'] if e.severity=="ERROR" else self.colors['warn'])

    def save_and_revalidate(self, path, editor, err_list, stat_lbl):
        content = editor.get("1.0", "end-1c")
        try:
            formatted_content = format_xml_content(content)
            if formatted_content:
                with open(path, 'w') as f: f.write(formatted_content)
                editor.delete("1.0", tk.END)
                editor.insert("1.0", formatted_content)
                fmt_msg = "Saved & Formatted"
            else:
                with open(path, 'w') as f: f.write(content)
                fmt_msg = "Saved (Syntax Error)"
            
            errs = validate_file_hybrid(path, self.metadata)
            e_cnt = sum(1 for e in errs if e.severity == "ERROR")
            w_cnt = sum(1 for e in errs if e.severity == "WARNING")
            stat = "✅ PASS" if not errs else ("⚠️ WARN" if e_cnt == 0 else "❌ FAIL")
            
            self.files[path].update({"status": stat, "errors": errs, "err_cnt": e_cnt, "warn_cnt": w_cnt})
            self._update_tree_row(path, stat, e_cnt, w_cnt)
            self._populate_errors(err_list, errs)
            self._update_gutter(editor, editor.master.winfo_children()[0])
            stat_lbl.config(text=f"{fmt_msg}. {len(errs)} Issues", fg="green" if not errs else "red")
        except Exception as e: messagebox.showerror("Error", str(e))

    def auto_fix_single(self, path, err_list, editor, stat_lbl):
        """Auto-fix the currently selected error"""
        # Get parent window for proper dialog anchoring
        parent_window = editor.winfo_toplevel()
        
        sel_idx = err_list.curselection()
        if not sel_idx:
            messagebox.showwarning("No Selection", "Please select an error to auto-fix.", parent=parent_window)
            return
        
        error = self.files[path]["errors"][sel_idx[0]]
        
        # Check if error is auto-fixable
        fixable_codes = ["E170", "E101", "E103", "E112", "E122", "E124", "E116", 
                        "E130", "E131", "E104", "E107", "E108", "E109", 
                        "E132", "E160", "E161"]
        
        if error.code not in fixable_codes:
            messagebox.showinfo("Not Auto-Fixable", 
                              f"Error {error.code} cannot be automatically fixed.\nPlease fix it manually using the tutorial guidance.",
                              parent=parent_window)
            return
        
        try:
            with open(path, 'r') as f:
                file_lines = f.readlines()
            
            success, msg = apply_auto_fix(path, error, file_lines)
            
            if success:
                # Write back to file
                with open(path, 'w') as f:
                    f.writelines(file_lines)
                
                # Reload content in editor
                editor.delete("1.0", tk.END)
                editor.insert("1.0", "".join(file_lines))
                
                # Re-validate
                self.save_and_revalidate(path, editor, err_list, stat_lbl)
                
                # Keep window in focus
                parent_window.lift()
                parent_window.focus_force()
                messagebox.showinfo("Success", f"✅ Auto-Fixed!\n\n{msg}", parent=parent_window)
            else:
                messagebox.showwarning("Cannot Fix", msg, parent=parent_window)
        
        except Exception as e:
            messagebox.showerror("Error", f"Auto-fix failed: {str(e)}", parent=parent_window)
    
    def auto_fix_batch(self, path, err_list, editor, stat_lbl):
        """Auto-fix all fixable errors in the file"""
        # Get parent window for proper dialog anchoring
        parent_window = editor.winfo_toplevel()
        
        errors = self.files[path]["errors"]
        
        if not errors:
            messagebox.showinfo("No Errors", "No errors to fix!", parent=parent_window)
            return
        
        result = messagebox.askyesno("Batch Auto-Fix", 
                                     f"This will attempt to automatically fix all fixable errors.\n\n"
                                     f"Total errors: {len(errors)}\n"
                                     f"Estimated fixable: {sum(1 for e in errors if e.code in ['E170', 'E101', 'E103', 'E112', 'E122', 'E124', 'E116', 'E130', 'E131', 'E104', 'E107', 'E108', 'E109', 'E132', 'E160', 'E161'])}\n\n"
                                     f"Continue?",
                                     parent=parent_window)
        
        if not result:
            return
        
        try:
            fixed_count, total_fixable, result_msg = batch_auto_fix(path, errors)
            
            if fixed_count > 0:
                # Reload content in editor
                with open(path, 'r') as f:
                    content = f.read()
                editor.delete("1.0", tk.END)
                editor.insert("1.0", content)
                
                # Re-validate
                self.save_and_revalidate(path, editor, err_list, stat_lbl)
                
                # Keep window in focus
                parent_window.lift()
                parent_window.focus_force()
                messagebox.showinfo("Batch Auto-Fix Complete", result_msg, parent=parent_window)
            else:
                messagebox.showinfo("No Fixes Applied", result_msg, parent=parent_window)
        
        except Exception as e:
            messagebox.showerror("Error", f"Batch auto-fix failed: {str(e)}", parent=parent_window)

    def clear_all(self):
        self.files.clear()
        self.tree.delete(*self.tree.get_children())
        self.summary.config(state="normal")
        self.summary.delete("1.0", tk.END)
        self.summary.config(state="disabled")
        self.status.set("Ready")

if __name__ == "__main__":
    root = tk.Tk()
    app = ValidatorApp(root)
    root.mainloop()