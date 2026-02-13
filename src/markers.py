from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import wraps
import inspect
import math
from typing import Any, Callable, Iterable, Iterator, overload, override, Self

import globals_
import path_dict


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

        raise NotImplementedError()

        new_marker = t(
            position,
            **kwargs
        )

        return new_marker

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
            'factory': factory
        }
        g[GLOBAL_KEY] = d


_init_global()


def get_global() -> dict:
    return globals_.get_global()[GLOBAL_KEY]


def get_factory() -> MarkerFactory:
    g = get_global()
    return g['factory']

#endregion


class Property(__builtins__.property):
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

        # TODO: Should we use __slot__ to optimize?
        self.name = name
        self.ignored = ignored
        self.from_dict = from_dict
        self.to_dict = to_dict


def property(
        name: str | None = None,
        ignored: bool = False,
        from_dict_like: Callable[[dict], Any] | None = None,
        to_dict_like: Callable[[Any], dict] | None = None,
) -> Callable[[Callable], Property]:
    def decorator(fget: Callable[[Node], Any]) -> Property:
        @Property
        @wraps(fget)
        def wrapper(self: Node) -> Any:
            return fget(self)

        p = wrapper

        p.name = name
        p.ignored = ignored
        p.from_dict = from_dict_like
        p.to_dict = to_dict_like

        return p

    return decorator

def is_property(obj: Any) -> bool:
    return isinstance(obj, Property)


class Node(metaclass=ABCMeta):
    def __init__(
            self,
            name: str | None = None,
            parent: Node | None = None,
            children: Iterable[Node] | None = None,  # Could be None for marker nodes.
            type_name: str | None = None  # Most of the time, it should be None.
    ) -> None:
        self._name: str | None = None
        self._parent: Node | None = None
        self._children: list[Node] | None = None
        self._type_name: str = ''

        self.__set_name(name)
        self.__set_parent(parent)
        self.__set_children(children)
        self.__set_type_name(type_name)

    @staticmethod
    @abstractmethod
    def this_type_name() -> str:
        raise NotImplementedError()
        # return '@node'

    @property(
        name='name'
    )
    def name(self) -> str | None:
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        self.__set_name(value)

    def __set_name(self, value: str | None) -> None:
        self._name = value

    @property(
        ignored=True
    )
    def parent(self) -> Node | None:
        return self._parent

    @parent.setter
    def parent(self, value: Node | None) -> None:
        self.__set_parent(value)

    def __set_parent(self, value: Node | None) -> None:
        self._transfer_parent(value)

    def _transfer_parent(self, new_parent: Node | None) -> None:
        if self._parent is not None:
            self._parent.remove(self)
        self._transfer_parent_without_linkage(new_parent)

    def _transfer_parent_without_linkage(self, new_parent: Node | None) -> None:
        # Directly called when it is removing from parent.
        self._parent = new_parent

    @property(
        name='children'
    )
    def children(self) -> list[Node] | None:
        return self._children

    @children.setter
    def children(self, value: Iterable[Node] | None) -> None:
        self.__set_children(value)

    def __set_children(self, value: Iterable[Node] | None) -> None:
        if self._children is not None:
            self.clear()
        self._children = None if value is None else list(value)

    @property(
        name='type'
    )
    def type_name(self) -> str:
        return self._type_name

    @type_name.setter
    def type_name(self, value: str | None = None) -> None:
        self.__set_type_name(value)

    def __set_type_name(self, value: str | None = None) -> None:
        self._type_name = self.this_type_name() if value is None else value  # TODO: Tested, calling static method from self is work. But is it right?

    @overload
    def add(self, item: Node) -> None:
        ...

    @overload
    def add(self, items: Iterable[Node]) -> None:
        ...

    def add(self, x: Node | Iterable[Node]) -> None:
        # Never check whether self._children is None.

        if isinstance(x, Node):
            if x.parent != self:
                x._transfer_parent(self)
                self._children.append(x)
        else:
            for one in x:
                self.add(one)

    @overload
    def remove(self, item: Node) -> None:
        ...

    @overload
    def remove(self, items: Iterable[Node]) -> None:
        ...

    def remove(self, x: Node | Iterable[Node]) -> None:
        # Never check whether self._children is None.

        if isinstance(x, Node):
            if x not in self._children:
                raise ValueError('Not a child of this node.')
            self._remove_one(x)
        else:
            for one in x:
                if one not in self._children:
                    raise ValueError('Not a child of this node.')
            for one in x:
                self._remove_one(one)

    def _remove_one(self, item: Node) -> None:
        # Never check whether self._children is None.

        item._transfer_parent_without_linkage(None)
        self._children.remove(item)

    def clear(self) -> None:
        # Never check whether self._children is None.

        for child in self._children:
            child._transfer_parent_without_linkage(None)
        self._children.clear()

    def __contains__(self, item: Node) -> bool:
        #if not isinstance(item, Node):
        #    return False

        return item in self._children

    def __iadd__(self, other: Node | Iterable[Node]) -> Self:
        self.add(other)
        return self

    def __isub__(self, other: Node | Iterable[Node]) -> Self:
        self.remove(other)
        return self

    def __delitem__(self, key: Node) -> None:
        self.remove(key)

    def __iter__(self) -> Iterator[Node]:
        return iter(self._children)

    def __len__(self) -> int:
        return len(self._children)

    def __pos__(self) -> Iterator[Node]:
        return self._children.__iter__()

    def __neg__(self) -> Iterator[Node]:
        return self._children.__reversed__()

    def __del__(self) -> None:
        if self._children is not None:
            self.clear()


class Group(Node):
    def __init__(
            self,
            name: str | None = None,
            parent: Node | None = None,
            children: Iterable[Node] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            children=children,
            type_name=type_name
        )

    @override
    @staticmethod
    def this_type_name() -> str:
        return '@group'


class Marker(Node, metaclass=ABCMeta):
    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: tuple[int, int] | None = None,  # TODO: Using float instead of int?
            tags: Iterable[str] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            children=None,
            type_name=type_name
        )

        self._position: tuple[int, int] | None = None
        self._tags: list[str] | None = None

        self.__set_position(position)
        self.__set_tags(tags)

    @override
    @staticmethod
    @abstractmethod
    def this_type_name() -> str:
        raise NotImplementedError()
        # return '@marker'

    @staticmethod
    def marker(cls: type[Marker]) -> type:
        if not inspect.isclass(cls):
            raise TypeError('This decorator can only be applied to classes.')

        factory = get_factory()
        factory.register(cls.this_type_name(), cls)

        # TODO: cls中变量到底是全class变量还是只是初始化值？
        # TODO: 直接移到node和marker中初始化
        cls.children.ignored = True  # TODO: 确保实例中的ignored也是正确的。
        cls.yaml_tag = '!CountAnywhere.Markers.' + cls.this_type_name()

        return cls

    @staticmethod
    def make_position(x: int, y: int) -> tuple[int, int]:
        return x, y

    @property(
        name='position'
    )
    def position(self) -> tuple[int, int] | None:
        return self._position

    @position.setter
    def position(self, value: tuple[int, int] | None) -> None:
        self.__set_position(value)

    def __set_position(self, value: tuple[int, int] | None) -> None:
        self._position = value

    @property(
        name='x',
        ignored=True
    )
    def x(self) -> int | None:
        return None if self._position is None else self._position[0]

    @property(
        name='y',
        ignored=True
    )
    def y(self) -> int | None:
        return None if self._position is None else self._position[1]

    @property(
        name='tags'
    )
    def tags(self) -> list[str]:
        return self._tags

    @tags.setter
    def tags(self, value: Iterable[str] | None) -> None:
        self.__set_tags(value)

    def __set_tags(self, value: Iterable[str] | None) -> None:
        self._tags = [] if value is None else list(value)

    # TODO: To figure out how to use to_yaml and from_yaml.
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
            name: str | None = None,
            parent: Group | None = None,  # TODO: Override property.
            position: tuple[int, int] | None = None,
            rotation: float | None = None,  # In rad.
            tags: list[str] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            position=position,
            tags=tags,
            type_name=type_name
        )

        self._rotation: float = 0.0

        self.__set_rotation(rotation)

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'ref'

    @property(
        name='rotation'
    )
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float | None) -> None:
        self.__set_rotation(value)

    def __set_rotation(self, value: float | None) -> None:
        self._rotation = 0.0 if value is None else (value % (2 * math.pi))


@Marker.marker
class CountMarker(Marker):
    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: tuple[int, int] | None = None,
            refers_to: ReferenceMarker | None = None,
            tags: list[str] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            position=position,
            tags=tags,
            type_name=type_name
        )

        self._refers_to: ReferenceMarker | None = None

        self.__set_refers_to(refers_to)

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'cnt'

    @property(
        name='refers_to'
    )
    def refers_to(self) -> ReferenceMarker | None:
        return self._refers_to

    @refers_to.setter
    def refers_to(self, value: ReferenceMarker | None) -> None:
        self.__set_refers_to(value)

    def __set_refers_to(self, value: ReferenceMarker | None) -> None:
        self._refers_to = value


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
        raise NotImplementedError()

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

                group.add(marker)

            ret.append(group)

        return ret

    @staticmethod
    def to_document(groups: Iterable[Group]) -> dict:
        raise NotImplementedError()

        document = {
            'groups': []
        }

        doc_groups = document['groups']

        for group in groups:
            doc_group = {}

            for marker in group:
                pass

    @staticmethod
    def load(file_path: str) -> list[Group]:
        raise NotImplementedError()

    @staticmethod
    def save(document: Iterable[Group], file_path: str) -> None:
        raise NotImplementedError()


def test():
    marker = ReferenceMarker()
    i = getattr(ReferenceMarker.children, 'ignored', None)
    print(i)
    print(type(marker.children))

    group = Group(children=[])
    print(group.children)
    pass


test()
