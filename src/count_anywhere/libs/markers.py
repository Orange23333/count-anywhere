from __future__ import annotations

from abc import ABCMeta, abstractmethod
import builtins
from functools import wraps
import inspect
import math
from typing import Any, Callable, Iterable, Iterator, overload, override, Self
from typing_extensions import ReadOnly
import warnings

from any_singleton import singleton_instance as sgt_i

from count_anywhere import sgt_dns
from count_anywhere.libs.collections import TypeManager
import count_anywhere.libs.io as io


class NodeProperty(builtins.property):
    def __init__(
            self,
            fget = None,
            fset = None,
            fdel = None,
            doc = None,
            name: str | None = None,  # Using `__set_name__()` to implement automatically filling name.
            ignored: bool = False,
            optional: bool = False,
            default: Any | None = None,
            recursive_construction: bool = False,
            from_dict_like: Callable[[dict], Any] | None = None,  # TODO: Never tested (used)!
            to_dict_like: Callable[[Any], dict] | None = None  # TODO: Never tested (used)!
    ) -> None:
        """
        Property attribute of nodes.

        :param fget: function to be used for getting an attribute value.

        :param fset: function to be used for setting an attribute value.

        :param fdel: function to be used for del'ing an attribute.

        :param doc: docstring.

        :param name:
        The name (key) of the property.
        It will be used to store and query the value of property in the file.

        :param ignored:
        If True, the property will be ignored.
        Typically used for inhibiting the property inherit from the parent node.

        :param optional:
        If True, the property is optional.
        If False, the property is required. If not found, it will raise a LookupError('`{name}` is required.').

        :param default:
        The default value of the property.
        This value will only be used to assignment at loading a file.

        :param recursive_construction:
        If True, the property will be recursively constructed.
        If False, the property will be constructed only once.
        By the way, if specified `from_dict_like` and `to_dict_like`, this parameter will be ignored.

        :param from_dict_like:
        A function that will be used to construct the property from a dict-like object.

        :param to_dict_like:
        A function that will be used to convert the property to a dict-like object.
        """

        # TODO: 暂不支持自动动态注册——在node注册后再增加property。因为目前是由@node修饰器进行自动注册的。

        if ignored and (
            optional is True or
            default is not None or
            recursive_construction is True or
            from_dict_like is not None or
            to_dict_like is not None
        ):
            warnings.warn('This property has been ignored. Other parameters will not be used.')

        has_from_dict = from_dict_like is not None
        has_to_dict = to_dict_like is not None
        if has_from_dict and has_to_dict and recursive_construction:
            warnings.warn('If specified `from_dict_like` and `to_dict_like`, `recursive_construction` is ignored.')
        if (has_from_dict or has_to_dict) and not (has_from_dict and has_to_dict):
            raise ValueError('If specified `from_dict_like` and `to_dict_like`, both must be specified.')

        super().__init__(fget, fset, fdel, doc)

        # TODO: Using __slot__ to optimize?
        # TODO: Make properties readonly?
        self.name: str | None = name
        self.ignored: bool = ignored
        self.optional: bool = optional
        self.default: Any | None = default
        self.recursive_construction: bool = recursive_construction
        self.from_dict_like: Callable[[dict], Any] = from_dict_like
        self.to_dict_like: Callable[[Any], dict] = to_dict_like

    @override
    def getter(self, f: Callable) -> NodeProperty:
        return self.__new(fget=f, fset=self.fset, fdel=self.fdel)

    @override
    def setter(self, f: Callable) -> NodeProperty:
        return self.__new(fget=self.fget, fset=f, fdel=self.fdel)

    @override
    def deleter(self, f: Callable) -> NodeProperty:
        return self.__new(fget=self.fget, fset=self.fset, fdel=f)

    def __new(self, fget: Callable, fset: Callable, fdel: Callable) -> NodeProperty:
        return NodeProperty(
            fget=fget,
            fset=fset,
            fdel=fdel,
            doc=self.__doc__,
            name=self.name,
            ignored=self.ignored,
            optional=self.optional,
            default=self.default,
            recursive_construction=self.recursive_construction,
            from_dict_like=self.from_dict_like,
            to_dict_like=self.to_dict_like
        )

    def __set_name__(self, owner: Any, name: str) -> None:
        # TODO: Make properties readonly?
        self._owner: object = owner
        self._name_in_owner: str = name

        super().__set_name__(owner, name)


    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

    @staticmethod
    def __call__(*args, **kwargs) -> NodeProperty:
        return NodeProperty(*args, **kwargs)


# TODO: Add default_value?
def node_property(
        name: str | None = None,
        ignored: bool = False,
        optional: bool = False,
        default: Any | None = None,
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
            optional = optional,
            default = default,
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
        raise NotImplementedError()  # '@node'

    @property
    def yaml_tag(self) -> str:
        return '!CountAnywhere.Nodes.' + self.this_type_name()  # TODO: 不知道有没有用？

    @node_property(
        name='name',
        optional=True,
        default=None
    )
    def name(self) -> str | None:  # TODO: 匿名节点——分配一个唯一的anonym_xxx名称。
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
        optional=True,
        default=None,
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
        name='type',
        optional=False
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
        if not isinstance(item, Node):
            return False

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


class NodeFactory(TypeManager[str]):
    def __init__(self) -> None:
        super().__init__(enable_fast_reserved_query = False)

    @staticmethod
    def __type_checker(t: type) -> None:
        if not issubclass(t, Node):
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

    @staticmethod
    def from_dict_like(root: dict) -> Node:
        global _factory

        typ = root['type']
        cls = _factory.find_type(typ)  # Get prototype.

        root_node = _factory.create(typ)

        for prop in dir(cls):
            prop = getattr(cls, prop)
            if isinstance(prop, NodeProperty) and not prop.ignored:
                if prop.name is None:
                    warnings.warn('`name` is None, but `ignore` is False. Has been ignored.')
                    continue

                def _set(value: Any) -> None:
                    setattr(root_node, prop._name_in_owner, value)

                if prop.name in root:
                    p = root[prop.name]

                    if prop.from_dict_like is None:
                        if prop.recursive_construction:
                            sub_nodes = []
                            for sub_node in p:
                                sub_nodes.append(NodeFactory.from_dict_like(sub_node))
                            _set(sub_nodes)
                        else:
                            _set(p)
                    else:
                        _set(prop.from_dict_like(p))
                else:
                    if prop.optional:
                        _set(prop.default)
                    else:
                        raise KeyError(f'`{prop.name}` is required.')

        return root_node

    @staticmethod
    def to_dict_like(root: Node) -> dict:
        props = {}

        # ATTENTION: It means we do not analyze changes of dynamic property in instances!
        for prop in dir(root.__class__):
            prop = getattr(root.__class__, prop)
            if isinstance(prop, NodeProperty) and not prop.ignored:
                if prop.name is None:
                    warnings.warn('`name` is None, but `ignore` is False. Has been ignored.')
                    continue

                p = prop.fget(root)

                if prop.to_dict_like is None:
                    if prop.recursive_construction:
                        sub_nodes = []
                        for sub_node in p:
                            sub_nodes.append(NodeFactory.to_dict_like(sub_node))
                        props[prop.name] = sub_nodes
                    else:
                        props[prop.name] = p
                else:
                    props[prop.name] = prop.to_dict_like(p)

        return props


_factory: NodeFactory = sgt_i(sgt_dns.NODE_FACTORY_DN, NodeFactory)


def node(cls: Any) -> Any:
    global _factory

    if not inspect.isclass(cls):
        raise TypeError('This decorator can only be applied to classes.')
    if not issubclass(cls, Node):
        raise TypeError('This decorator can only be applied to classes that inherit from Node.')

    # TODO: 怎么才能自动设置yaml_tag且不污染prototype呢？
    # cls.yaml_tag = '!CountAnywhere.Nodes.' + cls.this_type_name()

    _factory.register(cls.this_type_name(), cls)

    return cls


@node
class Tag(Node):
    def __init__(
            self,
            name: str | None = None,
            parent: Node | None = None,
            p: float | None = None,
            children: Iterable[Node] | None = None,
            type_name: str | None = None
    ) -> None:
        super().__init__(
            name=name,
            parent=parent,
            children=children,
            type_name=type_name
        )

        self.__p = p

    @property
    def p(self) -> float:
        return self.__p

    @p.setter
    def p(self, value: float) -> None:
        self.__p = value

    @override
    @staticmethod
    def this_type_name() -> str:
        return '@tag'

@node
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


# TODO: 支持子marker，即框中框。
class Marker(Node, metaclass=ABCMeta):
    type Position = tuple[int, int]

    @staticmethod
    def make_position(x: int, y: int) -> Marker.Position:
        return x, y

    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: Marker.Position | None = None,  # TODO: Using float instead of int?
            tags: Iterable[Tag] | None = None,
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
        raise NotImplementedError()  # '@marker'

    @node_property(
        ignored=True
    )
    def children(self) -> list[Node] | None:
        return None

    @children.setter
    def children(self, value: Iterable[Node] | None) -> None:
        raise NotImplementedError('Cannot set children of a simple marker.')

    @node_property(
        name='pos',
        optional=False
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
        name='tags',
        optional=True,
        default=None
    )
    def tags(self) -> list[Tag]:
        return self.__tags

    @tags.setter
    def tags(self, value: Iterable[Tag] | None) -> None:
        self.__set_tags(value)

    def __set_tags(self, value: Iterable[str] | None) -> None:
        self.__tags = [] if value is None else list(value)

    # TODO: To figure out how to use to_yaml and from_yaml of ruamel.taml.
    #@classmethod
    #@abstractmethod
    #def to_yaml(cls, representer, node):
    #    raise NotImplementedError('Instead, use @Property.')
    #
    #@classmethod
    #@abstractmethod
    #def from_yaml(cls, constructor, node):
    #    raise NotImplementedError('Instead, use @Property.')


def marker(cls: Any) -> Any:
    if not inspect.isclass(cls):
        raise TypeError('This decorator can only be applied to classes.')
    if not issubclass(cls, Marker):
        raise TypeError('This decorator can only be applied to classes that inherit from Marker.')

    ret = node(cls)

    # TODO: 怎么才能自动设置yaml_tag且不污染prototype呢？
    # cls.yaml_tag = '!CountAnywhere.Markers.' + cls.this_type_name()

    return ret


@marker
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
            tags: list[Tag] | None = None,
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
        name='ro',
        optional=True,
        default=0.0,
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
            tags: list[Tag] | None = None,
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


@marker
class CountMarker(Marker):
    def __init__(
            self,
            name: str | None = None,
            parent: Group | None = None,
            position: Marker.Position | None = None,
            refers_to: ReferenceMarker | None = None,
            tags: list[Tag] | None = None,
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
        name='ref',
        optional=False
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
            group = NodeFactory.from_dict_like(_doc_group)
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
            doc_groups.append(NodeFactory.to_dict_like(group))

        return document

    @staticmethod
    def load(file_path: str) -> list[Group]:
        yaml_doc = io.load_yaml_from_file(file_path)
        markers_doc = MarkerDocument.from_document(yaml_doc)
        return markers_doc

    @staticmethod
    def save(file_path: str, document: Iterable[Group]) -> None:
        yaml_doc = MarkerDocument.to_document(document)
        # TODO: 写入一个警告，告诉用户该yaml文件中的注释可能会被自动覆盖。
        io.save_yaml_to_file(file_path, yaml_doc)