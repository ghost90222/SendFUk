# ⚡ FUK FUK Sender (Multi-Platform)

An automated, human-like message sender designed for **Instagram**, **Discord**, **WhatsApp**, and **Telegram**.

---

## 🚀 Key Features

### 1. 🌐 Chrome Background Tab Lock (100% Background Execution)
- Lock onto any active Chrome tab (Instagram Web, Discord Web, WhatsApp Web, Telegram Web).
- **Work freely in background**: Minimize Chrome or switch to other windows, watch videos, write code, or play games.
- **Zero mouse cursor movement**: Never moves or locks your mouse pointer.
- **Zero OS focus stealing**: Chrome does not steal active window focus.

### 2. 🛡️ Zero Clipboard Hijacking (Direct Injection)
- No `Ctrl+C` or `Ctrl+V` copying.
- Your OS system clipboard is **100% untouched and safe** while the bot is running.
- In Chrome mode: Injects text directly into the page DOM.
- In Desktop mode: Uses native Windows `SendInput` Unicode to type text and emojis directly.

### 3. 🏷️ Real Interactive Mention Tagging
- Does not send flat, plain raw `@username` text.
- Types `@username`, waits for the platform's auto-complete mention suggestion list, and commits the tag (converting it into an active interactive mention badge/pill).
- Followed by the message body.

### 4. 👤 Usernames Pool (Add One-by-One or Bulk)
- Add usernames individually via the inline input box (`@username` + `Add`).
- When usernames are present: randomly picks a username, creates real tag, and sends.
- When 0 usernames are present: sends messages normally without tag prefix.
- Bulk editor with JSON formatting & validation.

### 5. 💬 Curated Messages Pool & Anti-Ban Protection
- Customizable JSON messages pool with in-app editor.
- Randomized delays between messages (e.g. `1.2s - 2.8s`).
- Anti-ban batch breaks (e.g. rest for `180s` every `35` messages) with real-time countdown timer.

---

## 📂 Project Structure

```text
SendFUck/
├── chrome_engine.py           # Chrome DevTools Protocol (CDP) background lock engine
├── native_input.py            # Windows SendInput direct Unicode typing engine
├── fuk_fuk_sender.py          # Main PyQt6 GUI application
├── insta_auto_sender.py       # Backward compatibility launcher
├── messages.json              # Curated pool of messages
├── usernames.json             # Usernames pool (add one-by-one or bulk)
├── settings.json              # Persistent settings & configuration
├── templates/                 # Visual anchor templates for desktop detection
├── requirements.txt           # Python dependencies (PyQt6, Playwright, etc.)
├── run.bat                    # 1-click Windows launcher
└── README.md                  # Documentation
```

---

## ⚡ How to Run

1. Double-click **`run.bat`** in the project folder.
2. Select your desired execution mode:
   - **🌐 Chrome Tab Lock**: Click `🚀 Launch Chrome`, log into your chat, select your tab from the dropdown, and click `▶ START BOT (F6)`. You can minimize Chrome and keep doing your work!
   - **🖥️ Desktop Active Window**: Click inside the chat box in your desktop app and click `▶ START BOT (F6)`.
3. Press **`F6`** anytime to toggle START / STOP.
4. Emergency Stop: Push your mouse cursor to the top-left corner (`0, 0`).
