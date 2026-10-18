import os
import sys
import tempfile
import threading
import time
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import apply, config, live_preview  # noqa: E402
from tests.test_apply import Base, wait_for  # noqa: E402


class LivePreviewTest(Base):
    def setUp(self):
        super().setUp()
        self.preview = live_preview.LivePreview()
        self.results = []
        self.args_log = self.engine_log

    def tearDown(self):
        self.preview.stop()
        super().tearDown()

    def done(self, ok, message):
        self.results.append((ok, message))

    def test_command_uses_window_mode_not_screen_root(self):
        cmd = live_preview.preview_command("123")
        self.assertIn("--window", cmd)
        self.assertNotIn("--screen-root", cmd)
        self.assertIn("--silent", cmd)
        self.assertEqual(cmd[cmd.index("--bg") + 1], os.path.join(config.WORKSHOP_DIR, "123"))
        self.assertIn("--volume", live_preview.preview_command("123", sound=True))

    def test_closes_itself_and_does_not_touch_the_desktop_state(self):
        self.write_engine("sleep 30")
        self.assertIsNone(self.preview.start("123", self.done, seconds=1.0))
        self.assertTrue(wait_for(lambda: self.preview.running))
        self.assertTrue(wait_for(lambda: self.results, timeout=8))
        self.assertEqual(self.results, [(True, "Prueba terminada.")])
        self.assertFalse(self.preview.running)
        # ni asignaciones, ni pidfiles de pantalla, ni "ultimo fondo bueno", ni known_bad
        conf = config.CONF_DIR
        self.assertFalse(os.path.exists(config.CURRENT_FILE))
        self.assertFalse([n for n in os.listdir(conf) if n.startswith(("pid_", "status_", "last_good"))])
        self.assertEqual(self.known_bad(), {})
        with open(self.engine_log) as f:
            self.assertIn("--window", f.read())

    def test_crash_reports_the_reason_without_a_rollback(self):
        self.write_engine('echo "terminate called after throwing x" >&2; ulimit -c 0; kill -ABRT $$')
        self.assertIsNone(self.preview.start("123", self.done, seconds=10))
        self.assertTrue(wait_for(lambda: self.results, timeout=10))
        ok, message = self.results[0]
        self.assertFalse(ok)
        self.assertIn("terminate called", message)
        self.assertEqual(self.known_bad(), {})  # una prueba no marca el fondo como roto

    def test_second_preview_replaces_the_first(self):
        self.write_engine("sleep 30")
        self.assertIsNone(self.preview.start("123", self.done, seconds=20))
        self.assertTrue(wait_for(lambda: self.preview.running))
        first = self.preview._proc.pid
        self.assertIsNone(self.preview.start("456", self.done, seconds=20))
        self.assertTrue(wait_for(lambda: not apply._alive(first)))
        self.assertTrue(self.preview.running)
        self.assertEqual(self.results, [])  # cerrar la primera no cuenta como fallo ni como fin

    def test_stop_closes_the_window(self):
        self.write_engine("sleep 30")
        self.assertIsNone(self.preview.start("123", self.done, seconds=20))
        self.assertTrue(wait_for(lambda: self.preview.running))
        pid = self.preview._proc.pid
        self.preview.stop()
        self.assertTrue(wait_for(lambda: not apply._alive(pid)))
        self.assertFalse(self.preview.running)

    def test_web_wallpapers_stay_blocked_until_allowed(self):
        config.atomic_write_json(os.path.join(config.WORKSHOP_DIR, "123", "project.json"), {"type": "web", "title": "w"})
        message = self.preview.start("123", self.done)
        self.assertIn("desactivados", message)
        self.assertFalse(self.preview.running)


if __name__ == "__main__":
    unittest.main()
