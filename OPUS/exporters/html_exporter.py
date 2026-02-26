#!/usr/bin/env python3
"""
HTML report exporter with modern styling.
"""

import os
import logging
from datetime import datetime
from typing import List

from ..models import ValidationResult, Severity
from ..config import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #f8f9fa; color: #212529; line-height: 1.6; padding: 24px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ color: #1976d2; margin-bottom: 8px; font-size: 1.8rem; }}
  .subtitle {{ color: #6c757d; margin-bottom: 24px; font-size: 0.9rem; }}
  .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
  .card .number {{ font-size: 2rem; font-weight: bold; }}
  .card .label {{ font-size: 0.85rem; color: #6c757d; }}
  .card.pass .number {{ color: #388e3c; }}
  .card.fail .number {{ color: #d32f2f; }}
  .card.warn .number {{ color: #f57c00; }}
  .card.total .number {{ color: #1976d2; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
  th {{ background: #1976d2; color: white; padding: 12px 16px; text-align: left; font-weight: 600; }}
  td {{ padding: 10px 16px; border-bottom: 1px solid #e9ecef; }}
  tr:hover {{ background: #f1f8ff; }}
  .status-pass {{ color: #388e3c; font-weight: 600; }}
  .status-fail {{ color: #d32f2f; font-weight: 600; }}
  .status-warn {{ color: #f57c00; font-weight: 600; }}
  .errors-section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .errors-section h3 {{ color: #495057; margin-bottom: 12px; border-bottom: 2px solid #e9ecef; padding-bottom: 8px; }}
  .error-item {{ padding: 8px 12px; margin: 4px 0; border-left: 4px solid; border-radius: 0 4px 4px 0; background: #fafafa; font-family: 'Consolas', monospace; font-size: 0.85rem; }}
  .error-item.severity-error {{ border-color: #d32f2f; }}
  .error-item.severity-warning {{ border-color: #f57c00; }}
  .footer {{ text-align: center; color: #6c757d; font-size: 0.8rem; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e9ecef; }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <p class="subtitle">Generated on {timestamp} by {app_name} v{app_version}</p>
  <div class="summary-cards">
    <div class="card total"><div class="number">{total_files}</div><div class="label">Total Files</div></div>
    <div class="card pass"><div class="number">{pass_count}</div><div class="label">Passed</div></div>
    <div class="card fail"><div class="number">{fail_count}</div><div class="label">Failed</div></div>
    <div class="card warn"><div class="number">{warn_count}</div><div class="label">Warnings Only</div></div>
  </div>
  <table>
    <thead><tr><th>File</th><th>Status</th><th>Errors</th><th>Warnings</th><th>Duration</th></tr></thead>
    <tbody>{file_rows}</tbody>
  </table>
  {error_details}
  <div class="footer">{app_name} v{app_version} &mdash; TestNG XML Validation Report</div>
</div>
</body>
</html>"""


def export_html(results: List[ValidationResult], output_path: str, title: str = "Validation Report") -> bool:
    """
    Export validation results as a styled HTML report.

    Args:
        results: List of ValidationResult objects
        output_path: Output HTML file path
        title: Report title

    Returns:
        True on success
    """
    try:
        pass_count = sum(1 for r in results if r.status == "PASS")
        fail_count = sum(1 for r in results if r.status == "FAIL")
        warn_count = sum(1 for r in results if r.status == "WARN")

        # Build file rows
        file_rows = ""
        for r in results:
            status_cls = f"status-{r.status.lower()}"
            file_rows += (
                f"<tr>"
                f"<td>{os.path.basename(r.file_path)}</td>"
                f"<td class='{status_cls}'>{r.status_icon} {r.status}</td>"
                f"<td>{r.error_count}</td>"
                f"<td>{r.warning_count}</td>"
                f"<td>{r.duration_ms:.1f}ms</td>"
                f"</tr>"
            )

        # Build error details
        error_details = ""
        for r in results:
            if r.errors:
                error_details += f'<div class="errors-section"><h3>{os.path.basename(r.file_path)}</h3>'
                for e in r.errors:
                    sev_cls = f"severity-{e.severity.value.lower()}"
                    error_details += (
                        f'<div class="error-item {sev_cls}">'
                        f"[{e.code}] Line {e.line or '?'}: {e.message}"
                        f"</div>"
                    )
                error_details += "</div>"

        html = HTML_TEMPLATE.format(
            title=title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            app_name=APP_NAME,
            app_version=APP_VERSION,
            total_files=len(results),
            pass_count=pass_count,
            fail_count=fail_count,
            warn_count=warn_count,
            file_rows=file_rows,
            error_details=error_details,
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info("HTML report exported to %s", output_path)
        return True

    except Exception as e:
        logger.error("Failed to export HTML report: %s", e)
        return False
