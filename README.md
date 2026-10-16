# claude-notify

A Claude Code plugin that shows a native desktop notification when Claude
**needs your input** (permission prompt, waiting for a reply) or **finishes a task**.

Works on macOS, Linux (`notify-send`) and Windows (PowerShell toast). Requires Python 3.

## Install

In Claude Code:

```
/plugin marketplace add hurman74/claude-notify
/plugin install desktop-notify@claude-notify
```

Restart Claude Code. Test it with `/desktop-notify test`.

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

## Releasing a new version (maintainer)

1. Edit files under `plugins/desktop-notify/`.
2. Bump `version` in `plugins/desktop-notify/.claude-plugin/plugin.json`.
3. Commit and push. Users with auto-update get it on their next start.
