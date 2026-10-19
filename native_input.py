import time
import random
import keyboard
import pyautogui
import pyperclip


def send_direct_message(message: str, username: str = None):
    """
    Directly types mention with real interactive tag pill and sends message.
    Preserves user clipboard and works reliably across Windows applications.
    """
    # 1. Real Mention Tagging
    if username and username.strip():
        u = username.strip()
        if not u.startswith("@"):
            u = f"@{u}"

        # Type @username
        keyboard.write(u)

        # Wait for platform mention suggestion dropdown (Discord, Telegram, WhatsApp, Instagram)
        time.sleep(random.uniform(0.30, 0.45))

        # Commit mention pill (Enter or Tab converts @name to an interactive tag)
        keyboard.send("enter")
        time.sleep(0.12)

        # Space separator
        keyboard.write(" ")
        time.sleep(0.06)

    # 2. Type Message Body
    # Try keyboard.write directly (zero clipboard)
    try:
        keyboard.write(message)
    except Exception:
        # Safe fallback: paste and immediately restore user's original clipboard
        old_clip = ""
        try:
            old_clip = pyperclip.paste()
        except Exception:
            pass
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass

    time.sleep(random.uniform(0.20, 0.35))

    # 3. Send Message
    keyboard.send("enter")
