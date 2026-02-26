#!/usr/bin/env python3
"""
Application configuration, constants, and theme definitions.
Centralizes all magic numbers, strings, and configurable behavior.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

# ─── Version ───────────────────────────────────────────────
APP_NAME = "TestNG Validator Pro"
APP_VERSION = "11.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# ─── Paths ─────────────────────────────────────────────────
APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "validator_config.json"
LOG_FILE = APP_DIR / "validator.log"
RECENT_FILES_PATH = APP_DIR / ".recent_files.json"
MAX_RECENT_FILES = 20

# ─── Logging ───────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.INFO

# ─── Validation ────────────────────────────────────────────
MAX_FILE_SIZE_MB = 50
SUPPORTED_EXTENSIONS = {".xml"}
ENCODING_FALLBACKS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

# TestNG valid attribute values
VALID_PARALLEL_VALUES = frozenset({"methods", "tests", "classes", "instances", "false", "none"})
VALID_BOOLEAN_VALUES = frozenset({"true", "false"})
VERBOSE_RANGE = range(0, 11)  # 0-10

# Java naming rules
JAVA_IDENTIFIER_PATTERN = r'^[a-zA-Z_$][a-zA-Z0-9_$]*$'
JAVA_PACKAGE_PATTERN = r'^[a-zA-Z_$][a-zA-Z0-9_$]*(\.[a-zA-Z_$][a-zA-Z0-9_$]*)*(\.\*)?$'
JAVA_FQCN_PATTERN = r'^[a-zA-Z_$][a-zA-Z0-9_$]*(\.[a-zA-Z_$][a-zA-Z0-9_$]*)*$'

# Auto-fixable error codes
AUTO_FIXABLE_CODES = frozenset({
    "E170", "E101", "E103", "E112", "E122", "E124", "E116",
    "E130", "E131", "E104", "E107", "E108", "E109",
    "E132", "E160", "E161"
})

# ─── Error Code Metadata ──────────────────────────────────
# Format: code -> (short_description, severity)
CODE_META: Dict[str, tuple] = {
    # Structural
    "E100": ("XML Syntax Error", "ERROR"),
    "E101": ("Suite missing name", "ERROR"),
    "E102": ("Multiple <suite> tags", "ERROR"),
    "E103": ("Test missing name", "ERROR"),
    "E104": ("Duplicate test name", "ERROR"),
    "E105": ("Missing <suite>", "ERROR"),
    "E106": ("Empty suite", "WARNING"),
    "E107": ("Empty <classes> block", "WARNING"),
    "E108": ("Empty <methods> block", "WARNING"),
    "E109": ("Empty <packages> block", "WARNING"),
    "E110": ("<classes> outside <test>", "ERROR"),
    "E111": ("<class> outside <classes>", "ERROR"),
    "E112": ("Class missing name", "ERROR"),
    "E113": ("<packages> outside <test>", "ERROR"),
    "E114": ("Cannot mix <packages> and <classes>", "ERROR"),
    "E115": ("<package> outside <packages>", "ERROR"),
    "E116": ("Package missing name", "ERROR"),
    "E117": ("Invalid package name format", "ERROR"),
    "E120": ("<methods> outside <class>", "ERROR"),
    "E121": ("<include> misplaced", "ERROR"),
    "E122": ("Include missing name", "ERROR"),
    "E123": ("<exclude> misplaced", "ERROR"),
    "E124": ("Exclude missing name", "ERROR"),
    "E130": ("Parameter missing 'name' attr", "ERROR"),
    "E131": ("Parameter missing 'value' attr", "ERROR"),
    "E132": ("Duplicate Parameter", "ERROR"),
    "E145": ("<listeners> misplaced", "ERROR"),
    "E160": ("Duplicate class", "WARNING"),
    "E161": ("Duplicate method", "WARNING"),
    "E170": ("Invalid Space in Name", "ERROR"),
    # Attribute Validation
    "E180": ("Invalid 'parallel' value", "ERROR"),
    "E181": ("Invalid 'thread-count' value", "ERROR"),
    "E182": ("Invalid 'verbose' value", "ERROR"),
    "E183": ("Invalid 'preserve-order' value", "ERROR"),
    "E184": ("Invalid boolean attribute", "ERROR"),
    "E185": ("Invalid numeric attribute", "ERROR"),
    # Structure
    "E200": ("Structure Mismatch", "ERROR"),
    "E201": ("Unclosed tag", "ERROR"),
    # Metadata
    "E300": ("Class not found in Project", "ERROR"),
    "E301": ("Method not found in Class", "ERROR"),
    "E303": ("Invalid Enum Value", "ERROR"),
    "E310": ("Suite file not found", "ERROR"),
    # Groups (new)
    "E400": ("Invalid group configuration", "ERROR"),
    "E401": ("Empty <groups> block", "WARNING"),
}

# ─── Theme ─────────────────────────────────────────────────
@dataclass
class ThemeColors:
    """Color palette for a theme."""
    bg: str = "#ffffff"
    fg: str = "#212121"
    accent: str = "#1976d2"
    error: str = "#d32f2f"
    warning: str = "#f57c00"
    success: str = "#388e3c"
    info: str = "#1565c0"
    surface: str = "#f5f5f5"
    border: str = "#e0e0e0"
    editor_bg: str = "#fafafa"
    gutter_bg: str = "#f0f0f0"
    highlight: str = "#fff3e0"
    err_highlight: str = "#ffebee"
    code_bg: str = "#e3f2fd"

LIGHT_THEME = ThemeColors()
DARK_THEME = ThemeColors(
    bg="#1e1e1e",
    fg="#e0e0e0",
    accent="#64b5f6",
    error="#ef5350",
    warning="#ffa726",
    success="#66bb6a",
    info="#42a5f5",
    surface="#2d2d2d",
    border="#424242",
    editor_bg="#1e1e1e",
    gutter_bg="#252525",
    highlight="#3e2723",
    err_highlight="#4e1e1e",
    code_bg="#1a237e",
)

# ─── Application Config (persisted) ───────────────────────
@dataclass
class AppConfig:
    """Persisted application configuration."""
    theme: str = "System"
    last_directory: str = ""
    recent_files: List[str] = field(default_factory=list)
    window_geometry: str = ""
    debug_mode: bool = False
    auto_validate_on_load: bool = False
    max_recent_files: int = MAX_RECENT_FILES
    default_encoding: str = "utf-8"

    def save(self) -> None:
        """Save config to disk."""
        try:
            data = {
                "theme": self.theme,
                "last_directory": self.last_directory,
                "recent_files": self.recent_files[:self.max_recent_files],
                "window_geometry": self.window_geometry,
                "debug_mode": self.debug_mode,
                "auto_validate_on_load": self.auto_validate_on_load,
                "default_encoding": self.default_encoding,
            }
            CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to save config: %s", e)

    @classmethod
    def load(cls) -> "AppConfig":
        """Load config from disk, returning defaults on failure."""
        try:
            if CONFIG_FILE.exists():
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to load config: %s", e)
        return cls()

    def add_recent_file(self, path: str) -> None:
        """Add a file to the recent files list."""
        path = str(Path(path).resolve())
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self.save()
