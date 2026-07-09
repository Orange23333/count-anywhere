from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import warnings

import ruamel.yaml

import any_singleton.singletons as sgt
import count_anywhere.sgt_dns as sgt_dns

# TODO: Hot reloading translations is so cool, but it will waste too much time on completing `bind_translated_text()`.
#       So, just remove it. And enforce users reboot after changing locale. It will reduce the complexity of the code.
#       .
#       Otherwise, is there a good practice to make binding translations more efficient (automatically)?
#       No QTranslator, I don't like its style.
#       .
#       Even we could delete binding operation, just refresh all the widgets?
#       Will it require cache status of widgets? How to refresh?

@dataclass
class Translation:
    label: str
    comparison_table: dict


def _load_locale(locales_dir: str, locale: str) -> Translation:
    d = Path(locales_dir).resolve()
    y = ruamel.yaml.YAML(typ='safe')

    ct = y.load(d / f'{locale}.yml')

    return Translation(
        label=locale,
        comparison_table=ct
    )


def get_available_locales(locales_dir: str) -> list[dict]:
    # Deprecated method to find available_locales:
    # ```
    # d = Path(locales_dir).resolve()
    # return [ f.stem for f in d.iterdir() if f.is_file() and f.suffix == '.yml' ]
    # ```
    # Reason: Using file system to find files with specific suffix is inefficient and unreliable.

    d = Path(locales_dir).resolve()
    y = ruamel.yaml.YAML(typ='safe')

    t = y.load(d / 'available_locales.yml')

    return t


# TODO: Using UI bindings to instead manually write a update function to update text is more convenient.
def on_translation_updated(handler: Callable[[Translator], None]) -> None:
    if sgt.is_singleton_exists(sgt_dns.TRANSLATOR):
        tr = sgt._get_singleton(sgt_dns.TRANSLATOR)
        tr.on_update_handlers.append(handler)
    else:
        cache = sgt.singleton(sgt_dns.ON_TRANSLATOR_UPDATED__QUEUED_HANDLERS, [])
        cache.append(handler)


class Translator:
    def __init__(
            self,
            locales_dir: str,
            default_locale: str = 'en-US',
            fallback_locale: str = 'zh-CN'
    ) -> None:
        self._locales_dir = locales_dir

        self._t = _load_locale(locales_dir, default_locale)
        self._ft = _load_locale(locales_dir, fallback_locale)

        self._on_update_handlers: list[Callable[[Translator], None]] = []

    @property
    def default_locale(self) -> str:
        return self._t.label

    @property
    def fallback_locale(self) -> str:
        return self._ft.label

    @property
    def on_update_handlers(self) -> list[Callable[[Translator], None]]:
        return self._on_update_handlers

    def update_with(
            self,
            default_locale: str | None = 'en-US',
            fallback_locale: str | None = 'zh-CN'
    ) -> None:
        changed = False

        if default_locale is not None and default_locale != self._t.label:
            self._t = _load_locale(self._locales_dir, default_locale)
            changed = True
        if fallback_locale is not None and fallback_locale != self._ft.label:
            self._ft = _load_locale(self._locales_dir, fallback_locale)
            changed = True

        if changed:
            for handler in self._on_update_handlers:
                handler(self)

    @staticmethod
    def _tr(t: Translation, path: str, **kwargs) -> str | None:
        parts = path.split('.')

        ret = t.comparison_table
        for part in parts:
            if part not in ret:
                return None
            ret = ret[part]

        return ret.format(**kwargs)

    def tr(self, path: str, **kwargs) -> str:
        ret = Translator._tr(self._t, path, **kwargs)
        if ret is None:
            ret = Translator._tr(self._ft, path, **kwargs)
            if ret is None:
                raise RuntimeError('Lost translation.')  # Or using `return path`?
            warnings.warn(f'Translation fallback: "{path}".')

        return ret

    def __call__(self, path: str, **kwargs) -> str:
        return self.tr(path, **kwargs)

class NullableTranslator:
    def __init__(self, tr: Translator | None):
        self._tr = tr

    def tr(self, path: str, **kwargs) -> str:
        if self._tr is None:
            return path
        return self._tr.tr(path, **kwargs)

    def __call__(self, path: str, **kwargs) -> str:
        return self.tr(path, **kwargs)
