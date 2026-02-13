from pathlib import Path

import ruamel.yaml

import globals_
from path_dict import get_by_path, set_by_path

__g = globals_.get_global()


def load_locale(locale) -> dict:
    global __g

    d = get_by_path(
        __g,
        'paths.app_path',
        always_return=False
    ) / 'locales'
    y = ruamel.yaml.YAML(typ='safe')

    t = y.load(d / f'{locale}.yml')

    return t


def set_locale(
        locale: str | None = None,
        fallback_locale: str | None = None
) -> None:
    global __g

    if locale is None:
        locale = 'en-US'
    if fallback_locale is None:
        fallback_locale = 'en-US'

    set_by_path(
        __g,
        'translations',
        load_locale(locale),
        prefix = GLOBAL_KEY,
        allow_create = False
    )
    set_by_path(
        __g,
        'fallback_translations',
        load_locale(fallback_locale),
        prefix = GLOBAL_KEY,
        allow_create = False
    )


#region  Global configuration of i18n.

GLOBAL_KEY = 'i18n'


def _init_global(locale: str) -> None:
    global __g

    if GLOBAL_KEY not in __g:
        set_by_path(
            __g,
            'translations',
            None,
            prefix=GLOBAL_KEY,
            allow_create=True
        )
        set_by_path(
            __g,
            'fallback_translations',
            None,
            prefix=GLOBAL_KEY,
            allow_create=True
        )

        set_locale(locale=locale)


_init_global(locale='en-US')


def get_global() -> dict:
    global __g

    return get_by_path(
        __g,
        GLOBAL_KEY,
        always_return = False
    )


def get_translations() -> tuple[dict, dict]:
    global __g

    return (
        get_by_path(
            __g,
            'fallback_translations',
            prefix=GLOBAL_KEY,
            always_return = False
        ),
        get_by_path(
            __g,
            'fallback_translations',
            prefix=GLOBAL_KEY,
            always_return = False
        )
    )


#endregion


def _tr(t: dict, path: str, **kwargs) -> str | None:
    parts = path.split('.')

    ret = t
    for part in parts:
        if part not in ret:
            return None
        ret = ret[part]

    return ret.format(**kwargs)


def tr(path: str, **kwargs) -> str:
    t, ft = get_translations()

    ret = _tr(t, path, **kwargs)
    if ret is None:
        ret = _tr(ft, path, **kwargs)
        if ret is None:
            raise RuntimeError('Lost translation.')

    return ret
