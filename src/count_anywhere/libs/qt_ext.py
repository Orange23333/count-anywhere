from enum import IntEnum
from typing import Callable

from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent


#                                   name, event
type PressEventCallback = Callable[[str, QMouseEvent | QKeyEvent], None]

class QPressEventType(IntEnum):
    UNKNOWN = -1

    PRESSED = 1
    RELEASED = 2

    CLICKED = 3
    DOUBLE_CLICKED = 4

    LONG_PRESSED = 5


class QPressEventAnalyzer:
    def __init__(self, name: str, callback: PressEventCallback) -> None:
        self.__name = name
        self.__callback = callback

        self.__allow_double_click = True
        self.__min_interval = 0.3  # Seconds.
                                   # Ignore shaking.
        self.__timeout = float('+inf')  # Seconds, allowing `+inf`.
                                        # If timeout, forced releasing.

        self.__timer = None

    @property
    def name(self) -> str:
        return self.name

    def pressed(self, event: QMouseEvent | QKeyEvent) -> None:
        pass

    def released(self, event: QMouseEvent | QKeyEvent) -> None:
        pass