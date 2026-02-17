from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import List

class CompletePage(QWidget):
    def __init__(self, *data: List[dict]):
        super().__init__()
        self.data = data[0] if data else {}
        self.status_code = data[1] if len(data) > 1 else 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = self.data.get("complete_page", {}).get("title", "Installation Complete")
        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)

        if self.status_code == 0:
            content = self.data.get("complete_page", {}).get("description", "The installation has been completed successfully.")
        elif self.status_code == 1:
            content = self.data.get("complete_page", {}).get("user_stop", "User stopped the installation.")
        else:
            content = self.data.get("complete_page", {}).get("error_description", f"Installation failed with error code {self.status_code}")

        content_browser = QLabel(content, self)
        content_browser.setStyleSheet("font-size: 12px;")
        layout.addWidget(content_browser)
