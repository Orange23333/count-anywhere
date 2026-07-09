from enum import Enum
from typing import Any, Callable, Self

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

class EventInvokeMode(Enum):
    All = 0
    StopAtTrue = 1

class Event:
    """
    Trying to implement a .NET-like event.
    """

    def __init__(self, invoke_mode: EventInvokeMode = EventInvokeMode.All) -> None:
        self.__receivers: list[Callable] = []
        #self.__waiter: Callable | None = None  # Handling returns of receivers, and decide if the event should be stopped.
        self.__invoke_mode: EventInvokeMode = invoke_mode

    @property
    def invoke_mode(self) -> EventInvokeMode:
        return self.__invoke_mode

    @invoke_mode.setter
    def invoke_mode(self, value: EventInvokeMode) -> None:
        self.__invoke_mode = value

    def append_receiver(self, receiver: Callable) -> None:
        if not isinstance(receiver, Callable):  # Callable including classes implemented __call__().
            raise ValueError('`other` must be callable.')
        self.__receivers.append(receiver)

    def remove_receiver(self, receiver: Callable) -> None:
        self.__receivers.remove(receiver)

    def clear_receivers(self) -> None:
        self.__receivers.clear()

    def __iadd__(self, other: Callable) -> Self:
        self.append_receiver(other)

    def __isub__(self, other: Callable) -> Self:
        self.remove_receiver(other)

    def invoke(self, *args, **kwargs) -> None:
        for receiver in self.__receivers:
            if self.__invoke_mode == EventInvokeMode.StopAtTrue:
                if receiver(*args, **kwargs):
                    break
            else:
                receiver(*args, **kwargs)


class DataChangeNotifier:
    """
    Trying to implement a WPF-like data binding helper.
    """

    def __init__(self) -> None:
        self.__on_changed: Event = Event(invoke_mode=EventInvokeMode.All)

    def notify(self, sender: object, key: str) -> None:
        self.__on_changed.invoke(sender=sender, key=key)
