import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "desktop-notify",
                      "skills", "desktop-notify", "scripts", "notify.py")


class NotifyHookTest(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()
        self.env = dict(os.environ, CLAUDE_NOTIFY_DRY_RUN="1", CLAUDE_NOTIFY_STATE_DIR=self.state,
                        CLAUDE_NOTIFY_WHEN_FOCUSED="1")

    def run_hook(self, payload, **env):
        payload = {"session_id": "s1", "cwd": "/work/my-app", **payload}
        out = subprocess.run([sys.executable, SCRIPT], input=json.dumps(payload), text=True,
                             capture_output=True, env={**self.env, **env}).stdout.strip()
        return json.loads(out) if out else None

    def start_turn(self, seconds_ago):
        self.run_hook({"hook_event_name": "UserPromptSubmit"})
        path = os.path.join(self.state, "s1.json")
        state = json.load(open(path))
        state["turn_start"] = time.time() - seconds_ago
        json.dump(state, open(path, "w"))

    def test_user_prompt_submit_prints_nothing(self):
        self.assertIsNone(self.run_hook({"hook_event_name": "UserPromptSubmit"}))

    def test_quick_turn_is_silent(self):
        self.start_turn(2)
        self.assertIsNone(self.run_hook({"hook_event_name": "Stop", "last_assistant_message": "hi"}))

    def test_long_turn_notifies_with_summary_and_duration(self):
        self.start_turn(125)
        n = self.run_hook({"hook_event_name": "Stop",
                           "last_assistant_message": "**All tests pass.**\nMore detail"})
        self.assertIn("my-app", n["title"])
        self.assertIn("2m", n["title"])
        self.assertEqual(n["message"], "All tests pass.")

    def test_summary_from_transcript(self):
        self.start_turn(60)
        path = os.path.join(self.state, "t.jsonl")
        with open(path, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"content": "do it"}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Deployed to staging."}]}}) + "\n")
        n = self.run_hook({"hook_event_name": "Stop", "transcript_path": path})
        self.assertEqual(n["message"], "Deployed to staging.")

    def test_stop_disabled(self):
        self.start_turn(60)
        self.assertIsNone(self.run_hook({"hook_event_name": "Stop"}, CLAUDE_NOTIFY_ON_STOP="0"))

    def test_stop_hook_active_is_silent(self):
        self.start_turn(60)
        self.assertIsNone(self.run_hook({"hook_event_name": "Stop", "stop_hook_active": True}))

    def test_permission_prompt(self):
        n = self.run_hook({"hook_event_name": "Notification",
                           "message": "Claude needs your permission to use Bash"})
        self.assertIn("permission", n["title"].lower())
        self.assertIn("Bash", n["message"])

    def test_idle_after_done_is_suppressed(self):
        self.start_turn(60)
        self.assertIsNotNone(self.run_hook({"hook_event_name": "Stop"}))
        idle = {"hook_event_name": "Notification", "notification_type": "idle_prompt",
                "message": "Claude is waiting for your input"}
        self.assertIsNone(self.run_hook(idle))

    def test_idle_without_recent_done_notifies(self):
        n = self.run_hook({"hook_event_name": "Notification",
                           "message": "Claude is waiting for your input"})
        self.assertIn("input", n["title"].lower())

    def test_bad_input_never_fails(self):
        result = subprocess.run([sys.executable, SCRIPT], input="not json", text=True,
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0)

    def test_manual_mode(self):
        out = subprocess.run([sys.executable, SCRIPT, "--title", "T", "--message", "M"],
                             text=True, capture_output=True, env=self.env).stdout
        self.assertEqual(json.loads(out), {"title": "T", "message": "M"})


if __name__ == "__main__":
    unittest.main()
