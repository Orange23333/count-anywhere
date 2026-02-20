from pathlib import Path
import platform
from typing import Literal
import warnings

import ruamel.yaml

import globals_
import i18n
from path_dict import PathDict

__g: PathDict = globals_.get_global()

def set_platform(
    value: str | None = None,
    key: Literal['os', 'desktop'] | None = None
) -> None:
    """
    Be supported platforms:
    - Windows
    - macOS
    - Linux:
      - X11
      - Wayland
      ...
      - KDE
      - GNOME
      ...
      - Xfce
      - LXQt
      - LXDE

    Looks like Python basically supports those platforms:
    Windows, macOS, iOS, Unix, Linux, Android, Java.

    不要盲猜怎么识别一个平台，并尝试实现它，先实现你当前开发环境的平台。
    """

    global __g

    if key is None:
        raise ValueError('`key` must be specified.')

    cfg = PathDict(
        d = __g,
        prefix = 'environment.platform'
    )

    def auto_detect_os() -> str:
        os_ = platform.system()
        match os_:
            case 'Windows':
                return 'windows'
            case '':
                raise RuntimeError('Can\'t auto detect the platform.')
            case _:
                raise NotImplementedError(f'`{os_}` system isn\'t supported.')

    def auto_detect_desktop() -> str:
        raise NotImplementedError(f'Auto detect desktop environment isn\'t implemented.')

    def auto_detect_hotkey_module() -> str:
        raise NotImplementedError(f'Auto detect hotkey module isn\'t implemented.')

    match key:
        case 'os':
            if value is None:
                value = '@auto'

            if value == '@auto':
                value = auto_detect_os()

            match value:
                case 'windows':
                    value = 'windows'
                case _:
                    warnings.warn(f'`{value} is an unknown operation system.')

            cfg['os'] = value
        case 'desktop':
            if value is None:
                value = '@auto'

            if value == '@auto':
                value = auto_detect_desktop()

            match value:
                case 'windows':
                    value = 'windows'
                case _:
                    warnings.warn(f'`{value} is an unknown desktop environment.')

            cfg['desktop'] = value
        case 'hotkey_module':
            if value is None:
                value = '@auto'

            if value == '@auto':
                value = auto_detect_hotkey_module()

            match value:
                case _:
                    warnings.warn(f'`{value} is an unknown desktop environment.')

            cfg['hotkey_module'] = value
        case _:
            raise KeyError(key)

def load_config() -> None:
    global __g

    y = ruamel.yaml.YAML(typ='safe')
    d = Path(__file__).resolve().parent

    config = ruamel.yaml.YAML(typ='safe').load(d / 'config.yml')

    config_handlers = [
        {
            'path': 'regular.locale',
            'required': True,
            'default': None,
            'handler': lambda v: i18n.set_locale(locale=v)
        },
        {
            'path': 'environment.platform.os',
            'required': True,
            'default': None,
            'handler': set_platform,
            'args': {
                'key': 'os'
            }
        },
        {
            'path': 'environment.platform.desktop',
            'required': True,
            'default': None,
            'handler': set_platform,
            'args': {
                'key': 'desktop'
            }
        },
        {
            'path': 'environment.platform.hotkey_module',
            'required': True,
            'default': None,
            'handler': set_platform,
            'args': {
                'key': 'hotkey_module'
            }
        }
    ]

    for h in config_handlers:
        path = h['path']
        parts = path.split('.')

        value = config
        for part in parts:
            if part not in value:
                if h['required']:
                    if 'default' in h:
                        value = h['default']
                    else:
                        raise RuntimeError(f'Config "{path}" is required.')
                else:
                    value = None
                    break
            value = value[part]

        h['handler'](
            value,
            **(
                {} if ('args' not in h or h['args'] is None)
                else h['args']
            )
        )
