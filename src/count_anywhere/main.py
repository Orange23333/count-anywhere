import atexit
from pathlib import Path
import sys

#from PySide6.QtQml import QQmlApplicationEngine
#from PySide6.QtQuick import QQuickView
from PySide6.QtWidgets import QApplication

import count_anywhere.libs.utils as utils
from count_anywhere.widgets import AboutWindow, SystemTray

app: QApplication | None = None
exit_code: int | None = None

#region Initialization
import rc_resources  # Initialize Qt Resources.

app_dir: Path = Path(__file__).resolve().parent

from count_anywhere.libs import configs as configs
from count_anywhere.libs import i18n as i18n

config = configs.load_config(utils.get_config_path(str(app_dir)))

tr: i18n.Translator = i18n.Translator(
    utils.get_locales_dir(str(app_dir)),
    default_locale=config['i18n.locale'],
    fallback_locale='zh-CN'
)  # TODO: Auto detect locale.
#endregion

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
