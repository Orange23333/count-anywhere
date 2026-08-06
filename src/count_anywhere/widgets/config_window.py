from typing import Callable

from PySide6.QtCore import Qt, QItemSelectionModel, QModelIndex, QSize
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel, QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox, QLabel, QSizePolicy,
    QTreeView, QHBoxLayout, QVBoxLayout, QWidget
)

from count_anywhere.libs.configs import _set_config
from count_anywhere.libs.data_bindings import bind_translated_text
from count_anywhere.libs.i18n import get_available_locales, Translator
import count_anywhere.libs.utils as utils

class ConfigPage(QWidget):
    def __init__(
            self,
            text: str,  # Translated.
            config: dict,
            controls: list[dict],
            tr: Translator,
            parent = None
    ) -> None:
        super().__init__(parent)

        self.__config = config
        self.__tr = tr

        self.__data_binding_removers = []

        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__title = QLabel(text)
        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                text,
                self.__title,
                lambda w, t: w.setText(t)
            )
        )
        self.__title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.__title.setFixedSize(QSize(self.width(), 32))
        self.__title.setStyleSheet('font-size: 24px; font-weight: bold;')
        self.__title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__layout.addWidget(self.__title)

        def handle_pre_text(_layout, _args) -> None:
            if 'pre_text' in _args:
                pre_text = QLabel(
                    _args['pre_text'],
                    wordWrap=True,
                )
                self.__data_binding_removers.append(
                    bind_translated_text(
                        self.__tr,
                        _args['pre_text'],
                        pre_text,
                        lambda w, t: w.setText(t)
                    )
                )
                pre_text.setStyleSheet('font-size: 12px;')
                _layout.addWidget(pre_text)

        def handle_post_text(_layout, _args) -> None:
            if 'post_text' in _args:
                post_text = QLabel(
                    _args['post_text'],
                    wordWrap=True,
                )
                self.__data_binding_removers.append(
                    bind_translated_text(
                        self.__tr,
                        _args['post_text'],
                        post_text,
                        lambda w, t: w.setText(t)
                    )
                )
                post_text.setStyleSheet('font-size: 12px;')
                _layout.addWidget(post_text)

        # - <group_text> ---------------------------------
        #    <text_text>
        #    <text_box_text> [                          ]
        #    <slider_text> ===|================== <value>
        #    <selection_text> [ <selection_item_text> v ]
        #    <checkboxs_text>
        #     [] <checkbox_item_text>
        #    <radio_buttons_text>
        #     () <radio_button_item_text>
        #    <$other_widget$>
        for control in controls:  # TODO: make this constructor into a function.
            args = control['args']

            match control['type']:
                case 'check_box':
                    layout = QHBoxLayout()
                    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                    handle_pre_text(layout, args)

                    check_box = QCheckBox()
                    if 'current_status' in args:
                        check_box.setChecked(args['current_status']())
                    check_box.setStyleSheet('font-size: 12px;')
                    if 'currentStatusChanged_event_handler' in args:
                        currentStatusChanged_event_handler = args['currentStatusChanged_event_handler']
                        if currentStatusChanged_event_handler is not None:
                            check_box.checkStateChanged.connect(currentStatusChanged_event_handler)
                    layout.addWidget(check_box)

                    handle_post_text(layout, args)

                    self.__layout.addLayout(layout)
                case 'group':  # As title.
                    if 'text' not in args or args['text'] is None:
                        args['text'] = ''

                    text = QLabel(
                        args['text'],
                        wordWrap = False,
                    )
                    self.__data_binding_removers.append(
                        bind_translated_text(
                            self.__tr,
                            args['text'],
                            text,
                            lambda w, t: w.setText(t)
                        )
                    )
                    text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
                    text.setStyleSheet('font-size: 18px; margin-top: 8px;')
                    self.__layout.addWidget(text)

                    split_line = QFrame(
                        frameShape = QFrame.Shape.HLine,
                        frameShadow = QFrame.Shadow.Plain
                    )
                    self.__layout.addWidget(split_line)
                case 'selection':
                    if 'options' not in args or args['options'] is None:
                        args['options'] = []
                    if not isinstance(args['options'], list):
                        raise ValueError('`options` must be a `list`.')

                    layout = QHBoxLayout()
                    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                    handle_pre_text(layout, args)

                    selections = QComboBox()
                    selections.addItems(args['options'])
                    if 'current_option' in args:
                        selections.setCurrentText(args['current_option']())
                    selections.setStyleSheet('font-size: 12px;')
                    if 'currentTextChanged_event_handler' in args:
                        currentTextChanged_event_handler = args['currentTextChanged_event_handler']
                        if currentTextChanged_event_handler is not None:
                            selections.currentTextChanged.connect(currentTextChanged_event_handler)
                    layout.addWidget(selections)

                    handle_post_text(layout, args)

                    self.__layout.addLayout(layout)
                case _:
                    NotImplementedError('Unknown or unimplemented control type.')

        self.setLayout(self.__layout)

        #TODO: 改动应该经过config.py保存!!!

    def __del__(self) -> None:
        for remover in self.__data_binding_removers:
            remover()


class ConfigWindow(QWidget):
    ITEM_NAME_ROLE = Qt.ItemDataRole.UserRole + 2

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

        self.__data_binding_removers = []

        self.setWindowTitle(self.__tr('configure'))
        self.setFixedSize(800, 600)

        def get_native_name_of_locale(code: str) -> str:
            available_locales = get_available_locales(
                utils.get_locales_dir(self.__app_dir)
            )

            for available_locale in available_locales:
                if available_locale['code'] == code:
                    return available_locale['native_name']

            raise ValueError(f'Locale "{code}" not found.')
        def set_locale(native_name: str) -> None:
            available_locales = get_available_locales(
                utils.get_locales_dir(self.__app_dir)
            )

            for available_locale in available_locales:
                if available_locale['native_name'] == native_name:
                    _set_config(config, native_name, 'regular.locale')
                    tr.update_with(default_locale = available_locale['code'])
                    return

            raise ValueError(f'Locale "{native_name}" not found.')
        def set_debug_mode(enabled: Qt.CheckState) -> None:
            if enabled == Qt.CheckState.PartiallyChecked:
                raise ValueError('Invalid value.')
            enabled = True if enabled == Qt.CheckState.Checked else False
            _set_config(config, enabled, 'debug')
        self._config_tree = {
            'children': [
                {
                    'name': 'general',
                    'title': 'general',
                    'children': [],
                    'controls': [
                        {
                            'type': 'group',
                            'args': {
                                'text': 'localization'
                            }
                        },
                        {
                            'type': 'selection',
                            'args': {
                                'pre_text': 'language',
                                'options': [
                                    locale['native_name'] for locale in get_available_locales(
                                        utils.get_locales_dir(self.__app_dir)
                                    )
                                ],
                                'current_option': lambda : get_native_name_of_locale(tr.default_locale),
                                'currentTextChanged_event_handler': set_locale
                            }
                        }
                    ]
                },
                {
                    'name': 'hotkeys',
                    'title': 'hotkeys',
                    'children': [],
                    'controls': []
                },
                {
                    'name': 'developer_options',
                    'title': 'developer_options',
                    'children': [],
                    'controls': [
                        {
                            'type': 'check_box',
                            'args': {
                                'pre_text': 'enable_debug_mode',
                                'current_status': lambda : config['debug'],
                                'currentStatusChanged_event_handler': set_debug_mode
                            }
                        }
                    ]
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
        #self.__tree_view.expandAll()

    def __del__(self) -> None:
        for remover in self.__data_binding_removers:
            remover()

    def _on_tree_view_current_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        paths = []
        index = current
        while index.column() != -1:
            item = self.__tree_view_model.itemFromIndex(index)
            paths.append(item.data(role = ConfigWindow.ITEM_NAME_ROLE))

            index = index.parent()
        paths.reverse()

        leaf = self._config_tree
        for path in paths:
            for child in leaf['children']:
                if child['title'] == path:
                    leaf = child
                    break

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
        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                current_node['title'],
                item,
                lambda w, t: w.setText(t)
            )
        )
        item.setData(current_node['name'], role = ConfigWindow.ITEM_NAME_ROLE)
        parent.appendRow(item)

        if 'children' in current_node:
            for sub_node in current_node['children']:
                self.__generate_config_tree(item, sub_node)

    def update_tree_view(self) -> None:
        # For avoiding duplicating removers,
        # this function should only be called at __init__().

        root = self.__tree_view_model.invisibleRootItem()
        root.clearData()

        for leaf in self._config_tree['children']:
            self.__generate_config_tree(root, leaf)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.__on_closed_handler is not None:
            self.__on_closed_handler(self)
