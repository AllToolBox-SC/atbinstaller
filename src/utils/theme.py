from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QWidget


def is_dark_mode(widget: QWidget) -> bool:
    window_color = widget.palette().color(QPalette.ColorRole.Window)
    return window_color.lightness() < 128


def window_qss(dark_mode: bool) -> str:
    if dark_mode:
        return "QWidget { background-color: #1f2328; color: #f0f3f6; }"
    return "QWidget { background-color: #f7f8fa; color: #1f2328; }"


def nav_list_qss(dark_mode: bool) -> str:
    hover_color = "rgba(80,80,80,100)" if dark_mode else "rgba(31,155,93,24)"
    return (
        "QListWidget { background-color: rgba(0,0,0,0); border: none; outline: none; }"
        "QListWidget::item { border: none; padding: 5px; outline: none; }"
        "QListWidget::item:selected { background-color: rgba(0,0,0,0); color: #1F9B5D; outline: none; }"
        f"QListWidget::item:hover {{ background-color: {hover_color}; }}"
    )


def button_qss(dark_mode: bool) -> str:
    if dark_mode:
        return (
            "QPushButton { background-color: rgba(0,0,0,0); border: 1px solid #ffffff; color: #ffffff; border-radius: 5px; }"
            "QPushButton:disabled { background-color: rgba(0,0,0,0); border: 1px solid #555555; color: #555555; }"
            "QPushButton:hover:!disabled { background-color: rgba(255,255,255,30); border: 1px solid #ffffff; }"
            "QPushButton:pressed:!disabled { background-color: #1F9B5D; border: 0; color: #ffffff; }"
        )
    return (
        "QPushButton { background-color: rgba(0,0,0,0); border: 1px solid #8c959f; color: #1f2328; border-radius: 5px; }"
        "QPushButton:disabled { background-color: rgba(0,0,0,0); border: 1px solid #c2c7cf; color: #9aa1ab; }"
        "QPushButton:hover:!disabled { background-color: rgba(31,35,40,24); border: 1px solid #69707a; }"
        "QPushButton:pressed:!disabled { background-color: #1F9B5D; border: 0; color: #ffffff; }"
    )


def progress_qss(dark_mode: bool) -> str:
    border_color = "#ffffff" if dark_mode else "#c2c7cf"
    return (
        f"QProgressBar {{ border: 1px solid {border_color}; border-radius: 5px; background-color: rgba(0,0,0,0); }}"
        "QProgressBar::chunk { background-color: #1F9B5D; }"
    )
