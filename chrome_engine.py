import os
import sys
import json
import time
import subprocess
import urllib.request
from typing import List, Dict, Optional, Tuple

CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
CHROME_USER_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "FukFukSenderChrome"
)

PLATFORM_PATTERNS = {
    "Instagram": ["instagram.com/direct", "instagram.com"],
    "Discord": ["discord.com/channels", "discord.com"],
    "WhatsApp": ["web.whatsapp.com"],
    "Telegram": ["web.telegram.org"]
}

SELECTORS_BY_PLATFORM = {
    "Discord": [
        'div[role="textbox"][data-slate-editor="true"]',
        'div[role="textbox"]',
        'div[class*="slateTextArea"]'
    ],
    "Instagram": [
        'div[contenteditable="true"][role="textbox"]',
        'div[aria-label="Message"]',
        'div[aria-label="Message..."]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="Message"]'
    ],
    "WhatsApp": [
        'div[contenteditable="true"][data-tab="10"]',
        'footer div[contenteditable="true"]',
        'div[title="Type a message"]',
        'div[role="textbox"]'
    ],
    "Telegram": [
        'div#editable-message-text',
        'div.input-message-input',
        'div[contenteditable="true"]'
    ]
}

UNIVERSAL_SELECTORS = [
    'div[contenteditable="true"][role="textbox"]',
    'div[role="textbox"]',
    'div[contenteditable="true"]',
    'textarea',
    'input[type="text"]'
]


def find_chrome_path() -> Optional[str]:
    """Finds Google Chrome executable path on Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), r"Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def is_cdp_available(port: int = CDP_PORT, timeout: float = 0.8) -> bool:
    """Checks if Chrome is running and responding on the remote debugging port."""
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=timeout)
        return req.getcode() == 200
    except Exception:
        return False


def get_chrome_tabs(port: int = CDP_PORT) -> List[Dict]:
    """Returns list of open browser page tabs from Chrome DevTools Protocol."""
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1.2)
        data = json.loads(req.read().decode("utf-8"))
        page_tabs = []
        for t in data:
            if t.get("type") == "page":
                url = t.get("url", "")
                if url.startswith("chrome-extension://") or url.startswith("chrome://intro"):
                    continue
                page_tabs.append({
                    "id": t.get("id"),
                    "title": t.get("title") or "Untitled Tab",
                    "url": url,
                    "webSocketDebuggerUrl": t.get("webSocketDebuggerUrl")
                })
        return page_tabs
    except Exception:
        return []


def launch_chrome_with_cdp(port: int = CDP_PORT, initial_url: str = None) -> Tuple[bool, str]:
    """Launches Chrome with remote debugging port and a dedicated profile."""
    if is_cdp_available(port):
        return True, "Chrome already running with Remote Debugging."

    chrome_exe = find_chrome_path()
    if not chrome_exe:
        return False, "Google Chrome not found in standard paths."

    os.makedirs(CHROME_USER_DATA_DIR, exist_ok=True)

    args = [
        chrome_exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={CHROME_USER_DATA_DIR}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    if initial_url:
        args.append(initial_url)
    else:
        args.append("https://www.google.com")

    try:
        subprocess.Popen(args)
        # Wait up to 5 seconds for CDP port to open
        for _ in range(25):
            time.sleep(0.2)
            if is_cdp_available(port):
                return True, "Chrome launched successfully on Port 9222."
        return True, "Chrome started (waiting for port to open)..."
    except Exception as e:
        return False, f"Failed to launch Chrome: {e}"


class BackgroundTabSender:
    """Manages background message dispatch into a locked Chrome tab via Playwright CDP."""

    def __init__(self, port: int = CDP_PORT):
        self.port = port
        self.playwright = None
        self.browser = None
        self.locked_page = None
        self.locked_tab_id = None

    def connect(self) -> Tuple[bool, str]:
        """Connects to Chrome via Playwright over CDP."""
        try:
            from playwright.sync_api import sync_playwright
            if self.browser:
                try:
                    if self.browser.is_connected():
                        return True, "Connected"
                except Exception:
                    pass

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{self.port}")
            return True, "Connected to Chrome"
        except Exception as e:
            self.disconnect()
            return False, f"Connection failed: {e}"

    def disconnect(self):
        """Cleanly releases Playwright CDP resources."""
        self.locked_page = None
        self.locked_tab_id = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

    def lock_target_tab(self, target_identifier: str = None, platform_name: str = None) -> Tuple[bool, str]:
        """
        Locks onto a specific tab by ID, title, or platform URL pattern.
        target_identifier: can be tab 'id', partial URL, or 'auto'.
        """
        ok, msg = self.connect()
        if not ok:
            return False, msg

        all_pages = []
        for ctx in self.browser.contexts:
            for p in ctx.pages:
                all_pages.append(p)

        if not all_pages:
            return False, "No tabs found in connected Chrome."

        # 1. Match by specific target identifier (ID, URL, or Title)
        if target_identifier and target_identifier != "auto":
            for p in all_pages:
                if target_identifier in p.url or target_identifier in p.title():
                    self.locked_page = p
                    return True, f"Locked tab: {p.title()[:25]} ({p.url[:30]})"

        # 2. Match by platform pattern
        if platform_name and platform_name in PLATFORM_PATTERNS:
            patterns = PLATFORM_PATTERNS[platform_name]
            for p in all_pages:
                for pat in patterns:
                    if pat in p.url.lower():
                        self.locked_page = p
                        return True, f"Locked {platform_name} tab: {p.title()[:25]}"

        # 3. Match any known platform
        for plat, patterns in PLATFORM_PATTERNS.items():
            for p in all_pages:
                for pat in patterns:
                    if pat in p.url.lower():
                        self.locked_page = p
                        return True, f"Locked {plat} tab: {p.title()[:25]}"

        # 4. Fallback to active/first page
        self.locked_page = all_pages[0]
        return True, f"Locked first tab: {self.locked_page.title()[:25]}"

    def find_chat_input(self, page, platform_name: str = None):
        """Finds the chat input element in the page without stealing window focus."""
        # 1. Check platform-specific selectors
        selectors = []
        if platform_name and platform_name in SELECTORS_BY_PLATFORM:
            selectors.extend(SELECTORS_BY_PLATFORM[platform_name])
        for s in UNIVERSAL_SELECTORS:
            if s not in selectors:
                selectors.append(s)

        for sel in selectors:
            try:
                loc = page.locator(sel)
                cnt = loc.count()
                if cnt > 0:
                    for i in range(cnt):
                        el = loc.nth(i)
                        if el.is_visible():
                            return el
            except Exception:
                continue

        # 2. Check document.activeElement
        try:
            is_active_input = page.evaluate("""() => {
                const a = document.activeElement;
                if (!a) return false;
                return (a.isContentEditable || a.tagName === 'TEXTAREA' || a.tagName === 'INPUT');
            }""")
            if is_active_input:
                return page.locator(":focus")
        except Exception:
            pass

        return None

    def send_message(self, message: str, username: str = None, platform_name: str = None) -> Tuple[bool, str]:
        """
        Sends message and handles real tagging directly into the locked background tab.
        Zero mouse movement, zero OS clipboard usage, zero focus stealing.
        """
        if not self.locked_page:
            return False, "No tab locked."

        try:
            page = self.locked_page
            chat_input = self.find_chat_input(page, platform_name)
            if not chat_input:
                return False, "Chat input box not found in locked tab."

            # DOM-level focus (does NOT steal Windows OS window focus)
            chat_input.click(timeout=1500)
            page.wait_for_timeout(100)

            # 1. Real Tagging (if username given)
            if username and username.strip():
                clean_user = username.strip()
                if not clean_user.startswith("@"):
                    clean_user = f"@{clean_user}"

                # Type @username
                page.keyboard.type(clean_user, delay=20)
                # Wait for suggestion dropdown to render
                page.wait_for_timeout(350)
                # Press Tab to commit the tag into a real mention pill
                page.keyboard.press("Tab")
                page.wait_for_timeout(100)
                page.keyboard.type(" ")
                page.wait_for_timeout(50)

            # 2. Direct Message Injection (No clipboard touched)
            page.keyboard.type(message, delay=10)
            page.wait_for_timeout(180)

            # 3. Send
            page.keyboard.press("Enter")
            return True, "Message sent successfully in background."

        except Exception as e:
            return False, f"Send failed: {e}"
