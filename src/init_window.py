from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt
from utils import get_packages
from utils.theme import is_dark_mode, window_qss, progress_qss
import os
import sys
import json
import asyncio


class InitWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AndroidToolBox Online Installer - Initial Setup")
        self.setFixedSize(400, 100)
        self.data = {}
        self.progress_bar = None
        self.init_ui()

    def init_ui(self):
        try:
            dark_mode = is_dark_mode(self)
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setStyleSheet(window_qss(dark_mode))

            title_label = QLabel("Initializing...", self)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title_label)

            self.progress_bar = QProgressBar(self)
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setStyleSheet(progress_qss(dark_mode))
            layout.addWidget(self.progress_bar)
            self.setLayout(layout)
        except Exception as e:
            print(f"Error in init_ui: {e}")

    async def init_package_data(self):
        try:
            api_url = open(os.path.join(os.path.dirname(__file__), "api_server.txt")).read().rstrip() or "http://atb.xgj.qzz.io/"
            packages_xml = await get_packages(api_url)
            return packages_xml
        except Exception as e:
            print(f"Error initializing package data: {e}")
            return None
