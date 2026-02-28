from pathlib import Path
import tomllib

from PySide6.QtWidgets import QLayout

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
