from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class VersionSelectionDialog(QDialog):
    def __init__(self, package_name, versions, current_version=None, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.versions = versions
        self.current_version = current_version
        self.selected_version = current_version

        self.setWindowTitle(f"Select Version - {package_name}")
        self.setMinimumSize(600, 400)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel(f"Select a version for {self.package_name}:")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        self.version_table = QTableWidget()
        self.version_table.setColumnCount(4)
        self.version_table.setHorizontalHeaderLabels(["Version", "Code", "Download URL", "File Type"])

        self.version_table.setStyleSheet("""
            QTableWidget {
                selection-background-color: rgba(0, 120, 215, 100);
                selection-color: black;
                alternate-background-color: #f0f0f0;
                show-decoration-selected: 0;
                border-left: 0px;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 120, 215, 100);
                border: none;
                border-left: 0px;
            }
            QTableWidget::item:selected:focus {
                background-color: rgba(0, 120, 215, 100);
                border: none;
                border-left: 0px;
            }
            QTableWidget::indicator {
                background: transparent;
                border: none;
            }
        """)

        header = self.version_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.populate_versions_table()

        self.version_table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.version_table)

        buttons_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        if self.current_version:
            self.select_current_version()

    def populate_versions_table(self):
        self.version_table.setRowCount(len(self.versions))

        for row, version in enumerate(self.versions):
            version_item = QTableWidgetItem(version.get('name', ''))
            version_item.setFlags(version_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.version_table.setItem(row, 0, version_item)

            code_item = QTableWidgetItem(str(version.get('code', '')))
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.version_table.setItem(row, 1, code_item)

            url_item = QTableWidgetItem(version.get('downloadurl', ''))
            url_item.setFlags(url_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.version_table.setItem(row, 2, url_item)

            filetype_item = QTableWidgetItem(version.get('filetype', ''))
            filetype_item.setFlags(filetype_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.version_table.setItem(row, 3, filetype_item)

    def select_current_version(self):
        for row in range(self.version_table.rowCount()):
            version_item = self.version_table.item(row, 0)
            if version_item.text() == self.current_version:
                self.version_table.selectRow(row)
                self.selected_version = self.current_version
                self.ok_button.setEnabled(True)
                break

    def on_selection_changed(self):
        selected_items = self.version_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            version_item = self.version_table.item(selected_row, 0)
            self.selected_version = version_item.text()
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def get_selected_version(self):
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.selected_version
        return None
