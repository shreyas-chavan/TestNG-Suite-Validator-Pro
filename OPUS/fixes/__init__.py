"""
Fixes package - Tutorial-style fix generation and auto-fix engine.
"""

from .fix_generator import generate_fix
from .auto_fixer import apply_auto_fix, batch_auto_fix
from .knowledge_base import (
    get_knowledge, get_class_reference, get_method_reference,
    get_missing_params_info,
)
