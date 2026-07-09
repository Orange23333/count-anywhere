from abc import ABC, abstractmethod
import ctypes
import ctypes.wintypes
from dataclasses import dataclass
import random
import threading
from typing import Callable, override, ReadOnly

# About global hotkey implementation:
#
# On Windows (As of 11th Mar 2026):
# - pywin32 (*Its updated date isn't important*)
# - pynput (Last updated in Mar 2025)
# - global-hotkeys (Last updated in 2024)
# - keyboard (Last updated in 2020)
#
# On macOS using pynput.
#
# On Linux using pynput is okay.
# But we have to know X11 provides it, not Wayland.
# Wayland implementation - desktop environments may provide an interface for Wayland.
#
# No Android implement.

from any_singleton import singleton

from count_anywhere.libs.collections import NumberIdManager
import count_anywhere.libs.win32 as win32

type HotkeyHandle = int
type Hotkey = str
type HotkeyEventHandler = Callable[[Hotkey], None]


@dataclass
class HotkeyHandlerItem:
    handle: ReadOnly[HotkeyHandle]
    hotkey_event_handler: ReadOnly[HotkeyEventHandler]


class HotkeyServiceProvider(ABC):
    def __init__(self) -> None:
        pass

    def __del__(self) -> None:
        self._unregister_all()

    @abstractmethod
    def _unregister_all(self) -> None:
        pass

    @abstractmethod
    def register(self, key: str, callback: HotkeyEventHandler) -> HotkeyHandle:
        pass

    @abstractmethod
    def unregister(self, handler: HotkeyHandle) -> None:
        pass


class WindowsHotkeyServiceProvider(HotkeyServiceProvider):
    def __init__(self) -> None:
        super().__init__()

        self.__handlers_lock = threading.Lock()
        self.__handlers = NumberIdManager()
        HEREEEEEEEEEEEEEEEEEEEEEEEEE!
        self.__event_handlers: dict[HotkeyHandle, HotkeyHandlerItem] = singleton(
            'count_anywhere.libs.hotkeys.HotkeyServiceProvider.__handlers',
            {}
        )

    @override
    def _unregister_all(self) -> None:
        for h, item in self.__even_handlers.items():
            pass

    @staticmethod
    def __analyse_hotkey_str(key: str) -> (ctypes.c_uint32, ctypes.c_uint32):
        # === Dead Keys ===
        # No specific:
        #   Super:
        #     Super - Space Cadet Keyboard used.
        #     Windows - Windows is using.
        #     Command - Mac is using.
        #     Meta - KDE is using.
        #   Meta:
        #     Meta - Space Cadet Keyboard used. Not Super key used by KDE. Usually be VK_APPS.
        #   Hyper:
        #     Hyper - Space Cadet Keyboard used. Usually be VK_CAPITAL or VK_TAB.
        #   Control:
        #     Control (Ctrl) - Gerneral in current.
        #   Alternate:
        #     Alternate (Alt) - Gerneral in current.
        #     VK_MENU - Windows API defined.
        #     Option - Mac is using.
        # Specific:
        #   Alternate Graphics:
        #     Alternate Graphics (AltGr) - Used by european keyboards, used to type some european characters.
        #                                  Usually be VK_RMENU.
        #   Application:
        #     VK_APP - Windows API defined. Used to open context menu.
        #   Compose:
        #     Compose - Could be defined by user in some Desktop Environments. Usually be VK_RWIN.
        #   Function:
        #     Fn - Implemented by hardware.

        vk_code = win32.Winuser.VirtualKeyCode

        aliases = {
            'super': '@win',
            'command': '@win',
            'meta': '@win',
            'hyper': '@win',
            'option': '@alt',
            'altgr': 'VK_RMENU',
            'compose': 'VK_RWIN'
        }

        combinations = {
            '@win': [vk_code.VK_LWIN, vk_code.VK_RWIN],
        }

        replacements = {
            '+': [vk_code.VK_SHIFT, vk_code.VK_SHIFT]
        }

        exclutions = {
            vk_code.VK_SHIFT: [vk_code.VK_LSHIFT, vk_code.VK_RSHIFT],
            vk_code.VK_CONTROL: [vk_code.VK_LCONTROL, vk_code.VK_RCONTROL],
            vk_code.VK_MENU: [vk_code.VK_LMENU, vk_code.VK_RMENU]
        }

        keys = key.split('+')

        for k in keys:
            k = k.lower()

            match k:
                case 'alt':
                    pass
                case 'ctrl':
                    pass
                case 'shift':
                    pass
                case 'win':
                    pass
                case _:
                    c = ord(k)
                    if (
                        ord('0') <= c <= ord('9') or
                        ord('A') <= c <= ord('Z') or
                        ord('a') <= c <= ord('z')
                    ):
                        pass
                    elif:
                        pass
                    else:
                        raise SyntaxError('Bad hotkey string.')

    @override
    def register(self, key: str, callback: HotkeyEventHandler) -> HotkeyHandle:
        import win32con
        import ctypes.wintypes

        fsModifiers, vk = WindowsHotkeyServiceProvider.__analyse_hotkey_str(key)

        with self.__handlers_lock:
            id_ = 0
            while id_ in self.__even_handlers:
                id_ = random.randint(1, 0x7FFF_FFFE)

            r: ctypes.wintypes.BOOL = win32.User32.RegisterHotKey(
                None,
                ctypes.c_int32(id_),
                fsModifiers,
                vk
            )

            if r == 0:
                error_code = int(win32.Kernel32.GetLastError().value)

                raise RuntimeError(f'Failed to register the hot key. ({error_code})')

            self.__event_handlers[id_] = HotkeyHandlerItem(id_, callback)

        return id_


def use_hotkey_provider(name: str) -> HotkeyServiceProvider | None:
    match name:
        case "win":
            path = 'count_anywhere.libs.hotkeys:WindowsHotkeyServiceProvider'
            pass
        case "unix":
            path = '@not_implemented'
            pass
        case "macos":
            path = '@not_implemented'
            pass
        case _:
            raise NotImplementedError('Not implemented loading custom hotkey providers.')

    # Fake module loader:
    match path:
        case 'count_anywhere.libs.hotkeys:WindowsHotkeyServiceProvider':
            hp = WindowsHotkeyServiceProvider()
        case '@not_implemented':
            hp = None
        case _:
            raise RuntimeError('Unknown error.')

    return hp