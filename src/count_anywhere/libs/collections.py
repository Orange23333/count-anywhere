from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, Iterable, ReadOnly, TypeVar

import rtree

TKey = TypeVar('TKey')  # Type of id. Could be int, str and so on.
TValue = TypeVar('TValue')  # Type of object to be stored.
TPrecision = TypeVar('TPrecision')  # Type of precision. Could be int, float and so on.


class SortedSet(Generic[TKey]):
    NOT_FOUND = -1

    def __init__(self, items: Iterable[int] | None = None, duplicatable: bool = False):
        self.__duplicatable = duplicatable

        self.__set = []

        if items is not None:
            self.add_more(items)

    def contains(self, item: TKey) -> bool:
        return self.index(item) != SortedSet.NOT_FOUND

    def __contains__(self, item: TKey) -> bool:
        return self.contains(item)

    def add(self, item: TKey) -> None:
        ...  # 二分法插入

    def add_more(self, items: Iterable[int]) -> None:
        items = sorted(items)

        last = None
        for item in items:
            if item == last and not self.__duplicatable:
                continue

            pass

            last = item

    def __binary_search(self, item: TKey) -> int:
        l = 0
        r = len(self.__set) - 1

        s = [self.__set[0] - 1, *(self.__set), self.__set[-1] + 1]

        target_eq = lambda l, m, r, item: item == self.__set[m]
        target_left_bound = lambda l, m, r, item: self.__set[l] < item and ()
        ???

        def is_find_left_bound():
            pass

        while l <= r:
            m = l + (r - l) // 2

            mid_item = self.__set[m]
            if mid_item < item:
                l = m + 1
            elif mid_item > item:
                r = m - 1
            else:
                m?

        return ret

    def index(self, item: TKey) -> int:
        nearst = self.__binary_search(item)

        return nearst if self.__set[nearst] == item else SortedSet.NOT_FOUND


class IdManager(Generic[TKey]):  # [<only> id]
    def __init__(self) -> None:
        self.__ids = SortedList

    def


#class ObjectManager:  # {id: object}, <optional> <reserved_query> {obejct: id}
#    pass  # Why not directly use dict?


# class TypeMatchMode:
#     """
#     Match the same class.
#     """
#     Accurate = 0
#
#     """
#     Match the same class or one of subclasses.
#     """
#     Fast = 1
#
#     """
#     Match the same class or one of the nearest subclasses.
#     """
#     Nearest = 2


class TypeManager(Generic[TKey]):
    def __init__(
            self,
            enable_fast_reserved_query: bool = True  # Create _t2i dictionary.
    ) -> None:
        """
        :param enable_fast_reserved_query:
        Enabled using a dict[type, TId] to make reserved query like `contains_type()`, `find_type_name()` and
        other operation faster.
        """

        self.__i2t: dict[TKey, type] = {}  # id -> type.
        self.__t2i: dict[type, TKey] | None = {} if enable_fast_reserved_query else None  # type -> id.
        self.__aliases: dict[TKey, TKey] = {}

    def contains_id(self, id_or_alias: TKey) -> bool:
        return (id_or_alias in self.__i2t) or (id_or_alias in self.__aliases)

    def contains_type(self, t: type) -> bool:
        if self.__t2i is not None:
            return t in self.__t2i
        else:
            return t in self.__i2t.values()

    def find_type(self, id_or_alias: TKey) -> type | None:
        if id_or_alias in self.__aliases:
            id_ = self.__aliases[id_or_alias]
        else:
            id_ = id_or_alias

        return self.__i2t.get(id_, None)

    def find_id(self, t: type) -> TKey | None:
        if self.__t2i is not None:
            return self.__t2i.get(t, None)
        else:
            for _id, _t in self.__i2t.items():
                if _t is t:
                    return _id
            return None

    def create(self, id_or_alias: TKey, *args, **kwargs) -> TValue | Any:
        t = self.find_type(id_or_alias)
        if t is None:
            raise KeyError('Unknown id.')

        new_instance = t(*args, **kwargs)

        return new_instance

    def register(self, id_: TKey, t: type) -> None:
        """
        Register a type with an id.
        :param id_: The id for the type.
        :param t: The type (excluding None, NoneType) to be registered.
                  DO NOT register a type instance like `type(int)`, just give `int` directly.
                  We can't make a comparison between `type(...)` (using `is` or `==`) in Python,
                  it will always return `True`.
        """

        if self.contains_id(id_):
            raise ValueError('Duplicated id.')
        if self.contains_type(t):
            raise ValueError('Duplicated type.')

        self.__i2t[id_] = t
        if self.__t2i is not None:
            self.__t2i[t] = id_

    def link(self, id_: TKey, alias: TKey) -> None:
        if id_ not in self.__i2t:
            # Also avoid link to link.
            raise ValueError('Unknown id.')
        if self.contains_id(alias):
            raise ValueError('Duplicated alias.')

        self.__aliases[alias] = id_

    def __unlink(self, alias: TKey) -> None:
        del self.__aliases[alias]

    def unlink(self, alias: TKey) -> None:
        if alias not in self.__aliases:
            raise ValueError('Unknown alias.')

        self.__unlink(alias)

    def __unregister(self, id_: TKey) -> None:
        if self.__t2i is not None:
            t = self.find_type(id_)
            del self.__t2i[t]
        del self.__i2t[id_]

        aliases = []
        for alias in self.__aliases:
            if self.__aliases[alias] == id_:
                aliases.append(alias)
        for alias in aliases:
            self.__unlink(alias)

    def unregister(self, id_or_alias: TKey) -> None:
        if id_or_alias in self.__aliases:
            id_ = self.__aliases[id_or_alias]
        else:
            id_ = id_or_alias
            if id_ not in self.__i2t:
                raise ValueError('Unknown id.')

        self.__unregister(id_)

    def __contains__(self, item: TKey) -> bool:
        return self.contains_id(item)

class Space:
    def __init__(self, dimension: int) -> None:
        p = rtree.index.Property()
        p.dimension = dimension
        self.__data = rtree.index.Index(properties=p)

    def __check_coordinate(self, coordinate: list[float]) -> None:
        dim = self.__data.properties.dimension
        if len(coordinate) != dim:
            raise ValueError('Bad dimension.')

    def add(self, coordinate: list[float], value: Any) -> int:
        self.__check_coordinate(coordinate)
        self.__data.add(?id, coordinate, value)

    def remove(self, key: int) -> None:
        pass

    def __getitem__(self, idx: list[float] | int) -> Any:
        pass

    def __iter__(self) -> Iterator[Any]:
        pass

    def contanins(self, coordinate: list[float] | int) -> bool:
        if isinstance(coordinate, int):
            return self.__data.contains(coordinate)?
        else:
            self.__check_coordinate(coordinate)
            return self.__data.contains(coordinate)?

    def nearest(self, coordinate: list[float]) -> tuple[list[TKey], TValue]:
        self.__check_coordinate(coordinate)
        self.__data.nearest()?
