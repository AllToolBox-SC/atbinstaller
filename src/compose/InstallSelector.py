from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QCheckBox, QFrame, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
import sys
from PyQt6.QtWidgets import QApplication

from .version_selection_dialog import VersionSelectionDialog

class InstallSelector(QWidget):
    selectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.Shape.StyledPanel)
        content_layout = QVBoxLayout(content_frame)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Component", "Description"])
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setRootIsDecorated(True)
        self.tree_widget.setAnimated(True)

        self.tree_widget.itemChanged.connect(self.on_item_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        content_layout.addWidget(self.tree_widget)

        buttons_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.select_all_btn)
        buttons_layout.addWidget(self.deselect_all_btn)

        content_layout.addLayout(buttons_layout)
        layout.addWidget(content_frame)

        self.setLayout(layout)

    def add_component_group(self, group_name, description="", hide_checkbox=False):
        group_item = QTreeWidgetItem([group_name, description])
        group_item.setCheckState(0, Qt.CheckState.Unchecked)
        group_item.setExpanded(True)

        if hide_checkbox:
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        self.tree_widget.addTopLevelItem(group_item)
        return group_item

    def add_component(self, parent_item, component_name, description="", checked=False, hide_checkbox=False, component_id=None):
        component_item = QTreeWidgetItem(parent_item, [component_name, description])
        component_item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

        if component_id is not None:
            component_item.setData(0, Qt.ItemDataRole.UserRole + 1, component_id)

        if hide_checkbox:
            component_item.setFlags(component_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            component_item.setFlags(component_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            component_item.setData(0, Qt.ItemDataRole.UserRole, True)
            component_item.setToolTip(0, "This component is automatically included")

        return component_item

    def select_all(self):
        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)
            if group_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                group_item.setCheckState(0, Qt.CheckState.Checked)

            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    child_item.setCheckState(0, Qt.CheckState.Checked)

        self.selectionChanged.emit()

    def deselect_all(self):
        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)
            if group_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                group_item.setCheckState(0, Qt.CheckState.Unchecked)

            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    child_item.setCheckState(0, Qt.CheckState.Unchecked)

        self.selectionChanged.emit()

    def get_selected_components(self):
        selected = []

        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)

            if group_item.checkState(0) == Qt.CheckState.Checked:
                for j in range(group_item.childCount()):
                    child_item = group_item.child(j)
                    selected.append(child_item.text(0))
            else:
                for j in range(group_item.childCount()):
                    child_item = group_item.child(j)
                    if child_item.checkState(0) == Qt.CheckState.Checked:
                        selected.append(child_item.text(0))

        return selected

    def get_selected_components_id(self):
        selected_ids = []

        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)

            if group_item.checkState(0) == Qt.CheckState.Checked:
                for j in range(group_item.childCount()):
                    child_item = group_item.child(j)
                    component_id = child_item.data(0, Qt.ItemDataRole.UserRole + 1)
                    if component_id is not None:
                        selected_ids.append(component_id)
            else:
                for j in range(group_item.childCount()):
                    child_item = group_item.child(j)
                    if child_item.checkState(0) == Qt.CheckState.Checked:
                        component_id = child_item.data(0, Qt.ItemDataRole.UserRole + 1)
                        if component_id is not None:
                            selected_ids.append(component_id)

        return selected_ids

    def get_selected_component_versions(self):
        selected_versions = {}

        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)

            if group_item.checkState(0) == Qt.CheckState.Checked:
                children = [group_item.child(j) for j in range(group_item.childCount())]
            else:
                children = [
                    group_item.child(j)
                    for j in range(group_item.childCount())
                    if group_item.child(j).checkState(0) == Qt.CheckState.Checked
                ]

            for child_item in children:
                component_id = child_item.data(0, Qt.ItemDataRole.UserRole + 1)
                if component_id is None:
                    continue

                selected_version = child_item.data(0, Qt.ItemDataRole.UserRole + 3)
                if selected_version:
                    selected_versions[component_id] = selected_version

        return selected_versions

    def on_item_double_clicked(self, item, column):
        if item.parent() is not None:
            versions_data = item.data(0, Qt.ItemDataRole.UserRole + 2)
            if versions_data:
                current_version = item.data(0, Qt.ItemDataRole.UserRole + 3)

                dialog = VersionSelectionDialog(
                    item.text(0),
                    versions_data,
                    current_version,
                    self
                )

                selected_version = dialog.get_selected_version()
                if selected_version:
                    item.setData(0, Qt.ItemDataRole.UserRole + 3, selected_version)

                    description = item.text(1)
                    updated_description = self.update_version_in_description(description, selected_version)
                    item.setText(1, updated_description)

                    self.selectionChanged.emit()

    def update_version_in_description(self, description, new_version):
        import re
        updated_desc = re.sub(r'\(v[^)]*\)', f'(v{new_version})', description)
        return updated_desc

    def on_item_changed(self, item, column):
        if item.childCount() > 0 and column == 0:
            check_state = item.checkState(0)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, check_state)

        elif item.parent() is not None and column == 0:
            parent = item.parent()
            all_checked = True
            all_unchecked = True

            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.checkState(0) == Qt.CheckState.Checked:
                    all_unchecked = False
                elif child.checkState(0) == Qt.CheckState.Unchecked:
                    all_checked = False
                else:
                    all_checked = False
                    all_unchecked = False

            if all_checked:
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif all_unchecked:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self.selectionChanged.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    selector = InstallSelector()

    python_group = selector.add_component_group("Python Environment", "Python runtime and core packages")
    selector.add_component(python_group, "Python 3.9", "Python 3.9 runtime", checked=True)
    selector.add_component(python_group, "Python 3.10", "Python 3.10 runtime", checked=False)
    selector.add_component(python_group, "pip", "Package installer for Python", checked=True)

    dev_tools_group = selector.add_component_group("Development Tools", "IDEs and development utilities")
    selector.add_component(dev_tools_group, "PyCharm Community", "PyCharm IDE Community Edition", checked=True)
    selector.add_component(dev_tools_group, "VSCode", "Visual Studio Code", checked=False)
    selector.add_component(dev_tools_group, "Git", "Version control system", checked=True)

    ui_frameworks_group = selector.add_component_group("UI Frameworks", "Graphical user interface frameworks")
    selector.add_component(ui_frameworks_group, "PyQt6", "PyQt6 framework", checked=True)
    selector.add_component(ui_frameworks_group, "Tkinter", "Tkinter GUI toolkit", checked=False)

    selector.show()

    sys.exit(app.exec())
