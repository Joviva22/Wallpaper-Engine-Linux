import os
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import cleanup, config  # noqa: E402


def write(path, size=10):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x" * size)


class CleanupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmp, "cache")
        self.conf = os.path.join(self.tmp, "conf")
        os.makedirs(self.conf)
        self.saved = (cleanup.CACHE_ROOT, config.CONF_DIR, config.CACHE_DIR, config.WORKSHOP_THUMB_CACHE, config.CURRENT_FILE)
        cleanup.CACHE_ROOT = self.cache
        config.CONF_DIR = self.conf
        config.CACHE_DIR = os.path.join(self.cache, "thumbs_v6")
        config.WORKSHOP_THUMB_CACHE = os.path.join(self.cache, "workshop_thumbs_v2")
        config.CURRENT_FILE = os.path.join(self.conf, "current.json")
        stage = os.path.join(self.cache, "cef", cleanup.STAGE_ID)
        write(os.path.join(self.cache, "thumbs_v5", "a.png"), 100)
        write(os.path.join(config.CACHE_DIR, "b.png"), 50)
        write(os.path.join(self.conf, "wallpaperengine_eDP-1.log.1"), 400)
        write(os.path.join(self.conf, "wallpaperengine_eDP-1.log"), 30)
        write(os.path.join(self.conf, "repair_1.lock"), 0)
        write(os.path.join(stage, "Default", "Cache", "c"), 1000)
        write(os.path.join(stage, "Default", "IndexedDB", "pack.blob"), 5000)
        write(os.path.join(stage, "Default", "Local Storage", "ls"), 20)
        self.stage = stage

    def tearDown(self):
        (cleanup.CACHE_ROOT, config.CONF_DIR, config.CACHE_DIR, config.WORKSHOP_THUMB_CACHE, config.CURRENT_FILE) = self.saved

    def by_key(self):
        return {c.key: c for c in cleanup.scan()}

    def test_scan_reports_sizes_and_defaults(self):
        cats = self.by_key()
        self.assertEqual(cats["old_thumbs"].size, 100)
        self.assertEqual(cats["old_logs"].size, 400)
        self.assertEqual(cats["stage_cache"].size, 1000)       # sin IndexedDB ni Local Storage
        self.assertFalse(cats["thumbs"].default)               # las actuales no se marcan por defecto
        self.assertFalse(cats["logs"].default)
        self.assertIn("locks", cats)

    def test_clean_removes_only_selected_regenerable_data(self):
        cats = self.by_key()
        freed, errors = cleanup.clean([cats["old_thumbs"], cats["old_logs"], cats["stage_cache"], cats["locks"]])
        self.assertEqual((freed, errors), (1500, []))
        self.assertFalse(os.path.exists(os.path.join(self.cache, "thumbs_v5")))
        self.assertFalse(os.path.exists(os.path.join(self.stage, "Default", "Cache")))
        self.assertFalse(os.path.exists(os.path.join(self.conf, "repair_1.lock")))
        # intacto: miniaturas actuales, log actual, y los datos descargados de Nikke Stage
        self.assertTrue(os.path.exists(os.path.join(config.CACHE_DIR, "b.png")))
        self.assertTrue(os.path.exists(os.path.join(self.conf, "wallpaperengine_eDP-1.log")))
        self.assertTrue(os.path.exists(os.path.join(self.stage, "Default", "IndexedDB", "pack.blob")))
        self.assertTrue(os.path.exists(os.path.join(self.stage, "Default", "Local Storage", "ls")))

    def test_nikke_stage_cache_is_blocked_while_it_runs(self):
        config.atomic_write_json(config.CURRENT_FILE, {"eDP-1": cleanup.STAGE_ID})
        with open(os.path.join(self.conf, "pid_eDP-1.pid"), "w") as f:
            f.write(str(os.getpid()))
        cat = self.by_key()["stage_cache"]
        self.assertTrue(cat.blocked)
        freed, errors = cleanup.clean([cat])
        self.assertEqual(freed, 0)
        self.assertTrue(errors)
        self.assertTrue(os.path.exists(os.path.join(self.stage, "Default", "Cache", "c")))

    def test_symlinks_are_removed_without_following_them(self):
        target = os.path.join(self.tmp, "precious")
        write(os.path.join(target, "keep.txt"), 7)
        link = os.path.join(self.cache, "thumbs_v3")
        os.symlink(target, link)
        cats = self.by_key()
        cleanup.clean([cats["old_thumbs"]])
        self.assertFalse(os.path.lexists(link))
        self.assertTrue(os.path.exists(os.path.join(target, "keep.txt")))

    def test_paths_outside_the_app_folders_are_refused(self):
        outside = os.path.join(self.tmp, "elsewhere", "x")
        write(outside)
        cat = cleanup.Category("x", "x", "x", [outside])
        freed, errors = cleanup.clean([cat])
        self.assertEqual(freed, 0)
        self.assertTrue(os.path.exists(outside))
        self.assertTrue(errors)

    def test_human_sizes(self):
        self.assertEqual(cleanup.human(512), "512 B")
        self.assertEqual(cleanup.human(1536), "1.5 KB")
        self.assertEqual(cleanup.human(3 * 1024 ** 3), "3.0 GB")


if __name__ == "__main__":
    unittest.main()
