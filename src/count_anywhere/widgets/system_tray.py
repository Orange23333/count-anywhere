import warnings
from pathlib import Path
import tomllib
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from count_anywhere.libs.data_bindings import bind_translated_text
from count_anywhere.libs.i18n import Translator, on_translation_updated
import count_anywhere.libs.utils as utils
from count_anywhere.widgets import AboutWindow, ConfigWindow, MarkerEditor


class SystemTray(QSystemTrayIcon):
    def __init__(
            self,
            on_exit: Callable[[int], None],
            app_dir: str,
            config: dict,
            tr: Translator,
            parent = None
    ) -> None:
        super().__init__(QIcon(':/icons/Logo'), parent)

        self.__on_exit = on_exit
        self.__app_dir = app_dir
        self.__config = config
        self.__tr = tr

        self.__about_window = None
        self.__config_window = None
        self.__status: bool = False  # TODO: 应当为全局变量

        self.__data_binding_removers = []

        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                'app.name',
                self,
                lambda w, t: w.setToolTip(t)
            )
        )

        self.__menu = QMenu()

        actions = [
            {
                'name': 'count_now',
                'text': 'count_now',
                'args': {
                    'toolTip': 'actions.count_now.tool_tip'
                },
                'callback': self.start_new_count
            },
            {
                'name': 'active',
                'text': 'active',
                'args': {
                    'checkable': True,
                    'toolTip': 'actions.active.tool_tip'
                },
                'callback': self.toggle_status
            },
            { 'type': 'separator' },
            {
                'name': 'configure',
                'text': 'configure',
                'args': {
                    'toolTip': 'actions.configure.tool_tip'
                },
                'callback': self.show_config_window
            },
            { 'type': 'separator' },
            {
                'name': 'help',
                'text': 'help',
                'args': {
                    'toolTip': 'actions.help.tool_tip'
                },
                'callback': self.show_help
            },
            {
                'name': 'about',
                'text': 'about',
                'args': {
                    'toolTip': 'actions.about.tool_tip'
                },
                'callback': self.show_about
            },
            { 'type': 'separator' },
            {
                'name': 'quit',
                'text': 'quit',
                'args': {
                    'toolTip': 'actions.quit.tool_tip'
                },
                'callback': self.quit
            }
        ]
        self.__actions = {}
        for action in actions:
            if 'type' in action and action['type'] == 'separator':
                self.__menu.addSeparator()
            else:
                new_action = QAction(
                    action['text'],
                    **action['args']
                )
                self.__data_binding_removers.append(
                    bind_translated_text(
                        self.__tr,
                        action['text'],
                        new_action,
                        lambda w, t: w.setText(t)
                    )
                )
                self.__data_binding_removers.append(
                    bind_translated_text(
                        self.__tr,
                        action['args']['toolTip'],
                        new_action,
                        lambda w, t: w.setToolTip(t)
                    )
                )
                new_action.triggered.connect(action['callback'])

                self.__menu.addAction(new_action)
                self.__actions[action['name']] = new_action

        self.setContextMenu(self.__menu)

        self.activated.connect(self._on_activated)

        self.toggle_status(True)
        self.update_hotkeys()

    def __del__(self) -> None:
        for remover in self.__data_binding_removers:
            remover()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        match reason:
            case QSystemTrayIcon.ActivationReason.Trigger:
                # Left Clicked.
                self.show_ui()
            case QSystemTrayIcon.ActivationReason.Context:
                # Right Clicked.
                pass
            case QSystemTrayIcon.ActivationReason.DoubleClick:
                # Double Clicked.
                pass
            case QSystemTrayIcon.ActivationReason.MiddleClick:
                # Middle Clicked.
                pass
            case QSystemTrayIcon.ActivationReason.Unknown | _:
                pass
                #raise RuntimeError('Unknown reason.')

    def update_hotkeys(self) -> None:
        pass
        #h = pynput.keyboard.GlobalHotKeys({
        #    '<cself.__trl>+<alt>+a': self.toggle_status
        #})  # TODO: How to unhook global hotkeys when exit?

    def show_ui(self) -> None:
        pass

    def toggle_status(self, status: bool | None = None) -> None:
        if status is None:
            status = not self.__status

        self.__status = status

        self.__actions['active'].setChecked(status)

        self.showMessage(
            self.__tr('status'),
            self.__tr('activated' if status else 'deactivated'),
            icon=QSystemTrayIcon.MessageIcon.Information,
            msecs=3000
        )

    def __other_widgets_on_closed_handler(self, sender: QWidget) -> None:
        if isinstance(sender, ConfigWindow):
            self.__config_window = None
        elif isinstance(sender, AboutWindow):
            self.__about_window = None
        else:
            warnings.warn('Unknown sender.')

        sender.deleteLater()

    def start_new_count(self) -> None:
        screen = utils.locate_cursor_on_which_screen()
        # picture = utils.take_screenshot(screen, using_available_geometry = True)

        editor = MarkerEditor(screen = screen, picture = None)
        utils.keep_widget(editor)

    def show_config_window(self) -> None:
        if self.__config_window is None:
            self.__config_window = ConfigWindow(
                self.__config,
                self.__app_dir,
                self.__tr,
                on_closed_handler = self.__other_widgets_on_closed_handler
            )

        self.__config_window.showNormal()
        self.__config_window.activateWindow()
        # TODO: Destory object when close the window.

    def show_help(self) -> None:
        pass

    def show_about(self) -> None:
        if self.__about_window is None:
            self.__about_window = AboutWindow(
                utils.get_version(
                    utils.get_pyproject_path(str(self.__app_dir))
                ),
                self.__tr,
                on_closed_handler = self.__other_widgets_on_closed_handler
            )

        self.__about_window.showNormal()
        self.__about_window.activateWindow()
        # TODO: Destory object when close the window.


    def quit(self) -> None:
        self.__on_exit(0)

    ## For MainWindow
    #def closeEvent(self, event: QCloseEvent) -> None:
    #    self.hide()
    #    event.ignore()