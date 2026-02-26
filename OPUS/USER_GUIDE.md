# User Guide — TestNG Validator Pro v11.0

## Getting Started

### Launching the Application

**GUI Mode (default):**
```bash
python -m OPUS.main
```

**CLI Mode:**
```bash
python -m OPUS.main --cli path/to/suite.xml
```

---

## GUI Walkthrough

### 1. Adding Files

- **Toolbar:** Click `+ Add Files` to browse for XML files
- **Folder:** Click `Add Folder` to recursively add all `.xml` files
- **Drag & Drop:** Drag XML files directly onto the window (requires `tkinterdnd2`)
- **Recent Files:** File → Recent Files shows your last 20 validated files

### 2. Validating

1. Check/uncheck files using the checkbox column (☑/☐)
2. Click `▶ Validate` or press **F5**
3. Results appear in the file list:
   - ✅ **PASS** — No errors found
   - ⚠️ **WARN** — Warnings only (no blocking errors)
   - ❌ **FAIL** — Errors detected

### 3. Viewing Details

- **Double-click** a file to open the detail editor
- The detail window has three panels:
  - **Issues List** (left) — Click an error to highlight it
  - **Code Editor** (center) — View and edit XML with line numbers
  - **Fix Panel** (bottom) — Tutorial-style fix instructions

### 4. Auto-Fix

- **Fix Selected:** Select an error → Click `🔧 Fix Selected`
- **Fix All:** Click `✨ Fix All` to batch-fix all auto-fixable errors
- Auto-fixable errors include: missing names, spaces in names, duplicates, empty blocks
- A `.bak` backup is always created before modification

### 5. Maven Integration

Click `🔍 Maven` in the toolbar to scan Java JARs for class/method metadata:

- **Option 1:** Select a single JAR file
- **Option 2:** Select a folder containing JARs
- **Option 3:** Enter Maven coordinates (Group ID + Artifact ID)

Once loaded, the validator will check if class names and method names in your XML actually exist in the project.

### 6. Exporting Reports

- **HTML:** Beautiful styled report with summary cards
- **CSV:** Spreadsheet-compatible error list
- **JSON:** Machine-readable structured report

Access via: Export menu or `📊 Report` toolbar button.

### 7. Themes

Toggle between Light, Dark, and System themes:
- Toolbar: Click `🌓 Theme`
- Menu: Theme → Light/Dark/System

---

## CLI Reference

```
Usage: python -m OPUS.main [options] [files...]

Options:
  --cli              Run in CLI mode (no GUI)
  -v, --verbose      Show detailed error output
  --debug            Enable debug logging
  -m, --metadata     Path to metadata JSON file
  -o, --output       Export report (.html, .csv, or .json)
  --version          Show version
  --help             Show help

Examples:
  # Validate a single file
  python -m OPUS.main --cli suite.xml

  # Validate with verbose output
  python -m OPUS.main --cli -v suite.xml

  # Validate a folder and export HTML report
  python -m OPUS.main --cli -o report.html ./suites/

  # Validate with metadata
  python -m OPUS.main --cli -m metadata.json -v suite.xml

  # Exit code: 0 = all pass, 1 = errors found
```

---

## Error Code Reference

| Code | Description | Auto-Fix |
|------|------------|----------|
| E100 | XML Syntax Error | ❌ |
| E101 | Suite missing name | ✅ |
| E102 | Multiple `<suite>` tags | ❌ |
| E103 | Test missing name | ✅ |
| E104 | Duplicate test name | ✅ |
| E105 | Missing `<suite>` | ❌ |
| E106 | Empty suite | ❌ |
| E107 | Empty `<classes>` | ✅ |
| E108 | Empty `<methods>` | ✅ |
| E109 | Empty `<packages>` | ✅ |
| E110 | `<classes>` outside `<test>` | ❌ |
| E111 | `<class>` outside `<classes>` | ❌ |
| E112 | Class missing name | ✅ |
| E113 | `<packages>` outside `<test>` | ❌ |
| E114 | Mix `<packages>`/`<classes>` | ❌ |
| E115 | `<package>` outside `<packages>` | ❌ |
| E116 | Package missing name | ✅ |
| E117 | Invalid package name | ❌ |
| E120 | `<methods>` outside `<class>` | ❌ |
| E121 | `<include>` misplaced | ❌ |
| E122 | Include missing name | ✅ |
| E123 | `<exclude>` misplaced | ❌ |
| E124 | Exclude missing name | ✅ |
| E130 | Parameter missing name | ✅ |
| E131 | Parameter missing value | ✅ |
| E132 | Duplicate parameter | ✅ |
| E145 | `<listeners>` misplaced | ❌ |
| E160 | Duplicate class | ✅ |
| E161 | Duplicate method | ✅ |
| E170 | Space in name | ✅ |
| E180 | Invalid `parallel` value | ❌ |
| E181 | Invalid `thread-count` | ❌ |
| E182 | Invalid `verbose` value | ❌ |
| E183 | Invalid `preserve-order` | ❌ |
| E200 | Structure mismatch | ❌ |
| E201 | Unclosed tag | ❌ |
| E300 | Class not in project | ❌ |
| E301 | Method not in class | ❌ |
| E303 | Invalid enum value | ❌ |
| E310 | Suite file not found | ❌ |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Add files |
| `F5` | Validate selected |
| `Double-click` | Open detail editor |
