# Architecture — TestNG Validator Pro v11.0

## Design Principles

| Principle | Application |
|-----------|------------|
| **SOLID** | Single-responsibility modules, open-closed fix registry, dependency inversion via abstractions |
| **DRY** | Centralized config, shared error codes, reusable models |
| **KISS** | Minimal abstractions, standard library where possible |
| **Defensive** | Encoding fallbacks, file size limits, thread-safe validation, backup on auto-fix |

## Module Dependency Graph

```
main.py
├── ui/app.py          ← GUI entry point
│   ├── config.py      ← Constants, themes, app config
│   ├── models.py      ← Data structures
│   ├── validators/    ← Validation engine
│   │   ├── preflight.py    ← Regex pre-scan
│   │   └── sax_validator.py ← SAX parser
│   ├── fixes/         ← Fix system
│   │   ├── fix_generator.py ← Tutorial fixes (registry pattern)
│   │   └── auto_fixer.py    ← File mutation
│   ├── exporters/     ← Report generation
│   │   ├── html_exporter.py
│   │   ├── csv_exporter.py
│   │   └── json_exporter.py
│   ├── maven/extractor.py ← JAR scanning (lazy import)
│   └── utils/         ← Cross-cutting utilities
│       ├── file_utils.py
│       ├── xml_utils.py
│       └── logging_config.py
└── CLI mode (argparse) ← Headless validation
```

## Data Flow

```
User Input (XML files)
       │
       ▼
┌─────────────────────┐
│  File Loading &      │  validate_file_path() + encoding detection
│  Input Validation    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Pre-Flight Scanner  │  Regex-based duplicate test name detection
│  (preflight.py)      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  SAX Hybrid Parser   │  Streaming XML parse with:
│  (sax_validator.py)  │  - Hierarchy validation
│                      │  - Attribute validation
│                      │  - Duplicate detection
│                      │  - Metadata-based semantic checks
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Context Injection   │  Attach source line content to errors
│  + Deduplication     │  Remove duplicate findings, sort by line
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ValidationResult    │  Aggregated result object with:
│                      │  - errors[], error_count, warning_count
│                      │  - status (PASS/WARN/FAIL)
│                      │  - duration_ms
└─────────┬───────────┘
          │
   ┌──────┴──────┐
   ▼              ▼
 GUI Display   Export (HTML/CSV/JSON)
```

## Key Design Decisions

### 1. Fix Registry Pattern (vs. if/elif chain)
The original code had a 530-line `generate_fix()` function with 30+ elif branches. The new architecture uses a **decorator-based registry**:

```python
@_register("E170")
def _fix_spaces(err, ctx, line_num, bad_code):
    return FixSuggestion(...)
```

Benefits: Open-closed (new fixes don't modify existing code), testable individually, self-documenting.

### 2. ValidationResult Aggregate
Instead of passing bare `List[ValidationError]`, the new `ValidationResult` dataclass provides computed properties (`error_count`, `is_valid`, `status`) and grouping methods (`errors_by_code`, `errors_by_severity`).

### 3. Encoding Fallback Chain
Files are read with `["utf-8", "utf-8-sig", "latin-1", "cp1252"]` fallback, preventing crashes on files with BOM or non-UTF-8 encoding.

### 4. Thread-Safe Validation
Validation runs in a daemon thread with a `threading.Lock` to prevent concurrent file mutations. UI updates use `root.after()` for tkinter thread safety.

### 5. Lazy Maven Import
The `jawa` library is imported lazily in `maven/extractor.py` to avoid import failures when the optional dependency is not installed.

## Error Code Taxonomy

| Range | Category | Example |
|-------|----------|---------|
| E100-E109 | XML/Suite structure | E100: Syntax error, E106: Empty suite |
| E110-E119 | Class/Package hierarchy | E110: `<classes>` outside `<test>` |
| E120-E129 | Method hierarchy | E121: `<include>` outside `<methods>` |
| E130-E139 | Parameters | E132: Duplicate parameter |
| E140-E149 | Listeners/Groups | E145: `<listeners>` misplaced |
| E160-E169 | Duplicates | E160: Duplicate class ref |
| E170-E179 | Naming rules | E170: Space in name |
| E180-E189 | Attribute values | E180: Invalid `parallel` value |
| E200-E209 | Structure mismatch | E201: Unclosed tag |
| E300-E319 | Metadata/Semantic | E300: Class not found |
