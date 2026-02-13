import os
import warnings
from pathlib import Path
import platform
from typing import Literal, Any

import ruamel.yaml

import globals_
import i18n

def set_platform(
    value: str | None = None,
    key: Literal['os', 'desktop'] | None = None
) -> None:
    if key is None:
        raise ValueError('`key` must be specified.')

    g = globals_.get_global()

    match key:
        case 'os':
            if value is None:
                value = '@auto'

            if value == '@auto':
                pass

            match value:
                case 'windows':
                    value = 'nt'
                case 'linux':
                    value = 'unix'
                case 'macos':
                    value = 'unix'

            if value not in [
                'windows',
                'linux',
                'macos'
            ]:
                warnings.warn('Unknown OS.')
                value = Noneko0

            g['environment']['platform']['os'] = value
        case 'desktop':
            if value is None:
                value = '@auto'

            # TODO: Support Wayland and Xorg for Linux.

            pass
        case _:
            raise ValueError('Unknown `key`.')

def load_config() -> None:
    y = ruamel.yaml.YAML(typ='safe')
    d = Path(__file__).resolve().parent

    config = ruamel.yaml.YAML(typ='safe').load(d / 'config.yml')

    config_handlers = [
        {
            'path': 'regular.locale',
            'required': False,
            'handler': lambda v: i18n.set_locale(locale=v)
        },
        {
            'path': 'environment.platform.os',
            'required': False,
            'handler': set_platform,
            'args': {
                'key': 'os'
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
