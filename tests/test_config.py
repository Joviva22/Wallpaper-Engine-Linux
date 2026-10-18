import os
import sys
import tempfile
import unittest

# CONF_DIR/CACHE_DIR se calculan al importar: apuntar HOME a un temporal antes.
_HOME = tempfile.mkdtemp()
os.environ["HOME"] = _HOME
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import config  # noqa: E402


class AtomicWriteTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "a.json")

    def test_roundtrip_and_overwrite(self):
        config.atomic_write_json(self.path, {"a": 1})
        config.atomic_write_json(self.path, {"a": 2})
        self.assertEqual(config.load_json(self.path, {}), {"a": 2})

    def test_mode_600_and_no_leftover_temp(self):
        config.atomic_write_json(self.path, [1])
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)
        self.assertEqual(os.listdir(self.dir), ["a.json"])

    def test_failed_write_keeps_old_file(self):
        config.atomic_write_json(self.path, {"ok": True})
        with self.assertRaises(TypeError):
            config.atomic_write_json(self.path, {"bad": object()})
        self.assertEqual(config.load_json(self.path, {}), {"ok": True})
        self.assertEqual(os.listdir(self.dir), ["a.json"])


class LoadJsonTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "x.json")

    def test_missing_returns_fresh_default(self):
        a = config.load_json(self.path, {})
        a["x"] = 1
        self.assertEqual(config.load_json(self.path, {}), {})

    def test_corrupt_is_quarantined(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(config.load_json(self.path, {}), {})
        self.assertFalse(os.path.exists(self.path))
        with open(self.path + ".corrupt") as f:
            self.assertEqual(f.read(), "{not json")

    def test_wrong_type_is_quarantined(self):
        with open(self.path, "w") as f:
            f.write("[1, 2]")
        self.assertEqual(config.load_json(self.path, {}), {})
        self.assertTrue(os.path.exists(self.path + ".corrupt"))

    def test_set_convert(self):
        config.atomic_write_json(self.path, ["b", "a"])
        self.assertEqual(config.load_json(self.path, set(), config._id_set), {"a", "b"})
        config.atomic_write_json(self.path, {"a": 1})
        self.assertEqual(config.load_json(self.path, set(), config._id_set), set())
        self.assertTrue(os.path.exists(self.path + ".corrupt"))


class HiddenPasswordTest(unittest.TestCase):
    def tearDown(self):
        config.clear_hidden_password()

    def test_no_password_allows_everything(self):
        config.clear_hidden_password()
        self.assertFalse(config.has_hidden_password())
        self.assertTrue(config.verify_hidden_password("anything"))

    def test_set_and_verify(self):
        config.set_hidden_password("1234")
        self.assertTrue(config.has_hidden_password())
        self.assertTrue(config.verify_hidden_password("1234"))
        self.assertFalse(config.verify_hidden_password("4321"))
        self.assertEqual(os.stat(config.HIDDEN_LOCK_FILE).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
