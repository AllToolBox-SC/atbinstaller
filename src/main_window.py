from PyQt6.QtWidgets import QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QCloseEvent
from main_pages.start import StartPage
from main_pages.license import LicensePage
from main_pages.custom import CustomPage
from main_pages.install import InstallPage
from main_pages.complete import CompletePage
from utils.theme import is_dark_mode, window_qss, nav_list_qss, button_qss
from typing import List, Optional, Dict
import sys

class MainWindow(QWidget):
    def __init__(self, *data: list):
        super().__init__()
        self.data = local_data = dict(data[0].get("main_window", {})) if data else {}
        global_data: dict = data[0].get("$global", {}) if data else {}

        self.webdata: dict = data[1] if len(data) > 1 else {}

        self.nmp: bool = data[2] if len(data) > 2 else False
        self.proxy: str = data[3] if len(data) > 3 else ""

        title = local_data.get("title", global_data.get("title", "AndroidToolBox Online Installer"))
        self.setWindowTitle(title)
        self.resize(800, 600)
        pix = QPixmap(1, 1)
        pix.fill(Qt.GlobalColor.transparent)
        empty_icon = QIcon(pix)
        self.setWindowIcon(empty_icon)
        self.init_ui()

        self.show()
        print(f"MainWindow created with title: {title}")

        self.destroyed.connect(self.on_destroyed)

    def on_destroyed(self):
        print("MainWindow destroyed")

    def closeEvent(self, event: QCloseEvent):
        try:
            # Block any window close action while installation is in progress.
            if hasattr(self, "nav_list") and self.nav_list.currentRow() == 3:
                QMessageBox.warning(self, "Warning", "Installation is in progress. Exiting is disabled.")
                event.ignore()
                return
        except Exception as e:
            print(f"Error in closeEvent: {e}")
        super().closeEvent(event)

    def init_ui(self):
        dark_mode = is_dark_mode(self)
        self.mainlayout = QHBoxLayout(self)
        self.setLayout(self.mainlayout)
        self.mainlayout.setContentsMargins(10, 10, 10, 10)
        self.setStyleSheet(window_qss(dark_mode))
        self.nav_list = QListWidget(self)
        for key, value in self.data.get("sidebar", {}).items():
            self.nav_list.addItem(value)
        self.nav_list.setFixedWidth(150)
        self.nav_list.setCurrentRow(0)
        self.nav_list.move(0, 0)
        self.nav_list.resize(150, self.height())
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setStyleSheet(nav_list_qss(dark_mode))
        self.nav_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.nav_list.setEditTriggers(QListWidget.EditTrigger.NoEditTriggers)
        self.nav_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.nav_list.setCurrentIndex(self.nav_list.model().index(0, 0))
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        self.nav_list.setEnabled(False)
        self.nav_list.setDisabled(True)

        self.contents = QVBoxLayout(self)
        self.contents.setContentsMargins(0, 10, 0, 0)
        self.contents.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel(self.nav_list.currentItem().text() if self.nav_list.currentItem() else "", self)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")

        self.contents.addWidget(self.title_label)

        self.focus_contents = QVBoxLayout(self)
        self.focus_contents.setContentsMargins(0, 10, 0, 0)
        self.focus_contents.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.contents.addLayout(self.focus_contents)
        self.contents.addStretch(1)

        self.button_group = QHBoxLayout(self)
        self.button_group.setContentsMargins(0, 10, 0, 0)
        self.button_group.setAlignment(Qt.AlignmentFlag.AlignRight)
        up = self.data.get("up", "< Previous")
        next = self.data.get("next", "Next >")
        self.control_btns: list[QPushButton] = [
            QPushButton(up, self),
            QPushButton(next, self)
        ]
        for button in self.control_btns:
            button.setFixedSize(100, 35)
            button.setStyleSheet(button_qss(dark_mode))
            self.button_group.addWidget(button)
        self.button_group.setSpacing(10)
        self.exit_btn = QPushButton(self.data.get("exit", "Cancel"), self)
        self.exit_btn.setFixedSize(100, 35)
        self.exit_btn.clicked.connect(self.close)
        self.exit_btn.setStyleSheet(button_qss(dark_mode))
        self.button_group.addWidget(self.exit_btn)
        self.update_button_states()
        self.control_btns[0].clicked.connect(self.go_previous)
        self.control_btns[1].clicked.connect(self.go_next)
        self.contents.addLayout(self.button_group)
        self.start_page = StartPage(self.data)
        self.focus_contents.addWidget(self.start_page)
        self.mainlayout.addWidget(self.nav_list)
        self.mainlayout.addLayout(self.contents)

        self.mainlayout.activate()
        self.mainlayout.update()

    def on_nav_changed(self, index):
        try:
            current_row = self.nav_list.currentRow()
            total_items = self.nav_list.count()
            current_item = self.nav_list.currentItem()
            if current_item:
                self.title_label.setText(current_item.text())
            print(f"Navigation changed to index: {index}")

            widget = self.focus_contents.itemAt(0)
            if widget and widget.widget():
                widget.widget().deleteLater()

            match current_row:
                case 0:
                    self.start_page = StartPage(self.data)
                    try:
                        self.control_btns[1].clicked.disconnect()
                    except TypeError:
                        pass
                    self.control_btns[1].clicked.connect(self.go_next)
                    self.focus_contents.addWidget(self.start_page)

                case 1:
                    self.license_page = LicensePage(self.data)
                    try:
                        self.control_btns[1].clicked.disconnect()
                    except TypeError:
                        pass
                    self.control_btns[1].clicked.connect(self.go_next)
                    self.focus_contents.addWidget(self.license_page)
                case 2:
                    self.custom_page = CustomPage(self.data, self.webdata)
                    try:
                        self.control_btns[1].clicked.disconnect()
                    except TypeError:
                        pass
                    self.control_btns[1].clicked.connect(lambda: {
                        self.go_install(),
                        self.go_next()
                    })
                    self.focus_contents.addWidget(self.custom_page)

                case 3:
                    try:
                        self.control_btns[1].clicked.disconnect()
                    except TypeError:
                        pass
                    self.control_btns[1].clicked.connect(self.go_next)
                    self.install_page = InstallPage(
                        self.data,
                        self.selected_components if hasattr(self, 'selected_components') else {},
                        self.installation_path if hasattr(self, 'installation_path') else "",
                        self.nmp,
                        self.proxy
                    )
                    self.install_page.installation_completed.connect(self.on_installation_completed)

                    install_result = self.install_page.start_installation()
                    if install_result == 0:
                        self.focus_contents.addWidget(self.install_page)
                        QTimer.singleShot(100, self.install_page.install_packages)

                    elif install_result == 1:
                        self.install_page.update_status("Failed to create installation directory, check permissions")
                        self.on_installation_completed(5)

                    elif install_result == 2:
                        self.install_page.update_status("Installation cancelled by user")
                        self.control_btns[1].clicked.disconnect()
                        self.control_btns[1].clicked.connect(lambda: {
                            self.go_install(),
                            self.go_next()
                        })
                        for button in self.control_btns:
                            button.setDisabled(False)
                        self.exit_btn.setDisabled(False)
                        self.nav_list.setCurrentRow(2)

                case 4:
                    self.complete_page = CompletePage(self.data, getattr(self, "install_status_code", 0))
                    self.focus_contents.addWidget(self.complete_page)

            self.update_button_states()
        except Exception as e:
            print(f"Error in on_nav_changed: {e}")
            QMessageBox.critical(self, "Error", f"Navigation failed: {str(e)}")

    def update_button_states(self):
        try:
            current_row = self.nav_list.currentRow()
            total_items = self.nav_list.count()

            self.control_btns[0].setEnabled(0 < current_row < total_items - 2)
            self.control_btns[1].setEnabled(current_row < total_items - 2)
            self.exit_btn.setEnabled(current_row != 3)

            self.exit_btn.setText(
                self.data.get("finish", "Finish") if current_row == total_items - 1 else self.data.get("exit", "Cancel")
            )
            self.control_btns[1].setText(
                self.data.get("install", "Install")
                if current_row == 2 else self.data.get("next", "Next >")
                if not current_row == 1 else self.data.get("agree", "Agree")
            )
        except Exception as e:
            print(f"Error in update_button_states: {e}")

    def go_next(self):
        try:
            current_index = self.nav_list.currentRow()
            if current_index < self.nav_list.count() - 1:
                self.nav_list.setCurrentRow(current_index + 1)
                self.nav_list.update()
                self.update_button_states()
        except Exception as e:
            print(f"Error in go_next: {e}")

    def go_previous(self):
        try:
            current_index = self.nav_list.currentRow()
            if current_index > 0:
                self.nav_list.setCurrentRow(current_index - 1)
                self.nav_list.update()
                self.update_button_states()
        except Exception as e:
            print(f"Error in go_previous: {e}")

    def go_install(self):
        try:
            if hasattr(self, 'custom_page') and self.custom_page:
                print("Getting selected components...")
                self.selected_components = self.custom_page.get_selected_components()
                self.installation_path = self.custom_page.get_installation_path()
                print(f"Selected components: {self.selected_components}")
                print(f"Installation path: {self.installation_path}")

                if not self.selected_components:
                    print("Warning: No components selected")
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    msg_box.setText("No components selected")
                    msg_box.setInformativeText("Please select at least one component to install")
                    msg_box.setWindowTitle("Warning")
                    msg_box.exec()
                else:
                    print(f"Found {len(self.selected_components)} selected components")
        except Exception as e:
            print(f"Error in go_install: {e}")
            QMessageBox.critical(self, "Error", f"Failed to get components: {str(e)}")

    def on_installation_completed(self, status_code: int = 0):
        try:
            self.install_status_code = status_code
            self.nav_list.setCurrentRow(4)
            self.update_button_states()
        except Exception as e:
            print(f"Error in on_installation_completed: {e}")
