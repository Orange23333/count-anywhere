from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
import inspect
import math
from typing import Any, Callable, Iterable, Iterator, overload, override, Self

import globals_


class MarkerFactory:
    def __init__(self) -> None:
        self._tn2t: dict[str, type] = {}
        self._t2tn: dict[type, str] = {}
        self._aliases: dict[str, str] = {}

    def create(
        self,
        type_name: str,
        position: tuple[int, int],
        /,
        **kwargs
    ) -> Any:
        try:
            t = self._tn2t[type_name]
        except KeyError:
            raise ValueError('Unknown type name.')

        new_marker = t(
            position,
            **kwargs
        )


    def find_type_name(self, type_: type) -> str | None:
        if not issubclass(type_, Marker):
            raise TypeError('Must be a subclass of `Marker`.')

        try:
            tn = self._t2tn[type_]
        except KeyError:
            return None

        return tn


    def register(self, type_name: str, type_: type) -> None:
        if type_name in self._tn2t or type_ in self._t2tn:
            raise ValueError('Duplicated type name or type.')
        if not issubclass(type_, Marker):
            raise TypeError('Must be a subclass of `Marker`.')

        self._tn2t[type_name] = type_
        self._t2tn[type_] = type_name

    def link(self, alias: str, type_name: str) -> None:
        if type_name not in self._tn2t:
            raise ValueError('Unknown type name.')
        if alias in self._aliases:
            raise ValueError('Duplicated alias.')

        self._aliases[alias] = type_name

    def _unlink(self, alias: str) -> None:
        del self._aliases[alias]

    def unlink(self, alias: str) -> None:
        if alias not in self._aliases:
            raise ValueError('Unknown alias.')

        self._unlink(alias)

    def unregister(self, key: str | type) -> None:
        if isinstance(key, str):
            tn = key
            if tn not in self._tn2t:
                raise ValueError('Unknown type name.')
            t = self._tn2t[tn]
        else:
            t = key
            if t not in self._t2tn:
                raise ValueError('Unknown type.')
            tn = self._t2tn[t]

        del self._tn2t[tn]
        del self._t2tn[t]

        aliases = []
        for alias in self._aliases:
            if self._aliases[alias] == tn:
                aliases.append(alias)
        for alias in aliases:
            self._unlink(alias)


class Node:
    def __init__(
        self,
        name: str | None = None,
        children: Iterable[Marker] | None = None
    ) -> None:
        self._name = name
        self._children: list[Marker] | None = None if children is None else list(children)

    class property(__builtins__.property):
        def __init__(
            self,
            fget = None,
            fset = None,
            fdel = None,
            doc = None,
            name: str | None = None,
            ignored: bool = False,
            from_dict: Callable[[dict], Any] | None = None,
            to_dict: Callable[[Any], dict] | None = None,
        ) -> None:
            super().__init__(fget, fset, fdel, doc)

        name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
        ignored = ...
        from_dict = ...
        to_dict = ...

    @staticmethod
    def is_property(obj) -> bool:
        return isinstance(obj, Node.property)


    @staticmethod
    def property(
        name: str,
        ignored: bool = False,
        from_dict: Callable[[dict], Any] | None = None,
        to_dict: Callable[[Any], dict] | None = None,
    ) -> Callable[[__builtins__.property | Callable], __builtins__.property]:
        def decorator(x: __builtins__.property | Callable) -> __builtins__.property:
            if isinstance(x, Callable) or inspect.isfunction(x):
                @__builtins__.property
                @wraps(x)
                def wrapper(self: Node) -> Any:
                    return x(self)

                p = wrapper
            else:
                p = x

            p._node_property_info = {
                'name': name,
                'ignored': ignored,
                'from_dict': from_dict,
                'to_dict': to_dict
            }

            return p

        return decorator

    @property(
        name = 'name'
    )
    def name(self) -> str | None:
        return self._name
    @name.setter
    def name(self, name: str | None) -> None:
        self._name = name

    @property(
        name = 'children'
    )
    def children(self) -> list[Marker]:
        return self._children
    @children.setter
    def children(self, children: Iterable[Marker]) -> None:
        self._children = list(children)


class Marker(Node, metaclass=ABCMeta):
    def __init__(
            self,
            position: tuple[int, int] | None = None,  # TODO: Using float instead of int?
            type_name: str | None = None,
            tags: Iterable[str] | None = None
    ) -> None:
        super().__init__(name, children = [])

        self._position = position
        self._type_name = self.this_type_name() if type_name is None else type_name
        self._tags = [] if tags is None else list(tags)

    @staticmethod
    def marker(cls: type[Marker]) -> type:
        if not inspect.isclass(cls):
            raise TypeError('This decorator can only be applied to classes.')

        factory = get_factory()
        factory.register(cls.this_type_name(), cls)

        cls.children._node_prorperty_info['ignored'] = True
        cls.yaml_tag = '!CountAnyWhere.Makers.' + cls.__name__

        return cls

    @staticmethod
    @abstractmethod
    def this_type_name() -> str:
        raise NotImplementedError()

    @staticmethod
    def make_position(x: int, y: int) -> tuple[int, int]:
        return x, y

    @marker_property(
        name='position'
    )
    def position(self) -> tuple[int, int] | None:
        return self._position

    @position.setter
    def position(self, position: tuple[int, int] | None):
        self._position = position


    @property
    def x(self) -> int | None:
        return None if self._position is None else self._position[0]

    @property
    def y(self) -> int | None:
        return None if self._position is None else self._position[1]

    @marker_property
    def type_name(self) -> str:
        return self._type_name

    @marker_property
    def tags(self) -> list[str]:
        return self._tags

    #@classmethod
    #@abstractmethod
    #def to_yaml(cls, representer, node):
    #    raise NotImplementedError('Instead, use @Marker.marker_property.')
    #
    #@classmethod
    #@abstractmethod
    #def from_yaml(cls, constructor, node):
    #    raise NotImplementedError('Instead, use @Marker.marker_property.')


@Marker.marker
class ReferenceMarker(Marker):
    """
    Records an absolute coordinate as origin.
    记录一个作为原点的绝对坐标。
    """

    def __init__(
        self,
        position: tuple[int, int] | None = None,
        rotation: float | None = None,  # in rad.
        type_name: str | None = None,
        tags: list[str] | None = None
    ) -> None:
        super().__init__(position, type_name=type_name, tags=tags)

        self._rotation = 0.0 if rotation is None else (rotation % (2 * math.pi))

    @Marker.marker_property
    def rotation(self) -> float:
        return self._rotation

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'ref'


@Marker.marker
class CountMarker(Marker):
    def __init__(
        self,
        position: tuple[int, int] | None = None,
        refers_to: ReferenceMarker | None = None,
        type_name: str | None = None,
        tags: list[str] | None = None
    ) -> None:
        super().__init__(position, type_name=type_name, tags=tags)

        self._refers_to = refers_to

    @Marker.marker_property
    def refers_to(self) -> ReferenceMarker | None:
        return self._refers_to

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'cnt'


# TODO: Should we implement Group in Group - tree-like group?
class Group(Node):
    def __init__(
        self,
        name: str | None = None,
        markers: Iterable[Marker] | None = None
    ) -> None:
        self._name = name

        self._markers: list[Marker] = [] if markers is None else list(markers)

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def markers(self) -> list[Marker]:
        return self._markers

    def append(self, item: Marker) -> None:
        if item in self._markers:
            raise KeyError(f'This group already contains it.')

        self._markers.append(item)

    def clear(self) -> None:
        self._markers.clear()

    def extend(self, iterable: Iterable[Marker]) -> None:
        self._markers.extend(iterable)

    def remove(self, item: Marker) -> None:
        self._markers.remove(item)

    def __contains__(self, item: Marker) -> bool:
        if not isinstance(item, Marker):
            return False

        return item in self._markers

    def __iadd__(self, other: Marker) -> Self:
        self.append(other)
        return self

    def __isub__(self, other: Marker) -> Self:
        self.remove(other)
        return self

    def __iter__(self) -> Iterator[Marker]:
        return iter(self._markers)

    def __len__(self) -> int:
        return len(self._markers)

    def __eq__(self, other: object) -> bool:
        if id(self) == id(other):
            return True
        if isinstance(other, Group):
            return self._markers == other._markers
        elif isinstance(other, Iterable):
            return self._markers == other
        else:
            return False


class MarkerDocument:
    def __init__(self):
        pass

    @staticmethod
    def default_extension() -> str:
        return '.awm.yml'

    @staticmethod
    def get_extensions() -> list[str]:
        YAML_EXT = ['.yml', '.yaml']

        """
        count AnyWhere Maker -> .awm
        Count Anywhere Maker -> .cam
        """
        MAKER_FILE_SECONDARY_EXT = ['.awm', '.cam']

        exts = []
        exts.extend(YAML_EXT)
        exts.extend(MAKER_FILE_SECONDARY_EXT)
        for sec_ext in MAKER_FILE_SECONDARY_EXT:
            for ext in YAML_EXT:
                exts.append(sec_ext + ext)

        if MarkerDocument.default_extension not in exts:
            exts.append(MarkerDocument.default_extension)

        return exts

    @staticmethod
    def from_document(document: dict) -> list[Group]:
        ret = []

        factory = get_factory()

        for doc_group in document['groups']:
            group = Group(doc_group['name'])

            for doc_marker in doc_group['markers']:
                position = doc_marker['pos']
                type_name = doc_marker['type']
                doc_marker.remove('pos')
                doc_marker.remove('type')

                if position is None:
                    raise ValueError('Position is None.')
                if (
                    position is not Iterable or
                    len(position) != 2 or
                    not all(isinstance(i, int) for i in position)
                ):
                    raise ValueError('Invalid position.')
                position = (position[0], position[1])

                marker = factory.create(
                    type_name,
                    position,
                    **doc_marker
                )

                group.append(marker)

            ret.append(group)

        return ret

    @staticmethod
    def to_document(groups: Iterable[Group]) -> dict:
        document = {
            'groups': []
        }

        doc_groups = document['groups']

        for group in groups:
            doc_group = {}

            for marker in group:
                doc_marker = marker.

    @staticmethod
    def load(file_path: str) -> list[Group]:
        pass

    @staticmethod
    def save(document: list[Group], file_path: str) -> None:
        pass


#region  Global configuration of markers.

GLOBAL_KEY = 'markers'

def _init_global() -> None:
    g = globals_.get_global()

    if GLOBAL_KEY not in g:
        """
        Initialize here:
        """

        factory = MarkerFactory()

        d = {
            'factory': MarkerFactory(),
            'yaml_converters': [
                #{
                #    'type': type,
                #    'se': se(),
                #    'de': de()
                #}
            ]
        }
        g[GLOBAL_KEY] = d

_init_global()

def get_global() -> dict:
    return globals_.get_global()[GLOBAL_KEY]

def get_factory() -> MarkerFactory:
    g = get_global()
    return g['factory']

#endregion
