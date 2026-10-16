---
name: desktop-notify
description: Desktop notifications (macOS, Linux, Windows) when Claude Code needs the user's input or finishes a task. Use when the user says "/desktop-notify", asks to test or turn notifications on/off, or wants to be pinged. Also use mid-task to ping the user when a decision from them is needed.
---

# Desktop notify

This plugin's hooks already send a native notification automatically:
- **Needs input**: `Notification` hook (permission prompts, idle waiting for a reply).
- **Task finished**: `Stop` hook, with the first line of Claude's final message.

Backends: macOS `terminal-notifier` if installed, else `osascript`; Linux `notify-send`;
Windows PowerShell toast. Failures are ignored so a hook never blocks Claude.

The script is `scripts/notify.py` in this skill's base directory (use `python` on Windows).

## Actions (`$ARGUMENTS`: `test`, `on`, `off`, or a message)

- **test** (default): `python3 <skill dir>/scripts/notify.py --title "Claude Code" --message "Notifications work 🎉"`
- **off**: tell the user to run `/plugin disable desktop-notify@claude-notify` (or `claude plugin disable desktop-notify@claude-notify`).
- **on**: `/plugin enable desktop-notify@claude-notify`.
- **Manual ping mid-task** when you need the user's decision during long work:
  `python3 <skill dir>/scripts/notify.py --title "Claude Code needs you" --message "<short question>"`
  Still ask the question in the chat reply too.

## Troubleshooting

- macOS shows nothing: System Settings → Notifications → allow your terminal app
  (or "Script Editor" for osascript); check Focus / Do Not Disturb.
  `brew install terminal-notifier` gives more reliable banners.
- Linux: install `libnotify-bin` (Debian/Ubuntu) or `libnotify` for `notify-send`.
