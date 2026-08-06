from pathlib import Path
import platform
from typing import Any, Literal
import warnings

import ruamel.yaml


def _set_config(
        config: dict,
        value: Any | None,
        path: str | None = None
) -> None:
    if path is None:
        raise ValueError('`path` is required.')
    config[path] = value


def set_platform(
        config: dict,
        value: str | None,
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

    DO NOT shoot in the dark.
    Never guess how to get and category platform identification and
    attempt to implement a platform-specific functions.
    Instead, start by implementing for your current development environment.
    """

    if key is None:
        raise ValueError('`key` must be specified.')

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

            _set_config(config, value, 'environment.os')
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

            _set_config(config, value, 'environment.desktop')
        case 'hotkey_module':
            if value is None:
                value = '@auto'

            if value == '@auto':
                value = auto_detect_hotkey_module()

            match value:
                case _:
                    warnings.warn(f'`{value}` is an unknown desktop environment.')

            _set_config(config, value, 'environment.hotkey_module')
        case _:
            raise KeyError(key)


def load_config(config_path: str) -> dict:
    y = ruamel.yaml.YAML(typ='safe')
    config = ruamel.yaml.YAML(typ='safe').load(Path(config_path))

    ret = {}

    # TODO: 支持分割线
    config_handlers = [
        {
            'path': 'debug',
            'required': False,
            'default': False,
            'handler': _set_config,
            'args': {
                'path': 'debug'
            }
        },
        {
            'path': 'regular.locale',
            'required': True,
            'default': 'en-US',
            'handler': _set_config,
            'args': {
                'path': 'i18n.locale'
            }
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

    for h in config_handlers:  # TODO: make this constructor into a function.
        path = h['path']
        parts = path.split('.')

        value = config
        for part in parts:
            if part not in value:
                if h['required']:
                    if 'default' in h:
                        value = h['default']
                        break
                    else:
                        raise RuntimeError(f'Config "{path}" is required.')
                else:
                    value = None
                    break
            value = value[part]

        h['handler'](
            ret,
            value,
            **(
                {} if ('args' not in h or h['args'] is None)
                else h['args']
            )
        )

    return ret
