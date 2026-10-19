import os
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import config, rotation, selection  # noqa: E402

ITEMS = [{"id": "1", "type": "Scene"}, {"id": "2", "type": "Web"}, {"id": "3", "type": "Video"},
         {"id": "4", "type": "Scene", "preset": True}, {"id": "5", "type": "Scene"}]


class RotationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = {n: getattr(config, n) for n in
                      ("CONF_DIR", "PLAYLISTS_FILE", "PLAYLISTS_LOCK", "load_wallpapers", "load_hidden_ids",
                       "load_known_bad", "web_wallpapers_allowed")}
        config.CONF_DIR = self.tmp
        config.PLAYLISTS_FILE = os.path.join(self.tmp, "playlists.json")
        config.PLAYLISTS_LOCK = os.path.join(self.tmp, "playlists.lock")
        config.load_wallpapers = lambda: ITEMS
        config.load_hidden_ids = lambda: set()
        config.load_known_bad = lambda: {}
        self.web = True
        config.web_wallpapers_allowed = lambda: self.web
        self.applied = []

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(config, name, value)

    def playlist(self, **entry):
        base = {"enabled": True, "interval_minutes": 1, "items": ["1", "2", "3"], "current_index": 0, "last_switch": 0}
        base.update(entry)
        config.atomic_write_json(config.PLAYLISTS_FILE, {"eDP-1": base})

    def apply(self, screen, wid):
        self.applied.append((screen, wid))
        return True

    def state(self):
        return config.load_json(config.PLAYLISTS_FILE, {})["eDP-1"]

    def test_web_items_rotate_only_when_allowed(self):
        self.assertIn("2", selection.eligible_ids())
        self.web = False
        self.assertNotIn("2", selection.eligible_ids())
        self.assertNotIn("4", selection.eligible_ids())  # presets nunca

    def test_advances_to_next_item_and_records_progress(self):
        self.playlist()
        rotation.tick(now=1000, apply_fn=self.apply)
        self.assertEqual(self.applied, [("eDP-1", "2")])
        self.assertEqual((self.state()["current_index"], self.state()["last_switch"]), (1, 1000))

    def test_waits_for_the_interval(self):
        self.playlist(last_switch=1000)
        rotation.tick(now=1030, apply_fn=self.apply)
        self.assertEqual(self.applied, [])
        rotation.tick(now=1061, apply_fn=self.apply)
        self.assertEqual(len(self.applied), 1)

    def test_disabled_or_paused_does_nothing(self):
        self.playlist(enabled=False)
        rotation.tick(now=1000, apply_fn=self.apply)
        self.playlist()
        open(os.path.join(self.tmp, "rotation_paused"), "w").close()
        rotation.tick(now=1000, apply_fn=self.apply)
        self.assertEqual(self.applied, [])

    def test_skips_ineligible_items_and_wraps_around(self):
        self.web = False
        self.playlist(items=["1", "2", "3"], current_index=0)
        rotation.tick(now=1000, apply_fn=self.apply)
        self.assertEqual(self.applied, [("eDP-1", "3")])  # salta el web
        self.assertEqual(self.state()["current_index"], 2)
        rotation.tick(now=2000, apply_fn=self.apply)
        self.assertEqual(self.applied[-1], ("eDP-1", "1"))  # vuelve al principio

    def test_failed_apply_does_not_advance(self):
        self.playlist()
        rotation.tick(now=1000, apply_fn=lambda s, w: False)
        self.assertEqual((self.state()["current_index"], self.state()["last_switch"]), (0, 0))

    def test_all_ineligible_does_nothing(self):
        self.web = False
        self.playlist(items=["2", "4"])
        rotation.tick(now=1000, apply_fn=self.apply)
        self.assertEqual(self.applied, [])

    # --- estado, pasos manuales y problemas de la lista -------------------------------------------------
    def test_status_reports_current_next_and_countdown(self):
        self.playlist(items=["1", "2", "3"], current_index=0, last_switch=1000, interval_minutes=2)
        info = rotation.status("eDP-1", now=1030)
        self.assertEqual((info["current"], info["next"], info["seconds_left"]), ("1", "2", 90))
        self.assertEqual((info["items"], info["playable"], info["enabled"]), (3, 3, True))

    def test_status_with_disabled_paused_and_unplayable(self):
        self.playlist(enabled=False)
        self.assertIsNone(rotation.status("eDP-1", now=5)["seconds_left"])
        self.playlist()
        open(os.path.join(self.tmp, "rotation_paused"), "w").close()
        info = rotation.status("eDP-1", now=5)
        self.assertTrue(info["paused"])
        self.assertIsNone(info["seconds_left"])
        os.remove(os.path.join(self.tmp, "rotation_paused"))
        self.web = False
        self.playlist(items=["2", "4"])
        info = rotation.status("eDP-1", now=5)
        self.assertEqual((info["playable"], info["next"]), (0, None))

    def test_status_of_unknown_screen_is_empty(self):
        info = rotation.status("HDMI-9", now=5)
        self.assertEqual((info["items"], info["enabled"], info["current"]), (0, False, None))

    def test_step_forward_and_back_even_if_disabled(self):
        self.playlist(enabled=False, items=["1", "3", "5"], current_index=1)
        self.assertEqual(rotation.step("eDP-1", 1, now=500, apply_fn=self.apply), (True, "5"))
        self.assertEqual((self.state()["current_index"], self.state()["last_switch"]), (2, 500))
        self.assertEqual(rotation.step("eDP-1", -1, now=600, apply_fn=self.apply), (True, "3"))
        self.assertEqual(rotation.step("eDP-1", -1, now=700, apply_fn=self.apply), (True, "1"))
        self.assertEqual(rotation.step("eDP-1", -1, now=800, apply_fn=self.apply), (True, "5"))  # da la vuelta

    def test_step_skips_unplayable_and_reports_failures(self):
        self.web = False
        self.playlist(items=["2", "1"], current_index=1)
        self.assertEqual(rotation.step("eDP-1", 1, apply_fn=self.apply), (True, "1"))
        self.assertFalse(rotation.step("eDP-1", 1, apply_fn=lambda s, w: False)[0])
        self.playlist(items=["2", "4"])
        ok, message = rotation.step("eDP-1", 1, apply_fn=self.apply)
        self.assertFalse(ok)
        self.assertIn("puede rotar", message)
        self.playlist(items=[])
        self.assertFalse(rotation.step("eDP-1", 1, apply_fn=self.apply)[0])

    def test_playlist_problems_explain_each_skipped_item(self):
        self.web = False
        problems = selection.playlist_problems(["1", "2", "4", "999"])
        self.assertEqual(sorted(problems), ["2", "4", "999"])
        self.assertIn("web", problems["2"])
        self.assertIn("preset", problems["4"])
        self.assertIn("instalado", problems["999"])


if __name__ == "__main__":
    unittest.main()
