from __future__ import annotations
import bisect
import importlib
import importlib.util
from pathlib import Path
import sys
import tomllib
from types import ModuleType
from typing import Any, Callable, Iterable

from PySide6.QtCore import QDir, QPoint, QRect, QStandardPaths, Qt, QTimer, Slot
from PySide6.QtGui import QCursor, QImageWriter, QPixmap, QScreen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout,
    QMessageBox, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget
)

import any_singleton.singletons as sgt


def get_version(pyproject_path: str) -> str:
    with open(pyproject_path, 'rb') as f:
        toml = tomllib.load(f)
    return toml['project']['version']


def get_config_path(app_dir: str) -> str:
    return str(Path(app_dir) / 'config.yml')


def get_pyproject_path(app_dir: str) -> str:
    return str(Path(app_dir) / 'pyproject.toml')


def get_locales_dir(app_dir: str) -> str:
    return str(Path(app_dir) / 'locales')


def clear_layout(layout: QLayout) -> None:
    while layout.count() > 0:
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        layout.removeItem(item)


# TODO: Module loader.
# def load_module_from_(module_name: str, only_load_from_script_file: bool = False) -> ModuleType:
#     m = None
#
#     # Step:
#     # - Load from context.
#     # - Load using import from CWD.
#     # - Load using import from given path.
#     #
#     # Load plugin:
#     # using given name load from given directory.
#
#     if not only_load_from_script_file:
#
#         # Try loading the module from context.
#         try:
#             m = eval(module_name)
#         except Exception:
#             pass
#
#         if m is None:
#             try:
#                 m = importlib.import_module(module_name)
#             except Exception:
#                 pass
#
#     pass


def locate_cursor_on_which_screen() -> QScreen | None:
    cursor_pos = QCursor.pos()

    for screen in QApplication.screens():
        if screen.geometry().contains(cursor_pos, proper=False):
            return screen

    return None


def take_screenshot(screen: QScreen, using_available_geometry: bool = True) -> QPixmap | None:
    p = (
        screen
        .grabWindow(0)
        .copy(QRect(
            QPoint(0, 0),
            screen.availableGeometry().size() if using_available_geometry else screen.geometry().size())
        )
    )

    return p


def keep_widget(w: QWidget) -> None:
    widgets = sgt.singleton('count_anywhere.libs.utils.keep_temp_widget.widgets', [])
    widgets.append(w)


def bisect_insert_many(
    a: list[Any],
    items: Iterable[Any],
    *,
    key: Callable[[Any], Any] = None
) -> None:
    items = sorted(items, key=key)

    insert_point = 0  # Also lo.
    for item in items:
        insert_point = bisect.bisect_right(a, item, lo=insert_point, key=key)
        a.insert(insert_point, item)
