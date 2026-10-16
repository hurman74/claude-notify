#!/usr/bin/env python3
"""Cross-platform desktop notification for Claude Code hooks.

Runs as a UserPromptSubmit / Notification / Stop hook (reads the hook JSON
from stdin), or directly:  notify.py --title "Claude Code" --message "Hello"

Only notifies when it is useful:
  - skips "done" for quick turns (CLAUDE_NOTIFY_MIN_SECONDS, default 10)
  - skips everything while the terminal running Claude is the focused app (macOS)
  - skips the "waiting for your input" reminder right after a "done" notification

Settings (environment variables, e.g. in the "env" block of ~/.claude/settings.json):
  CLAUDE_NOTIFY_MIN_SECONDS   turns shorter than this don't send "done" (default 10)
  CLAUDE_NOTIFY_WHEN_FOCUSED  1 = notify even when the terminal is focused (default 0)
  CLAUDE_NOTIFY_ON_STOP       0 = never send "done", only "needs input" (default 1)
  CLAUDE_NOTIFY_SOUND         macOS sound name, or "none" (default Glass)
  CLAUDE_NOTIFY_DRY_RUN       1 = print the notification as JSON instead of showing it
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

IDLE_AFTER_DONE_WINDOW = 600  # seconds


def env_flag(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def env_number(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# ---------------------------------------------------------------- state

def state_path(session_id):
    base = os.environ.get("CLAUDE_NOTIFY_STATE_DIR") or os.path.join(
        tempfile.gettempdir(), "claude-desktop-notify")
    os.makedirs(base, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")
    return os.path.join(base, safe + ".json")


def load_state(session_id):
    try:
        with open(state_path(session_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(session_id, state):
    try:
        with open(state_path(session_id), "w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError:
        pass


# ---------------------------------------------------------------- message text

def clean(text, limit=160):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_#>|]", "", text)
    for line in text.splitlines():
        line = " ".join(line.split())
        if line:
            return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"
    return ""


def last_assistant_text(data):
    if data.get("last_assistant_message"):
        return data["last_assistant_message"]
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 512 * 1024))
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return ""
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            text = "\n".join(b.get("text", "") for b in content
                             if isinstance(b, dict) and b.get("type") == "text")
            if text.strip():
                return text
    return ""


def duration(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def notification_kind(data):
    kind = data.get("notification_type") or ""
    if kind:
        return kind
    message = (data.get("message") or "").lower()
    if "permission" in message:
        return "permission_prompt"
    if "waiting for your input" in message:
        return "idle_prompt"
    return "other"


# ---------------------------------------------------------------- focus (macOS)

def terminal_bundle_id():
    return os.environ.get("__CFBundleIdentifier", "")


def terminal_is_focused():
    if platform.system() != "Darwin" or not shutil.which("lsappinfo"):
        return False
    bundle = terminal_bundle_id()
    if not bundle:
        return False
    try:
        front = subprocess.run(["lsappinfo", "front"], capture_output=True,
                               text=True, timeout=2).stdout.strip()
        info = subprocess.run(["lsappinfo", "info", "-only", "bundleid", front],
                              capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return f'"{bundle}"' in info


# ---------------------------------------------------------------- backends

def notify(title, message, group="claude-code"):
    if env_flag("CLAUDE_NOTIFY_DRY_RUN", False):
        out = json.dumps({"title": title, "message": message}, ensure_ascii=False) + "\n"
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.stdout.flush()
        return
    sound = os.environ.get("CLAUDE_NOTIFY_SOUND", "Glass")
    muted = sound.lower() == "none"
    system = platform.system()
    if system == "Darwin":
        if shutil.which("terminal-notifier"):
            cmd = ["terminal-notifier", "-title", title, "-message", message, "-group", group]
            if not muted:
                cmd += ["-sound", sound]
            if terminal_bundle_id():
                cmd += ["-activate", terminal_bundle_id()]  # click → back to the terminal
            subprocess.run(cmd, check=False, timeout=5)
        else:
            sound_part = "" if muted else ' sound name (item 3 of argv)'
            script = ("on run argv\n"
                      "display notification (item 2 of argv) with title (item 1 of argv)"
                      + sound_part + "\nend run")
            subprocess.run(["osascript", "-e", script, title, message, sound],
                           check=False, timeout=5)
    elif system == "Linux":
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", "-a", "Claude Code", "-i", "dialog-information",
                            title, message], check=False, timeout=5)
    elif system == "Windows":
        # PowerShell's own AppUserModelID, so the toast shows without registering an app.
        app_id = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
        ps = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null;"
            "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
            "$x=$t.GetElementsByTagName('text');"
            "$x.Item(0).AppendChild($t.CreateTextNode($env:CC_TITLE)) > $null;"
            "$x.Item(1).AppendChild($t.CreateTextNode($env:CC_MSG)) > $null;"
            "$n=[Windows.UI.Notifications.ToastNotification]::new($t);"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:CC_APP).Show($n)"
        )
        env = dict(os.environ, CC_TITLE=title, CC_MSG=message, CC_APP=app_id)
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       env=env, check=False, timeout=10)


# ---------------------------------------------------------------- hook flow

def handle_hook(data):
    event = data.get("hook_event_name", "")
    session = data.get("session_id", "")
    project = os.path.basename((data.get("cwd") or os.getcwd()).rstrip("/\\")) or "Claude Code"
    now = time.time()
    state = load_state(session)

    if event == "UserPromptSubmit":
        state["turn_start"] = now
        save_state(session, state)
        return

    if event == "Stop":
        if data.get("stop_hook_active") or not env_flag("CLAUDE_NOTIFY_ON_STOP", True):
            return
        start = state.get("turn_start")
        elapsed = now - start if start else None
        if elapsed is not None and elapsed < env_number("CLAUDE_NOTIFY_MIN_SECONDS", 10):
            return
        title = f"✅ Done · {project}" + (f" · {duration(elapsed)}" if elapsed else "")
        message = clean(last_assistant_text(data)) or "Task finished"
        state["last_done"] = now

    elif event == "Notification":
        kind = notification_kind(data)
        if kind == "auth_success":
            return
        if kind == "idle_prompt" and now - state.get("last_done", 0) < IDLE_AFTER_DONE_WINDOW:
            return  # already told them it's done; don't nag
        if kind == "permission_prompt":
            title = f"🔐 Needs permission · {project}"
        else:
            title = f"💬 Needs your input · {project}"
        message = data.get("message") or "Claude is waiting for you"

    else:
        return

    save_state(session, state)
    if terminal_is_focused() and not env_flag("CLAUDE_NOTIFY_WHEN_FOCUSED", False):
        return
    notify(title, message, group=f"claude-code-{session[:8]}" if session else "claude-code")


def main():
    args = sys.argv[1:]
    if "--title" in args or "--message" in args:
        def get(key, default):
            i = args.index(key) if key in args else -1
            return args[i + 1] if 0 <= i < len(args) - 1 else default
        notify(get("--title", "Claude Code"), get("--message", "Notification"))
        return
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace") if not sys.stdin.isatty() else ""
        data = json.loads(raw or "{}")
    except (ValueError, OSError):
        data = {}
    handle_hook(data)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a notification problem must never block Claude
