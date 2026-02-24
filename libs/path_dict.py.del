from __future__ import annotations
from typing import Any


def _get_parts_of_path(
        path: str | None = None,
        prefix: str | None = None
) -> list[str]:
    # Never check for empty (whitespace) strings.

    parts = [] if prefix is None else prefix.split('.')
    parts += path.split('.')
    return parts


def get_by_path(
        d: dict,
        path: str,
        prefix: str | None = None,
        always_return: bool = True,
        default: Any = None
) -> Any:
    parts = _get_parts_of_path(path, prefix)

    target = d
    for part in parts:
        if part not in target:
            if always_return:
                return default
            raise KeyError(f'Not found.')

        target = target[part]

    return target


def set_by_path(
        d: dict,
        path: str,
        value: Any,
        prefix: str | None = None,
        allow_create: bool = True  # It always return `True` if `True`.
) -> bool:

    parts = _get_parts_of_path(path, prefix)

    target = d
    r = range(len(d) - 1)
    for i in r:
        part = parts[i]

        if part not in target:
            if not allow_create:
                return False

            target[part] = {}
            target = target[part]
            break

        target = target[part]
    for i in r:
        part = parts[i]

        target = target[part] = {}

    part = parts[-1]
    if (part not in target) and not allow_create:
        return False
    target[part] = value

    return True


def del_by_path(
        d: dict,
        path: str,
        prefix: str | None = None
) -> bool:
    parts = _get_parts_of_path(path, prefix)

    target = d
    for part in parts[:-1]:
        if part not in target:
            return False

        target = target[part]

    part = parts[-1]
    if part not in target:
        return False
    del target[part]
    return True


class PathDict:
    def __init__(
            self,
            d: dict | PathDict | None = None,   # If giving a `PathDict`, this `PathDict` will refer its inner `dict`,
                                                # not the given `PathDict`.
            prefix: str | None = None
    ) -> None:
        if d is None:
            self._d: dict = {}
        elif isinstance(d, dict):
            self._d: dict = d
        elif isinstance(d, PathDict):
            self._d: dict = d.inner_dict
        else:
            raise TypeError('`d` must be `None`, `dict` or `PathDict`.')

        if isinstance(d, PathDict) and d.prefix is not None:
            self._prefix: str | None = d.prefix
            if prefix is not None:
                self._prefix += '.' + prefix
        else:
            self._prefix: str | None = prefix

    @property
    def inner_dict(self) -> dict:
        return self._d

    @property
    def prefix(self) -> str | None:
        return self._prefix

    def __contains__(self, item: str) -> bool:
        return item in self._d

    def get(
            self,
            path: str,
            always_return: bool = True,
            default: Any = None
    ) -> Any:
        return get_by_path(
            self._d,
            path,
            prefix = self._prefix,
            always_return = always_return,
            default = default
        )

    def __getitem__(self, key: str) -> Any:
        return self.get(key, always_return = False)

    def set(
            self,
            path: str,
            value: Any,
            allow_create: bool = True
    ) -> None:
        set_by_path(
            self._d,
            path,
            value,
            prefix=self._prefix,
            allow_create=allow_create
        )

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value, allow_create=True)


    def delete(self, path: str) -> None:
        if not del_by_path(
                self._d,
                path,
                prefix=self._prefix
        ):
            raise KeyError(path)

    def __delitem__(self, key: str) -> None:
        self.delete(key)
