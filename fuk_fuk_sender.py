"""
⚡ FUK FUK Sender - Multi-Platform Auto Sender (Instagram, Discord, WhatsApp, Telegram)
Author: Production Ready Build
"""

import sys
import os
import json
import time
import random

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox, QSpinBox, QCheckBox, QFrame,
    QGroupBox, QDialog, QTextEdit, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QCursor, QFont
import pyautogui
import pyperclip
import keyboard
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")
USERNAMES_FILE = os.path.join(BASE_DIR, "usernames.json")

# Visual templates for multi-platform chat input bars
PLATFORM_TEMPLATES = {
    "Instagram": [
        (os.path.join(BASE_DIR, "templates", "instagram", "template_smiley.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "instagram", "template_left.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "instagram", "template_mic.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "instagram", "instagram_input_bar.png"), 0.65),
    ],
    "Discord": [
        (os.path.join(BASE_DIR, "templates", "discord", "plus.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "discord", "right_icons.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "discord", "bar.png"), 0.65),
    ],
    "WhatsApp": [
        (os.path.join(BASE_DIR, "templates", "whatsapp", "left.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "whatsapp", "mic.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "whatsapp", "bar.png"), 0.65),
    ],
    "Telegram": [
        (os.path.join(BASE_DIR, "templates", "telegram", "mic_purple.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "telegram", "paperclip_left.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "telegram", "right_icons.png"), 0.72),
        (os.path.join(BASE_DIR, "templates", "telegram", "bar.png"), 0.65),
    ]
}

DEFAULT_SETTINGS = {
    "target_platform": "All Platforms (Auto-Detect)",
    "min_delay": 1.2,
    "max_delay": 2.8,
    "batch_limit": 35,
    "break_duration_s": 180,
    "verify_layout": True,
    "always_on_top": True
}


def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save settings: {e}")


def parse_list_text(raw_text: str):
    """Intelligently parses JSON array, JSON object, or plain line-by-line items."""
    raw_text = raw_text.strip()
    if not raw_text or raw_text == "[]" or raw_text == "{}":
        return []

    try:
        data = json.loads(raw_text)
        if isinstance(data, list):
            return [str(m).strip() for m in data if str(m).strip()]
        elif isinstance(data, dict):
            for k in ["messages", "usernames", "users", "data"]:
                if k in data and isinstance(data[k], list):
                    return [str(m).strip() for m in data[k] if str(m).strip()]
    except Exception:
        pass

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned = []
    for l in lines:
        if l in ["[", "]", "{", "}", "],", "[]", "{}"]:
            continue
        item = l.strip('",\'')
        if item:
            cleaned.append(item)
    return cleaned


def load_messages_pool():
    if not os.path.exists(MESSAGES_FILE):
        sample = [
            "Hey! How is your day going so far? 😊",
            "Hope you're having an awesome week ahead! ✨",
            "Just saw your profile, really loved your content! 🔥",
            "Hey there! Free for a quick conversation?",
            "Hope everything is great on your end! 🙌"
        ]
        try:
            with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
                json.dump(sample, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return sample

    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            msgs = parse_list_text(content)
            return msgs if msgs else ["Hello!"]
    except Exception as e:
        print(f"[ERROR] Failed to read messages: {e}")
        return ["Error reading messages.json"]


def load_usernames_pool():
    if not os.path.exists(USERNAMES_FILE):
        return []
    try:
        with open(USERNAMES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            return parse_list_text(content)
    except Exception as e:
        print(f"[ERROR] Failed to read usernames: {e}")
        return []


def save_usernames_pool(usernames_list):
    try:
        with open(USERNAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(usernames_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save usernames: {e}")
        return False


class HotkeyEmitter(QObject):
    toggle_requested = pyqtSignal()


class GenericListEditorDialog(QDialog):
    """Reusable modal allowing users to view, edit, or paste JSON or plain text lists."""
    items_saved = pyqtSignal(int)

    def __init__(self, title: str, file_path: str, item_name: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.item_name = item_name

        self.setWindowTitle(title)
        self.resize(520, 440)
        self.setStyleSheet("background-color: #12131a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_lbl = QLabel(f"Paste your {item_name} below (as JSON array or line-by-line):")
        header_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        layout.addWidget(header_lbl)

        self.editor = QTextEdit()
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1a1b26;
                color: #f1f5f9;
                border: 1px solid #323547;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.editor)

        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.lbl_info)

        btn_row = QHBoxLayout()

        btn_format = QPushButton("⚡ Format as Clean JSON")
        btn_format.setStyleSheet("""
            QPushButton { background: #262738; color: #cbd5e1; border: 1px solid #3e4157; border-radius: 6px; padding: 7px 12px; font-size: 11px; }
            QPushButton:hover { background: #32354b; color: white; }
        """)
        btn_format.clicked.connect(self.format_as_json)

        btn_clear = QPushButton("🗑 Clear All")
        btn_clear.setStyleSheet("""
            QPushButton { background: #332026; color: #f87171; border: 1px solid #4a2830; border-radius: 6px; padding: 7px 12px; font-size: 11px; }
            QPushButton:hover { background: #45242c; color: #fca5a5; }
        """)
        btn_clear.clicked.connect(self.clear_all)

        btn_save = QPushButton("💾 Save & Apply")
        btn_save.setStyleSheet("""
            QPushButton { background: #10b981; color: white; border: none; border-radius: 6px; padding: 7px 16px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background: #059669; }
        """)
        btn_save.clicked.connect(self.save_and_close)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton { background: #262738; color: #94a3b8; border: 1px solid #3e4157; border-radius: 6px; padding: 7px 12px; font-size: 11px; }
            QPushButton:hover { background: #32354b; color: white; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_format)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self.load_current_items()

    def load_current_items(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.setPlainText(content)
            self.update_count_preview()
        except Exception as e:
            self.lbl_info.setText(f"Error loading: {e}")

    def update_count_preview(self):
        items = parse_list_text(self.editor.toPlainText())
        self.lbl_info.setText(f"✓ Detected {len(items)} {self.item_name} ready.")

    def clear_all(self):
        self.editor.setPlainText("[]")
        self.lbl_info.setText(f"✓ Cleared all {self.item_name} (0 items).")

    def format_as_json(self):
        items = parse_list_text(self.editor.toPlainText())
        formatted = json.dumps(items, indent=2, ensure_ascii=False)
        self.editor.setPlainText(formatted)
        self.lbl_info.setText(f"✓ Formatted {len(items)} items into valid JSON.")

    def save_and_close(self):
        items = parse_list_text(self.editor.toPlainText())
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            self.items_saved.emit(len(items))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", f"Failed to save {self.file_path}:\n{e}")


class SenderWorker(QThread):
    status_changed = pyqtSignal(str, str)     # status_text, color_code
    message_sent = pyqtSignal(int, str, int)  # total_sent, message_text, batch_count
    countdown_tick = pyqtSignal(str)          # countdown description
    finished_loop = pyqtSignal()

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        self.config_getter = config_getter
        self.is_running = False
        self.total_sent = 0
        self.batch_count = 0
        self.messages = []
        self.usernames = []

    def stop(self):
        self.is_running = False

    def sleep_interruptible(self, duration_sec, prefix="Wait"):
        end_time = time.time() + duration_sec
        while time.time() < end_time and self.is_running:
            rem = max(0.0, end_time - time.time())
            if duration_sec >= 1.0:
                self.countdown_tick.emit(f"{prefix}: {rem:.1f}s")
            time.sleep(0.05)
        self.countdown_tick.emit("")

    def detect_platform_on_screen(self, target_platform: str):
        """Scans screen to detect Instagram, Discord, WhatsApp, or Telegram chat bar."""
        if target_platform == "All Platforms (Auto-Detect)":
            platforms_to_check = ["Instagram", "Discord", "WhatsApp", "Telegram"]
        elif target_platform in PLATFORM_TEMPLATES:
            platforms_to_check = [target_platform]
        else:
            platforms_to_check = ["Instagram", "Discord", "WhatsApp", "Telegram"]

        for plat in platforms_to_check:
            templates = PLATFORM_TEMPLATES.get(plat, [])
            for tpath, conf in templates:
                if not os.path.exists(tpath):
                    continue
                try:
                    loc = pyautogui.locateOnScreen(tpath, confidence=conf)
                    if loc is not None:
                        return plat
                except Exception:
                    pass
        return None

    def paste_and_send(self, text: str):
        """Pastes message cleanly into active input and sends - zero mouse cursor movement."""
        pyperclip.copy(text)
        time.sleep(random.uniform(0.04, 0.08))

        pyautogui.hotkey('ctrl', 'v')

        time.sleep(random.uniform(0.25, 0.48))

        pyautogui.press('enter')

    def run(self):
        self.is_running = True
        try:
            self.messages = load_messages_pool()
            self.usernames = load_usernames_pool()

            if not self.messages:
                self.status_changed.emit("No Messages in JSON", "#ef4444")
                self.is_running = False
                self.finished_loop.emit()
                return

            self.status_changed.emit("Starting...", "#10b981")

            while self.is_running:
                cfg = self.config_getter()
                batch_limit = max(1, cfg.get("batch_limit", 35))
                break_duration = max(1, cfg.get("break_duration_s", 180))
                verify_layout = cfg.get("verify_layout", True)
                target_platform = cfg.get("target_platform", "All Platforms (Auto-Detect)")

                # 1. Anti-Ban Rest Check
                if self.batch_count >= batch_limit:
                    self.status_changed.emit(f"Anti-Ban Rest ({break_duration}s)", "#f59e0b")
                    self.sleep_interruptible(break_duration, prefix="Resting")
                    if not self.is_running:
                        break
                    self.batch_count = 0
                    random.shuffle(self.messages)
                    if self.usernames:
                        random.shuffle(self.usernames)
                    self.status_changed.emit("Resuming...", "#10b981")

                # 2. Check if Current Tab has Platform Chat Layout (Insta / Discord / WhatsApp / Telegram)
                if verify_layout:
                    self.status_changed.emit("Scanning Screen...", "#38bdf8")
                    detected_platform = self.detect_platform_on_screen(target_platform)
                    if not detected_platform:
                        self.status_changed.emit("Waiting: Chat Not on Screen", "#f59e0b")
                        self.countdown_tick.emit("Waiting for chat box (Insta / Discord / WA / Telegram)")
                        time.sleep(0.7)
                        continue
                    else:
                        self.countdown_tick.emit(f"{detected_platform} detected ✓")

                if not self.is_running:
                    break

                # 3. Prepare Message (Prepend Username if available)
                msg = random.choice(self.messages)

                self.usernames = load_usernames_pool()

                if self.usernames:
                    uname = random.choice(self.usernames).strip()
                    if uname:
                        final_text = f"{uname} {msg}"
                    else:
                        final_text = msg
                else:
                    final_text = msg

                # 4. Paste & Send (No mouse cursor hijacking)
                self.status_changed.emit("Pasting & Sending...", "#3b82f6")
                self.paste_and_send(final_text)

                self.total_sent += 1
                self.batch_count += 1
                self.message_sent.emit(self.total_sent, final_text, self.batch_count)

                # 5. Variable Random Delay Between Messages (Anti-Detection)
                min_d = min(cfg.get("min_delay", 1.2), cfg.get("max_delay", 2.8))
                max_d = max(cfg.get("min_delay", 1.2), cfg.get("max_delay", 2.8))
                delay = random.uniform(min_d, max_d)

                self.status_changed.emit(f"Next in {delay:.1f}s", "#818cf8")
                self.sleep_interruptible(delay, prefix="Next msg")

        except pyautogui.FailSafeException:
            self.status_changed.emit("FailSafe (Mouse Corner)", "#ef4444")
            self.countdown_tick.emit("Emergency stop triggered by mouse in corner!")
        except Exception as e:
            self.status_changed.emit(f"Error: {str(e)[:25]}", "#ef4444")
            self.countdown_tick.emit(str(e))
        finally:
            self.is_running = False
            self.status_changed.emit("Stopped", "#9ca3af")
            self.countdown_tick.emit("")
            self.finished_loop.emit()


class FukFukSenderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.worker = None

        self.setWindowTitle("⚡ FUK FUK Sender (Multi-Platform)")
        self.resize(370, 620)
        self.apply_window_flags()

        self.init_ui()
        self.init_hotkey()

    def apply_window_flags(self):
        flags = Qt.WindowType.Window
        if self.settings.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def init_hotkey(self):
        self.hotkey_emitter = HotkeyEmitter()
        self.hotkey_emitter.toggle_requested.connect(self.toggle_bot)
        try:
            keyboard.add_hotkey("f6", lambda: self.hotkey_emitter.toggle_requested.emit())
        except Exception as e:
            print(f"[WARN] Hotkey error: {e}")

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: #11121a; color: #e2e8f0; font-family: 'Segoe UI', sans-serif;")

        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top Bar with Software Branding
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("⚡ FUK FUK Sender")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #f43f5e;")
        sub_lbl = QLabel("Multi-Platform (Insta • Discord • WA • Telegram)")
        sub_lbl.setStyleSheet("font-size: 9px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        self.chk_top = QCheckBox("📌 Top")
        self.chk_top.setChecked(self.settings.get("always_on_top", True))
        self.chk_top.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.chk_top.stateChanged.connect(self.toggle_always_on_top)

        top_bar.addLayout(title_box)
        top_bar.addStretch()
        top_bar.addWidget(self.chk_top)
        layout.addLayout(top_bar)

        # Status & Statistics Card
        status_card = QFrame()
        status_card.setStyleSheet("background-color: #181924; border: 1px solid #2b2d3d; border-radius: 8px; padding: 6px;")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(8, 8, 8, 8)
        sc_layout.setSpacing(4)

        status_row = QHBoxLayout()
        lbl_status_tag = QLabel("Status:")
        lbl_status_tag.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_status = QLabel("STOPPED")
        self.lbl_status.setStyleSheet("color: #9ca3af; font-weight: bold; font-size: 12px;")
        self.lbl_countdown = QLabel("")
        self.lbl_countdown.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 11px;")

        status_row.addWidget(lbl_status_tag)
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_countdown)
        sc_layout.addLayout(status_row)

        counts_row = QHBoxLayout()
        self.lbl_sent_total = QLabel("Sent: 0 msgs")
        self.lbl_sent_total.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: bold;")
        self.lbl_batch_stat = QLabel("Batch: 0 / 35")
        self.lbl_batch_stat.setStyleSheet("color: #94a3b8; font-size: 11px;")
        counts_row.addWidget(self.lbl_sent_total)
        counts_row.addStretch()
        counts_row.addWidget(self.lbl_batch_stat)
        sc_layout.addLayout(counts_row)

        self.lbl_last_msg = QLabel("Last sent: None")
        self.lbl_last_msg.setStyleSheet("color: #64748b; font-size: 10px;")
        sc_layout.addWidget(self.lbl_last_msg)

        layout.addWidget(status_card)

        # Big START / STOP Button
        self.btn_toggle = QPushButton("▶ START BOT (F6)")
        self.btn_toggle.setFixedHeight(44)
        self.btn_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle.clicked.connect(self.toggle_bot)
        self.update_button_style(False)
        layout.addWidget(self.btn_toggle)

        # Section 1: Multi-Platform Target & Screen Layout Check
        box_platform = QGroupBox("🌐 Target Platform & Screen Detection")
        box_platform.setStyleSheet("""
            QGroupBox {
                border: 1px solid #2b2d3d;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
                font-size: 11px;
                font-weight: 600;
                color: #cbd5e1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        bp_layout = QVBoxLayout(box_platform)
        bp_layout.setSpacing(6)

        plat_row = QHBoxLayout()
        lbl_plat = QLabel("Platform:")
        lbl_plat.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.combo_platform = QComboBox()
        self.combo_platform.addItems([
            "All Platforms (Auto-Detect)",
            "Instagram",
            "Discord",
            "WhatsApp",
            "Telegram"
        ])
        current_plat = self.settings.get("target_platform", "All Platforms (Auto-Detect)")
        idx = self.combo_platform.findText(current_plat)
        if idx >= 0:
            self.combo_platform.setCurrentIndex(idx)
        self.combo_platform.setStyleSheet("""
            QComboBox {
                background-color: #1e1f2b;
                color: #38bdf8;
                border: 1px solid #37394b;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self.combo_platform.currentIndexChanged.connect(self.on_settings_change)
        plat_row.addWidget(lbl_plat)
        plat_row.addWidget(self.combo_platform, 1)
        bp_layout.addLayout(plat_row)

        self.chk_verify_layout = QCheckBox("Scan screen for chat input bar before sending")
        self.chk_verify_layout.setChecked(self.settings.get("verify_layout", True))
        self.chk_verify_layout.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: bold;")
        self.chk_verify_layout.stateChanged.connect(self.on_settings_change)
        bp_layout.addWidget(self.chk_verify_layout)

        lbl_plat_tip = QLabel("✓ Screen par kahin bhi Insta, Discord, WA ya Telegram dikhte hi send karega.\n✓ User ka mouse cursor bilkul move ya lock nahi hoga.")
        lbl_plat_tip.setWordWrap(True)
        lbl_plat_tip.setStyleSheet("color: #94a3b8; font-size: 9px;")
        bp_layout.addWidget(lbl_plat_tip)

        layout.addWidget(box_platform)

        # Section 2: Usernames Pool (Add One-by-One)
        box_users = QGroupBox("👤 Usernames Pool (Add One-by-One)")
        box_users.setStyleSheet(box_platform.styleSheet())
        bu_layout = QVBoxLayout(box_users)
        bu_layout.setSpacing(6)

        u_top_row = QHBoxLayout()
        self.lbl_user_count = QLabel("Usernames: 0 added")
        self.lbl_user_count.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 11px;")
        btn_view_users = QPushButton("📋 View / Bulk Edit")
        btn_view_users.setStyleSheet("""
            QPushButton { background: #222538; color: #c084fc; border: 1px solid #3e4157; border-radius: 6px; padding: 3px 8px; font-weight: bold; font-size: 10px; }
            QPushButton:hover { background: #2c3049; color: #e9d5ff; }
        """)
        btn_view_users.clicked.connect(self.open_usernames_editor)
        u_top_row.addWidget(self.lbl_user_count, 1)
        u_top_row.addWidget(btn_view_users)
        bu_layout.addLayout(u_top_row)

        input_row = QHBoxLayout()
        self.txt_username_input = QLineEdit()
        self.txt_username_input.setPlaceholderText("Type @username and press Enter...")
        self.txt_username_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1f2b;
                color: #f1f5f9;
                border: 1px solid #37394b;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #a855f7; }
        """)
        self.txt_username_input.returnPressed.connect(self.add_username_single)

        btn_add_user = QPushButton("➕ Add")
        btn_add_user.setStyleSheet("""
            QPushButton {
                background-color: #a855f7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #9333ea; }
        """)
        btn_add_user.clicked.connect(self.add_username_single)

        input_row.addWidget(self.txt_username_input, 1)
        input_row.addWidget(btn_add_user)
        bu_layout.addLayout(input_row)

        self.lbl_user_hint = QLabel("💡 0 usernames = message only. Usernames added = random username + msg")
        self.lbl_user_hint.setStyleSheet("color: #64748b; font-size: 9px;")
        bu_layout.addWidget(self.lbl_user_hint)

        layout.addWidget(box_users)

        # Section 3: Messages Pool
        box_msgs = QGroupBox("💬 Messages Pool")
        box_msgs.setStyleSheet(box_platform.styleSheet())
        bm_layout = QHBoxLayout(box_msgs)
        bm_layout.setSpacing(8)

        self.lbl_msg_count = QLabel("Messages: 5 loaded")
        self.lbl_msg_count.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        btn_edit_msgs = QPushButton("📝 Edit Messages")
        btn_edit_msgs.setStyleSheet("""
            QPushButton { background: #222538; color: #38bdf8; border: 1px solid #3e4157; border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background: #2c3049; color: #7dd3fc; }
        """)
        btn_edit_msgs.clicked.connect(self.open_messages_editor)
        bm_layout.addWidget(self.lbl_msg_count, 1)
        bm_layout.addWidget(btn_edit_msgs)
        layout.addWidget(box_msgs)

        self.refresh_pool_counts()

        # Section 4: Timing & Anti-Ban Break
        box_timing = QGroupBox("⏱ Send Delay Settings (Anti-Detection)")
        box_timing.setStyleSheet(box_platform.styleSheet())
        bt_layout = QVBoxLayout(box_timing)
        bt_layout.setSpacing(6)

        delays_row = QHBoxLayout()
        lbl_min = QLabel("Min Delay:")
        lbl_min.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0.2, 30.0)
        self.spin_min.setSingleStep(0.1)
        self.spin_min.setDecimals(2)
        self.spin_min.setValue(self.settings.get("min_delay", 1.2))
        self.spin_min.setSuffix(" s")
        self.style_spin(self.spin_min)
        self.spin_min.valueChanged.connect(self.on_settings_change)

        lbl_max = QLabel("Max Delay:")
        lbl_max.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0.5, 60.0)
        self.spin_max.setSingleStep(0.1)
        self.spin_max.setDecimals(2)
        self.spin_max.setValue(self.settings.get("max_delay", 2.8))
        self.spin_max.setSuffix(" s")
        self.style_spin(self.spin_max)
        self.spin_max.valueChanged.connect(self.on_settings_change)

        delays_row.addWidget(lbl_min)
        delays_row.addWidget(self.spin_min)
        delays_row.addSpacing(6)
        delays_row.addWidget(lbl_max)
        delays_row.addWidget(self.spin_max)
        bt_layout.addLayout(delays_row)

        self.lbl_ms_hint = QLabel("")
        self.lbl_ms_hint.setStyleSheet("color: #64748b; font-size: 10px;")
        bt_layout.addWidget(self.lbl_ms_hint)
        self.update_ms_hint()

        break_row = QHBoxLayout()
        lbl_batch = QLabel("Break every:")
        lbl_batch.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(5, 500)
        self.spin_batch.setValue(self.settings.get("batch_limit", 35))
        self.spin_batch.setSuffix(" msgs")
        self.style_spin(self.spin_batch)
        self.spin_batch.valueChanged.connect(self.on_settings_change)

        lbl_dur = QLabel("Rest for:")
        lbl_dur.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(10, 3600)
        self.spin_duration.setSingleStep(15)
        self.spin_duration.setValue(self.settings.get("break_duration_s", 180))
        self.spin_duration.setSuffix(" sec")
        self.style_spin(self.spin_duration)
        self.spin_duration.valueChanged.connect(self.on_settings_change)

        break_row.addWidget(lbl_batch)
        break_row.addWidget(self.spin_batch)
        break_row.addSpacing(6)
        break_row.addWidget(lbl_dur)
        break_row.addWidget(self.spin_duration)
        bt_layout.addLayout(break_row)

        layout.addWidget(box_timing)

        hint = QLabel("💡 Chat box par ek baar click karein, phir START dabayein.\n🚨 Emergency Stop: Mouse ko top-left corner par le jayein")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 10px; padding: 2px;")
        layout.addWidget(hint)

    def style_spin(self, sb):
        sb.setStyleSheet("""
            QAbstractSpinBox {
                background-color: #1e1f2b;
                color: #f1f5f9;
                border: 1px solid #37394b;
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 11px;
                font-weight: 600;
            }
        """)

    def update_ms_hint(self):
        mn = int(self.spin_min.value() * 1000)
        mx = int(self.spin_max.value() * 1000)
        self.lbl_ms_hint.setText(f"Random delay: {mn} ms se {mx} ms per message")

    def update_button_style(self, running: bool):
        if running:
            self.btn_toggle.setText("⏹ STOP BOT (F6)")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #dc2626; }
            """)
        else:
            self.btn_toggle.setText("▶ START BOT (F6)")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #059669; }
            """)

    def add_username_single(self):
        """Adds a single username from the input box directly to usernames.json."""
        text = self.txt_username_input.text().strip()
        if not text:
            return

        if not text.startswith("@"):
            text = f"@{text}"

        current_users = load_usernames_pool()
        if text not in current_users:
            current_users.append(text)
            save_usernames_pool(current_users)
            self.refresh_pool_counts()
            self.lbl_user_hint.setText(f"✓ Added {text} (Total: {len(current_users)})")
            self.lbl_user_hint.setStyleSheet("color: #10b981; font-size: 10px; font-weight: bold;")
        else:
            self.lbl_user_hint.setText(f"⚠️ {text} is already in the list.")
            self.lbl_user_hint.setStyleSheet("color: #f59e0b; font-size: 10px;")

        self.txt_username_input.clear()
        self.txt_username_input.setFocus()

    def get_config(self):
        return {
            "target_platform": self.combo_platform.currentText(),
            "min_delay": self.spin_min.value(),
            "max_delay": self.spin_max.value(),
            "batch_limit": self.spin_batch.value(),
            "break_duration_s": self.spin_duration.value(),
            "verify_layout": self.chk_verify_layout.isChecked(),
            "always_on_top": self.chk_top.isChecked()
        }

    def on_settings_change(self):
        self.update_ms_hint()
        self.lbl_batch_stat.setText(f"Batch: 0 / {self.spin_batch.value()}")
        save_settings(self.get_config())

    def toggle_always_on_top(self):
        is_on_top = self.chk_top.isChecked()
        pos = self.pos()
        self.settings["always_on_top"] = is_on_top
        save_settings(self.get_config())

        flags = Qt.WindowType.Window
        if is_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.move(pos)

    def open_messages_editor(self):
        dlg = GenericListEditorDialog("📝 Messages Pool Editor", MESSAGES_FILE, "messages", self)
        dlg.items_saved.connect(self.on_messages_saved)
        dlg.exec()

    def open_usernames_editor(self):
        dlg = GenericListEditorDialog("👤 Usernames Pool Editor", USERNAMES_FILE, "usernames", self)
        dlg.items_saved.connect(self.on_usernames_saved)
        dlg.exec()

    def on_messages_saved(self, count):
        self.refresh_pool_counts()
        self.lbl_last_msg.setText(f"Updated: {count} messages saved.")

    def on_usernames_saved(self, count):
        self.refresh_pool_counts()
        self.lbl_last_msg.setText(f"Updated: {count} usernames saved.")

    def refresh_pool_counts(self):
        msgs = load_messages_pool()
        users = load_usernames_pool()
        self.lbl_msg_count.setText(f"Messages: {len(msgs)} loaded")
        self.lbl_user_count.setText(f"Usernames: {len(users)} added")

    def toggle_bot(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.update_button_style(False)
            self.lbl_status.setText("STOPPING...")
            self.lbl_status.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 12px;")
        else:
            self.worker = SenderWorker(self.get_config, self)
            self.worker.status_changed.connect(self.on_worker_status)
            self.worker.message_sent.connect(self.on_worker_message_sent)
            self.worker.countdown_tick.connect(self.on_worker_countdown)
            self.worker.finished_loop.connect(self.on_worker_finished)
            self.worker.start()
            self.update_button_style(True)

    def on_worker_status(self, text, color):
        self.lbl_status.setText(text.upper())
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")

    def on_worker_message_sent(self, total_sent, msg, batch_count):
        self.lbl_sent_total.setText(f"Sent: {total_sent} msgs")
        limit = self.spin_batch.value()
        self.lbl_batch_stat.setText(f"Batch: {batch_count} / {limit}")
        preview = msg if len(msg) <= 30 else msg[:27] + "..."
        self.lbl_last_msg.setText(f"Last sent: {preview}")

    def on_worker_countdown(self, text):
        if hasattr(self, 'lbl_countdown'):
            self.lbl_countdown.setText(text)

    def on_worker_finished(self):
        self.update_button_style(False)
        self.lbl_status.setText("STOPPED")
        self.lbl_status.setStyleSheet("color: #9ca3af; font-weight: bold; font-size: 12px;")
        if hasattr(self, 'lbl_countdown'):
            self.lbl_countdown.setText("")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        save_settings(self.get_config())
        event.accept()


def main():
    pyautogui.FAILSAFE = True
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = FukFukSenderWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
