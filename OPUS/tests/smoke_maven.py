#!/usr/bin/env python3
"""Smoke test: validate TEST_DUPLICATE_NAMES - Copy.xml with Maven metadata."""
import logging, sys, os
logging.basicConfig(level=logging.WARNING, format="%(message)s")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import OPUS.maven.extractor as ext_mod
ext_mod._jawa_available = None
from OPUS.maven.extractor import MavenMetadataExtractor
from OPUS.validators import validate_file

JAR = r"C:\Users\schavan\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13\NxtGenNPTCliApi-10.2.13.jar"
XML = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "TEST_DUPLICATE_NAMES - Copy.xml")

ext = MavenMetadataExtractor()
metadata = ext.extract_from_jar(JAR)
print(f"Metadata: {len(metadata)} classes")

result = validate_file(XML, metadata=metadata)
print(f"Total errors: {len(result.errors)}\n")
for e in result.errors:
    icon = "ERR" if str(e.severity) != "WARNING" else "WARN"
    line_str = str(e.line or "?").rjust(3)
    print(f"  L{line_str} [{e.code}] {icon}: {e.message}")
    if e.suggestion:
        print(f"        >> {e.suggestion}")

# Summary by code
print("\n--- Summary by code ---")
codes = {}
for e in result.errors:
    codes[e.code] = codes.get(e.code, 0) + 1
for code, count in sorted(codes.items()):
    print(f"  {code}: {count}")
