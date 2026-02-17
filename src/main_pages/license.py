from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PyQt6.QtCore import Qt
import os

class LicensePage(QWidget):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = self.data.get("license_page", {}).get("title", "License Agreement")
        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)

        content = self.data.get("license_page", {}).get("description", "Please read the license agreement carefully before proceeding.")
        content_browser = QLabel(content, self)
        content_browser.setStyleSheet("font-size: 12px;")
        layout.addWidget(content_browser)

        browser = QTextBrowser(self)
        license_text: str
        license_text_value = self.data.get("license_page", {}).get("license_text", "License agreement text goes here.")
        if license_text_value.startswith("$file:"):
            license_file = license_text_value[6:]
            try:
                with open(os.path.join(os.path.dirname(__file__), "..", license_file), "r", encoding="utf-8") as f:
                    license_text = f.read()
            except Exception as e:
                license_text = f"Failed to load license file: {e}"
        else:
            license_text = license_text_value
        browser.setText(license_text)
        browser.setReadOnly(True)
        browser.setContentsMargins(0, 10, 0, 0)
        browser.setFixedHeight(self.contentsRect().height() - title_label.height() - content_browser.height() - 20)
        layout.addWidget(browser)
