"""Snippets management window."""

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
    QInputDialog,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QWidget,
)
from PyQt6.QtCore import Qt

from whispa.core.controller import AppController
from whispa.text_processing.snippets import Snippet

logger = logging.getLogger(__name__)


class SnippetsWindow(QDialog):
    """Window for managing snippets."""

    def __init__(self, controller: AppController, parent: Optional[QWidget] = None):
        """Initialize snippets window.

        Args:
            controller: Application controller
            parent: Parent widget
        """
        super().__init__(parent)

        self.controller = controller

        self.setWindowTitle("Snippets Manager")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_snippets()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Filter/search
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Search snippets...")
        self._filter_edit.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._filter_edit)

        self._category_filter = QComboBox()
        self._category_filter.addItem("All Categories")
        self._category_filter.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._category_filter)

        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Trigger", "Expansion", "Category", "Description"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Edit form
        edit_group = QGroupBox("Edit Snippet")
        edit_layout = QFormLayout(edit_group)

        self._trigger_edit = QLineEdit()
        edit_layout.addRow("Trigger:", self._trigger_edit)

        self._expansion_edit = QLineEdit()
        edit_layout.addRow("Expansion:", self._expansion_edit)

        self._category_edit = QLineEdit()
        edit_layout.addRow("Category:", self._category_edit)

        self._description_edit = QLineEdit()
        edit_layout.addRow("Description:", self._description_edit)

        layout.addWidget(edit_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("Add New")
        add_btn.clicked.connect(self._add_snippet)
        buttons_layout.addWidget(add_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_snippet)
        buttons_layout.addWidget(save_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_snippet)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        import_btn = QPushButton("Import...")
        import_btn.clicked.connect(self._import_snippets)
        buttons_layout.addWidget(import_btn)

        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._export_snippets)
        buttons_layout.addWidget(export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def _load_snippets(self) -> None:
        """Load snippets from database."""
        self._table.setRowCount(0)

        snippets = self.controller.snippets_repo.get_all()

        # Update category filter
        categories = set()
        for snippet in snippets:
            if snippet.category:
                categories.add(snippet.category)

        self._category_filter.clear()
        self._category_filter.addItem("All Categories")
        for cat in sorted(categories):
            self._category_filter.addItem(cat)

        # Populate table
        for snippet in snippets:
            self._add_table_row(snippet)

    def _add_table_row(self, snippet: Snippet) -> None:
        """Add a snippet to the table.

        Args:
            snippet: Snippet to add
        """
        row = self._table.rowCount()
        self._table.insertRow(row)

        trigger_item = QTableWidgetItem(snippet.trigger)
        trigger_item.setData(Qt.ItemDataRole.UserRole, snippet.id)
        self._table.setItem(row, 0, trigger_item)
        self._table.setItem(row, 1, QTableWidgetItem(snippet.expansion))
        self._table.setItem(row, 2, QTableWidgetItem(snippet.category))
        self._table.setItem(row, 3, QTableWidgetItem(snippet.description))

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        rows = self._table.selectedItems()
        if not rows:
            return

        row = rows[0].row()
        self._trigger_edit.setText(self._table.item(row, 0).text())
        self._expansion_edit.setText(self._table.item(row, 1).text())
        self._category_edit.setText(self._table.item(row, 2).text())
        self._description_edit.setText(self._table.item(row, 3).text())

    def _apply_filter(self) -> None:
        """Apply filter to table."""
        filter_text = self._filter_edit.text().lower()
        category = self._category_filter.currentText()

        for row in range(self._table.rowCount()):
            show = True

            # Text filter
            if filter_text:
                trigger = self._table.item(row, 0).text().lower()
                expansion = self._table.item(row, 1).text().lower()
                if filter_text not in trigger and filter_text not in expansion:
                    show = False

            # Category filter
            if category != "All Categories":
                row_category = self._table.item(row, 2).text()
                if row_category != category:
                    show = False

            self._table.setRowHidden(row, not show)

    def _add_snippet(self) -> None:
        """Add a new snippet."""
        trigger = self._trigger_edit.text().strip()
        expansion = self._expansion_edit.text().strip()

        if not trigger or not expansion:
            QMessageBox.warning(self, "Error", "Trigger and expansion are required.")
            return

        snippet = self.controller.snippets_repo.create(
            trigger=trigger,
            expansion=expansion,
            category=self._category_edit.text().strip(),
            description=self._description_edit.text().strip(),
        )

        if snippet:
            self._add_table_row(snippet)
            self.controller.reload_data()
            self._clear_form()
            QMessageBox.information(self, "Success", "Snippet added.")

    def _save_snippet(self) -> None:
        """Save changes to selected snippet."""
        rows = self._table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Error", "No snippet selected.")
            return

        row = rows[0].row()
        snippet_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        snippet = self.controller.snippets_repo.get_by_id(snippet_id)
        if snippet:
            snippet.trigger = self._trigger_edit.text().strip()
            snippet.expansion = self._expansion_edit.text().strip()
            snippet.category = self._category_edit.text().strip()
            snippet.description = self._description_edit.text().strip()

            if self.controller.snippets_repo.update(snippet):
                self._table.item(row, 0).setText(snippet.trigger)
                self._table.item(row, 1).setText(snippet.expansion)
                self._table.item(row, 2).setText(snippet.category)
                self._table.item(row, 3).setText(snippet.description)
                self.controller.reload_data()
                QMessageBox.information(self, "Success", "Snippet updated.")

    def _delete_snippet(self) -> None:
        """Delete selected snippet."""
        rows = self._table.selectedItems()
        if not rows:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this snippet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = rows[0].row()
            snippet_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)

            if self.controller.snippets_repo.delete(snippet_id):
                self._table.removeRow(row)
                self.controller.reload_data()
                self._clear_form()

    def _clear_form(self) -> None:
        """Clear the edit form."""
        self._trigger_edit.clear()
        self._expansion_edit.clear()
        self._category_edit.clear()
        self._description_edit.clear()

    def _import_snippets(self) -> None:
        """Import snippets from JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json

        path, _ = QFileDialog.getOpenFileName(
            self, "Import Snippets", "", "JSON Files (*.json)"
        )

        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = self.controller.snippets_repo.import_snippets(data)
                self._load_snippets()
                self.controller.reload_data()
                QMessageBox.information(self, "Success", f"Imported {count} snippets.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Import failed: {e}")

    def _export_snippets(self) -> None:
        """Export snippets to JSON."""
        from PyQt6.QtWidgets import QFileDialog
        import json

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Snippets", "snippets.json", "JSON Files (*.json)"
        )

        if path:
            try:
                data = self.controller.snippets_repo.export_snippets()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Success", f"Exported {len(data)} snippets.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Export failed: {e}")
