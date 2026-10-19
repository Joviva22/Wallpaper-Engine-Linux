import os
import sys
import tempfile
import threading
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import compat, config  # noqa: E402


class CompatTest(unittest.TestCase):
    def setUp(self):
        self._conf = config.CONF_DIR
        config.CONF_DIR = tempfile.mkdtemp()
        self.item = {"id": "1", "type": "Scene"}

    def tearDown(self):
        config.CONF_DIR = self._conf

    def status(self, item=None, bad=None, web=True):
        return compat.status(item or self.item, bad or {}, compat.load_history(), web)

    def test_untested_by_default(self):
        self.assertEqual(self.status()[0], compat.UNTESTED)

    def test_ok_after_a_stable_run_and_failure_after_a_crash(self):
        compat.record("1", True)
        state, label, why = self.status()
        self.assertEqual((state, label), (compat.OK, "✓ Funciona"))
        self.assertIn("como fondo", why)
        compat.record("1", False, "boom\nsecond line")
        state, _, why = self.status()
        self.assertEqual(state, compat.FAILED)
        self.assertIn("boom", why)
        self.assertNotIn("second line", why)

    def test_latest_result_wins_and_preview_is_labelled(self):
        compat.record("1", False, "x")
        compat.record("1", True, source="preview")
        state, _, why = self.status()
        self.assertEqual(state, compat.OK)
        self.assertIn("en una prueba", why)

    def test_known_bad_beats_history_and_clear_forgets(self):
        compat.record("1", True)
        bad = {"1": {"detected_at": "2026-10-18T10:00:00+02:00", "returncode": -11, "detail": ""}}
        state, _, why = self.status(bad=bad)
        self.assertEqual(state, compat.FAILED)
        self.assertIn("-11", why)
        compat.clear("1")
        self.assertEqual(self.status()[0], compat.UNTESTED)

    def test_web_blocked_unless_allowed(self):
        web = {"id": "2", "type": "Web"}
        self.assertEqual(self.status(web, web=False)[0], compat.BLOCKED)
        self.assertEqual(self.status(web, web=True)[0], compat.UNTESTED)

    def test_corrupt_history_is_ignored(self):
        with open(compat.history_file(), "w") as f:
            f.write("{not json")
        self.assertEqual(self.status()[0], compat.UNTESTED)
        compat.record("1", True)
        self.assertEqual(self.status()[0], compat.OK)

    def test_concurrent_records_do_not_lose_entries(self):
        threads = [threading.Thread(target=compat.record, args=(str(n), True)) for n in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(compat.load_history()), 12)


if __name__ == "__main__":
    unittest.main()
