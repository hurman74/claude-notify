# claude-notify

A Claude Code plugin that shows a native desktop notification when Claude
**needs your input** (permission prompt, waiting for a reply) or **finishes a task**.

Works on macOS, Linux (`notify-send`) and Windows (PowerShell toast). Requires Python 3.

It tries to ping you only when you're not watching:

- **🔐 Needs permission** / **💬 Needs your input**: when Claude is blocked on you.
- **✅ Done · my-app · 2m 14s**: when a task finishes, with the first line of Claude's answer.
- Quick turns (under 10 s) don't send "done".
- On macOS nothing is sent while the terminal running Claude is the focused app.
- No "waiting for your input" reminder right after a "done" notification.
- With `terminal-notifier` installed (macOS), clicking the notification brings the terminal back.

## Install

In Claude Code:

```
/plugin marketplace add hurman74/claude-notify
/plugin install desktop-notify@claude-notify
```

Restart Claude Code. Test it with `/desktop-notify test`.

## Settings

Set these in the `env` block of `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_NOTIFY_MIN_SECONDS": "30",
    "CLAUDE_NOTIFY_SOUND": "none"
  }
}
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `CLAUDE_NOTIFY_MIN_SECONDS` | `10` | Turns shorter than this don't send "done" |
| `CLAUDE_NOTIFY_WHEN_FOCUSED` | `0` | `1` = notify even while the terminal is focused |
| `CLAUDE_NOTIFY_ON_STOP` | `1` | `0` = only "needs input", never "done" |
| `CLAUDE_NOTIFY_SOUND` | `Glass` | macOS sound name, or `none` |

## Updates

Turn on auto-update once: `/plugin` → Marketplaces → claude-notify → Enable auto-update.
Or update manually: `/plugin marketplace update claude-notify`.

## Turn off

```
/plugin disable desktop-notify@claude-notify
```

## Troubleshooting

- **macOS:** System Settings → Notifications → allow your terminal app (or "Script Editor").
  Check Focus / Do Not Disturb. Optional: `brew install terminal-notifier`.
- **Linux:** install `libnotify-bin` (Debian/Ubuntu) or `libnotify`.
- **Nothing while testing?** Your terminal is probably focused. Use `/desktop-notify test`
  (always shows) or set `CLAUDE_NOTIFY_WHEN_FOCUSED=1`.

## Releasing a new version (maintainer)

1. Edit files under `plugins/desktop-notify/`.
2. Bump `version` in `plugins/desktop-notify/.claude-plugin/plugin.json`.
3. Add a line to `CHANGELOG.md`. Run `python3 -m unittest discover -s tests`.
4. Commit and push. Users with auto-update get it on their next start.
