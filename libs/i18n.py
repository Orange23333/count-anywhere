from dataclasses import dataclass

from pathlib import Path
import ruamel.yaml


@dataclass
class Translation:
    label: str
    translation: dict


def _load_locale(locales_dir: str, locale: str) -> Translation:
    d = Path(locales_dir).resolve()
    y = ruamel.yaml.YAML(typ='safe')

    t = y.load(d / f'{locale}.yml')

    return Translation(
        label=locale,
        translation=t
    )


def get_available_locales(locales_dir: str) -> list[str]:
    d = Path(locales_dir).resolve()

    return [ f.stem for f in d.iterdir() if f.is_file() and f.suffix == '.yml' ]


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

        self._on_update_handlers = []

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
                handler()

    @staticmethod
    def _tr(t: Translation, path: str, **kwargs) -> str | None:
        parts = path.split('.')

        ret = t.translation
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
                raise RuntimeError('Lost translation.')
                #return path

        return ret

    def __call__(self, path: str, **kwargs) -> str:
        return self.tr(path, **kwargs)
