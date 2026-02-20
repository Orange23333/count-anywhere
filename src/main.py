import atexit
import sys

import pynput.keyboard
#from PySide6.QtCore import QTranslator
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from __init__ import *

exit_code: int | None = None
app: QApplication | None = None
#translator: QTranslator | None = None

class ConfigWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(tr('configure.title'))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()

        event.ignore()


class SystemTray(QSystemTrayIcon):
    def __init__(self) -> None:
        super().__init__(QIcon(':/icons/Logo'))

        self.__status: bool = False

        self.setToolTip(tr('app.name'))

        # 创建托盘的右键菜单
        self.__menu = QMenu()

        actions = [
            {
                'name': 'active',
                'text': tr('action.active.text'),
                'args': {
                    'checkable': True,
                    'toolTip': tr('action.active.tool_tip')
                },
                'callback': self.toggle_status
            },
            {
                'name': 'configure',
                'text': tr('action.configure.text'),
                'args': {
                    'toolTip': tr('action.configure.tool_tip')
                },
                'callback': self.show_config_window
            },
            {
                'name': 'help',
                'text': tr('action.help.text'),
                'args': {
                    'toolTip': tr('action.help.tool_tip')
                },
                'callback': self.show_help
            },
            {
                'name': 'quit',
                'text': tr('action.quit.text'),
                'args': {
                    'toolTip': tr('action.quit.tool_tip')
                },
                'callback': self.quit
            }
        ]
        self.__actions = {}
        for action in actions:
            new_action = QAction(
                action['text'],
                **action['args']
            )
            new_action.triggered.connect(action['callback'])

            self.__menu.addAction(new_action)
            self.__actions[action['name']] = new_action

        self.setContextMenu(self.__menu)

        self.activated.connect(self.on_activated)

        self.toggle_status(True)
        self.update_hotkeys()

    def on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
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
        h = pynput.keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+a': self.toggle_status
        })# TODO: How to unhook global hotkeys when exit?

    def toggle_status(self, status: bool | None = None) -> None:
        if status is None:
            status = not self.__status

        self.__status = status

        self.__actions['active'].setChecked(status)

        self.showMessage(
            tr('message.status.title'),
            tr('message.status.' + ('activated' if status else 'deactivated')),
            icon=QSystemTrayIcon.MessageIcon.Information,
            msecs=3000
        )

    def show_ui(self) -> None:
        pass

    def show_config_window(self) -> None:
        pass

    def show_help(self) -> None:
        pass

    def quit(self) -> None:
        global app

        exit_with(0)


@atexit.register
def exit_() -> None:
    global exit_code
    global app

    if exit_code is None:
        exit_code = -1

    if app is not None:
        app.exit(exit_code)
        app = None

    sys.exit(exit_code)


def exit_with(code: int) -> None:
    global exit_code

    exit_code = code
    exit_()


def main() -> None:
    global app



    #translator = QTranslator()
    #translator.load(':/languages/zh_CN')

    app = QApplication(sys.argv)  # TODO: Handling arguments.
    #app.installTranslator(translator)
    app.setQuitOnLastWindowClosed(False)

    tray = SystemTray()
    tray.show()

    exit_code = app.exec()

    exit_with(exit_code)


if __name__ == '__main__':
    main()
