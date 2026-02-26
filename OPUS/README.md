# TestNG Validator Pro v11.0

A **production-grade**, cross-platform TestNG XML suite validator with a modern GUI, CLI mode, auto-fix engine, Maven integration, and comprehensive reporting.

## Features

- **42+ Validation Rules** — Structural, hierarchy, attribute, duplicate, and semantic checks
- **Tutorial-Style Fix Suggestions** — Step-by-step guidance for every error code
- **Auto-Fix Engine** — Automatically fix 16+ common error types with one click
- **Maven JAR Scanning** — Extract class/method metadata from JARs for semantic validation
- **Report Export** — HTML, CSV, and JSON report generation
- **Dark/Light Theme** — System-aware theme toggle
- **CLI Mode** — Headless validation for CI/CD pipelines
- **Batch Validation** — Validate multiple files and folders at once
- **Drag & Drop** — Drop XML files directly into the application
- **Recent Files** — Quick access to previously validated files

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI
python -m OPUS.main

# CLI mode
python -m OPUS.main --cli path/to/suite.xml

# CLI with report export
python -m OPUS.main --cli -v -o report.html path/to/suite.xml
```

## Project Structure

```
OPUS/
├── main.py              # Entry point (GUI + CLI)
├── config.py            # Configuration, constants, themes
├── models.py            # Data structures
├── validators/          # Validation engine
│   ├── preflight.py     # Regex pre-flight scanner
│   └── sax_validator.py # SAX-based hybrid validator
├── fixes/               # Fix system
│   ├── fix_generator.py # Tutorial fix generation
│   └── auto_fixer.py    # Auto-fix engine
├── maven/               # Maven integration
│   └── extractor.py     # JAR metadata extractor
├── exporters/           # Report generation
│   ├── html_exporter.py # Styled HTML reports
│   ├── csv_exporter.py  # CSV export
│   └── json_exporter.py # JSON export
├── ui/                  # GUI
│   └── app.py           # Main application window
├── utils/               # Utilities
│   ├── file_utils.py    # File I/O
│   ├── xml_utils.py     # XML formatting
│   └── logging_config.py
└── tests/               # Test suite (62 tests)
    ├── test_validators.py
    └── test_fixes.py
```

## Requirements

- **Python**: 3.8+
- **Required**: tkinter (bundled with Python)
- **Optional**: customtkinter, Pillow, darkdetect (modern UI), pygments (syntax highlighting), jawa (Maven JAR scanning)

## Documentation

- [USER_GUIDE.md](USER_GUIDE.md) — How to use the application
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Architecture and contribution guide
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and patterns
- [INSTALLATION.md](INSTALLATION.md) — Detailed installation instructions

## License

Internal tool — not for public distribution.
