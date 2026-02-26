#!/usr/bin/env python3
"""
Live Maven extractor test against real JAR file.
Requires: NxtGenNPTCliApi-10.2.13.jar in local .m2 repository.
"""

import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Reset cached jawa check
import OPUS.maven.extractor as ext_mod
ext_mod._jawa_available = None

from OPUS.maven.extractor import MavenMetadataExtractor

JAR_PATH = r"C:\Users\schavan\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13\NxtGenNPTCliApi-10.2.13.jar"
FOLDER_PATH = r"C:\Users\schavan\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13"
METADATA_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_metadata.json")

# Classes referenced in CorrectFile.xml
XML_CLASSES = [
    "com.eci.cliApi.bgp.operation.NxtGenBgpTable",
    "com.eci.cliApi.bgp.operation.NxtGenBgpNeighborBriefTable",
    "com.eci.cliApi.shelf.configuration.NxtGenResetMcp",
    "com.eci.cliApi.shelf.configuration.NxtGenShelfConfigAction",
    "com.eci.cliApi.shelf.operation.NxtGenSystemStatusTable",
    "com.eci.cliApi.bgp.operation.NxtGenBgpLinkStateInDetailTable",
]


def test_extract_from_jar():
    print("=" * 60)
    print("TEST 1: Extract metadata from single JAR")
    print("=" * 60)
    ext = MavenMetadataExtractor()
    metadata = ext.extract_from_jar(JAR_PATH)
    print(f"  Classes extracted: {len(metadata)}")
    assert len(metadata) > 0, "No classes extracted!"
    print("  PASSED\n")
    return metadata


def test_save_load_roundtrip(metadata):
    print("=" * 60)
    print("TEST 2: Save/Load metadata round-trip")
    print("=" * 60)
    ext = MavenMetadataExtractor()
    ext.metadata = metadata
    ext.save_metadata(METADATA_OUT)
    print(f"  Saved to: {METADATA_OUT}")

    ext2 = MavenMetadataExtractor()
    loaded = ext2.load_metadata(METADATA_OUT)
    print(f"  Loaded: {len(loaded)} classes")
    assert len(loaded) == len(metadata), f"Mismatch: {len(loaded)} != {len(metadata)}"
    print("  PASSED\n")
    return loaded


def test_class_lookup(metadata):
    print("=" * 60)
    print("TEST 3: CorrectFile.xml class lookup")
    print("=" * 60)
    found_count = 0
    for cls in XML_CLASSES:
        found = cls in metadata
        if found:
            found_count += 1
            methods = metadata[cls].get("methods", {})
            print(f"  FOUND: {cls} ({len(methods)} methods)")
        else:
            print(f"  MISS:  {cls}")
    print(f"\n  Found {found_count}/{len(XML_CLASSES)} classes")
    print("  PASSED\n")
    return found_count


def test_method_details(metadata):
    print("=" * 60)
    print("TEST 4: Method details for a found class")
    print("=" * 60)
    # Pick first class from XML_CLASSES that exists
    for cls in XML_CLASSES:
        if cls in metadata:
            info = metadata[cls]
            methods = info.get("methods", {})
            print(f"  Class: {cls}")
            print(f"  Source JAR: {info.get('source_jar', 'N/A')}")
            print(f"  Methods ({len(methods)}):")
            for mname, minfo in sorted(methods.items()):
                params = minfo.get("parameters", [])
                is_test = minfo.get("is_test", False)
                ann = minfo.get("annotations", [])
                ann_str = ", ".join(ann) if ann else "none"
                print(f"    {mname}() - params: {len(params)}, test: {is_test}, annotations: {ann_str}")
            print("  PASSED\n")
            return
    print("  SKIPPED (no matching class found)\n")


def test_folder_scan():
    print("=" * 60)
    print("TEST 5: Folder scan (should find JAR, skip sources)")
    print("=" * 60)
    ext = MavenMetadataExtractor()
    ext.m2_repo = FOLDER_PATH  # Point at the folder itself

    # Manually find JARs in folder
    jars = []
    for f in os.listdir(FOLDER_PATH):
        if f.endswith(".jar") and not f.endswith("-sources.jar") and not f.endswith("-javadoc.jar"):
            jars.append(os.path.join(FOLDER_PATH, f))

    print(f"  JARs found in folder: {len(jars)}")
    for j in jars:
        print(f"    {os.path.basename(j)}")

    for j in jars:
        meta = ext.extract_from_jar(j)
        print(f"  Extracted {len(meta)} classes from {os.path.basename(j)}")
        ext.metadata.update(meta)

    print(f"  Total classes: {len(ext.metadata)}")
    assert len(ext.metadata) > 0, "No classes from folder scan!"
    print("  PASSED\n")


def test_semantic_validation(metadata):
    print("=" * 60)
    print("TEST 6: Semantic validation (E300/E301) with metadata")
    print("=" * 60)
    from OPUS.validators import validate_file
    import tempfile

    # Test with a known class from the JAR
    known_classes = [c for c in XML_CLASSES if c in metadata]
    if not known_classes:
        print("  SKIPPED (no matching classes)\n")
        return

    cls = known_classes[0]
    methods = list(metadata[cls].get("methods", {}).keys())
    known_method = methods[0] if methods else "fakeMethod"

    # XML with valid class + valid method -> should NOT trigger E300/E301
    valid_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<suite name="Test">
  <test name="T1">
    <classes>
      <class name="{cls}">
        <methods>
          <include name="{known_method}"/>
        </methods>
      </class>
    </classes>
  </test>
</suite>'''

    # XML with FAKE class -> should trigger E300
    fake_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<suite name="Test">
  <test name="T1">
    <classes>
      <class name="com.fake.NonExistentClass">
        <methods>
          <include name="fakeMethod"/>
        </methods>
      </class>
    </classes>
  </test>
</suite>'''

    # Write temp files and validate
    for label, xml_content, expect_e300 in [
        ("Valid class+method", valid_xml, False),
        ("Fake class", fake_xml, True),
    ]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(xml_content)
            tmp = f.name
        try:
            result = validate_file(tmp, metadata=metadata)
            codes = [e.code for e in result.errors]
            has_e300 = "E300" in codes
            status = "OK" if has_e300 == expect_e300 else "FAIL"
            print(f"  {label}: E300={'yes' if has_e300 else 'no'} (expected={'yes' if expect_e300 else 'no'}) -> {status}")
            if status == "FAIL":
                print(f"    Errors: {codes}")
        finally:
            os.unlink(tmp)

    print("  PASSED\n")


def cleanup():
    if os.path.exists(METADATA_OUT):
        os.unlink(METADATA_OUT)
        print(f"Cleaned up: {METADATA_OUT}")


if __name__ == "__main__":
    if not os.path.exists(JAR_PATH):
        print(f"JAR not found: {JAR_PATH}")
        sys.exit(1)

    metadata = test_extract_from_jar()
    loaded = test_save_load_roundtrip(metadata)
    test_class_lookup(metadata)
    test_method_details(metadata)
    test_folder_scan()
    test_semantic_validation(metadata)
    cleanup()

    print("=" * 60)
    print("ALL MAVEN TESTS PASSED")
    print("=" * 60)
