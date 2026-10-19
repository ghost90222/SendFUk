import win32gui
import win32process
import win32con
import win32api
import os

PLATFORM_KEYWORDS = ["instagram", "discord", "whatsapp", "telegram"]
BROWSER_KEYWORDS = ["chrome", "edge", "brave", "opera", "firefox"]


def is_real_window(hwnd):
    """Checks if HWND corresponds to a real top-level application window."""
    if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetWindowTextLength(hwnd) == 0:
        return False
    # Filter out invisible or tool/helper windows
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False
    return True


def get_all_open_windows():
    """
    Returns a list of all visible top-level application windows.
    Each item: {'hwnd': int, 'title': str, 'app_type': str}
    """
    results = []

    def enum_cb(hwnd, _):
        if is_real_window(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and title != "Program Manager":
                lower_title = title.lower()
                app_type = "App"
                if any(k in lower_title for k in PLATFORM_KEYWORDS):
                    app_type = "Chat"
                elif any(k in lower_title for k in BROWSER_KEYWORDS):
                    app_type = "Browser"

                results.append({
                    "hwnd": hwnd,
                    "title": title,
                    "app_type": app_type
                })
        return True

    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception as e:
        print(f"[WARN] EnumWindows error: {e}")

    # Sort chat/browser windows to the top
    results.sort(key=lambda x: (0 if x["app_type"] == "Chat" else (1 if x["app_type"] == "Browser" else 2)))
    return results


def focus_window(hwnd):
    """Brings the specified window to the foreground reliably using AttachThreadInput."""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        fore_hwnd = win32gui.GetForegroundWindow()
        if fore_hwnd == hwnd:
            return True

        fore_thread, _ = win32process.GetWindowThreadProcessId(fore_hwnd)
        app_thread = win32api.GetCurrentThreadId()

        if fore_thread != app_thread:
            win32process.AttachThreadInput(fore_thread, app_thread, True)
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(fore_thread, app_thread, False)
        else:
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        print(f"[WARN] focus_window error: {e}")
        return False


def restore_window(prev_hwnd):
    """Restores the user's previously active window."""
    if prev_hwnd and win32gui.IsWindow(prev_hwnd):
        focus_window(prev_hwnd)
