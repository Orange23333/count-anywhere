import ruamel.yaml

import globals_
from path_dict import PathDict

__g: PathDict = globals_.get_global()

#region  Global configuration of i18n.
GLOBAL_KEY = 'i18n'


def get_global() -> PathDict:
    global __g

    return PathDict(
        d=__g,
        prefix=GLOBAL_KEY
    )


__i18n: PathDict = get_global()
#endregion


def load_locale(locale) -> dict:
    global __g

    d = __g['paths.app_path'] / 'locales'
    y = ruamel.yaml.YAML(typ='safe')

    t = y.load(d / f'{locale}.yml')

    return t


def set_locale(
        locale: str | None = None,
        fallback_locale: str | None = None
) -> None:
    global __i18n

    BASIC_LOCAL = 'zh-CN'

    if locale is None:
        locale = BASIC_LOCAL
    if fallback_locale is None:
        fallback_locale = BASIC_LOCAL

    __i18n['translations'] = load_locale(locale)
    __i18n['fallback_translations'] = load_locale(fallback_locale)


#region  Global configuration of i18n.
def _init_global(locale: str) -> None:
    global __g

    if GLOBAL_KEY not in __g:
        __g[GLOBAL_KEY] = {
            'translations': None,
            'fallback_translations': None
        }

        set_locale(locale=locale)


def get_translations() -> tuple[dict, dict]:
    global __i18n

    return (
        __i18n['translations'],
        __i18n['fallback_translations']
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
