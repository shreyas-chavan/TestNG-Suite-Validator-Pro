#!/usr/bin/env python3
"""
Main GUI Application - TestNG Validator Pro.
Modern tkinter-based interface with:
- File management panel with batch operations
- Validation with threaded execution
- Detailed error viewer with code editor
- Tutorial-style fix suggestions
- Auto-fix engine
- Maven JAR scanning
- Report export (HTML/CSV/JSON)
- Theme toggle (Light/Dark/System)
- Drag & drop support
- Recent files history
"""

import os
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Dict, List
from pathlib import Path

from ..config import (
    APP_TITLE, APP_VERSION, CODE_META, AUTO_FIXABLE_CODES,
    LIGHT_THEME, DARK_THEME, ThemeColors, AppConfig,
)
from ..models import (
    ValidationError, ValidationResult, FileEntry, Severity,
)
from ..validators import validate_file
from ..fixes import generate_fix, apply_auto_fix, batch_auto_fix
from ..utils import format_xml_content, format_xml_file, read_file_safe
from ..utils.file_utils import find_xml_files, validate_file_path
from ..exporters import export_html, export_csv, export_json

logger = logging.getLogger(__name__)

# Optional modern UI
try:
    import customtkinter as ctk
    HAS_MODERN_UI = True
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
except ImportError:
    HAS_MODERN_UI = False

# Optional syntax highlighting
try:
    from pygments import lex
    from pygments.lexers import XmlLexer
    from pygments.token import Token
    HAS_SYNTAX_HIGHLIGHT = True
except ImportError:
    HAS_SYNTAX_HIGHLIGHT = False


class ValidatorApp:
    """Main application window for TestNG Validator Pro."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(900, 600)
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)

        # State
        self.config = AppConfig.load()
        self.files: Dict[str, FileEntry] = {}
        self.metadata: Optional[dict] = None
        self.maven_metadata: Optional[dict] = None
        self.current_theme = self.config.theme
        self.colors = LIGHT_THEME
        self._validation_lock = threading.Lock()

        self._setup_styles()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_statusbar()
        self._setup_drag_drop()
        self._apply_theme(self.current_theme)

        # Restore window geometry
        if self.config.window_geometry:
            try:
                self.root.geometry(self.config.window_geometry)
            except tk.TclError:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("Application initialized")

    # ─── Setup ─────────────────────────────────────────────

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        c = self.colors

        # ── Global defaults ──
        self.style.configure(".", background=c.bg, foreground=c.fg, font=('Segoe UI', 10))

        # ── Treeview (file list) ──
        self.style.configure("Treeview",
            rowheight=30, font=('Consolas', 10),
            background=c.surface, foreground=c.fg,
            fieldbackground=c.surface, borderwidth=0,
        )
        self.style.configure("Treeview.Heading",
            font=('Segoe UI', 10, 'bold'),
            background=c.toolbar_bg, foreground=c.fg,
            borderwidth=0, relief="flat",
        )
        self.style.map("Treeview",
            background=[("selected", c.selection)],
            foreground=[("selected", c.fg)],
        )
        self.style.map("Treeview.Heading",
            background=[("active", c.border)],
        )

        # ── Buttons ──
        self.style.configure("Toolbar.TButton",
            padding=(12, 6), font=('Segoe UI', 9, 'bold'),
            background=c.toolbar_bg, foreground=c.fg,
            borderwidth=1, relief="flat",
        )
        self.style.map("Toolbar.TButton",
            background=[("active", c.selection), ("pressed", c.accent)],
            foreground=[("active", c.fg)],
        )
        self.style.configure("Accent.TButton",
            padding=(14, 7), font=('Segoe UI', 10, 'bold'),
            background=c.accent, foreground="#ffffff",
        )
        self.style.map("Accent.TButton",
            background=[("active", c.info)],
        )

        # ── Frames & Labels ──
        self.style.configure("TFrame", background=c.bg)
        self.style.configure("Toolbar.TFrame", background=c.toolbar_bg)
        self.style.configure("TLabel", background=c.bg, foreground=c.fg, font=('Segoe UI', 10))
        self.style.configure("Muted.TLabel", foreground=c.muted, font=('Segoe UI', 9))
        self.style.configure("Heading.TLabel", foreground=c.heading, font=('Segoe UI', 12, 'bold'))
        self.style.configure("TLabelframe", background=c.bg, foreground=c.fg)
        self.style.configure("TLabelframe.Label", background=c.bg, foreground=c.accent, font=('Segoe UI', 10, 'bold'))

        # ── Status bar ──
        self.style.configure("Status.TLabel",
            padding=(8, 4), font=('Consolas', 9),
            background=c.statusbar_bg, foreground=c.statusbar_fg,
        )

        # ── Separator ──
        self.style.configure("TSeparator", background=c.border)

        # ── Scrollbar ──
        self.style.configure("TScrollbar",
            background=c.surface, troughcolor=c.bg,
            borderwidth=0, arrowsize=12,
        )

        # ── PanedWindow ──
        self.style.configure("TPanedwindow", background=c.border)

        # ── Entry ──
        self.style.configure("TEntry",
            fieldbackground=c.surface, foreground=c.fg,
            insertcolor=c.fg, borderwidth=1,
        )

    def _setup_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        # File menu
        file_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_m)
        file_m.add_command(label="Add Files...", command=self.add_files, accelerator="Ctrl+O")
        file_m.add_command(label="Add Folder...", command=self.add_folder)
        file_m.add_separator()
        file_m.add_command(label="Load Metadata (JSON)...", command=self.load_metadata)
        file_m.add_command(label="Scan Maven JARs...", command=self.scan_maven_jars)
        file_m.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(file_m, tearoff=0)
        file_m.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()

        file_m.add_separator()
        file_m.add_command(label="Exit", command=self._on_close)

        # Validate menu
        val_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Validate", menu=val_m)
        val_m.add_command(label="Validate Selected", command=self.run_validation, accelerator="F5")
        val_m.add_command(label="Validate All", command=self.validate_all)
        val_m.add_separator()
        val_m.add_command(label="Format Selected", command=self.format_file_ui)

        # Export menu
        exp_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Export", menu=exp_m)
        exp_m.add_command(label="HTML Report...", command=lambda: self._export_report("html"))
        exp_m.add_command(label="CSV Report...", command=lambda: self._export_report("csv"))
        exp_m.add_command(label="JSON Report...", command=lambda: self._export_report("json"))

        # Theme menu
        theme_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Theme", menu=theme_m)
        theme_m.add_command(label="Light Mode", command=lambda: self._apply_theme("Light"))
        theme_m.add_command(label="Dark Mode", command=lambda: self._apply_theme("Dark"))
        theme_m.add_command(label="System Default", command=lambda: self._apply_theme("System"))

        # Help menu
        help_m = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_m)
        help_m.add_command(label="About", command=self._show_about)

        # Key bindings
        self.root.bind("<Control-o>", lambda e: self.add_files())
        self.root.bind("<F5>", lambda e: self.run_validation())

    def _setup_toolbar(self):
        tb = ttk.Frame(self.root, style="Toolbar.TFrame")
        tb.pack(fill=tk.X, padx=0, pady=0)

        # Inner padding frame
        inner = ttk.Frame(tb, style="Toolbar.TFrame")
        inner.pack(fill=tk.X, padx=10, pady=6)

        # ── Left: File actions ──
        ttk.Button(inner, text="Add Files", command=self.add_files,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(inner, text="Add Folder", command=self.add_folder,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=3)

        ttk.Separator(inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        # ── Validate (accent) ──
        ttk.Button(inner, text="Validate", command=self.run_validation,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(inner, text="Format", command=self.format_file_ui,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=3)

        ttk.Separator(inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        # ── Maven / Metadata ──
        ttk.Button(inner, text="Metadata", command=self.load_metadata,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(inner, text="Maven", command=self.scan_maven_jars,
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=3)

        ttk.Separator(inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        ttk.Button(inner, text="Report", command=lambda: self._export_report("html"),
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=3)

        # ── Right side ──
        ttk.Button(inner, text="Clear All", command=self.clear_all,
                   style="Toolbar.TButton").pack(side=tk.RIGHT, padx=(3, 0))

        self.theme_btn = ttk.Button(inner, text="Theme", command=self._toggle_theme,
                                    style="Toolbar.TButton")
        self.theme_btn.pack(side=tk.RIGHT, padx=3)

        # Metadata status indicator
        self.meta_lbl = tk.Label(inner, text="No Metadata", padx=10, pady=2,
                                 font=('Consolas', 9), relief=tk.FLAT)
        self.meta_lbl.pack(side=tk.RIGHT, padx=8)

        # Separator line below toolbar
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)

    def _setup_main_layout(self):
        pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Left panel: File list
        left = ttk.Frame(pane)
        pane.add(left, weight=3)

        # Drop zone hint label (hidden when files exist)
        self.drop_hint = tk.Label(
            left, text="Drop XML files here\nor use Add Files / Add Folder",
            font=('Segoe UI', 12), justify="center",
        )

        cols = ("check", "file", "status", "errors", "warnings")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("check", text="\u2611", command=self._toggle_all_checks)
        self.tree.heading("file", text="File")
        self.tree.heading("status", text="Status")
        self.tree.heading("errors", text="Err")
        self.tree.heading("warnings", text="Warn")
        self.tree.column("check", width=35, anchor="center", minwidth=35)
        self.tree.column("file", width=340, minwidth=150)
        self.tree.column("status", width=80, anchor="center", minwidth=70)
        self.tree.column("errors", width=50, anchor="center", minwidth=40)
        self.tree.column("warnings", width=55, anchor="center", minwidth=40)

        # Treeview scrollbar
        tree_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._update_summary)

        # Right panel: Summary
        right = ttk.LabelFrame(pane, text="Summary")
        pane.add(right, weight=1)

        self.summary = scrolledtext.ScrolledText(
            right, width=35, font=('Consolas', 10), wrap="word", state="disabled",
            borderwidth=0, relief="flat",
        )
        self.summary.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _setup_statusbar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="Ready.")
        self.status_lbl = ttk.Label(
            status_frame, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor="w", style="Status.TLabel",
        )
        self.status_lbl.pack(fill=tk.X, padx=2, pady=1)

    def _setup_drag_drop(self):
        """Setup drag and drop support using tkinterdnd2 if available,
        otherwise fall back to native Windows OLE drag & drop via tkdnd."""
        self._dnd_available = False
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._on_drop)
            self._dnd_available = True
            logger.info("Drag & drop enabled (tkinterdnd2)")
        except (ImportError, tk.TclError):
            # Try loading tkdnd directly (bundled with some Python installs)
            try:
                self.root.tk.eval('package require tkdnd')
                self.root.tk.eval(
                    'tkdnd::drop_target register %s *' % self.root._w
                )
                self.root.bind('<<Drop>>', self._on_drop_tkdnd)
                self._dnd_available = True
                logger.info("Drag & drop enabled (tkdnd)")
            except tk.TclError:
                logger.debug("No drag & drop library found — feature disabled")

        # Show drop hint if no files and DnD is available
        self._update_drop_hint()

    def _on_drop(self, event):
        """Handle dropped files (tkinterdnd2)."""
        paths = self.root.tk.splitlist(event.data)
        self._process_dropped_paths(paths)

    def _on_drop_tkdnd(self, event):
        """Handle dropped files (native tkdnd)."""
        data = event.data if hasattr(event, 'data') else ''
        paths = self.root.tk.splitlist(data) if data else []
        self._process_dropped_paths(paths)

    def _process_dropped_paths(self, paths):
        """Process a list of dropped file/folder paths."""
        added = 0
        for p in paths:
            p = p.strip('{}')  # Windows wraps paths with spaces in braces
            if os.path.isfile(p) and p.lower().endswith('.xml'):
                if self._add_single_file(p):
                    added += 1
            elif os.path.isdir(p):
                for xml_path in find_xml_files(p):
                    if self._add_single_file(xml_path):
                        added += 1
        if added:
            self._set_status(f"Added {added} file(s) via drag & drop")
            self._update_drop_hint()

    def _update_drop_hint(self):
        """Show or hide the drop hint overlay based on file count."""
        try:
            if not self.files:
                self.drop_hint.place(relx=0.3, rely=0.4, anchor="center")
            else:
                self.drop_hint.place_forget()
        except (tk.TclError, AttributeError):
            pass

    # ─── Theme ─────────────────────────────────────────────

    def _apply_theme(self, theme: str):
        self.current_theme = theme
        self.config.theme = theme

        if theme == "Dark":
            self.colors = DARK_THEME
        else:
            self.colors = LIGHT_THEME

        c = self.colors

        # Re-apply all ttk styles with new colors
        self._setup_styles()

        # Apply to root window
        try:
            self.root.configure(bg=c.bg)
        except tk.TclError:
            pass

        # Apply to tk.Text widgets (summary)
        try:
            self.summary.configure(bg=c.surface, fg=c.fg, insertbackground=c.fg,
                                   selectbackground=c.selection, selectforeground=c.fg)
        except (tk.TclError, AttributeError):
            pass

        # Apply to metadata label
        try:
            if self.maven_metadata or self.metadata:
                self.meta_lbl.configure(bg=c.accent, fg="#ffffff")
            else:
                self.meta_lbl.configure(bg=c.surface, fg=c.muted)
        except (tk.TclError, AttributeError):
            pass

        # Apply to drop hint
        try:
            self.drop_hint.configure(bg=c.bg, fg=c.muted)
        except (tk.TclError, AttributeError):
            pass

        # Apply to menus
        try:
            for menu_widget in self.root.winfo_children():
                if isinstance(menu_widget, tk.Menu):
                    self._style_menu(menu_widget)
        except Exception:
            pass

        if HAS_MODERN_UI:
            try:
                ctk.set_appearance_mode(theme)
            except Exception:
                pass

        try:
            self.theme_btn.config(text=f"{theme} Theme")
        except (tk.TclError, AttributeError):
            pass
        self._set_status(f"Theme: {theme}")

    def _style_menu(self, menu):
        """Recursively style menu widgets."""
        c = self.colors
        try:
            menu.configure(bg=c.menu_bg, fg=c.menu_fg, activebackground=c.accent,
                          activeforeground="#ffffff", relief="flat", borderwidth=0)
            for i in range(menu.index("end") + 1 if menu.index("end") is not None else 0):
                try:
                    submenu = menu.nametowidget(menu.entrycget(i, "menu"))
                    self._style_menu(submenu)
                except (tk.TclError, KeyError):
                    pass
        except (tk.TclError, TypeError):
            pass

    def _toggle_theme(self):
        themes = ["Light", "Dark", "System"]
        idx = themes.index(self.current_theme) if self.current_theme in themes else 0
        self._apply_theme(themes[(idx + 1) % len(themes)])

    # ─── File Management ───────────────────────────────────

    def add_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
            initialdir=self.config.last_directory or None,
        )
        added = 0
        for p in paths:
            if self._add_single_file(p):
                added += 1
        if paths:
            self.config.last_directory = str(Path(paths[0]).parent)
        if added:
            self._set_status(f"Added {added} file(s)")

    def add_folder(self):
        folder = filedialog.askdirectory(initialdir=self.config.last_directory or None)
        if not folder:
            return
        self.config.last_directory = folder
        xml_files = find_xml_files(folder)
        added = 0
        for p in xml_files:
            if self._add_single_file(p):
                added += 1
        self._set_status(f"Added {added} file(s) from folder")

    def _add_single_file(self, path: str) -> bool:
        path = str(Path(path).resolve())
        if path in self.files:
            return False

        valid, err_msg = validate_file_path(path)
        if not valid:
            logger.warning("Skipping invalid file %s: %s", path, err_msg)
            return False

        entry = FileEntry(path=path)
        self.files[path] = entry
        self.tree.insert("", "end", iid=path,
                         values=("\u2611", entry.basename, "\u23f3 Pending", "-", "-"))
        self.config.add_recent_file(path)
        self._update_recent_menu()
        self._update_drop_hint()
        return True

    def _update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for path in self.config.recent_files[:10]:
            basename = os.path.basename(path)
            self.recent_menu.add_command(
                label=basename,
                command=lambda p=path: self._add_single_file(p),
            )

    # ─── Check Toggle ──────────────────────────────────────

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) == "#1":
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self._toggle_check(row_id)
            return "break"

    def _toggle_check(self, item_id: str):
        entry = self.files.get(item_id)
        if not entry:
            return
        entry.checked = not entry.checked
        icon = "\u2611" if entry.checked else "\u2610"
        current = self.tree.item(item_id, "values")
        self.tree.item(item_id, values=(icon, *current[1:]))

    def _toggle_all_checks(self):
        if not self.files:
            return
        first_key = next(iter(self.files))
        target = not self.files[first_key].checked
        icon = "\u2611" if target else "\u2610"
        for item_id, entry in self.files.items():
            entry.checked = target
            vals = self.tree.item(item_id, "values")
            self.tree.item(item_id, values=(icon, *vals[1:]))

    def _get_selected_files(self) -> List[str]:
        return [p for p, e in self.files.items() if e.checked]

    # ─── Validation ────────────────────────────────────────

    def run_validation(self):
        targets = self._get_selected_files()
        if not targets:
            messagebox.showwarning("No Files", "No files selected for validation.")
            return
        self._set_status(f"Validating {len(targets)} file(s)...")
        threading.Thread(target=self._validate_task, args=(targets,), daemon=True).start()

    def validate_all(self):
        for entry in self.files.values():
            entry.checked = True
        self.run_validation()

    def _validate_task(self, targets: List[str]):
        with self._validation_lock:
            # Merge metadata sources
            merged_meta = None
            if self.metadata or self.maven_metadata:
                merged_meta = {}
                if self.metadata:
                    merged_meta.update(self.metadata)
                if self.maven_metadata:
                    merged_meta.update(self.maven_metadata)

            for path in targets:
                try:
                    result = validate_file(path, merged_meta)
                except Exception as e:
                    logger.error("Validation crash for %s: %s", path, e)
                    result = ValidationResult(
                        file_path=path,
                        errors=[ValidationError(
                            code="E000", message=f"Crash: {e}",
                            severity=Severity.ERROR,
                        )],
                    )

                self.files[path].result = result
                self.root.after(0, self._update_tree_row, path)

            self.root.after(0, self._set_status, f"Validation complete. {len(targets)} file(s) processed.")

    def _update_tree_row(self, path: str):
        entry = self.files.get(path)
        if not entry or not self.tree.exists(path):
            return
        result = entry.result
        if result is None:
            return
        icon = "\u2611" if entry.checked else "\u2610"
        self.tree.item(path, values=(
            icon,
            entry.basename,
            entry.status_display,
            result.error_count or "-",
            result.warning_count or "-",
        ))
        # Update summary if this file is selected
        sel = self.tree.selection()
        if sel and sel[0] == path:
            self._update_summary(None)

    # ─── Summary ───────────────────────────────────────────

    def _update_summary(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        entry = self.files.get(sel[0])
        if not entry:
            return

        self.summary.config(state="normal")
        self.summary.delete("1.0", tk.END)

        txt = f"File: {entry.basename}\n"
        txt += f"Path: {entry.path}\n"
        txt += f"Status: {entry.status_display}\n\n"

        if entry.result and entry.result.errors:
            txt += f"Errors: {entry.result.error_count}\n"
            txt += f"Warnings: {entry.result.warning_count}\n"
            txt += f"Duration: {entry.result.duration_ms:.1f}ms\n\n"

            # Group by code
            by_code = entry.result.errors_by_code()
            txt += "Breakdown:\n"
            for code, errs in by_code.items():
                desc = CODE_META.get(code, (code, ""))[0]
                txt += f"  [{code}] x{len(errs)}: {desc}\n"

            txt += f"\nFirst 10 issues:\n"
            for e in entry.result.errors[:10]:
                if e.severity == Severity.ERROR:
                    icon = "\u274c"
                elif e.severity == Severity.WARNING:
                    icon = "\u26a0"
                else:
                    icon = "\u2139"
                txt += f"  {icon} L{e.line or '?'} [{e.code}] {e.message}\n"
        elif entry.result:
            txt += "\u2705 No issues found!\n"
        else:
            txt += "Not yet validated.\n"

        self.summary.insert("1.0", txt)
        self.summary.config(state="disabled")

    # ─── Details Window ────────────────────────────────────

    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) != "#1":
            sel = self.tree.selection()
            if sel:
                self._open_details(sel[0])

    def _open_details(self, path: str):
        entry = self.files.get(path)
        if not entry:
            return

        c = self.colors
        win = tk.Toplevel(self.root)
        win.title(f"{entry.basename} — Editor")
        win.configure(bg=c.bg)
        win.minsize(800, 500)
        try:
            win.state('zoomed')
        except tk.TclError:
            win.geometry("1200x800")

        # Main layout: Vertical split (upper: errors+editor, lower: fix panel)
        pane = ttk.PanedWindow(win, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        upper = ttk.PanedWindow(pane, orient=tk.HORIZONTAL)
        pane.add(upper, weight=3)

        # ── Error List ──
        err_fr = ttk.LabelFrame(upper, text="Issues")
        upper.add(err_fr, weight=1)

        err_list = tk.Listbox(err_fr, font=('Consolas', 10), activestyle='dotbox',
                              bg=c.surface, fg=c.fg, selectbackground=c.selection,
                              selectforeground=c.fg, borderwidth=0, highlightthickness=0)
        err_scroll = ttk.Scrollbar(err_fr, orient=tk.VERTICAL, command=err_list.yview)
        err_list.configure(yscrollcommand=err_scroll.set)
        err_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        err_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Code Editor ──
        code_fr = ttk.LabelFrame(upper, text="Editor")
        upper.add(code_fr, weight=2)

        # Editor toolbar
        editor_tb = ttk.Frame(code_fr)
        editor_tb.pack(fill=tk.X, pady=(2, 2), padx=2)

        stat_lbl = tk.Label(editor_tb, text="Unchanged", fg=c.muted, bg=c.bg,
                            font=('Consolas', 9))
        stat_lbl.pack(side=tk.RIGHT, padx=5)

        ttk.Button(editor_tb, text="Save & Validate",
                   command=lambda: self._save_and_revalidate(path, code_txt, err_list, stat_lbl, win),
                   style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(editor_tb, text="Fix Selected",
                   command=lambda: self._auto_fix_single(path, err_list, code_txt, stat_lbl, win),
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(editor_tb, text="Fix All",
                   command=lambda: self._auto_fix_batch(path, err_list, code_txt, stat_lbl, win),
                   style="Toolbar.TButton").pack(side=tk.LEFT, padx=2)

        # Code area with gutter
        code_cont = ttk.Frame(code_fr)
        code_cont.pack(fill=tk.BOTH, expand=True)

        gutter = tk.Text(code_cont, width=5, bg=c.gutter_bg, fg=c.muted,
                         state="disabled", font=('Consolas', 10), takefocus=0,
                         cursor="arrow", borderwidth=0, highlightthickness=0,
                         padx=4)
        gutter.pack(side=tk.LEFT, fill=tk.Y)

        code_txt = tk.Text(code_cont, wrap="none", font=('Consolas', 10), undo=True,
                           bg=c.editor_bg, fg=c.fg, insertbackground=c.accent,
                           selectbackground=c.selection, selectforeground=c.fg,
                           borderwidth=0, highlightthickness=0, padx=4, pady=2)
        code_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vs = ttk.Scrollbar(code_cont,
                           command=lambda *a: (code_txt.yview(*a), gutter.yview(*a)))
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        code_txt.config(yscrollcommand=lambda *a: (vs.set(*a), gutter.yview_moveto(a[0])))

        # Error highlighting tag
        code_txt.tag_config("err_line", background=c.err_highlight)

        # ── Fix Panel ──
        fix_fr = ttk.LabelFrame(pane, text="Fix Suggestions")
        pane.add(fix_fr, weight=1)

        fix_txt = scrolledtext.ScrolledText(
            fix_fr, bg=c.surface, fg=c.fg, font=('Segoe UI', 10), wrap="word",
            borderwidth=0, highlightthickness=0, padx=8, pady=4,
            selectbackground=c.selection, selectforeground=c.fg,
        )
        fix_txt.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for rich formatting
        fix_txt.tag_config("header", font=('Segoe UI', 11, 'bold'), foreground=c.accent)
        fix_txt.tag_config("bold", font=('Segoe UI', 10, 'bold'), foreground=c.heading)
        fix_txt.tag_config("context", font=('Consolas', 10),
                           background=c.highlight, foreground=c.fg, lmargin1=10)
        fix_txt.tag_config("code", font=('Consolas', 10),
                           background=c.code_bg, foreground=c.success, lmargin1=10)

        # Load file content
        file_lines: List[str] = []
        content, enc = read_file_safe(path)
        if content:
            code_txt.insert("1.0", content)
            file_lines = content.splitlines()
            self._update_gutter(code_txt, gutter)

        # Populate error list
        errors = entry.result.errors if entry.result else []
        self._populate_errors(err_list, errors)

        # Error selection handler
        def on_select(evt):
            sel_idx = err_list.curselection()
            if not sel_idx or not entry.result:
                return
            err = entry.result.errors[sel_idx[0]]

            # Highlight error line
            code_txt.tag_remove("err_line", "1.0", "end")
            if err.line:
                code_txt.tag_add("err_line", f"{err.line}.0", f"{err.line}.end")
                code_txt.see(f"{err.line}.0")

            # Render fix suggestion
            fix = generate_fix(err, file_lines)
            fix_txt.config(state="normal")
            fix_txt.delete("1.0", "end")

            fix_txt.insert("end", f"{fix.title}\n\n", "header")

            if fix.context:
                fix_txt.insert("end", "\U0001f4cd Your Code (Context):\n", "bold")
                fix_txt.insert("end", fix.context + "\n\n", "context")

            for step in fix.steps:
                fix_txt.insert("end", f"{step}\n")

            if fix.code:
                fix_txt.insert("end", "\n\U0001f4a1 Example Fix:\n", "bold")
                fix_txt.insert("end", fix.code, "code")

            fix_txt.config(state="disabled")

        err_list.bind("<<ListboxSelect>>", on_select)
        code_txt.bind("<Key>", lambda e: stat_lbl.config(text="\u2022 Modified", fg="blue"))

    # ─── Editor Actions ────────────────────────────────────

    def _update_gutter(self, txt: tk.Text, gutter: tk.Text):
        lines = int(txt.index("end-1c").split('.')[0])
        gutter.config(state="normal")
        gutter.delete("1.0", tk.END)
        gutter.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        gutter.config(state="disabled")

    def _populate_errors(self, listbox: tk.Listbox, errors: List[ValidationError]):
        listbox.delete(0, tk.END)
        for e in errors:
            if e.severity == Severity.ERROR:
                icon = "\u274c"
                color = self.colors.error
            elif e.severity == Severity.WARNING:
                icon = "\u26a0"
                color = self.colors.warning
            else:
                icon = "\u2139"
                color = self.colors.info
            listbox.insert(tk.END, f"{icon} L{e.line or '?'} [{e.code}] {e.message}")
            listbox.itemconfig(tk.END, fg=color)

    def _save_and_revalidate(self, path, editor, err_list, stat_lbl, parent_win):
        content = editor.get("1.0", "end-1c")
        try:
            formatted = format_xml_content(content)
            if formatted:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                editor.delete("1.0", tk.END)
                editor.insert("1.0", formatted)
                fmt_msg = "Saved & Formatted"
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fmt_msg = "Saved (Syntax Error)"

            # Re-validate
            merged = self._get_merged_metadata()
            result = validate_file(path, merged)
            self.files[path].result = result
            self._update_tree_row(path)
            self._populate_errors(err_list, result.errors)

            gutter = editor.master.winfo_children()[0]
            self._update_gutter(editor, gutter)

            color = "green" if result.is_valid else "red"
            stat_lbl.config(text=f"{fmt_msg}. {len(result.errors)} issues", fg=color)

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=parent_win)

    def _auto_fix_single(self, path, err_list, editor, stat_lbl, parent_win):
        sel_idx = err_list.curselection()
        if not sel_idx:
            messagebox.showwarning("No Selection", "Select an error to fix.", parent=parent_win)
            return

        entry = self.files.get(path)
        if not entry or not entry.result:
            return

        error = entry.result.errors[sel_idx[0]]

        if error.code not in AUTO_FIXABLE_CODES:
            messagebox.showinfo("Not Fixable",
                              f"Error {error.code} cannot be auto-fixed.\nUse the tutorial guidance.",
                              parent=parent_win)
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()

            success, msg = apply_auto_fix(error, file_lines)
            if success:
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(file_lines)

                editor.delete("1.0", tk.END)
                editor.insert("1.0", "".join(file_lines))
                self._save_and_revalidate(path, editor, err_list, stat_lbl, parent_win)

                parent_win.lift()
                parent_win.focus_force()
                messagebox.showinfo("Fixed", f"\u2705 {msg}", parent=parent_win)
            else:
                messagebox.showwarning("Cannot Fix", msg, parent=parent_win)

        except Exception as e:
            messagebox.showerror("Error", f"Auto-fix failed: {e}", parent=parent_win)

    def _auto_fix_batch(self, path, err_list, editor, stat_lbl, parent_win):
        entry = self.files.get(path)
        if not entry or not entry.result or not entry.result.errors:
            messagebox.showinfo("No Errors", "No errors to fix!", parent=parent_win)
            return

        errors = entry.result.errors
        fixable = sum(1 for e in errors if e.code in AUTO_FIXABLE_CODES)

        if fixable == 0:
            messagebox.showinfo("No Fixable", "No auto-fixable errors found.", parent=parent_win)
            return

        if not messagebox.askyesno("Batch Fix",
                                    f"Auto-fix {fixable} fixable error(s) out of {len(errors)} total?\n\n"
                                    "A backup will be created.",
                                    parent=parent_win):
            return

        try:
            fixed, total, msg = batch_auto_fix(path, errors, create_backup=True)
            if fixed > 0:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                editor.delete("1.0", tk.END)
                editor.insert("1.0", content)
                self._save_and_revalidate(path, editor, err_list, stat_lbl, parent_win)

                parent_win.lift()
                parent_win.focus_force()
                messagebox.showinfo("Batch Fix Complete", msg, parent=parent_win)
            else:
                messagebox.showinfo("No Fixes", msg, parent=parent_win)
        except Exception as e:
            messagebox.showerror("Error", f"Batch fix failed: {e}", parent=parent_win)

    # ─── Format ────────────────────────────────────────────

    def format_file_ui(self):
        targets = self._get_selected_files()
        if not targets:
            messagebox.showwarning("No Files", "No files selected.")
            return
        count = 0
        for p in targets:
            ok, _ = format_xml_file(p)
            if ok:
                count += 1
        messagebox.showinfo("Format", f"Formatted {count}/{len(targets)} file(s).")

    # ─── Metadata & Maven ──────────────────────────────────

    def load_metadata(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as f:
                self.metadata = json.load(f)
            self.meta_lbl.config(
                text=f"\u2705 Meta: {len(self.metadata)} classes",
                bg="#e8f5e9", fg="#2e7d32",
            )
            self._set_status(f"Loaded metadata: {len(self.metadata)} classes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load metadata:\n{e}")

    def scan_maven_jars(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Maven JAR Scanner")
        dialog.geometry("650x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Scan Maven JARs for Metadata",
                  font=('Segoe UI', 14, 'bold')).pack(pady=10)
        ttk.Label(dialog, text="Choose an option below (metadata accumulates across scans):",
                  font=('Segoe UI', 10)).pack(pady=5)

        # Option 1: Multiple JAR files
        f1 = ttk.LabelFrame(dialog, text="Option 1: Select JAR File(s) - supports multiple selection", padding=10)
        f1.pack(fill=tk.X, padx=20, pady=6)
        jar_var = tk.StringVar()
        jar_entry = ttk.Entry(f1, textvariable=jar_var, width=50)
        jar_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def browse_jars():
            paths = filedialog.askopenfilenames(
                title="Select JAR(s)", filetypes=[("JAR Files", "*.jar"), ("All Files", "*.*")],
                parent=dialog,
            )
            if paths:
                jar_var.set(";".join(paths))

        browse_jar_btn = ttk.Button(f1, text="Browse JAR(s)", command=browse_jars)
        browse_jar_btn.pack(side=tk.LEFT, padx=(4, 0))

        # Option 2: Folder
        f2 = ttk.LabelFrame(dialog, text="Option 2: Select JAR Folder", padding=10)
        f2.pack(fill=tk.X, padx=20, pady=6)
        folder_var = tk.StringVar()
        folder_entry = ttk.Entry(f2, textvariable=folder_var, width=50)
        folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def browse_folder():
            path = filedialog.askdirectory(title="Select Folder", parent=dialog)
            if path:
                folder_var.set(path)

        browse_folder_btn = ttk.Button(f2, text="Browse Folder", command=browse_folder)
        browse_folder_btn.pack(side=tk.LEFT, padx=(4, 0))

        # Option 3: Maven coordinates
        f3 = ttk.LabelFrame(dialog, text="Option 3: Maven Coordinates", padding=10)
        f3.pack(fill=tk.X, padx=20, pady=6)
        ttk.Label(f3, text="Group ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        group_var = tk.StringVar()
        ttk.Entry(f3, textvariable=group_var, width=40).grid(row=0, column=1, padx=5)
        ttk.Label(f3, text="Artifact ID:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        artifact_var = tk.StringVar()
        ttk.Entry(f3, textvariable=artifact_var, width=40).grid(row=1, column=1, padx=5)

        # Status display
        status_frame = ttk.LabelFrame(dialog, text="Metadata Status", padding=6)
        status_frame.pack(fill=tk.X, padx=20, pady=6)
        current_count = len(self.maven_metadata) if self.maven_metadata else 0
        status_var = tk.StringVar(value=f"Currently loaded: {current_count} classes")
        ttk.Label(status_frame, textvariable=status_var, font=('Segoe UI', 9)).pack(anchor=tk.W)

        def start_scan():
            jar_str = jar_var.get().strip()
            folder = folder_var.get().strip()
            gid = group_var.get().strip()
            aid = artifact_var.get().strip()

            if jar_str:
                jar_paths = [j.strip() for j in jar_str.split(";") if j.strip()]
                self._scan_multiple_jars(jar_paths, dialog)
            elif folder:
                self._scan_jar_folder(folder, dialog)
            elif gid and aid:
                self._scan_maven_coords(gid, aid, dialog)
            else:
                messagebox.showwarning("Input Required",
                                       "Select JAR(s), a folder, or enter Maven coordinates.",
                                       parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Start Scan", command=start_scan).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Clear Metadata",
                   command=lambda: self._clear_maven_metadata(status_var)).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=8)

    def _scan_multiple_jars(self, jar_paths: List[str], dialog: tk.Toplevel):
        """Scan one or more JAR files and accumulate metadata."""
        missing = [j for j in jar_paths if not os.path.exists(j)]
        if missing:
            messagebox.showerror("Error", f"JAR(s) not found:\n" + "\n".join(missing), parent=dialog)
            return
        try:
            from ..maven.extractor import MavenMetadataExtractor
            dialog.destroy()
            self._set_status(f"Scanning {len(jar_paths)} JAR file(s)...")
            extractor = MavenMetadataExtractor()
            all_meta = {}
            for jar_path in jar_paths:
                meta = extractor.extract_from_jar(jar_path)
                all_meta.update(meta)
            names = ", ".join(os.path.basename(j) for j in jar_paths)
            self._apply_maven_metadata(all_meta, f"{len(jar_paths)} JAR(s): {names}")
        except Exception as e:
            messagebox.showerror("Error", f"Scan failed:\n{e}")
            self._set_status("Ready")

    def _scan_jar_folder(self, folder: str, dialog: tk.Toplevel):
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder not found: {folder}", parent=dialog)
            return
        try:
            from ..maven.extractor import MavenMetadataExtractor
            import glob
            jars = glob.glob(os.path.join(folder, "*.jar"))
            if not jars:
                messagebox.showwarning("No JARs", f"No JAR files in: {folder}", parent=dialog)
                return
            dialog.destroy()
            self._set_status(f"Scanning {len(jars)} JAR files...")
            extractor = MavenMetadataExtractor()
            all_meta = {}
            for jar in jars:
                all_meta.update(extractor.extract_from_jar(jar))
            self._apply_maven_metadata(all_meta, f"{len(jars)} JARs from folder")
        except Exception as e:
            messagebox.showerror("Error", f"Scan failed:\n{e}")
            self._set_status("Ready")

    def _scan_maven_coords(self, gid: str, aid: str, dialog: tk.Toplevel):
        try:
            from ..maven.extractor import MavenMetadataExtractor
            dialog.destroy()
            self._set_status(f"Scanning Maven repo for {gid}:{aid}...")
            extractor = MavenMetadataExtractor()
            metadata = extractor.scan_project_jars([gid], [aid])
            self._apply_maven_metadata(metadata, f"Maven: {gid}:{aid}")
        except Exception as e:
            messagebox.showerror("Error", f"Scan failed:\n{e}")
            self._set_status("Ready")

    def _apply_maven_metadata(self, metadata: dict, source: str):
        c = self.colors
        if metadata:
            if self.maven_metadata is None:
                self.maven_metadata = {}
            self.maven_metadata.update(metadata)
            total = len(self.maven_metadata)
            self.meta_lbl.config(
                text=f"Maven: {total} classes",
                bg=c.accent, fg="#ffffff",
            )
            messagebox.showinfo("Success",
                f"Extracted {len(metadata)} classes from {source}\n"
                f"Total metadata: {total} classes")
        else:
            messagebox.showwarning("No Data", "No classes found.")
        self._set_status("Ready")

    def _clear_maven_metadata(self, status_var=None):
        """Clear all loaded Maven metadata."""
        c = self.colors
        self.maven_metadata = None
        self.meta_lbl.config(
            text="No Metadata", bg=c.surface, fg=c.muted,
        )
        if status_var:
            status_var.set("Currently loaded: 0 classes")
        self._set_status("Maven metadata cleared.")

    def _get_merged_metadata(self) -> Optional[dict]:
        if not self.metadata and not self.maven_metadata:
            return None
        merged = {}
        if self.metadata:
            merged.update(self.metadata)
        if self.maven_metadata:
            merged.update(self.maven_metadata)
        return merged

    # ─── Export ─────────────────────────────────────────────

    def _export_report(self, fmt: str):
        targets = self._get_selected_files()
        if not targets:
            messagebox.showwarning("No Files", "No files selected.")
            return

        results = [self.files[p].result for p in targets if self.files[p].result]
        if not results:
            messagebox.showwarning("No Results", "Validate files first.")
            return

        ext_map = {"html": ".html", "csv": ".csv", "json": ".json"}
        ft_map = {"html": [("HTML", "*.html")], "csv": [("CSV", "*.csv")], "json": [("JSON", "*.json")]}

        path = filedialog.asksaveasfilename(
            defaultextension=ext_map[fmt],
            filetypes=ft_map[fmt],
        )
        if not path:
            return

        success = False
        if fmt == "html":
            success = export_html(results, path)
        elif fmt == "csv":
            success = export_csv(results, path)
        elif fmt == "json":
            success = export_json(results, path)

        if success:
            messagebox.showinfo("Export", f"Report saved to:\n{path}")
        else:
            messagebox.showerror("Error", "Export failed. Check logs.")

    # ─── Utility ───────────────────────────────────────────

    def clear_all(self):
        self.files.clear()
        self.tree.delete(*self.tree.get_children())
        self.summary.config(state="normal")
        self.summary.delete("1.0", tk.END)
        self.summary.config(state="disabled")
        self._update_drop_hint()
        self._set_status("Cleared.")

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n\n"
            f"A production-grade TestNG XML Suite Validator.\n\n"
            f"Features:\n"
            f"  \u2022 42+ validation rules\n"
            f"  \u2022 Tutorial-style fix suggestions\n"
            f"  \u2022 Auto-fix engine\n"
            f"  \u2022 Maven JAR metadata scanning\n"
            f"  \u2022 HTML/CSV/JSON report export\n"
            f"  \u2022 Dark/Light theme support\n\n"
            f"Python {os.sys.version.split()[0]}"
        )

    def _on_close(self):
        try:
            self.config.window_geometry = self.root.geometry()
            self.config.save()
        except Exception:
            pass
        self.root.destroy()
