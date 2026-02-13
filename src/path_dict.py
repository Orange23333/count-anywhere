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
        allow_create: bool = True
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
