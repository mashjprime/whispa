"""Dictionary management window."""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QHeaderView,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from whispa.core.controller import AppController
from whispa.text_processing.dictionary import DictionaryEntry

logger = logging.getLogger(__name__)


class DictionaryWindow(QDialog):
    """Window for managing dictionary entries."""

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None):
        """Initialize dictionary window.

        Args:
            controller: Application controller
            parent: Parent widget
        """
        super().__init__(parent)

        self.controller = controller

        self.setWindowTitle("Personal Dictionary")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_entries()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Filter/search
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Search entries...")
        self._filter_edit.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Original", "Replacement", "Case Sensitive", "Whole Word"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Edit form
        edit_group = QGroupBox("Edit Entry")
        edit_layout = QFormLayout(edit_group)

        self._original_edit = QLineEdit()
        edit_layout.addRow("Original:", self._original_edit)

        self._replacement_edit = QLineEdit()
        edit_layout.addRow("Replacement:", self._replacement_edit)

        options_layout = QHBoxLayout()
        self._case_sensitive = QCheckBox("Case sensitive")
        options_layout.addWidget(self._case_sensitive)

        self._whole_word = QCheckBox("Whole word only")
        self._whole_word.setChecked(True)
        options_layout.addWidget(self._whole_word)
        options_layout.addStretch()

        edit_layout.addRow("Options:", options_layout)

        layout.addWidget(edit_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("Add New")
        add_btn.clicked.connect(self._add_entry)
        buttons_layout.addWidget(add_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_entry)
        buttons_layout.addWidget(save_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_entry)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        import_btn = QPushButton("Import...")
        import_btn.clicked.connect(self._import_entries)
        buttons_layout.addWidget(import_btn)

        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._export_entries)
        buttons_layout.addWidget(export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def _load_entries(self) -> None:
        """Load dictionary entries from database."""
        self._table.setRowCount(0)

        entries = self.controller.dictionary_repo.get_all()

        for entry in entries:
            self._add_table_row(entry)

    def _add_table_row(self, entry: DictionaryEntry) -> None:
        """Add an entry to the table.

        Args:
            entry: Entry to add
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        original_item = QTableWidgetItem(entry.original)
        original_item.setData(Qt.ItemDataRole.UserRole, entry.id)
        self._table.setItem(row, 0, original_item)
        self._table.setItem(row, 1, QTableWidgetItem(entry.replacement))
        self._table.setItem(row, 2, QTableWidgetItem("Yes" if entry.case_sensitive else "No"))
        self._table.setItem(row, 3, QTableWidgetItem("Yes" if entry.whole_word else "No"))

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        rows = self._table.selectedItems()
        if not rows:
            return

        row = rows[0].row()
        self._original_edit.setText(self._table.item(row, 0).text())
        self._replacement_edit.setText(self._table.item(row, 1).text())
        self._case_sensitive.setChecked(self._table.item(row, 2).text() == "Yes")
        self._whole_word.setChecked(self._table.item(row, 3).text() == "Yes")

    def _apply_filter(self) -> None:
        """Apply filter to table."""
        filter_text = self._filter_edit.text().lower()

        for row in range(self._table.rowCount()):
            show = True

            if filter_text:
                original = self._table.item(row, 0).text().lower()
                replacement = self._table.item(row, 1).text().lower()
                if filter_text not in original and filter_text not in replacement:
                    show = False

            self._table.setRowHidden(row, not show)

    def _add_entry(self) -> None:
        """Add a new dictionary entry."""
        original = self._original_edit.text().strip()
        replacement = self._replacement_edit.text().strip()

        if not original or not replacement:
            QMessageBox.warning(self, "Error", "Original and replacement are required.")
            return

        entry = self.controller.dictionary_repo.create(
            original=original,
            replacement=replacement,
            case_sensitive=self._case_sensitive.isChecked(),
            whole_word=self._whole_word.isChecked(),
        )

        if entry:
            self._add_table_row(entry)
            self.controller.reload_data()
            self._clear_form()
            QMessageBox.information(self, "Success", "Entry added.")

    def _save_entry(self) -> None:
        """Save changes to selected entry."""
        rows = self._table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Error", "No entry selected.")
            return

        row = rows[0].row()
        entry_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        entry = self.controller.dictionary_repo.get_by_id(entry_id)
        if entry:
            entry.original = self._original_edit.text().strip()
            entry.replacement = self._replacement_edit.text().strip()
            entry.case_sensitive = self._case_sensitive.isChecked()
            entry.whole_word = self._whole_word.isChecked()

            if self.controller.dictionary_repo.update(entry):
                self._table.item(row, 0).setText(entry.original)
                self._table.item(row, 1).setText(entry.replacement)
                self._table.item(row, 2).setText("Yes" if entry.case_sensitive else "No")
                self._table.item(row, 3).setText("Yes" if entry.whole_word else "No")
                self.controller.reload_data()
                QMessageBox.information(self, "Success", "Entry updated.")

    def _delete_entry(self) -> None:
        """Delete selected entry."""
        rows = self._table.selectedItems()
        if not rows:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = rows[0].row()
            entry_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)

            if self.controller.dictionary_repo.delete(entry_id):
                self._table.removeRow(row)
                self.controller.reload_data()
                self._clear_form()

    def _clear_form(self) -> None:
        """Clear the edit form."""
        self._original_edit.clear()
        self._replacement_edit.clear()
        self._case_sensitive.setChecked(False)
        self._whole_word.setChecked(True)

    def _import_entries(self) -> None:
        """Import entries from JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json

        path, _ = QFileDialog.getOpenFileName(
            self, "Import Dictionary", "", "JSON Files (*.json)"
        )

        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = self.controller.dictionary_repo.import_entries(data)
                self._load_entries()
                self.controller.reload_data()
                QMessageBox.information(self, "Success", f"Imported {count} entries.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Import failed: {e}")

    def _export_entries(self) -> None:
        """Export entries to JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Dictionary", "dictionary.json", "JSON Files (*.json)"
        )

        if path:
            try:
                data = self.controller.dictionary_repo.export_entries()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Success", f"Exported {len(data)} entries.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Export failed: {e}")
