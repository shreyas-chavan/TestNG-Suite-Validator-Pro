#!/usr/bin/env python3
"""
Smoke test for Maven semantic validation (E300/E301/E302).
Tests each intentional error from TEST_DUPLICATE_NAMES - Copy.xml in isolation
so SAX doesn't stop at the first structural error.

JAR facts (verified):
  - Package is 'commans' not 'commons' (that's actually the real name)
  - Method is 'grepAndCountBgpNeigbhorBriefTable' (8 params) — typo IS in the JAR
  - NxtGenBgpNeighborBriefTable.getBgpNeighborBriefTable has 3 params
  - NxtGenBgpRouteOutDetail.getBgpRouteOutDetailTable has 3 params
  - NxtGenBgpRouteOutDetail.saveBgpRouteOutDetailTableAttribute has 5 params
"""
import logging, sys, os, tempfile
logging.basicConfig(level=logging.WARNING, format="%(message)s")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import OPUS.maven.extractor as ext_mod
ext_mod._jawa_available = None
from OPUS.maven.extractor import MavenMetadataExtractor
from OPUS.validators import validate_file

JAR = r"C:\Users\schavan\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13\NxtGenNPTCliApi-10.2.13.jar"

ext = MavenMetadataExtractor()
metadata = ext.extract_from_jar(JAR)
print(f"Metadata: {len(metadata)} classes\n")


def validate_xml_string(xml, label):
    """Write XML to temp file, validate, print results."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        f.write(xml)
        tmp = f.name
    try:
        result = validate_file(tmp, metadata=metadata)
        codes = [e.code for e in result.errors]
        print(f"--- {label} ---")
        if result.errors:
            for e in result.errors:
                line_str = str(e.line or "?").rjust(3)
                print(f"  L{line_str} [{e.code}] {e.message}")
                if e.suggestion:
                    print(f"        >> {e.suggestion}")
        else:
            print("  (no errors)")
        print()
        return codes
    finally:
        os.unlink(tmp)


passed = 0
failed = 0

def check(label, xml, expected_codes, not_expected=None):
    global passed, failed
    codes = validate_xml_string(xml, label)
    ok = True
    for ec in expected_codes:
        if ec not in codes:
            print(f"  ** FAIL: Expected {ec} not found!")
            ok = False
    if not_expected:
        for nec in not_expected:
            if nec in codes:
                print(f"  ** FAIL: Unexpected {nec} found!")
                ok = False
    if ok:
        passed += 1
    else:
        failed += 1


# ===== TEST 1: E300 - Class missing 'operation' in package =====
check("E300: Missing package segment (bgp.NxtGenBgpRouteOutDetail)", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.NxtGenBgpRouteOutDetail">
    <methods><include name="getBgpRouteOutDetailTable">
      <parameter name="shelfUID" value="N1"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E300"])

# ===== TEST 2: E300 - External class (TestAPI.TeqStreams) =====
check("E300: TestAPI.TeqStreams (not in JAR)", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="TestAPI.TeqStreams">
    <methods><include name="regenerateAllTrafficItems"/></methods>
  </class>
</classes></test></suite>''', ["E300"])

# ===== TEST 3: E300 - Class typo (NxtGenBgpTble) =====
check("E300: Suggestion quality for typo class", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpTble">
    <methods><include name="getBgpTable"/></methods>
  </class>
</classes></test></suite>''', ["E300"])

# ===== TEST 4: E301 - Method name with spaces =====
check("E301+E170: Method with spaces", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpRouteOutDetail">
    <methods><include name="getBgpRouteOutDetail   Table">
      <parameter name="shelfUID" value="N1"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E170", "E301"])

# ===== TEST 5: E301 - Method that doesn't exist in class =====
check("E301: fakeMethod not in NxtGenBgpTable", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpTable">
    <methods><include name="fakeMethodName"/></methods>
  </class>
</classes></test></suite>''', ["E301"])

# ===== TEST 6: E302 - Param count mismatch (fewer params) =====
# getBgpNeighborBriefTable has 3 params in bytecode, we give 2
check("E302: Fewer params than method expects", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpNeighborBriefTable">
    <methods><include name="getBgpNeighborBriefTable">
      <parameter name="shelfUID" value="N1"/>
      <parameter name="greps" value="ESTABLISHED"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E302"])

# ===== TEST 7: E302 - Param count mismatch (more params) =====
# getBgpNeighborBriefTable has 3 params, we give 5
check("E302: More params than method expects", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpNeighborBriefTable">
    <methods><include name="getBgpNeighborBriefTable">
      <parameter name="shelfUID" value="N1"/>
      <parameter name="greps" value="ESTABLISHED"/>
      <parameter name="expectedCount" value="5"/>
      <parameter name="extra1" value="a"/>
      <parameter name="extra2" value="b"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E302"])

# ===== TEST 8: CLEAN - Valid class + method + correct param count =====
# getBgpNeighborBriefTable has 3 params, we give 3
check("CLEAN: Correct class + method + 3 params", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpNeighborBriefTable">
    <methods><include name="getBgpNeighborBriefTable">
      <parameter name="shelfUID" value="N1"/>
      <parameter name="greps" value="ESTABLISHED"/>
      <parameter name="expectedCount" value="5"/>
    </include></methods>
  </class>
</classes></test></suite>''', [], not_expected=["E300", "E301", "E302"])

# ===== TEST 9: E170 + E300 - Space in class name =====
check("E170+E300: Space in class name", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.    NxtGenBgpNeighborBriefTable">
    <methods><include name="getBgpNeighborBriefTable">
      <parameter name="expectedCount" value="5"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E170", "E300"])

# ===== TEST 10: E302 on saveBgpRouteOutDetailTableAttribute (5 params, give 3) =====
check("E302: saveBgpRouteOutDetailTableAttribute expects 5, got 3", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpRouteOutDetail">
    <methods><include name="saveBgpRouteOutDetailTableAttribute">
      <parameter name="shelfUID" value="N1"/>
      <parameter name="recordFilterKeys" value="Prefix"/>
      <parameter name="recordFilterValue" value="122.1.0.0/32"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E302"])

# ===== TEST 11: No E302 when method not found (E301 takes priority) =====
check("E301 only (no E302) when method unknown", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.cliApi.bgp.operation.NxtGenBgpTable">
    <methods><include name="nonExistentMethod">
      <parameter name="p1" value="v1"/>
    </include></methods>
  </class>
</classes></test></suite>''', ["E301"], not_expected=["E302"])

# ===== TEST 12: commans IS valid (it's the real package name in JAR) =====
check("VALID: commans.timeutils.TimeApi exists in JAR", '''<?xml version="1.0"?>
<suite name="S"><test name="T"><classes>
  <class name="com.eci.commans.timeutils.TimeApi">
    <methods><include name="waitTime">
      <parameter name="delayInMilliseconds" value="10000"/>
      <parameter name="dummy" value="x"/>
    </include></methods>
  </class>
</classes></test></suite>''', [], not_expected=["E300"])

# ===== SUMMARY =====
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)
