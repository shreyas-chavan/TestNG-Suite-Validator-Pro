# Maven Integration Guide — TestNG Validator Pro v11.0

## Overview

The Maven integration allows you to scan Java JAR files from your Maven `.m2` repository (or standalone JARs) and extract **class/method metadata**. This metadata is then used during XML validation to perform **semantic checks**:

- **E300** — Class name in XML not found in any scanned JAR
- **E301** — Method name in XML not found in the referenced class
- **E302** — Parameter count in XML doesn't match method's bytecode signature
- **E303** — Parameter value doesn't match allowed enum values

This catches real bugs like typos in class names, referencing methods that don't exist, or passing the wrong number of parameters.

---

## Prerequisites

```bash
# Install jawa (Java bytecode parser)
pip install jawa
```

Verify installation:
```bash
python -c "from jawa.cf import ClassFile; print('jawa OK')"
```

---

## Quick Start

### Option 1: GUI Mode

1. Launch the application: `python -m OPUS.main`
2. Click **Maven** in the toolbar
3. Choose one of:
   - **JAR File(s)** — Browse and select one or **multiple** JAR files (Ctrl+click)
   - **Folder** — Select a folder containing JARs
   - **Maven Coordinates** — Enter Group ID + Artifact ID
4. Wait for extraction to complete
5. **Metadata accumulates** — scan additional JARs to add more classes
6. Use **Clear Metadata** button to reset
7. Load your XML files and click **Validate**
8. Semantic errors (E300/E301/E302) will now appear for mismatches

> **Multi-JAR Support**: You can select multiple JARs in a single browse dialog
> (hold Ctrl or Shift). You can also scan multiple times — metadata accumulates
> across scans, so classes from all scanned JARs are available for validation.

### Option 2: CLI Mode

```bash
# Step 1: Extract metadata from a JAR and save to JSON
python -c "
from OPUS.maven.extractor import MavenMetadataExtractor
ext = MavenMetadataExtractor()
metadata = ext.extract_from_jar(r'path\to\your.jar')
ext.metadata = metadata
ext.save_metadata('metadata.json')
print(f'Extracted {len(metadata)} classes')
"

# Step 2: Validate XML with metadata
python -m OPUS.main --cli -v -m metadata.json your_suite.xml
```

### Option 3: Python API

```python
from OPUS.maven.extractor import MavenMetadataExtractor
from OPUS.validators import validate_file

# Extract
ext = MavenMetadataExtractor()
metadata = ext.extract_from_jar(r"C:\path\to\your.jar")

# Validate with metadata
result = validate_file("suite.xml", metadata=metadata)
for err in result.errors:
    print(f"  L{err.line} [{err.code}] {err.message}")
```

---

## API Reference

### `MavenMetadataExtractor`

#### Constructor

```python
ext = MavenMetadataExtractor(m2_repo_path=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `m2_repo_path` | `str` or `None` | `~/.m2/repository` | Custom Maven repo path |

#### Methods

##### `extract_from_jar(jar_path, progress_callback=None) -> dict`

Extract class/method metadata from a single JAR file.

```python
metadata = ext.extract_from_jar(r"C:\path\to\mylib-1.0.jar")
# Returns: {"com.example.MyClass": {"methods": {...}, "source_jar": "mylib-1.0.jar"}}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `jar_path` | `str` | Full path to the JAR file |
| `progress_callback` | `Callable[[int, int], None]` | Optional `(current, total)` progress callback |

##### `find_jars(group_id=None, artifact_id=None) -> List[str]`

Find JAR files in the Maven `.m2` repository by coordinates.

```python
jars = ext.find_jars("com.eci.raft.tests", "NxtGenNPTCliApi")
# Returns: ["C:\Users\...\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13\NxtGenNPTCliApi-10.2.13.jar"]
```

- Automatically skips `-sources.jar` and `-javadoc.jar`
- If no coordinates given, scans the entire `.m2` repository

##### `scan_project_jars(group_ids, artifact_ids, progress_callback=None) -> dict`

Scan multiple Maven artifacts and combine metadata.

```python
metadata = ext.scan_project_jars(
    group_ids=["com.eci.raft.tests", "com.eci.raft.tests"],
    artifact_ids=["NxtGenNPTCliApi", "NxtGenSomeOtherApi"],
)
```

##### `save_metadata(output_path) -> None`

Save extracted metadata to a JSON file for reuse.

```python
ext.metadata = metadata
ext.save_metadata("project_metadata.json")
```

##### `load_metadata(input_path) -> dict`

Load previously saved metadata from a JSON file.

```python
metadata = ext.load_metadata("project_metadata.json")
```

---

## Metadata Format

The extracted metadata JSON has this structure:

```json
{
  "com.eci.cliApi.bgp.operation.NxtGenBgpTable": {
    "methods": {
      "getBgpTable": {
        "parameters": [
          {"name": "arg0", "type": "java.lang.String"},
          {"name": "arg1", "type": "java.lang.String"},
          {"name": "arg2", "type": "java.lang.String"}
        ],
        "is_test": false,
        "return_type": "void",
        "annotations": []
      },
      "verifyBgpTable": {
        "parameters": [...],
        "is_test": false,
        "return_type": "void",
        "annotations": []
      }
    },
    "source_jar": "NxtGenNPTCliApi-10.2.13.jar"
  }
}
```

| Field | Description |
|-------|-------------|
| `methods` | Dict of method name → method info |
| `parameters` | List of `{name, type}` for each method parameter |
| `is_test` | `true` if method has a `@Test` annotation |
| `return_type` | Java return type |
| `annotations` | List of annotation descriptors |
| `source_jar` | Which JAR this class was found in |

---

## Real-World Example

### Step-by-step: Validate `CorrectFile.xml` against your project JARs

```bash
# 1. Extract metadata from your project JAR
python -c "
from OPUS.maven.extractor import MavenMetadataExtractor
ext = MavenMetadataExtractor()
jar = r'C:\Users\schavan\.m2\repository\com\eci\raft\tests\NxtGenNPTCliApi\10.2.13\NxtGenNPTCliApi-10.2.13.jar'
metadata = ext.extract_from_jar(jar)
ext.metadata = metadata
ext.save_metadata('npt_metadata.json')
print(f'Extracted {len(metadata)} classes')
"
# Output: Extracted 870 classes

# 2. Validate your XML suite against the metadata
python -m OPUS.main --cli -v -m npt_metadata.json CorrectFile.xml
```

### What to expect

- If a `<class name="com.eci.cliApi.bgp.operation.NxtGenBgpTable"/>` exists in the JAR → **No error**
- If a `<class name="com.eci.cliApi.shelf.configuration.NxtGenResetMcp"/>` is NOT in the JAR → **E300: Class unknown**
- If `<include name="nonExistentMethod"/>` is not in the class → **E301: Method not in class**

### Multiple JARs

If your project uses classes from multiple JARs, extract and merge:

```python
from OPUS.maven.extractor import MavenMetadataExtractor

ext = MavenMetadataExtractor()

# Extract from multiple JARs
for jar_path in [
    r"C:\path\to\first.jar",
    r"C:\path\to\second.jar",
    r"C:\path\to\third.jar",
]:
    meta = ext.extract_from_jar(jar_path)
    ext.metadata.update(meta)
    print(f"  {len(meta)} classes from {jar_path}")

print(f"Total: {len(ext.metadata)} classes")
ext.save_metadata("combined_metadata.json")
```

> **GUI Tip**: In the Maven Scanner dialog, the Browse button supports multi-select.
> Metadata accumulates across scans, so you can scan multiple JARs across sessions.

### Maven Coordinates (from `.m2` repository)

```python
ext = MavenMetadataExtractor()  # defaults to ~/.m2/repository

# Find all JARs for a specific artifact
jars = ext.find_jars("com.eci.raft.tests", "NxtGenNPTCliApi")
print(f"Found {len(jars)} JARs")

# Or scan by coordinates directly
metadata = ext.scan_project_jars(
    group_ids=["com.eci.raft.tests"],
    artifact_ids=["NxtGenNPTCliApi"],
)
```

---

## Running the Maven Test Suite

```bash
# Run all Maven integration tests (requires JAR on disk)
python OPUS/tests/test_maven_live.py
```

### Tests included:

| Test | What it verifies |
|------|-----------------|
| **1. JAR Extraction** | Reads `.class` files from JAR, extracts class/method metadata |
| **2. Save/Load Round-trip** | Metadata survives JSON serialization and deserialization |
| **3. Class Lookup** | Classes from `CorrectFile.xml` are found in the JAR |
| **4. Method Details** | Method parameters, annotations, return types are correct |
| **5. Folder Scan** | Finds JARs in a folder, correctly skips `-sources.jar` |
| **6. Semantic Validation** | E300/E301/E302 fire correctly for class/method/param mismatches |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `jawa library not available` | Run `pip install jawa` |
| `Invalid JAR file` | Ensure the file is a valid `.jar` (ZIP format with `.class` files) |
| `No classes extracted` | JAR may contain only resources (no `.class` files) |
| `Class not found (E300)` | The class may be in a different JAR — scan additional JARs |
| `Method not found (E301)` | Check for typos; method may be inherited from a parent class |
| `Maven path not found` | Verify `~/.m2/repository` exists or provide custom path |
| Slow extraction | Large JARs (1000+ classes) take a few seconds — progress callback helps |

---

## Architecture Notes

- **`jawa`** is imported lazily — the app works fine without it (Maven features simply disabled)
- Metadata is a plain `dict` — no special classes needed to serialize/deserialize
- The extractor skips constructors (`<init>`, `<clinit>`) and inner class synthetic methods
- Parameter names are not available in bytecode; they appear as `arg0`, `arg1`, etc.
- `is_test` is determined by checking if any annotation contains the string `Test`
