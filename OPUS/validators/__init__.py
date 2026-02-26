"""
Validators package - Contains all validation logic for TestNG XML files.
"""

from .sax_validator import validate_file
from .preflight import preflight_scan
