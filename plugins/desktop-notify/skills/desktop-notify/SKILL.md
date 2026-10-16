---
name: desktop-notify
description: Desktop notifications (macOS, Linux, Windows) when Claude Code needs the user's input or finishes a task. Use when the user says "/desktop-notify", asks to test or turn notifications on/off, or wants to be pinged. Also use mid-task to ping the user when a decision from them is needed.
---

# Desktop notify

This plugin's hooks already send a native notification automatically:
- **Needs input**: `Notification` hook (permission prompts, idle waiting for a reply).
- **Task finished**: `Stop` hook, with the duration and first line of Claude's final message.
- A `UserPromptSubmit` hook times each turn. Quick turns (< `CLAUDE_NOTIFY_MIN_SECONDS`,
  default 10) don't send "done"; on macOS nothing is sent while the terminal is focused;
  the idle "waiting for input" reminder is skipped right after a "done".
- Settings are env vars (`CLAUDE_NOTIFY_MIN_SECONDS`, `CLAUDE_NOTIFY_WHEN_FOCUSED`,
  `CLAUDE_NOTIFY_ON_STOP`, `CLAUDE_NOTIFY_SOUND`) in the `env` block of `~/.claude/settings.json`.
  Edit that block when the user asks to change behaviour (e.g. "less noisy", "mute").

Backends: macOS `terminal-notifier` if installed, else `osascript`; Linux `notify-send`;
Windows PowerShell toast. Failures are ignored so a hook never blocks Claude.

The script is `scripts/notify.py` in this skill's base directory (use `python` on Windows).

## Actions (`$ARGUMENTS`: `test`, `on`, `off`, or a message)

- **test** (default): `python3 <skill dir>/scripts/notify.py --title "Claude Code" --message "Notifications work 🎉"`
- **off**: tell the user to run `/plugin disable desktop-notify@claude-notify` (or `claude plugin disable desktop-notify@claude-notify`).
- **on**: `/plugin enable desktop-notify@claude-notify`.
- **Manual mode always shows**, even when the terminal is focused (good for testing).
- **Manual ping mid-task** when you need the user's decision during long work:
  `python3 <skill dir>/scripts/notify.py --title "Claude Code needs you" --message "<short question>"`
  Still ask the question in the chat reply too.

## Troubleshooting

- macOS shows nothing: System Settings → Notifications → allow your terminal app
  (or "Script Editor" for osascript); check Focus / Do Not Disturb.
  `brew install terminal-notifier` gives more reliable banners.
- Nothing appears while testing hooks: the terminal is focused, which is by design.
- Linux: install `libnotify-bin` (Debian/Ubuntu) or `libnotify` for `notify-send`.
