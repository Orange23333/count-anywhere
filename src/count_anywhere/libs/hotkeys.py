from abc import ABCMeta
import importlib.util


# About global hotkey implementation:
#
# On Windows using pywin32 or pynput.
# On macOS using pynput.
# On Linux using pynput is okay,
# we have to know X11 provides it, not Wayland.
# Wayland implementation - desktop environments may provide an interface for Wayland.

class HotKeyServiceProvider(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

    def make_native(self) -> None:
        pass


def use_hotkey_provider(name: str) -> None:
    match name:
        case "win":
            pass
        case "unix":
            pass
        case _:
            raise NotImplementedError('Not implemented loading custom hotkey providers.')