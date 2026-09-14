import atexit
from pathlib import Path
import sys

from PySide6.QtCore import QMessageLogContext, qInstallMessageHandler, QtMsgType
#from PySide6.QtQml import QQmlApplicationEngine
#from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QApplication

import any_singleton.singletons as sgt
import count_anywhere.libs.utils as utils
import count_anywhere.sgt_dns as sgt_dns
from count_anywhere.widgets import AboutWindow, SystemTray

app: QApplication | None = None
exit_code: int | None = None

#region Initialization
import rc_resources  # Initialize Qt Resources.

app_dir: Path = Path(__file__).resolve().parent

from count_anywhere.libs import configs as configs
from count_anywhere.libs import i18n as i18n

config = sgt.singleton(
    sgt_dns.CONFIG,
    configs.load_config(utils.get_config_path(str(app_dir)))
)

tr: i18n.Translator = sgt.singleton(
    sgt_dns.TRANSLATOR,
    i18n.Translator(
        utils.get_locales_dir(str(app_dir)),
        default_locale=config['i18n.locale'],
        fallback_locale='zh-CN'
    )  # TODO: Auto detect locale.
)
if sgt.is_singleton_exists(sgt_dns.ON_TRANSLATOR_UPDATED__QUEUED_HANDLERS):
    tr.on_update_handlers.extend(
        sgt._get_singleton(sgt_dns.ON_TRANSLATOR_UPDATED__QUEUED_HANDLERS)
    )
    sgt._remove_singleton(sgt_dns.ON_TRANSLATOR_UPDATED__QUEUED_HANDLERS)
#endregion


def qt_message_handler(type_: QtMsgType, context: QMessageLogContext, msg: str) -> None:
    print(f'[{type_.name}] {msg}')
    print(f'{context}')

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
    global config
    global exit_code
    global tr

    qInstallMessageHandler(qt_message_handler)

    app = QApplication(sys.argv)  # TODO: Handling arguments.
    #app.installTranslator(translator)
    app.setQuitOnLastWindowClosed(False)

    #engine = QQmlApplicationEngine()
    #engine.load(str(app_path / 'widgets' / 'main.qml'))
    #if not engine.rootObjects():
    #    exit_with(-1)

    #view = QQuickView()
    #view_path = str(app_dir / 'widgets' / 'something.qml')
    #view.setSource(view_path)
    #view.setResizeMode(QQuickView.SizeRootObjectToView)
    #view.show()

    tray = SystemTray(exit_with, str(app_dir), config, tr)
    tray.show()

    exit_code = app.exec()

    exit_with(exit_code)


if __name__ == '__main__':
    main()
