# Developer Guide — TestNG Validator Pro v11.0

## Prerequisites

- Python 3.8+
- `tkinter` (included with standard Python on Windows/macOS; install `python3-tk` on Linux)

## Setup

```bash
# Clone and enter project
cd SuiteValidation

# Install dependencies
pip install -r OPUS/requirements.txt

# Run application
python -m OPUS.main

# Run tests
python -m unittest discover -s OPUS/tests -v
```

## Adding a New Validation Rule

### 1. Define the error code in `config.py`

```python
CODE_META["E400"] = ("Invalid group configuration", "ERROR")
```

### 2. Add detection logic in `validators/sax_validator.py`

In the `startElement` or `endElement` method of `HybridValidator`:

```python
elif name == "groups":
    if not self._parent("suite") and not self._parent("test"):
        self._err("E400", "Invalid group placement", line, col)
```

### 3. Register a fix handler in `fixes/fix_generator.py`

```python
@_register("E400")
def _fix_invalid_group(err, ctx, line_num, bad_code):
    return FixSuggestion(
        title="❌ Fix: Invalid Group Configuration",
        steps=["1. **The Issue:** Groups must be inside <suite> or <test>."],
        code='<suite name="S"><groups>...</groups></suite>',
    )
```

### 4. (Optional) Add auto-fix in `fixes/auto_fixer.py`

Add the code to `AUTO_FIXABLE_CODES` in `config.py` and add a handler in `apply_auto_fix()`.

### 5. Write tests in `tests/test_validators.py`

```python
def test_e400_invalid_group(self):
    xml = '<suite name="S"><class><groups/></class></suite>'
    result = self._validate_xml(xml)
    self._assert_has_code(result, "E400")
```

## Adding a New Export Format

1. Create `exporters/pdf_exporter.py` with an `export_pdf(results, path)` function
2. Register it in `exporters/__init__.py`
3. Add a menu command in `ui/app.py` `_setup_menu()` and `_export_report()`

## Code Style

- **Type hints** on all function signatures
- **Docstrings** on all public functions (Google style)
- **Logging** via `logging.getLogger(__name__)` — never `print()`
- **Constants** in `config.py` — never magic strings/numbers
- **Error handling** — never bare `except:`, always specific exceptions

## Testing

```bash
# Run all tests
python -m unittest discover -s OPUS/tests -v

# Run specific test class
python -m unittest OPUS.tests.test_validators.TestStructuralErrors -v

# Run single test
python -m unittest OPUS.tests.test_validators.TestStructuralErrors.test_e101_suite_missing_name -v
```

## Packaging

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "TestNG-Validator" OPUS/main.py

# Output: dist/TestNG-Validator.exe (Windows) or dist/TestNG-Validator (macOS/Linux)
```
