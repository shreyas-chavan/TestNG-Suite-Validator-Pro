#!/usr/bin/env python3
"""Smoke test: verify all imports, config, and models work after UI changes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from OPUS.config import APP_TITLE, LIGHT_THEME, DARK_THEME, ThemeColors, CODE_META
from OPUS.models import ValidationError, ValidationResult, Severity, FileEntry
from OPUS.validators import validate_file
from OPUS.fixes import generate_fix, apply_auto_fix, batch_auto_fix
from OPUS.exporters import export_html, export_csv, export_json

# Verify new theme fields exist
for attr in ['toolbar_bg', 'sidebar_bg', 'statusbar_bg', 'heading', 'muted', 'selection',
             'tab_bg', 'tab_active', 'menu_bg', 'menu_fg']:
    assert hasattr(DARK_THEME, attr), f"Missing {attr}"
    assert hasattr(LIGHT_THEME, attr), f"Missing {attr} in LIGHT_THEME"

# Verify E302 is INFO
assert CODE_META['E302'][1] == 'INFO', f"E302 should be INFO, got {CODE_META['E302'][1]}"

# Verify info_count exists
r = ValidationResult(file_path='test.xml', errors=[
    ValidationError(code='E302', message='test', severity=Severity.INFO),
    ValidationError(code='E100', message='test', severity=Severity.ERROR),
    ValidationError(code='E160', message='test', severity=Severity.WARNING),
])
assert r.info_count == 1, f"info_count should be 1, got {r.info_count}"
assert r.error_count == 1
assert r.warning_count == 1

# Verify UI module imports without crash
from OPUS.ui.app import ValidatorApp

print("ALL IMPORT AND CONFIG CHECKS PASSED")
print(f"  Theme fields: {len(ThemeColors.__dataclass_fields__)} fields")
print(f"  Error codes: {len(CODE_META)} defined")
print(f"  Dark theme bg: {DARK_THEME.bg} (Monokai)")
print(f"  Dark theme accent: {DARK_THEME.accent}")
print(f"  E302 severity: {CODE_META['E302'][1]} (INFO)")
print(f"  info_count: {r.info_count}")
