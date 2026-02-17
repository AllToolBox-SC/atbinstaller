from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class StartPage(QWidget):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = self.data.get("start_page", {}).get("title", "Welcome to AndroidToolBox Online Installer")
        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)

        content = self.data.get("start_page", {}).get("description", "This installer will guide you through the installation process.")
        content_browser = QLabel(content, self)
        content_browser.setStyleSheet("font-size: 12px;")
        layout.addWidget(content_browser)
