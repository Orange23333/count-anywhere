# Question

`@file src/count_anywhere/libs/markers.py` 这里发生了一个问题，在调试过程中，虽然每次node_property修饰器被正确的调用，node_property修饰器初始化的NodeProperty的字段也被在朱行执行过程中被被正确赋值，但每当一个类，比如Node被定义完成后，再次检查该类中的每一个NodeProperty，其字段又变成了默认值，这是为什么？
```Python
NodeProperty
```

# Answered by CodeGeeX (GLM 5.1):

没关系，这个问题确实涉及到 Python 底层一些比较隐蔽的机制，让我用更直白的方式一步步为你解释。

### 1. 问题的核心：类定义时的“狸猫换太子”

在 Python 中，当你使用 `@node_property(name='name')` 和 `@xxx.setter` 时，实际上发生了两步操作。

我们来看 `Node` 类中的这段代码：
```python
@node_property(name='name')   # 第一步
def name(self) -> str | None: 
    return self.__name

@name.setter                  # 第二步
def name(self, value: str | None) -> None:
    self.__set_name(value)
```

**第一步**：`@node_property(name='name')` 执行，它创建了一个 `NodeProperty` 对象，并且正确地把 `name='name'` 存进了这个对象里。此时，类字典中的 `name` 指向这个正确的 `NodeProperty` 对象。

**第二步**：`@name.setter` 执行。这是导致问题的罪魁祸首。`name.setter` 其实是调用了父类 `property` 的 `setter` 方法。`property.setter` 的默认行为是：**不管你原来是什么自定义类，它都会创建一个全新的、标准的 `property` 对象**，把你的 getter 和新的 setter 复制进去，然后把这个新对象返回。

所以，当第二步执行完后，类字典里的 `name` 被替换成了一个**全新的标准 `property` 对象**。这个新对象根本没有你定义的 `name`、`ignored` 这些字段，它们自然就变成了默认值（甚至可能报错说找不到属性）。

### 2. 为什么 Python 会允许这种替换？

这是由 Python 的**描述符协议**和**类体执行机制**决定的。

`NodeProperty` 继承自 `property`，所以它是一个“数据描述符”（拥有 `__set__` 方法）。当 Python 在类体中执行 `def name(...): ...` 进行赋值操作时，如果发现左侧的对象是数据描述符，它不会直接覆盖这个对象，而是去调用描述符的 `__set__` 方法。

但是，`property` 原本的 `__set__` 方法是设计用来给**类的实例**赋值的，它没有处理“在类定义时给自己设置 setter”这种情况。于是它发现传入的不是实例，就不知所措，最终导致 Python 放弃了调用 `__set__`，转而直接把那个全新的标准 `property` 对象塞进了类的字典里，完成了“狸猫换太子”。

### 3. 解决方法：拦截替换行为

我们要做的，就是重写 `NodeProperty` 的 `__set__` 方法，告诉 Python：**如果在类定义时给我赋值，不要用新的 `property` 替换我，而是把新的 setter 函数更新到我自己的身上。**

代码位置：[markers.py](src/count_anywhere/libs/markers.py#L14-L43)

请在 `NodeProperty` 类中添加 `__set__` 和 `__delete__` 方法的重写：

```python
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
        has_from_dict = from_dict_like is not None
        has_to_dict = to_dict_like is not None
        if has_from_dict and has_to_dict and recursive_construction:
            warnings.warn('If specified `from_dict_like` and `to_dict_like`, `recursive_construction` is ignored.')
        if (has_from_dict or has_to_dict) and (has_from_dict != has_to_dict):
            raise ValueError('If specified `from_dict_like` and `to_dict_like`, both must be specified.')

        super().__init__(fget, fset, fdel, doc)

        self.name = name
        self.ignored = ignored
        self.recursive_construction = recursive_construction
        self.from_dict_like = from_dict_like
        self.to_dict_like = to_dict_like

    # --- 新增以下两个方法 ---
    def __set__(self, obj, value):
        # 当 obj 是类本身时，说明是在类定义体内部进行赋值（比如 @prop.setter 触发）
        # 此时 value 是传入的 setter 函数，我们把它保存下来，并返回自身以防被替换
        if isinstance(obj, type):
            self.fset = value
            return self
        # 如果是正常的实例对象赋值（比如 obj.name = "xxx"），则调用父类 property 的逻辑
        super().__set__(obj, value)

    def __delete__(self, obj):
        # 同理，处理 @prop.deleter 的情况
        if isinstance(obj, type):
            self.fdel = obj
            return self
        super().__delete__(obj)
    # ------------------------

```

添加这段代码后，当执行 `@name.setter` 时，Python 会调用我们重写的 `__set__` 方法。我们识别出这是在类定义阶段，于是将 setter 函数保留在当前的 `NodeProperty` 对象中，并返回 `self`。这样，原本那个带有 `name='name'` 的 `NodeProperty` 对象就不会被替换掉，字段也就完好无损地保留下来了。