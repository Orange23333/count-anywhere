from typing import Callable

from PySide6.QtCore import Qt, QItemSelectionModel, QModelIndex, QSize
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel, QCloseEvent
from PySide6.QtWidgets import QAbstractItemView, QGridLayout, QLabel, QSizePolicy, QTreeView, QHBoxLayout, QVBoxLayout, QWidget

from count_anywhere.libs.i18n import get_available_locales, Translator
import count_anywhere.libs.utils as utils

class ConfigPage(QWidget):
    def __init__(
            self,
            title: str,  # Translated.
            config: dict,
            controls: list[dict],
            tr: Translator,
            parent = None
    ) -> None:
        super().__init__(parent)

        self.__config = config
        self.__tr = tr

        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__title = QLabel(title)
        self.__title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.__title.setFixedSize(QSize(self.width(), 32))
        self.__title.setStyleSheet('font-size: 24px; bold: true;')
        self.__title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__layout.addWidget(self.__title)

        for control in controls:
            pass

        self.setLayout(self.__layout)

        #TODO: 改动应该经过config.py保存



class ConfigWindow(QWidget):
    def __init__(
            self,
            config: dict,
            app_dir: str,
            tr: Translator,
            on_closed_handler: Callable[[QWidget], None] | None = None,
            parent=None
    ) -> None:
        super().__init__(parent)

        self.__config = config
        self.__app_dir = app_dir
        self.__tr = tr
        self.__on_closed_handler = on_closed_handler

        self.setWindowTitle(self.__tr('configure'))
        self.setFixedSize(800, 600)

        self._config_tree = {
            'children': [
                {
                    'title': self.__tr('general'),
                    'children': [],
                    'controls': [
                        {'type': 'group', 'args': {'title': self.__tr('localization')}},
                        {
                            'type': 'selection',
                            'args': {
                                'title': self.__tr('language'),
                                'options': [
                                    locale['native_name'] for locale in get_available_locales(
                                        utils.get_locales_dir(self.__app_dir)
                                    )
                                ]
                            }
                        }
                    ]
                },
                {
                    'title': self.__tr('hotkeys'),
                    'children': [],
                    'controls': []
                }
            ]
        }

        self.__layout = QHBoxLayout()

        self.__tree_view_model = QStandardItemModel()
        #self.__tree_view_model.setHorizontalHeaderLabels([self.__tr('configure')])

        self.__tree_view = QTreeView()
        self.__tree_view.setHeaderHidden(True)
        self.__tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.__tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.__tree_view.setModel(self.__tree_view_model)
        self.__tree_view.setMinimumSize(80, 0)
        self.__tree_view.setMaximumSize(0xFF, 0xFFFF)
        self.__tree_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__tree_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.__tree_view.selectionModel().currentChanged.connect(
            self._on_tree_view_current_changed
        )
        self.__layout.addWidget(self.__tree_view, 1)

        self.__current_config_page = None

        self.__config_view = QGridLayout()
        self.__layout.addLayout(self.__config_view, 3)

        self.setLayout(self.__layout)

        self.update_tree_view()
        self.__tree_view.expandAll()

    def _on_tree_view_current_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        paths = []
        index = current
        while index.column() != -1:
            item = self.__tree_view_model.itemFromIndex(index)
            paths.append(item.text())

            index = index.parent()
        paths.reverse()

        leaf = self._config_tree
        for path in paths:
            for child in leaf['children']:
                if child['title'] == path:
                    leaf = child

        self.__current_config_page = ConfigPage(
                paths[-1],
                self.__config,
                leaf['controls'],
                self.__tr
            )
        self.__current_config_page.setMinimumSize(0xFF, 0)
        self.__current_config_page.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        utils.clear_layout(self.__config_view)
        self.__config_view.addWidget(self.__current_config_page)

    def __generate_config_tree(self, parent: QStandardItem, current_node: dict) -> None:
        item = QStandardItem(current_node['title'])
        parent.appendRow(item)

        if 'children' in current_node:
            for sub_node in current_node['children']:
                self.__generate_config_tree(item, sub_node)

    def update_tree_view(self) -> None:
        root = self.__tree_view_model.invisibleRootItem()
        root.clearData()

        for leaf in self._config_tree['children']:
            self.__generate_config_tree(root, leaf)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.__on_closed_handler is not None:
            self.__on_closed_handler(self)
