#!/usr/bin/env python3
"""
Data models for the TestNG Validator.
Defines all core data structures used across the application.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class Severity(Enum):
    """Validation error severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

    def __str__(self) -> str:
        return self.value


@dataclass
class ValidationError:
    """
    Represents a single validation finding.

    Attributes:
        code: Error code (e.g., 'E100', 'E170')
        message: Human-readable error description
        line: 1-based line number where the error occurs
        col: Column number (0-based)
        severity: ERROR, WARNING, or INFO
        context_data: Dynamic data relevant to the error (e.g., the duplicate name)
        line_content: The actual source line text for display
        auto_fixable: Whether this error can be automatically fixed
        suggestion: Suggested correction (e.g., 'Did you mean: ...')
        fix_action: Description of what the auto-fix will do
    """
    code: str
    message: str
    line: Optional[int] = None
    col: Optional[int] = None
    severity: Severity = Severity.ERROR
    context_data: Optional[str] = None
    line_content: Optional[str] = None
    auto_fixable: bool = False
    suggestion: Optional[str] = None
    fix_action: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return self.severity == Severity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == Severity.WARNING

    @property
    def location(self) -> str:
        """Human-readable location string."""
        if self.line and self.col:
            return f"Line {self.line}, Col {self.col}"
        elif self.line:
            return f"Line {self.line}"
        return "Unknown"


@dataclass
class ValidationResult:
    """
    Aggregated result of validating a single file.

    Attributes:
        file_path: Path to the validated file
        errors: List of all validation findings
        validated_at: Timestamp of validation
        duration_ms: Validation duration in milliseconds
        file_size: File size in bytes
        metadata_used: Whether project metadata was used
    """
    file_path: str
    errors: List[ValidationError] = field(default_factory=list)
    validated_at: Optional[datetime] = None
    duration_ms: float = 0.0
    file_size: int = 0
    metadata_used: bool = False

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == Severity.INFO)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    @property
    def status(self) -> str:
        if not self.errors:
            return "PASS"
        elif self.error_count == 0:
            return "PASS"
        return "FAIL"

    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0

    @property
    def status_label(self) -> str:
        """Human-readable status with warning qualifier."""
        if not self.errors:
            return "PASS"
        elif self.error_count == 0:
            return "PASS (warnings)"
        return "FAIL"

    @property
    def status_icon(self) -> str:
        if self.error_count > 0:
            return "\u274c"
        elif self.warning_count > 0 or self.info_count > 0:
            return "\u26a0\ufe0f"
        return "\u2705"

    def errors_by_code(self) -> Dict[str, List[ValidationError]]:
        """Group errors by their code."""
        grouped: Dict[str, List[ValidationError]] = {}
        for e in self.errors:
            grouped.setdefault(e.code, []).append(e)
        return grouped

    def errors_by_severity(self) -> Dict[Severity, List[ValidationError]]:
        """Group errors by severity."""
        grouped: Dict[Severity, List[ValidationError]] = {}
        for e in self.errors:
            grouped.setdefault(e.severity, []).append(e)
        return grouped


@dataclass
class FixSuggestion:
    """
    Tutorial-style fix suggestion for a validation error.

    Attributes:
        title: Fix title with icon
        steps: Ordered list of instructions
        code: Example corrected code snippet
        context: Surrounding source lines for reference
    """
    title: str
    steps: List[str] = field(default_factory=list)
    code: str = ""
    context: str = ""


@dataclass
class FileEntry:
    """
    Tracks a file loaded into the application.

    Attributes:
        path: Absolute file path
        result: Validation result (None if not yet validated)
        checked: Whether the file is selected for batch operations
    """
    path: str
    result: Optional[ValidationResult] = None
    checked: bool = True

    @property
    def status(self) -> str:
        if self.result is None:
            return "Pending"
        return self.result.status

    @property
    def status_display(self) -> str:
        if self.result is None:
            return "\u23f3 Pending"
        return f"{self.result.status_icon} {self.result.status_label}"

    @property
    def basename(self) -> str:
        import os
        return os.path.basename(self.path)


@dataclass
class MavenCoordinates:
    """Maven artifact coordinates."""
    group_id: str
    artifact_id: str
    version: Optional[str] = None

    def __str__(self) -> str:
        parts = [self.group_id, self.artifact_id]
        if self.version:
            parts.append(self.version)
        return ":".join(parts)


@dataclass
class ClassMetadata:
    """Metadata for a Java class extracted from a JAR."""
    class_name: str
    methods: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    source_jar: str = ""
    annotations: List[str] = field(default_factory=list)
    package: str = ""

    @property
    def method_names(self) -> List[str]:
        return list(self.methods.keys())

    @property
    def test_methods(self) -> List[str]:
        return [name for name, info in self.methods.items()
                if info.get("is_test", False)]
