#!/usr/bin/env python3
"""Cross-platform desktop notification for Claude Code hooks.

Used as a Notification / Stop hook (reads the hook JSON from stdin), or
directly:  notify.py --title "Claude Code" --message "Hello"
Supports macOS (osascript), Linux (notify-send) and Windows (PowerShell toast).
"""
import json
import os
import platform
import shutil
import subprocess
import sys


def read_hook_input():
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return {}


def build_message(data):
    event = data.get("hook_event_name", "")
    project = os.path.basename(data.get("cwd") or os.getcwd()) or "Claude Code"
    if event == "Notification":
        return f"Claude Code · {project}", data.get("message") or "Claude needs your input"
    if event in ("Stop", "SubagentStop"):
        last = (data.get("last_assistant_message") or "").strip().splitlines()
        summary = last[0][:140] if last else "Task finished"
        return f"Claude Code · {project} ✅ done", summary
    return f"Claude Code · {project}", data.get("message") or "Claude Code update"


def notify(title, message):
    system = platform.system()
    if system == "Darwin":
        if shutil.which("terminal-notifier"):
            subprocess.run(["terminal-notifier", "-title", title, "-message", message,
                            "-sound", "Glass", "-group", "claude-code"], check=False)
        else:
            script = ("on run argv\n"
                      "display notification (item 2 of argv) with title (item 1 of argv) sound name \"Glass\"\n"
                      "end run")
            subprocess.run(["osascript", "-e", script, title, message], check=False)
    elif system == "Linux":
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", "-a", "Claude Code", title, message], check=False)
        else:
            sys.stdout.write("\a")
    elif system == "Windows":
        ps = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null;"
            "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
            "$x=$t.GetElementsByTagName('text');"
            "$x.Item(0).AppendChild($t.CreateTextNode($env:CC_TITLE)) > $null;"
            "$x.Item(1).AppendChild($t.CreateTextNode($env:CC_MSG)) > $null;"
            "$n=[Windows.UI.Notifications.ToastNotification]::new($t);"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($n)"
        )
        env = dict(os.environ, CC_TITLE=title, CC_MSG=message)
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], env=env, check=False)


def main():
    args = sys.argv[1:]
    if "--title" in args or "--message" in args:
        get = lambda k, d: args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else d
        title, message = get("--title", "Claude Code"), get("--message", "Notification")
    else:
        data = read_hook_input()
        if data.get("stop_hook_active"):
            return
        title, message = build_message(data)
    try:
        notify(title, message)
    except Exception:
        pass  # never block Claude because a notification failed


if __name__ == "__main__":
    main()
