# Changelog

## 1.1.1

- Windows: read hook input and write output as UTF-8, so emoji and non-English text work.

## 1.1.0

- Smarter: no "done" for quick turns (`CLAUDE_NOTIFY_MIN_SECONDS`, default 10 s).
- macOS: no notification while the terminal running Claude is the focused app.
- No "waiting for your input" reminder right after a "done" notification.
- Clearer titles: 🔐 Needs permission, 💬 Needs your input, ✅ Done with project and duration.
- "Done" summary falls back to the session transcript and strips Markdown.
- Click a notification to return to the terminal (macOS with `terminal-notifier`).
- Settings via env vars: `CLAUDE_NOTIFY_MIN_SECONDS`, `CLAUDE_NOTIFY_WHEN_FOCUSED`,
  `CLAUDE_NOTIFY_ON_STOP`, `CLAUDE_NOTIFY_SOUND`.
- Windows toasts use PowerShell's app id so they show reliably.
- Tests plus CI on macOS, Linux and Windows.

## 1.0.0

- First release: notification when Claude needs input or finishes a task.
