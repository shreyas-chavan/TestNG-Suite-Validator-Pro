# Installation Guide — TestNG Validator Pro v11.0

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8+ | 3.11+ |
| OS | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest |
| RAM | 256 MB | 512 MB |
| Disk | 50 MB | 100 MB |

## Step-by-Step Installation

### 1. Install Python

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation

**macOS:**
```bash
brew install python3
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

### 2. Install Dependencies

```bash
# Navigate to the project folder
cd SuiteValidation

# Install all dependencies
pip install -r OPUS/requirements.txt
```

### 3. Verify Installation

```bash
python -m OPUS.main --version
```

## Dependencies

### Required (Core)

| Package | Version | Purpose |
|---------|---------|---------|
| Python stdlib | — | tkinter, xml.sax, json, csv, threading |

### Optional (Enhanced UI)

| Package | Version | Purpose |
|---------|---------|---------|
| `customtkinter` | ≥5.2.0 | Modern UI components |
| `Pillow` | ≥10.0.0 | Image processing for icons |
| `darkdetect` | ≥0.8.0 | Auto-detect system theme |
| `pygments` | ≥2.16.0 | Syntax highlighting |

### Optional (Maven Integration)

| Package | Version | Purpose |
|---------|---------|---------|
| `jawa` | ≥2.2.0 | Java bytecode / JAR parsing |

### Optional (Drag & Drop)

| Package | Version | Purpose |
|---------|---------|---------|
| `tkinterdnd2` | ≥0.3.0 | Drag & drop file support |

### Install only required extras:

```bash
# Modern UI only
pip install customtkinter Pillow darkdetect

# Maven support only
pip install jawa

# All extras
pip install customtkinter Pillow darkdetect pygments jawa tkinterdnd2
```

## Running the Application

```bash
# GUI mode
python -m OPUS.main

# CLI mode
python -m OPUS.main --cli path/to/suite.xml

# With debug logging
python -m OPUS.main --debug
```

## Building Executables

### Windows (.exe)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "TestNG-Validator" --icon=icon.ico OPUS/main.py
```

The executable will be in `dist/TestNG-Validator.exe`.

### macOS (.app)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "TestNG-Validator" OPUS/main.py
```

### Linux (AppImage)

```bash
pip install pyinstaller
pyinstaller --onefile --name "testng-validator" OPUS/main.py
chmod +x dist/testng-validator
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'tkinter'` | Install `python3-tk` (Linux) or reinstall Python with tkinter (Windows) |
| `ModuleNotFoundError: No module named 'customtkinter'` | Run `pip install customtkinter` — the app works without it |
| `ModuleNotFoundError: No module named 'jawa'` | Run `pip install jawa` — only needed for Maven JAR scanning |
| Theme toggle does nothing | Install `customtkinter` and `darkdetect` |
| Drag & drop not working | Install `tkinterdnd2` |
