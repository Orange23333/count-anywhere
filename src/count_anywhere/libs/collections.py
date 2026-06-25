from __future__ import annotations
import bisect
from dataclasses import dataclass
from enum import Enum
import random
from typing import Any, Callable, Generic, Iterable, Iterator, ReadOnly, TypeVar

import rtree

from count_anywhere.libs import utils as utils

TKey = TypeVar('TKey')  # Type of id. Could be int, str and so on.
TValue = TypeVar('TValue')  # Type of object to be stored.
TPrecision = TypeVar('TPrecision')  # Type of precision. Could be int, float and so on.


class SequenceSlot(Generic[TKey]):  # 用于自动合并连续区间的
    NOT_FOUND = -1

    def __init__(self, items: Iterable[TKey] | None = None) -> None:
        # TODO: 算法中很多地方需要解算end的位置，所以，或许直接存储end而不是length会更好一些，甚至也方便用bisect查找end附近的值。

        if items is not None:
            self.__begins, self.__lengths, self.__len = SequenceSlot._merge(items)
        else:
            self.__begins, self.__lengths, self.__len = [], [], 0

    def contains(self, item: TKey) -> bool:
        begin_index, _ = self._index(item)
        return begin_index != SequenceSlot.NOT_FOUND

    def __contains__(self, item: TKey) -> bool:
        return self.contains(item)

    def __len__(self) -> int:
        return self.__len

    def __getitem__(self, item: int | tuple[int, int]) -> tuple[int, int] | int:
        """
        `ss = SequenceSlot([3, 4, 5, 9])` as `[{begin: 3, length: 3}, {begin: 9, length: 1}]`

        Usage: `ss[<index of range>]` or `ss[(<index of range>, <index in range>)]`

        For example:
        - `ss[0]` returns the information of the first range `(3, 3)`
        - `ss[(0, 1)]` returns the second element of the first range `4`
        """

        if isinstance(item, int):
            range_index: int = item
            return self.__begins[range_index], self.__lengths[range_index]
        elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int):
            range_index: int = item[0]
            index: int = item[1]

            length = self.__lengths[range_index]

            if index >= length or index < -length:
                raise IndexError('Out of range.')

            begin = self.__begins[range_index]

            if index >= 0:
                return begin + index
            else:
                return begin + length + index
        else:
            raise ValueError('Bad query.')

    def __iter__(self) -> Iterable[TKey]:
        for begin, length in zip(self.__begins, self.__lengths):
            for i in range(length):
                yield begin + i


    @staticmethod
    def _merge(items: Iterable[TKey]) -> tuple[list[TKey], list[TKey], int]:
        items = sorted(items)

        if len(items) == 0:
            return [], [], 0

        begins = [items[0]]
        lengths = [1]
        len_ = 1

        items_iter = items.__iter__()
        last = next(items_iter)

        for item in items_iter:
            if item == last:
                continue

            if item == last + 1:
                lengths[-1] += 1
            else:
                begins.append(item)
                lengths.append(1)

            len_ += 1
            last = item

        return begins, lengths, len_

    def _add_near_range(self, range_index: int, head_not_tail: bool) -> None:
        # head, x, y, z, tail.
        # No checks.

        self.__lengths[range_index] += 1

        if head_not_tail:
            self.__begins[range_index] -= 1

            pre_range_index = range_index - 1
            if pre_range_index >= 0:
                pre_next_to_end = self.__begins[pre_range_index] + self.__lengths[pre_range_index]
                if pre_next_to_end == self.__begins[range_index]:
                    self.__lengths[pre_range_index] += self.__lengths[range_index]
                    del self.__begins[range_index]
                    del self.__lengths[range_index]
        else:
            next_to_end = self.__begins[range_index] + self.__lengths[range_index]
            next_range_index = range_index + 1
            if next_range_index < len(self.__begins) and next_to_end == self.__begins[next_range_index]:
                self.__lengths[range_index] += self.__lengths[next_range_index]
                del self.__begins[next_range_index]
                del self.__lengths[next_range_index]

        self.__len += 1

    def add(self, item: TKey) -> None:
        # index of begin: 0, 0, _, _, 1, _, 2
        # virtual items:  4, 5, _, _, 7, _, 9
        #
        # insert 2:  right_insert_point = 0 -> new range,          created.
        # insert 3:  right_insert_point = 0 -> near next range,    merged.
        # insert 4:  right_insert_point = 1 -> in range,           ignored.
        # insert 5:  right_insert_point = 1 -> in range,           ignored.
        # insert 6:  right_insert_point = 1 -> near current range, merged.
        # insert 7:  right_insert_point = 2 -> in range,           ignored.
        # insert 8:  right_insert_point = 2 -> near ranges,        merged twice.
        # insert 9:  right_insert_point = 3 -> in range,           ignored.
        # insert 10: right_insert_point = 3 -> near current range, merged.
        # insert 11: right_insert_point = 3 -> new range,          created.

        def init() -> None:
            self.__begins.append(item)
            self.__lengths.append(1)
            self.__len = 1
        def create(where: int) -> None:
            self.__begins.insert(where, item)
            self.__lengths.insert(where, 1)
            self.__len += 1
        def expand(where: int) -> None:
            self.__lengths[where] += 1
            self.__len += 1
        def try_merge_with_right(where: int, next_to_end: int) -> None:
            next_ = where + 1
            if next_ < len(self.__begins) and next_to_end == self.__begins[next_]:
                self.__lengths[where] += self.__lengths[next_]
                del self.__begins[next_]
                del self.__lengths[next_]

        if self.__len == 0:  # Just initialization.
            init()
            return

        insert_point = self._bisect_right_of_begins(item)
        if insert_point == 0:
            create(0)
            try_merge_with_right(0, item + 1)
            return

        index = insert_point - 1
        next_to_end = self.__begins[index] + self.__lengths[index]

        if item < next_to_end:
            return  # Ignored.
        if item == next_to_end:
            expand(index)
            try_merge_with_right(index, next_to_end)
        else:
            create(insert_point)
            try_merge_with_right(insert_point, item + 1)

    #def add_more(self, items: Iterable[TKey]) -> None:
    #    begins, lengths, _ = SequenceSlot._merge(items)
    #
    #    for begin, length in zip(begins, lengths):
    #        self.add_range(begin, begin + length - 1)

    #def add_range(self, left: TKey, right: TKey) -> None:
    #    if right < left:
    #        raise ValueError('`right` must be greater than or equal to `left`.')
    #
    #    raise NotImplementedError()

    def _remove_in_range(self, range_index: int, index: int) -> None:
        # No checks.

        def decrease_size_by_one() -> None:
            self.__lengths[range_index] -= 1

            if self.__lengths[range_index] == 0:
                del self.__begins[range_index]

        if index == 0:
            self.__begins[range_index] += 1
            decrease_size_by_one()
        elif index == self.__lengths[range_index] - 1:
            decrease_size_by_one()
        else:
            new_begin = self.__begins[range_index] + index + 1
            new_length = self.__lengths[range_index] - index - 1
            self.__lengths[range_index] = index
            self.__begins.insert(range_index + 1, new_begin)
            self.__lengths.insert(range_index + 1, new_length)

        self.__len -= 1

    def _remove_range_in_range(self, range_index: int, left_index: int, right_index: int) -> None:
        # Including left and right.
        # No checks.

        begin = self.__begins[range_index]
        length = self.__lengths[range_index]

        left_length = left_index

        right_begin_index = right_index + 1
        right_begin = begin + right_begin_index
        right_length = length - right_begin_index

        if left_length == 0:
            if right_length == 0:
                self.__begins.pop(range_index)
                self.__lengths.pop(range_index)
            else:
                self.__begins[range_index] = right_begin
                self.__lengths[range_index] = right_length
        else:
            self.__lengths[range_index] = left_length

            if right_length != 0:
                self.__begins.insert(range_index + 1, right_begin)
                self.__lengths.insert(range_index + 1, right_length)

        del_length = right_index - left_index + 1
        self.__len -= del_length


    def remove(self, item: TKey) -> None:
        begin_index, i = self._index(item)

        if begin_index == SequenceSlot.NOT_FOUND:
            return

        self._remove_in_range(begin_index, i)

    #def remove_more(self, items: Iterable[TKey]) -> None:
    #    begins, lengths, _ = SequenceSlot._merge(items)
    #
    #    for begin, length in zip(begins, lengths):
    #        self.remove_range(begin, begin + length - 1)

    #def remove_range(self, left: TKey, right: TKey) -> None:
    #    if right < left:
    #        raise ValueError('`right` must be greater than or equal to `left`.')
    #
    #    raise NotImplementedError()
    #
    #    while left <= right:
    #        if self.__len == 0:
    #            return
    #
    #        insert_point = self._bisect_right(left)
    #
    #        if insert_point == 0:  # left, ..., next_range
    #            begin = self.__begins[0]
    #
    #            if begin > right:
    #                return
    #            elif begin == left:
    #                self.remove(left)
    #            else:
    #                pass

    def clear(self) -> None:
        self.__begins.clear()
        self.__lengths.clear()
        self.__len = 0

    def _bisect_right_of_begins(self, item: TKey) -> int:
        # r = bisect.bisect_right(arr, x)
        # arr = [1, 3, 3, 5]
        # x = 0, 1, 2, 3, 4, 5, 6
        # r = 0, 1, 1, 3, 3, 4, 4

        insert_point = bisect.bisect_right(self.__begins, item)
        return insert_point

    def _index(self, item: TKey) -> tuple[int, int]:
        NOT_FOUND = SequenceSlot.NOT_FOUND, SequenceSlot.NOT_FOUND

        #if self.__len == 0:
        #    return NOT_FOUND

        insert_point = self._bisect_right_of_begins(item)
        if insert_point == 0:
            return NOT_FOUND

        index = insert_point - 1
        begin = self.__begins[index]
        length = self.__lengths[index]

        # If `insert_point` is 0, `item` could less than `begin`.
        if item < begin + length:
            return index, item - begin
        return NOT_FOUND


class SortedSet(Generic[TKey]):
    NOT_FOUND = -1

    def __init__(self, items: Iterable[TKey] | None = None, duplicatable: bool = False):
        self.__duplicatable: bool = duplicatable

        self.__set: list[TKey] = []

        if items is not None:
            self.add_more(items)

    def contains(self, item: TKey) -> bool:
        return self._index_left(item) != SortedSet.NOT_FOUND

    def __contains__(self, item: TKey) -> bool:
        return self.contains(item)

    def __len__(self) -> int:
        return len(self.__set)

    #def __iter__(self) -> Iterator[TKey]:
    #    return iter(self.__set)

    def add(self, item: TKey) -> None:
        if len(self.__set) == 0:
            self.__set.append(item)
            return

        insert_point = bisect.bisect_right(self.__set, item)
        if (not self.__duplicatable) and insert_point > 0 and self.__set[insert_point - 1] == item:
            return
        self.__set.insert(insert_point, item)

    def add_more(self, items: Iterable[TKey]) -> None:
        items = sorted(items)
        if len(self.__set) == 0:
            self.__set.extend(items)
            return

        insert_point = 0  # Also lo.
        for item in items:
            insert_point = bisect.bisect_right(self.__set, item, lo=insert_point)
            if (not self.__duplicatable) and insert_point > 0 and self.__set[insert_point - 1] == item:
                continue
            self.__set.insert(insert_point, item)

    def remove(self, item: TKey) -> None:
        idx = self._index_right(item)
        if idx != SortedSet.NOT_FOUND:
            del self.__set[idx]

    def remove_all(self, item: TKey) -> None:
        l, r = self._index_range(item)
        if l != SortedSet.NOT_FOUND:
            del self.__set[l:r]

    def clear(self) -> None:
        self.__set.clear()

    def _index_left(self, item: TKey) -> int:
        if len(self.__set) == 0:
            return SortedSet.NOT_FOUND

        insert_point = bisect.bisect_left(self.__set, item)

        if insert_point < len(self.__set) and self.__set[insert_point] == item:
            return insert_point

        return SortedSet.NOT_FOUND

    def _index_right(self, item: TKey) -> int:
        if len(self.__set) == 0:
            return SortedSet.NOT_FOUND

        insert_point = bisect.bisect_right(self.__set, item)

        if insert_point > 0 and self.__set[insert_point - 1] == item:
            return insert_point - 1

        return SortedSet.NOT_FOUND

    def _index_range(self, item: TKey) -> tuple[int, int]:  # [l, r]
        if len(self.__set) == 0:
            return SortedSet.NOT_FOUND, SortedSet.NOT_FOUND

        left = bisect.bisect_left(self.__set, item)

        if left >= len(self.__set) or self.__set[left] != item:
            return SortedSet.NOT_FOUND, SortedSet.NOT_FOUND

        right = bisect.bisect_right(self.__set, item) - 1

        return left, right

    def _data(self) -> list[TKey]:
        return self.__set

    def index(self, item: TKey) -> int:
        return self._index_right(item)


#class IdManager(Generic[TKey]):  # [<only> id]
#    pass


class NumberIdManager:  # [<only> id]
    def __init__(self) -> None:
        self.__min: int = 1

        self.__ids: SequenceSlot[int] = SequenceSlot[int]()

    def _generate_one(self) -> int:
        if len(self.__ids) == 0 or (not self.__ids.contains(self.__min)):
            return self.__min
        else:
            return self.__ids[0, -1] + 1

    def apply(self) -> int:
        new_id: int = self._generate_one()
        self.__ids.add(new_id)
        return new_id

    def revoke(self, id_: int) -> None:
        self.__ids.remove(id_)


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

        self.__ids = NumberIdManager()
        self.__data = rtree.index.Index(
            properties=p,
            interleaved=True  # Using [xmin, ymin, …, kmin, xmax, ymax, …, kmax]
        )

    @staticmethod
    def _as_bounding_box(coordinate: list[float]) -> list[float]:
        ret = []
        ret.extend(coordinate)
        ret.extend(coordinate)
        return ret

    def __check_coordinate(self, coordinate: list[float]) -> None:
        dim = self.__data.properties.dimension
        if len(coordinate) != dim:
            raise ValueError('Bad dimension.')

    def __check_boundary(self, boundary: list[float]) -> None:
        dim = self.__data.properties.dimension
        if len(boundary) != dim * 2:
            raise ValueError('Bad dimension.')

    def add(self, coordinate: list[float], value: Any) -> int:
        self.__check_coordinate(coordinate)
        new_id = self.__ids.apply()
        bb = self._as_bounding_box(coordinate)
        self.__data.add(new_id, bb, value)
        return new_id

    def remove(self, id_: int, coordinate: list[float]) -> None:
        self.__check_coordinate(coordinate)
        bb = self._as_bounding_box(coordinate)
        self.__data.delete(id_, bb)
        self.__ids.revoke(id_)

    def __getitem__(self, id_: int) -> rtree.index.Item | None:
        bb = self.__data.bounds()
        if bb is None:
            return None
        objects = self.__data.intersection(bb, objects=True)
        for obj in objects:
            if obj.id == id_:
                return obj
        return None

    def __contains__(self, id_: int) -> bool:
        return self[id_] is not None

    def __iter__(self) -> Iterator[rtree.index.Item]:
        bb = self.__data.bounds()
        if bb is not None:
            return self.__data.intersection(bb, objects=True)
        return iter([])

    def nearest(self, coordinate: list[float], num_results: int = 1) -> Iterable[rtree.index.Item]:
        self.__check_coordinate(coordinate)
        return self.__data.nearest(coordinate, num_results=num_results, objects=True)

    def intersection(self, boundary: list[float]) -> Iterable[rtree.index.Item]:
        self.__check_boundary(boundary)
        return self.__data.intersection(boundary, objects=True)
