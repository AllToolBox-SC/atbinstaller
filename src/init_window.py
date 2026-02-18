from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt
from utils import get_packages
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
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title_label = QLabel("Initializing...", self)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title_label)

            self.progress_bar = QProgressBar(self)
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setStyleSheet(
                "QProgressBar { border: 1px solid #fff; border-radius: 5px; background-color: rgba(0,0,0,0); }"
                "QProgressBar::chunk { background-color: #1F9B5D; }"
            )
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
