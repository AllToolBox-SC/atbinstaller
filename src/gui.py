from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication
from main_window import MainWindow
from init_window import InitWindow
from qasync import QEventLoop
import sys
import asyncio

class App(QApplication):
    def __init__(self, *data: list):
        super().__init__(sys.argv)
        self.data = data[0] if len(data) > 0 else {}
        self.nmp = data[1] if len(data) > 1 else False
        self.proxy = data[2] if len(data) > 2 else ""
        self.init_window = None
        self.main_window = None

        try:
            self.init_window = InitWindow()
            self.init_window.show()
            self.init_window.raise_()
            self.init_window.activateWindow()
        except Exception as e:
            print(f"Failed to create InitWindow: {e}")
            self._show_error("Failed to initialize application", str(e))
            sys.exit(1)

    def _show_error(self, title, message):
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(title)
            msg_box.setInformativeText(message)
            msg_box.setWindowTitle("Error")
            msg_box.exec()
        except Exception:
            pass

    async def load_package_data(self):
        try:
            if not self.init_window:
                raise RuntimeError("InitWindow not created")

            self.package_xml = await self.init_window.init_package_data()

            if self.package_xml is None:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setText("Failed to fetch package info")
                msg_box.setInformativeText("Please check your network connection or contact the developer")
                msg_box.setWindowTitle("Error")
                msg_box.exec()
                sys.exit(1)

            if self.init_window:
                self.init_window.close()
                self.init_window.deleteLater()

            self.main_window = MainWindow(self.data, self.package_xml, self.nmp, self.proxy)
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
        except asyncio.CancelledError:
            print("Package data loading cancelled")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading package data: {e}")
            self._show_error("Error loading package data", str(e))
            sys.exit(1)
