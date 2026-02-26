# TestNG Validator Pro v11.0

A **production-grade**, cross-platform TestNG XML suite validator with a modern Monokai-themed GUI, Smart Fix Assistant, CLI mode, auto-fix engine, Maven bytecode integration, and comprehensive reporting.

## Features

- **45+ Validation Rules** — Structural, hierarchy, attribute, duplicate, and semantic checks
- **Smart Fix Assistant** — 4-tab fix window: Quick Fix, Explain, Sample Usage, Reference
- **Knowledge Base** — Plain-English explanations for every error code
- **Auto-Fix Engine** — Automatically fix 16+ common error types with one click
- **Maven JAR Scanning** — Extract class/method/parameter metadata from JARs via bytecode analysis
- **Bytecode Reference** — View class methods, parameters, and annotations from scanned JARs
- **E302 Smart Suggestions** — Shows missing optional parameters with suggested XML
- **Report Export** — HTML, CSV, and JSON report generation
- **Monokai Dark Theme** — Sublime Text-inspired dark theme with Light mode option
- **CLI Mode** — Headless validation for CI/CD pipelines
- **Batch Validation** — Validate multiple files and folders at once
- **Drag & Drop** — Drop XML files directly into the application (requires tkinterdnd2)
- **Recent Files** — Quick access to previously validated files
- **Persistent Paths** — Remembers last-used Maven JAR paths and validation directories
- **In-App Help** — How to Use guide and Error Code Reference in the Help menu

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI
python -m OPUS.main

# CLI mode
python -m OPUS.main --cli path/to/suite.xml

# CLI with verbose output and HTML report
python -m OPUS.main --cli -v -o report.html path/to/suite.xml
```

For first-time users, see [GETTING_STARTED.md](../GETTING_STARTED.md) for step-by-step installation.

## Project Structure

```
OPUS/
├── main.py              # Entry point (GUI + CLI, TkinterDnD support)
├── config.py            # Configuration, constants, themes, AppConfig
├── models.py            # Data structures (ValidationError, FileEntry, etc.)
├── validators/          # Validation engine
│   ├── preflight.py     # Regex pre-flight scanner
│   └── sax_validator.py # SAX-based hybrid validator (45+ rules)
├── fixes/               # Fix system
│   ├── fix_generator.py # Tutorial fix generation (registry pattern)
│   ├── auto_fixer.py    # Auto-fix engine (16+ codes)
│   └── knowledge_base.py # Knowledge base + bytecode reference helpers
├── maven/               # Maven integration
│   └── extractor.py     # JAR metadata extractor (jawa bytecode)
├── exporters/           # Report generation
│   ├── html_exporter.py # Styled HTML reports
│   ├── csv_exporter.py  # CSV export
│   └── json_exporter.py # JSON export
├── ui/                  # GUI
│   └── app.py           # Main application (Monokai theme, Smart Fix tabs)
├── utils/               # Utilities
│   ├── file_utils.py    # File I/O
│   ├── xml_utils.py     # XML formatting
│   └── logging_config.py
└── tests/               # Test suite (65 tests)
    ├── test_validators.py  # 52 validator tests
    ├── test_fixes.py       # 13 fix tests
    ├── smoke_imports.py    # Import + config smoke test
    └── smoke_maven_semantic.py  # 12 Maven semantic tests
```

## Requirements

- **Python**: 3.8+
- **Required**: tkinter (bundled with Python)
- **Recommended**: tkinterdnd2 (drag & drop), Pygments (syntax highlighting), jawa (Maven JAR scanning)
- **Optional**: customtkinter, Pillow, darkdetect (enhanced UI)

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| Validators | 52 | All Pass |
| Fixes | 13 | All Pass |
| Maven Semantic | 12 | All Pass |
| CLI Smoke | 1 | Pass |
| GUI Launch | 1 | Pass |

## Documentation

- [GETTING_STARTED.md](../GETTING_STARTED.md) — First-time setup guide for beginners
- [USER_GUIDE.md](USER_GUIDE.md) — How to use the application
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Architecture and contribution guide
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and patterns
- [INSTALLATION.md](INSTALLATION.md) — Detailed installation instructions

## License

Internal tool — not for public distribution.
