from typing import Any, Callable

from count_anywhere.libs.i18n import Translator


def bind_translated_text(
        tr: Translator,
        key: str,
        target: Any,
        updater: Callable[[Any, str], None],
        **kwargs
) -> Callable[[], None]:
    def _on_update(from_: Translator):
        #updater(target, from_(key))
        updater(target, tr(key, **kwargs))

    _on_update(tr)

    tr.on_update_handlers.append(_on_update)

    def remover():
        tr.on_update_handlers.remove(_on_update)

    return remover