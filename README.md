# ⚡ FUK FUK Sender (Multi-Platform)

An automated, human-like message sender designed for **Instagram**, **Discord**, **WhatsApp**, and **Telegram**.

---

## 🚀 Features

- **Multi-Platform Support**: Auto-detects chat input bars on:
  - 📷 **Instagram** (`😊 Message... 🎙️`)
  - 💬 **Discord** (`+ |Message #channel 🎁 GIF 😊`)
  - 📱 **WhatsApp Web / Desktop** (`📎 😊 Type a message 🎙️`)
  - ✈️ **Telegram Desktop / Web** (`📎 |Message ⏱️ 😊 🟣🎙️`)
- **Zero Cursor Hijacking**: Does NOT move or lock your mouse cursor across the screen. Your mouse remains 100% free.
- **Smart Tab Detection**: Confirms the active window/tab has the chat input bar before sending. Automatically pauses when switching away from chat tabs.
- **Dynamic Usernames Prepending**: Add usernames one-by-one via the inline input box. When usernames are present, randomly picks and prepends `@username message`. When 0 usernames, sends normal messages.
- **In-App JSON & Text Editor**: View, edit, format, or bulk paste messages and usernames directly inside the app with 1-click JSON validation.
- **Anti-Ban Architecture**:
  - Variable randomized intervals between messages (e.g., `1.2s – 2.8s`).
  - Automatic batch limits & rest breaks (e.g., rests for `180s` every `35` messages) with real-time countdown timer.
  - Human review hesitation pause before pressing Enter.
- **Emergency Stop (Fail-Safe)**: Push your mouse cursor to the top-left corner (`0, 0`) to instantly kill/stop the sender.

---

## 📂 Project Structure

```text
SendFUck/
├── templates/                 # High-precision visual anchor templates
│   ├── discord/
│   ├── instagram/
│   ├── telegram/
│   └── whatsapp/
├── messages.json              # Curated pool of messages
├── usernames.json             # Pool of usernames (add one-by-one or bulk)
├── settings.json              # Saved preferences & timings
├── fuk_fuk_sender.py          # Main application
├── insta_auto_sender.py       # Backward compatibility entrypoint
├── requirements.txt           # Pinned production dependencies
├── run.bat                    # 1-click launcher script
└── README.md                  # Project documentation
```

---

## ⚡ How to Run

1. Double-click **`run.bat`** in the project folder.
2. The **FUK FUK Sender** floating panel will appear on screen.
3. Click inside your Instagram, Discord, WhatsApp, or Telegram chat box to focus the cursor.
4. Click **`▶ START BOT (F6)`** (or press **`F6`** on your keyboard).
