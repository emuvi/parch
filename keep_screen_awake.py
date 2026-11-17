"""
Keep the display and system awake while simulating mouse activity.

Every 30 seconds, send a mouse movement of up to 10 pixels, alternating left
and right within the current monitor. The script prints the resulting position.
Movements may be shorter near an edge, and their direction reverses if the
cursor is already at an edge.

Windows requires no additional packages. For macOS or Linux, install the
dependencies with ``python -m pip install -r keep_screen_awake_requirements.txt``.
Linux requires an X11 session; native Wayland is not supported. On macOS,
grant the terminal or Python permission to control the computer in Privacy &
Security > Accessibility.

Run with ``python keep_screen_awake.py`` and press Ctrl+C to stop. The wakefulness
request is cleared on exit. Screen savers, security policies, manual locking,
or desktop environments that ignore inhibition can still lock the session.
"""

import ctypes
from ctypes import wintypes
import os
import platform
import time


class MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class InputData(ctypes.Union):
    _fields_ = [
        ("mi", MouseInput),
        ("ki", KeyboardInput),
        ("hi", HardwareInput),
    ]


class Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("data", InputData)]


def main_windows():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.SetProcessDPIAware.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL
    user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HANDLE
    user32.GetMonitorInfoW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(MonitorInfo),
    ]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    kernel32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    kernel32.SetThreadExecutionState.restype = wintypes.DWORD

    if not user32.SetProcessDPIAware():
        raise ctypes.WinError(ctypes.get_last_error())

    es_continuous = 0x80000000
    es_system_required = 0x00000001
    es_display_required = 0x00000002
    if not kernel32.SetThreadExecutionState(
        es_continuous | es_system_required | es_display_required
    ):
        raise OSError("Could not request that Windows keep the display and system awake.")

    try:
        direction = -1
        print("Keeping the display awake and moving the mouse every 30 seconds. Press Ctrl+C to stop.")
        while True:
            time.sleep(30)
            point = wintypes.POINT()
            if not user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())

            monitor = user32.MonitorFromPoint(point, 2)
            if not monitor:
                raise ctypes.WinError(ctypes.get_last_error())

            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(info)
            if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                raise ctypes.WinError(ctypes.get_last_error())

            left = info.rcMonitor.left
            right = info.rcMonitor.right - 1
            if left == right:
                continue
            target_x = max(left, min(right, point.x + 10 * direction))
            if target_x == point.x:
                direction = -direction
                target_x = max(left, min(right, point.x + 10 * direction))

            virtual_left = user32.GetSystemMetrics(76)
            virtual_top = user32.GetSystemMetrics(77)
            virtual_width = user32.GetSystemMetrics(78)
            virtual_height = user32.GetSystemMetrics(79)
            if virtual_width <= 0 or virtual_height <= 0:
                raise OSError("Could not determine the virtual screen dimensions.")

            # Absolute SendInput coordinates use the entire virtual desktop.
            x = min(65535, ((target_x - virtual_left) * 65536 + 32768) // virtual_width)
            y = min(65535, ((point.y - virtual_top) * 65536 + 32768) // virtual_height)
            mouse_input = Input(type=0, data=InputData(mi=MouseInput(
                dx=x, dy=y, dwFlags=0x0001 | 0x8000 | 0x4000
            )))
            if user32.SendInput(1, ctypes.byref(mouse_input), ctypes.sizeof(Input)) != 1:
                raise OSError(
                    "Could not send mouse input; Windows may have blocked the event."
                )
            if not user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())
            print(f"Mouse moved to ({point.x}, {point.y}).", flush=True)
            direction = -direction
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if not kernel32.SetThreadExecutionState(es_continuous):
            raise OSError("Could not clear the Windows wakefulness request.")


def next_position(x, left, right, direction):
    """Return the next horizontal position and the following direction."""
    if right <= left:
        raise RuntimeError("The current monitor is too narrow to move the mouse.")
    target_x = max(left, min(right, x + 10 * direction))
    if target_x == x:
        direction = -direction
        target_x = max(left, min(right, x + 10 * direction))
    return target_x, -direction


def main_other(system):
    if system == "Linux" and (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        or os.environ.get("WAYLAND_DISPLAY")
    ):
        raise RuntimeError(
            "Global mouse control is not supported in Wayland. Use an X11 session."
        )

    try:
        from wakepy import keep
        if system == "Darwin":
            import Quartz
        else:
            from pynput.mouse import Controller
            from screeninfo import get_monitors
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Missing dependency. Run: python -m pip install -r "
            "keep_screen_awake_requirements.txt"
        ) from error

    if system == "Darwin":
        def position_and_bounds():
            event = Quartz.CGEventCreate(None)
            if event is None:
                raise RuntimeError("Could not read the mouse position.")
            point = Quartz.CGEventGetLocation(event)
            error, displays, _ = Quartz.CGGetActiveDisplayList(32, None, None)
            if error:
                raise RuntimeError(f"Could not list displays (error {error}).")
            for display in displays:
                bounds = Quartz.CGDisplayBounds(display)
                if (bounds.origin.x <= point.x < bounds.origin.x + bounds.size.width
                        and bounds.origin.y <= point.y < bounds.origin.y + bounds.size.height):
                    return point.x, point.y, bounds.origin.x, bounds.origin.x + bounds.size.width - 1
            raise RuntimeError("The mouse is not on an active monitor.")

        def move(x, y):
            event = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft
            )
            if event is None:
                raise RuntimeError("Could not create a mouse event.")
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
    else:
        mouse = Controller()

        def position_and_bounds():
            x, y = mouse.position
            for monitor in get_monitors():
                if (monitor.x <= x < monitor.x + monitor.width
                        and monitor.y <= y < monitor.y + monitor.height):
                    return x, y, monitor.x, monitor.x + monitor.width - 1
            raise RuntimeError("The mouse is not on an active monitor.")

        def move(x, y):
            mouse.position = (x, y)

    with keep.presenting(on_fail="error"):
        direction = -1
        print(f"{system}: keeping the display awake and moving the mouse every 30 seconds. Press Ctrl+C to stop.")
        while True:
            time.sleep(30)
            x, y, left, right = position_and_bounds()
            target_x, direction = next_position(x, left, right, direction)
            move(target_x, y)
            time.sleep(0.1)
            actual_x, actual_y, _, _ = position_and_bounds()
            if abs(actual_x - target_x) > 1:
                raise RuntimeError(
                    "Mouse movement failed. Check accessibility permissions and the graphical session."
                )
            print(f"Mouse moved to ({actual_x}, {actual_y}).", flush=True)


def main():
    system = platform.system()
    print(f"Detected platform: {system}", flush=True)
    try:
        if system == "Windows":
            main_windows()
        elif system in ("Darwin", "Linux"):
            main_other(system)
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
