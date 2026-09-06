from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .gui_model import (
    ALL_RESULTS,
    AMBIGUOUS_UNIQUE,
    IDENTITY_ISSUES,
    NO_CLASSIFIED_MODS,
    UNMATCHED_UNIQUE,
    ResultRow,
    build_result_rows,
    collect_selected_replacements,
)
from .patcher import (
    apply_mod_match_to_line,
    write_mod_matches_to_file,
)
from .report import format_analysis_report
from .workflow import analyze_files


FILTER_VALUES = (
    ALL_RESULTS,
    "Replacement",
    "Unresolved",
    "Ambiguous",
    "Already current",
    IDENTITY_ISSUES,
    NO_CLASSIFIED_MODS,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _existing_path(path: Path) -> str:
    return str(path) if path.is_file() else ""


class UniqueModIdPatcherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PoB Unique Mod-ID Patcher")
        self.root.geometry("1220x780")
        self.root.minsize(920, 620)

        repository_root = _repository_root()
        self.dataset_path = tk.StringVar(
            value=_existing_path(repository_root / "uniques.json")
        )
        self.mod_text_path = tk.StringVar(
            value=_existing_path(
                repository_root / "src" / "Data" / "ModItemExclusive.lua"
            )
        )
        self.unique_lua_path = tk.StringVar(
            value=_existing_path(
                repository_root
                / "src"
                / "Export"
                / "Uniques"
                / "boots.lua"
            )
        )
        self.search_text = tk.StringVar()
        self.status_filter = tk.StringVar(value=ALL_RESULTS)
        self.summary_text = tk.StringVar(
            value="Choose the input files, then select Analyze."
        )
        self.selection_text = tk.StringVar(value="0 safe replacements selected")
        self.status_text = tk.StringVar(value="Ready")

        self.analyses = ()
        self.result_rows: tuple[ResultRow, ...] = ()
        self.rows_by_key: dict[str, ResultRow] = {}
        self.selected_keys: set[str] = set()
        self.analyzed_paths: tuple[Path, Path, Path] | None = None

        self._build_layout()
        self.search_text.trace_add(
            "write",
            lambda *_: self._refresh_result_tree(),
        )
        for path_variable in (
            self.dataset_path,
            self.mod_text_path,
            self.unique_lua_path,
        ):
            path_variable.trace_add(
                "write",
                self._mark_analysis_stale,
            )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        input_frame = ttk.LabelFrame(
            main_frame,
            text="Inputs",
            padding=10,
        )
        input_frame.grid(row=0, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        self._add_path_row(
            input_frame,
            row=0,
            label="Authoritative JSON",
            variable=self.dataset_path,
            browse_command=lambda: self._browse_for_file(
                self.dataset_path,
                "Choose uniques.json",
                (("JSON files", "*.json"), ("All files", "*.*")),
            ),
        )
        self._add_path_row(
            input_frame,
            row=1,
            label="Mod text resolver",
            variable=self.mod_text_path,
            browse_command=lambda: self._browse_for_file(
                self.mod_text_path,
                "Choose ModItemExclusive.lua",
                (("Lua files", "*.lua"), ("All files", "*.*")),
            ),
        )
        self._add_path_row(
            input_frame,
            row=2,
            label="Unique export",
            variable=self.unique_lua_path,
            browse_command=lambda: self._browse_for_file(
                self.unique_lua_path,
                "Choose one unique export file",
                (("Lua files", "*.lua"), ("All files", "*.*")),
            ),
        )

        action_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 10))
        action_frame.grid(row=1, column=0, sticky="ew")
        action_frame.columnconfigure(2, weight=1)

        ttk.Button(
            action_frame,
            text="Analyze",
            command=self._analyze,
        ).grid(row=0, column=0, padx=(0, 8))

        self.apply_button = ttk.Button(
            action_frame,
            text="Apply selected batch",
            command=self._apply_selected_batch,
            state="disabled",
        )
        self.apply_button.grid(row=0, column=1)

        ttk.Label(
            action_frame,
            textvariable=self.status_text,
            anchor="e",
        ).grid(row=0, column=2, sticky="ew")

        workspace = ttk.Panedwindow(
            main_frame,
            orient=tk.HORIZONTAL,
        )
        workspace.grid(row=2, column=0, sticky="nsew")

        sidebar = ttk.Frame(workspace, padding=(0, 0, 10, 0))
        sidebar.columnconfigure(0, weight=1)
        workspace.add(sidebar, weight=0)

        summary_frame = ttk.LabelFrame(
            sidebar,
            text="Analysis summary",
            padding=10,
        )
        summary_frame.grid(row=0, column=0, sticky="ew")
        summary_frame.columnconfigure(0, weight=1)
        ttk.Label(
            summary_frame,
            textvariable=self.summary_text,
            justify=tk.LEFT,
        ).grid(row=0, column=0, sticky="w")

        filter_frame = ttk.LabelFrame(
            sidebar,
            text="Find and filter",
            padding=10,
        )
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        filter_frame.columnconfigure(0, weight=1)

        ttk.Label(filter_frame, text="Search").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Entry(
            filter_frame,
            textvariable=self.search_text,
        ).grid(row=1, column=0, sticky="ew", pady=(2, 8))

        ttk.Label(filter_frame, text="Status").grid(
            row=2,
            column=0,
            sticky="w",
        )
        filter_box = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter,
            values=FILTER_VALUES,
            state="readonly",
        )
        filter_box.grid(row=3, column=0, sticky="ew", pady=(2, 0))
        filter_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._refresh_result_tree(),
        )

        selection_frame = ttk.LabelFrame(
            sidebar,
            text="Batch selection",
            padding=10,
        )
        selection_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        selection_frame.columnconfigure(0, weight=1)

        ttk.Label(
            selection_frame,
            textvariable=self.selection_text,
            wraplength=230,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Button(
            selection_frame,
            text="Select all safe replacements",
            command=self._select_all_safe,
        ).grid(row=1, column=0, sticky="ew")
        ttk.Button(
            selection_frame,
            text="Clear selection",
            command=self._clear_selection,
        ).grid(row=2, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(
            selection_frame,
            text="Toggle highlighted rows",
            command=self._toggle_highlighted_rows,
        ).grid(row=3, column=0, sticky="ew", pady=(4, 0))

        results_frame = ttk.Frame(workspace)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        workspace.add(results_frame, weight=1)

        columns = (
            "apply",
            "status",
            "item",
            "base",
            "line",
            "existing",
            "proposed",
        )
        self.result_tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
        )
        headings = {
            "apply": "Apply",
            "status": "Status",
            "item": "Unique item",
            "base": "Base type",
            "line": "Line",
            "existing": "Existing mod ID",
            "proposed": "Proposed mod ID",
        }
        widths = {
            "apply": 55,
            "status": 115,
            "item": 180,
            "base": 140,
            "line": 55,
            "existing": 235,
            "proposed": 235,
        }
        for column in columns:
            self.result_tree.heading(column, text=headings[column])
            self.result_tree.column(
                column,
                width=widths[column],
                minwidth=45,
                stretch=column in {"item", "existing", "proposed"},
            )

        vertical_scroll = ttk.Scrollbar(
            results_frame,
            orient=tk.VERTICAL,
            command=self.result_tree.yview,
        )
        horizontal_scroll = ttk.Scrollbar(
            results_frame,
            orient=tk.HORIZONTAL,
            command=self.result_tree.xview,
        )
        self.result_tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        self.result_tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        self.result_tree.tag_configure(
            "Replacement",
            background="#e8f5e9",
        )
        self.result_tree.tag_configure(
            "Unresolved",
            background="#fff8e1",
        )
        self.result_tree.tag_configure(
            "Ambiguous",
            background="#fff3e0",
        )
        self.result_tree.tag_configure(
            "Identity_issue",
            background="#ffebee",
        )
        self.result_tree.bind(
            "<<TreeviewSelect>>",
            self._show_selected_detail,
        )
        self.result_tree.bind(
            "<Double-1>",
            self._toggle_double_clicked_row,
        )

        detail_frame = ttk.LabelFrame(
            main_frame,
            text="Selected result",
            padding=8,
        )
        detail_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        detail_frame.columnconfigure(0, weight=1)

        self.detail_text = tk.Text(
            detail_frame,
            height=7,
            wrap="none",
            font=("Consolas", 10),
            state="disabled",
        )
        self.detail_text.grid(row=0, column=0, sticky="ew")

    def _add_path_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command: object,
    ) -> None:
        ttk.Label(parent, text=label, width=20).grid(
            row=row,
            column=0,
            sticky="w",
            pady=2,
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(6, 6),
            pady=2,
        )
        ttk.Button(
            parent,
            text="Browse...",
            command=browse_command,
        ).grid(row=row, column=2, pady=2)

    def _browse_for_file(
        self,
        variable: tk.StringVar,
        title: str,
        file_types: tuple[tuple[str, str], ...],
    ) -> None:
        selected_path = filedialog.askopenfilename(
            parent=self.root,
            title=title,
            filetypes=file_types,
        )
        if selected_path:
            variable.set(selected_path)

    def _validated_path(
        self,
        variable: tk.StringVar,
        label: str,
    ) -> Path:
        raw_path = variable.get().strip().strip('"')
        if not raw_path:
            raise ValueError(f"{label} path is required")

        path = Path(raw_path)
        if not path.is_file():
            raise ValueError(f"{label} file does not exist: {path}")
        return path

    def _analyze(self) -> None:
        try:
            dataset_path = self._validated_path(
                self.dataset_path,
                "Authoritative JSON",
            )
            mod_text_path = self._validated_path(
                self.mod_text_path,
                "Mod text resolver",
            )
            unique_lua_path = self._validated_path(
                self.unique_lua_path,
                "Unique export",
            )
            analyses = analyze_files(
                dataset_path=dataset_path,
                mod_text_path=mod_text_path,
                unique_lua_path=unique_lua_path,
            )
        except Exception as error:
            self.status_text.set("Analysis failed")
            messagebox.showerror(
                "Analysis failed",
                str(error),
                parent=self.root,
            )
            return

        self.analyses = analyses
        self.analyzed_paths = (
            dataset_path.resolve(),
            mod_text_path.resolve(),
            unique_lua_path.resolve(),
        )
        self.result_rows = build_result_rows(analyses)
        self.rows_by_key = {
            row.key: row
            for row in self.result_rows
        }
        self.selected_keys = {
            row.key
            for row in self.result_rows
            if row.is_patchable
        }

        summary_lines = format_analysis_report(analyses).splitlines()[:8]
        self.summary_text.set("\n".join(summary_lines))
        self.status_text.set(
            f"Analyzed {unique_lua_path.name}"
        )
        self._refresh_result_tree()

    def _mark_analysis_stale(self, *_arguments: object) -> None:
        if self.analyzed_paths is None:
            return
        self.status_text.set("Inputs changed; analyze again before applying")
        self.apply_button.configure(state="disabled")

    def _row_is_visible(self, row: ResultRow) -> bool:
        selected_filter = self.status_filter.get()

        if selected_filter == IDENTITY_ISSUES:
            if row.status not in {UNMATCHED_UNIQUE, AMBIGUOUS_UNIQUE}:
                return False
        elif (
            selected_filter != ALL_RESULTS
            and row.status != selected_filter
        ):
            return False

        query = self.search_text.get().strip().casefold()
        if not query:
            return True

        searchable_text = " ".join(
            (
                row.block_name,
                row.base_type,
                row.status,
                row.existing_mod_id,
                row.proposed_mod_id,
                row.raw_line,
            )
        ).casefold()
        return query in searchable_text

    def _refresh_result_tree(self) -> None:
        for item_id in self.result_tree.get_children():
            self.result_tree.delete(item_id)

        for row in self.result_rows:
            if not self._row_is_visible(row):
                continue

            if row.is_patchable:
                apply_marker = (
                    "Yes"
                    if row.key in self.selected_keys
                    else "No"
                )
            else:
                apply_marker = ""

            if row.status in {UNMATCHED_UNIQUE, AMBIGUOUS_UNIQUE}:
                tag = "Identity_issue"
            elif row.status in {
                "Replacement",
                "Unresolved",
                "Ambiguous",
            }:
                tag = row.status
            else:
                tag = ""

            self.result_tree.insert(
                "",
                tk.END,
                iid=row.key,
                values=(
                    apply_marker,
                    row.status,
                    row.block_name,
                    row.base_type,
                    row.line_number or "",
                    row.existing_mod_id,
                    row.proposed_mod_id,
                ),
                tags=(tag,) if tag else (),
            )

        self._update_selection_state()

    def _update_selection_state(self) -> None:
        replacement_matches = collect_selected_replacements(
            self.result_rows,
            self.selected_keys,
        )
        replacement_count = len(replacement_matches)
        replacement_word = (
            "replacement"
            if replacement_count == 1
            else "replacements"
        )
        self.selection_text.set(
            f"{replacement_count} safe {replacement_word} selected"
        )
        self.apply_button.configure(
            state="normal" if replacement_count else "disabled"
        )

    def _select_all_safe(self) -> None:
        self.selected_keys = {
            row.key
            for row in self.result_rows
            if row.is_patchable
        }
        self._refresh_result_tree()

    def _clear_selection(self) -> None:
        self.selected_keys.clear()
        self._refresh_result_tree()

    def _toggle_highlighted_rows(self) -> None:
        for row_key in self.result_tree.selection():
            row = self.rows_by_key.get(row_key)
            if row is None or not row.is_patchable:
                continue
            if row_key in self.selected_keys:
                self.selected_keys.remove(row_key)
            else:
                self.selected_keys.add(row_key)
        self._refresh_result_tree()

    def _toggle_double_clicked_row(self, event: tk.Event) -> None:
        row_key = self.result_tree.identify_row(event.y)
        row = self.rows_by_key.get(row_key)
        if row is None or not row.is_patchable:
            return
        if row_key in self.selected_keys:
            self.selected_keys.remove(row_key)
        else:
            self.selected_keys.add(row_key)
        self._refresh_result_tree()

    def _show_selected_detail(self, _event: object = None) -> None:
        selected_rows = self.result_tree.selection()
        if not selected_rows:
            self._set_detail_text("")
            return

        row = self.rows_by_key[selected_rows[0]]
        proposed_line = row.raw_line

        if row.is_patchable and row.match is not None:
            proposed_line = apply_mod_match_to_line(
                row.raw_line,
                row.match,
            )

        candidate_text = (
            ", ".join(row.candidate_ids)
            if row.candidate_ids
            else "(none)"
        )
        detail = (
            f"Unique: {row.block_name}\n"
            f"Base type: {row.base_type or '(unresolved)'}\n"
            f"Status: {row.status}\n"
            f"Line: {row.line_number or '(none)'}\n"
            f"Candidates: {candidate_text}\n"
            f"Original: {row.raw_line}\n"
            f"Preview:  {proposed_line}"
        )
        self._set_detail_text(detail)

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state="disabled")

    def _apply_selected_batch(self) -> None:
        replacement_matches = collect_selected_replacements(
            self.result_rows,
            self.selected_keys,
        )
        if not replacement_matches:
            messagebox.showinfo(
                "Nothing selected",
                "Select at least one safe replacement.",
                parent=self.root,
            )
            return

        try:
            dataset_path = self._validated_path(
                self.dataset_path,
                "Authoritative JSON",
            )
            mod_text_path = self._validated_path(
                self.mod_text_path,
                "Mod text resolver",
            )
            unique_lua_path = self._validated_path(
                self.unique_lua_path,
                "Unique export",
            )
        except ValueError as error:
            messagebox.showerror(
                "Cannot apply batch",
                str(error),
                parent=self.root,
            )
            return

        current_paths = (
            dataset_path.resolve(),
            mod_text_path.resolve(),
            unique_lua_path.resolve(),
        )
        if self.analyzed_paths != current_paths:
            messagebox.showerror(
                "Analyze again",
                (
                    "One or more input paths changed after analysis. "
                    "Analyze the current inputs before applying a batch."
                ),
                parent=self.root,
            )
            return

        confirmed = messagebox.askyesno(
            "Apply selected batch?",
            (
                f"Apply {len(replacement_matches)} replacements to:\n\n"
                f"{unique_lua_path}\n\n"
                "Unresolved and ambiguous rows will not be changed."
            ),
            parent=self.root,
            icon="warning",
        )
        if not confirmed:
            return

        try:
            write_mod_matches_to_file(
                unique_lua_path,
                replacement_matches,
            )
        except Exception as error:
            self.status_text.set("Batch failed; no partial write was made")
            messagebox.showerror(
                "Batch failed",
                str(error),
                parent=self.root,
            )
            return

        messagebox.showinfo(
            "Batch applied",
            (
                f"Applied {len(replacement_matches)} replacements.\n"
                "The file will now be analyzed again."
            ),
            parent=self.root,
        )
        self._analyze()


def main() -> None:
    root = tk.Tk()
    UniqueModIdPatcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
