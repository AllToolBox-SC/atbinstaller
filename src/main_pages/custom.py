from typing import List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
import os
from compose.InstallSelector import InstallSelector
from compose.package_parser import parse_packages_xml, populate_install_selector


class CustomPage(QWidget):
    def __init__(self, *data: List[dict]):
        super().__init__()
        self.data = data[0] if data else {}
        self.webdata = data[1] if len(data) > 1 else {}
        self.sections = []
        self.install_selector = None
        self.init_ui()

    def init_ui(self):
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            title = self.data.get("custom_page", {}).get("title", "Custom Installation")
            title_label = QLabel(title, self)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
            layout.addWidget(title_label)

            content = self.data.get("custom_page", {}).get("description", "Select the components you want to install:")
            content_label = QLabel(content, self)
            content_label.setStyleSheet("font-size: 12px; padding: 5px;")
            layout.addWidget(content_label)

            self.install_selector = InstallSelector()

            packages_xml = self.webdata
            if packages_xml:
                try:
                    self.sections = parse_packages_xml(packages_xml)
                    populate_install_selector(self.install_selector, self.sections)
                except Exception as e:
                    print(f"Failed to parse packages XML: {e}")
                    error_label = QLabel(f"Failed to load package list: {str(e)}", self)
                    error_label.setStyleSheet("color: red; font-size: 12px;")
                    layout.addWidget(error_label)
            else:
                error_label = QLabel("No package data available", self)
                error_label.setStyleSheet("color: red; font-size: 12px;")
                layout.addWidget(error_label)

            layout.addWidget(self.install_selector)

            install_to_layout = QHBoxLayout(self)
            install_to_label = QLabel(self.data.get("custom_page", {}).get("install_to", "Install to:"), self)
            install_to_label.setStyleSheet("font-size: 12px; padding: 5px;")
            install_to_layout.addWidget(install_to_label)
            install_to_textbox = QTextEdit(self)
            install_to_textbox.setFixedHeight(30)
            default_path = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "AndroidToolBox")
            install_to_textbox.setText(default_path)
            setattr(self, 'install_to', default_path)
            install_to_textbox.textChanged.connect(lambda: setattr(self, 'install_to', install_to_textbox.toPlainText()))
            install_to_layout.addWidget(install_to_textbox)
            install_to_btn = QPushButton(self.data.get("custom_page", {}).get("browser", "Browse"), self)
            install_to_btn.setFixedSize(80, 30)
            install_to_btn.setStyleSheet(
                "QPushButton { background-color: rgba(0,0,0,0); border: 1px solid #fff; color: #fff; border-radius: 5px; }"
                "QPushButton:disabled { background-color: rgba(0,0,0,0); border: 1px solid #555; color: #555; }"
                "QPushButton:hover:!disabled { background-color: rgba(255,255,255,30); border: 1px solid #fff; }"
            )
            install_to_btn.clicked.connect(lambda: self.browse_folder(install_to_textbox))
            install_to_layout.addWidget(install_to_btn)
            layout.addLayout(install_to_layout)
        except Exception as e:
            print(f"Error in init_ui: {e}")

    def get_selected_components(self):
        try:
            if not self.install_selector:
                return []

            selected_ids = set(self.install_selector.get_selected_components_id())
            selected_versions = self.install_selector.get_selected_component_versions()
            print(f"Selected IDs from InstallSelector: {selected_ids}")
            print(f"Selected versions from InstallSelector: {selected_versions}")

            selected_components = []
            for section in self.sections:
                for package in section.get('packages', []):
                    is_user_selected = package.get('id') in selected_ids
                    is_required = package.get('required', False)
                    is_nouserselect = package.get('nouserselect', False)

                    if is_user_selected or is_required or is_nouserselect:
                        versions = package.get('versions', [])
                        if not versions:
                            continue

                        package_id = package.get('id')
                        selected_version_name = selected_versions.get(package_id) or package.get('version')

                        selected_version = None
                        for version_info in versions:
                            if version_info.get('name') == selected_version_name:
                                selected_version = version_info
                                break

                        if selected_version is None:
                            selected_version = max(
                                versions,
                                key=lambda v: int(v.get('code', 0) or 0)
                            )

                        selected_components.append({
                            'id': package.get('id'),
                            'name': package.get('name'),
                            'version': str(selected_version.get('code')),
                            'version_name': selected_version.get('name'),
                            'code': selected_version.get('code'),
                            'downloadurl': selected_version.get('downloadurl'),
                            'filetype': selected_version.get('filetype'),
                            'installto': selected_version.get('installto', '/'),
                            'unpack': selected_version.get('unpack', True)
                        })

            print(f"Final selected components: {[comp['id'] for comp in selected_components]}")
            return selected_components
        except Exception as e:
            print(f"Error in get_selected_components: {e}")
            QMessageBox.critical(self, "Error", f"Failed to get selected components: {str(e)}")
            return []

    def get_installation_path(self):
        try:
            return getattr(self, 'install_to', '') or os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "AndroidToolBox")
        except Exception:
            return os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "AndroidToolBox")

    def browse_folder(self, textbox):
        try:
            folder_path = QFileDialog.getExistingDirectory(
                self,
                self.data.get("custom_page", {}).get("select_folder", "Select Installation Folder")
            )
            if folder_path:
                textbox.setText(folder_path)
        except Exception as e:
            print(f"Error in browse_folder: {e}")
            QMessageBox.critical(self, "Error", f"Failed to select folder: {str(e)}")
