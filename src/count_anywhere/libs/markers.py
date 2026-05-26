from __future__ import annotations

import warnings
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
import inspect
import math
from typing import Any, Callable, Iterable, Iterator, overload, override, Self

import ruamel.yaml as yaml

from any_singleton import singleton_instance as sgt_i, singleton_value as sgt_v

from count_anywhere.libs.object_managers import TypeManager


class NodeFactory(TypeManager[str]):
    type_checked = None

    def __init__(self) -> None:
        super().__init__(enable_fast_reserved_query = False)

    @staticmethod
    def __type_checker(t: type) -> None:
        if not issubclass(t, NodeFactory.type_checked):
            raise TypeError("Must be a subclass of Node.")

    @override
    def contains_type(self, t: type) -> bool:
        NodeFactory.__type_checker(t)
        return super().contains_type(t)

    @override
    def find_id(self, t: type) -> str | None:
        NodeFactory.__type_checker(t)
        return super().find_id(t)

    @override
    def register(self, id_: str, t: type) -> None:
        NodeFactory.__type_checker(t)
        super().register(id_, t)


_FACTORY_DN: str = 'count_anywhere.markers.factory'
_factory: NodeFactory = sgt_i(_FACTORY_DN, NodeFactory)


class NodeProperty(__builtins__.property):
    def __init__(
            self,
            fget = None,
            fset = None,
            fdel = None,
            doc = None,
            name: str | None = None,
            ignored: bool = False,
            recursive_construction: bool = False,
            from_dict_like: Callable[[dict], Any] | None = None,
            to_dict_like: Callable[[Any], dict] | None = None
    ) -> None:
        # if name is None:
        #    raise ValueError("`name` must be specified.")

        has_from_dict = from_dict_like is not None
        has_to_dict = to_dict_like is not None
        if has_from_dict and has_to_dict and recursive_construction:
            warnings.warn('If specified `from_dict_like` and `to_dict_like`, `recursive_construction` is ignored.')
        if (has_from_dict or has_to_dict) and (has_from_dict != has_to_dict):
            raise ValueError('If specified `from_dict_like` and `to_dict_like`, both must be specified.')

        super().__init__(fget, fset, fdel, doc)

        # TODO: Should we use __slot__ to optimize?
        self.name = name
        self.ignored = ignored
        self.recursive_construction = recursive_construction
        self.from_dict_like = from_dict_like
        self.to_dict_like = to_dict_like


@dataclass
class NodeMeta:
    properties: list[NodeProperty]


_NODE_PROPERTIES_DN: str = 'count_anywhere.markers.node_properties'
_node_properties: dict[str, NodeMeta] = sgt_i(_NODE_PROPERTIES_DN, dict[str, NodeMeta])


# TODO: Add default_value?
def node_property(
        name: str | None = None,
        ignored: bool = False,
        recursive_construction: bool = False,
        from_dict_like: Callable[[dict], Any] | None = None,
        to_dict_like: Callable[[Any], dict] | None = None,
) -> Callable[[Callable], NodeProperty]:
    def decorator(fget: Callable[[Node], Any]) -> NodeProperty:
        @wraps(fget)
        def wrapper(self: Node) -> Any:
            return fget(self)

        p = NodeProperty(
            fget = wrapper,
            name = name,
            ignored = ignored,
            recursive_construction = recursive_construction,
            from_dict_like = from_dict_like,
            to_dict_like = to_dict_like
        )

        return p

    return decorator


def is_property(obj: object) -> bool:
    return isinstance(obj, NodeProperty)


class Node(metaclass=ABCMeta):
    def __init__(
            self,
            name: str | None = None,
            parent: Node | None = None,
            children: Iterable[Node] | None = None,  # Could be None for marker nodes.
            type_name: str | None = None  # Most of the time, it should be None.
    ) -> None:
        self.__name: str | None = None
        self.__parent: Node | None = None
        self.__children: list[Node] | None = None
        self.__type_name: str = ''

        self.__set_name(name)
        self.__set_parent(parent)
        self.__set_children(children)
        self.__set_type_name(type_name)

    @staticmethod
    @abstractmethod
    def this_type_name() -> str:
        raise NotImplementedError()
        # return '@node'

    @node_property(
        name='name'
    )
    def name(self) -> str | None:
        return self.__name

    @name.setter
    def name(self, value: str | None) -> None:
        self.__set_name(value)

    def __set_name(self, value: str | None) -> None:
        self.__name = value

    @node_property(
        ignored=True
    )
    def parent(self) -> Node | None:
        return self.__parent

    @parent.setter
    def parent(self, value: Node | None) -> None:
        self.__set_parent(value)

    def __set_parent(self, value: Node | None) -> None:
        self._transfer_parent(value)

    def _transfer_parent(self, new_parent: Node | None) -> None:
        if self.__parent is not None:
            self.__parent.remove(self)
        self._transfer_parent_without_linkage(new_parent)

    def _transfer_parent_without_linkage(self, new_parent: Node | None) -> None:
        # Directly called when it is removing from parent.
        self.__parent = new_parent

    @node_property(
        name='children',
        recursive_construction=True
    )
    def children(self) -> list[Node] | None:
        return self.__children

    @children.setter
    def children(self, value: Iterable[Node] | None) -> None:
        self.__set_children(value)

    def __set_children(self, value: Iterable[Node] | None) -> None:
        if self.__children is not None:
            self.clear()
        self.__children = None if value is None else list(value)

    @node_property(
        name='type'
    )
    def type_name(self) -> str:
        return self.__type_name

    @type_name.setter
    def type_name(self, value: str | None = None) -> None:
        self.__set_type_name(value)

    def __set_type_name(self, value: str | None = None) -> None:
        self.__type_name = self.this_type_name() if value is None else value
        # Using `Node.this_type_name()` is wrong, because it may be overridden.
        # Tested, calling static method from `self` is work correctly.

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
                self.__children.append(x)
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
            if x not in self.__children:
                raise ValueError('Not a child of this node.')
            self._remove_one(x)
        else:
            for one in x:
                if one not in self.__children:
                    raise ValueError('Not a child of this node.')
            for one in x:
                self._remove_one(one)

    def _remove_one(self, item: Node) -> None:
        # Never check whether self._children is None.

        item._transfer_parent_without_linkage(None)
        self.__children.remove(item)

    def clear(self) -> None:
        # Never check whether self._children is None.

        for child in self.__children:
            child._transfer_parent_without_linkage(None)
        self.__children.clear()

    def __contains__(self, item: Node) -> bool:
        #if not isinstance(item, Node):
        #    return False

        return item in self.__children

    def __iadd__(self, other: Node | Iterable[Node]) -> Self:
        self.add(other)
        return self

    def __isub__(self, other: Node | Iterable[Node]) -> Self:
        self.remove(other)
        return self

    def __delitem__(self, key: Node) -> None:
        self.remove(key)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__children)

    def __len__(self) -> int:
        return len(self.__children)

    def __pos__(self) -> Iterator[Node]:
        return self.__children.__iter__()

    def __neg__(self) -> Iterator[Node]:
        return self.__children.__reversed__()

    def __del__(self) -> None:
        if self.__children is not None:
            self.clear()

    @staticmethod
    def node(cls: Any) -> Any:
        global _factory

        if not inspect.isclass(cls):
            raise TypeError('This decorator can only be applied to classes.')
        if not issubclass(cls, Node):
            raise TypeError('This decorator can only be applied to classes that inherit from Node.')

        cls.yaml_tag = '!CountAnywhere.Nodes.' + cls.this_type_name()

        _factory.register(cls.this_type_name(), cls)

        return cls

    # TODO: Never tested.
    @staticmethod
    def from_dict_like(root: dict) -> Node:
        global _factory

        typ = root['type']
        cls = _factory.find_type(typ)  # Get prototype.
        props = {}

        for prop in dir(cls):
            prop = getattr(cls, prop)
            if isinstance(prop, NodeProperty) and prop.name is not None:
                if prop.name in root:
                    if prop.name == 'parent':
                        raise KeyError('Specified `parent` here is illegal.')
                    if prop.from_dict_like is None:
                        if prop.recursive_construction:
                            sub_nodes = []
                            for sub_node in root[prop.name]:
                                sub_nodes.append(Node.from_dict_like(sub_node))
                            props[prop.name] = sub_nodes
                        else:
                            props[prop.name] = root[prop.name]
                    else:
                        props[prop.name] = prop.from_dict_like(root[prop.name])
                else:
                    pass

        root_node = _factory.create(typ, **props)
        return root_node

    # TODO: Never tested.
    @staticmethod
    def to_dict_like(root: Node) -> dict:
        props = {}
        for prop in dir(root.__class__):  # Attention: It means we do not analyze changes of dymatic property in instances.
            if isinstance(prop, NodeProperty) and not prop.ignored and prop.name is not None:
                if prop.to_dict_like is None:
                    if prop.recursive_construction:
                        sub_nodes = []
                        for sub_node in prop.fget():
                            sub_nodes.append(Node.to_dict_like(sub_node))
                        props[prop.name] = sub_nodes
                    else:
                        props[prop.name] = prop.fget()
                else:
                    props[prop.name] = prop.to_dict_like(root)

        return props


NodeFactory.type_checked = Node


@Node.node
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
    type Position = tuple[int, int]

    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: Marker.Position | None = None,  # TODO: Using float instead of int?
            tags: Iterable[str] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            children=None,
            type_name=type_name
        )

        self.__position: Marker.Position | None = None
        self.__tags: list[str] | None = None

        self.__set_position(position)
        self.__set_tags(tags)

    @override
    @staticmethod
    @abstractmethod
    def this_type_name() -> str:
        raise NotImplementedError()
        # return '@marker'

    @staticmethod
    def marker(cls: Any) -> Any:
        global _factory

        if not inspect.isclass(cls):
            raise TypeError('This decorator can only be applied to classes.')
        if not issubclass(cls, Marker):
            raise TypeError('This decorator can only be applied to classes that inherit from Marker.')

        # TODO: cls中变量到底是全class变量还是只是初始化值？
        cls.children.ignored = True         ！！！！这里发生了prototype污染！！！！这意味着一些属性的属性不能存储在class这个原型中。
                                            或许我们可以用一个全局表来注册，每个class通过@node或@marker注册一个。
                                            每次修饰类先扫描所有property，后面如果动态添加property就让修饰属性自动检测到已存在的meta，然后写入。
        cls.yaml_tag = '!CountAnywhere.Markers.' + cls.this_type_name()

        _factory.register(cls.this_type_name(), cls)

        return cls

    @staticmethod
    def make_position(x: int, y: int) -> Marker.Position:
        return x, y

    @node_property(
        name='pos'
    )
    def position(self) -> Marker.Position | None:
        return self.__position

    @position.setter
    def position(self, value: Marker.Position | None) -> None:
        self.__set_position(value)

    def __set_position(self, value: Marker.Position | None) -> None:
        self.__position = value

    @node_property(
        name='x',
        ignored=True
    )
    def x(self) -> int | None:
        return None if self.__position is None else self.__position[0]

    @node_property(
        name='y',
        ignored=True
    )
    def y(self) -> int | None:
        return None if self.__position is None else self.__position[1]

    @node_property(
        name='tags'
    )
    def tags(self) -> list[str]:
        return self.__tags

    @tags.setter
    def tags(self, value: Iterable[str] | None) -> None:
        self.__set_tags(value)

    def __set_tags(self, value: Iterable[str] | None) -> None:
        self.__tags = [] if value is None else list(value)

    # TODO: To figure out how to use to_yaml and from_yaml.
    #@classmethod
    #@abstractmethod
    #def to_yaml(cls, representer, node):
    #    raise NotImplementedError('Instead, use @Property.')
    #
    #@classmethod
    #@abstractmethod
    #def from_yaml(cls, constructor, node):
    #    raise NotImplementedError('Instead, use @Property.')


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
            position: Marker.Position | None = None,
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

        self.__rotation: float = 0.0

        self.__set_rotation(rotation)

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'ref'

    @node_property(
        name='ro'
    )
    def rotation(self) -> float:
        return self.__rotation

    @rotation.setter
    def rotation(self, value: float | None) -> None:
        self.__set_rotation(value)

    def __set_rotation(self, value: float | None) -> None:
        self.__rotation = 0.0 if value is None else (value % (2 * math.pi))

    @staticmethod
    def zero_origin(
            name: str | None = None,
            parent: Group | None = None,
            tags: list[str] | None = None,
            type_name: str | None = None
    ) -> ReferenceMarker:
        return ReferenceMarker(
            name=name,
            parent=parent,
            position=Marker.make_position(0, 0),
            rotation=0.0,
            tags=tags,
            type_name=type_name
        )


@Marker.marker
class CountMarker(Marker):
    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: Marker.Position | None = None,
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

        self.__reference: ReferenceMarker | None = None

        self.__set_refers_to(refers_to)

    @override
    @staticmethod
    def this_type_name() -> str:
        return 'cnt'

    # TODO: 如果每个都要记录ref那就太浪费存储空间了，最好搞一个group节点，可以自动设置所有子节点的ref为group的ref。
    @node_property(
        name='ref'
    )
    def reference(self) -> ReferenceMarker | None:
        return self.__reference

    @reference.setter
    def reference(self, value: ReferenceMarker | None) -> None:
        self.__set_refers_to(value)

    def __set_refers_to(self, value: ReferenceMarker | None) -> None:
        self.__reference = value


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
        count AnyWhere Marker -> .awm
        Count Anywhere Marker -> .cam
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
        groups = []

        for _doc_group in document['groups']:
            group = Node.from_dict_like(_doc_group)
            if not isinstance(group, Group):
                raise TypeError('Group expected.')

            groups.append(group)

        return groups

    @staticmethod
    def to_document(groups: Iterable[Group]) -> dict:
        document = {
            'groups': []
        }

        doc_groups = document['groups']

        for group in groups:
            doc_groups.append(Node.to_dict_like(group))

        return document

    @staticmethod
    def load(file_path: str) -> list[Group]:
        raise NotImplementedError()

    @staticmethod
    def save(file_path: str, document: Iterable[Group]) -> None:
        raise NotImplementedError()

if __name__ == '__main__':
    import count_anywhere.libs.io as io
    yaml_doc = io.load_yaml_from_file('../../../tests/example.awm.yml')
    markers_doc = MarkerDocument.from_document(yaml_doc)
    pass
