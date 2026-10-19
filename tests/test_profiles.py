import os
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import apply, config, profiles  # noqa: E402

NAMES = ("CONF_DIR", "CURRENT_FILE", "CONFIG_FILE", "AUDIO_FILE", "SCALING_FILE", "SPEED_FILE", "PLAYLISTS_FILE", "PLAYLISTS_LOCK")


class ProfilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = {n: getattr(config, n) for n in NAMES}
        config.CONF_DIR = self.tmp
        for attr, name in (("CURRENT_FILE", "current.json"), ("CONFIG_FILE", "config.json"), ("AUDIO_FILE", "audio.json"),
                           ("SCALING_FILE", "scaling.json"), ("SPEED_FILE", "speed.json"),
                           ("PLAYLISTS_FILE", "playlists.json"), ("PLAYLISTS_LOCK", "playlists.lock")):
            setattr(config, attr, os.path.join(self.tmp, name))
        self.monitors = ["eDP-1", "HDMI-A-1"]
        self.ids = {"1", "2", "3"}

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(config, name, value)

    def write(self, name, data):
        config.atomic_write_json(os.path.join(self.tmp, name), data)

    def read(self, name):
        return config.load_json(os.path.join(self.tmp, name), {})

    def scenario(self):
        self.write("current.json", {"eDP-1": "1", "HDMI-A-1": "2", "DP-9": "3"})
        self.write("audio.json", {"eDP-1": {"muted": False, "volume": 80}, "DP-9": {"muted": True, "volume": 1}})
        self.write("scaling.json", {"eDP-1": "fit"})
        self.write("speed.json", {"eDP-1": 0.5})
        self.write("playlists.json", {"eDP-1": {"enabled": True, "interval_minutes": 5, "mode": "random",
                                                "items": ["1", "2", "3"], "current_index": 0, "last_switch": 5,
                                                "history": ["1"], "bag": ["2"]}})
        config.set_fps(15)

    def test_capture_only_includes_the_given_screens_and_no_item_lists(self):
        self.scenario()
        data = profiles.capture(self.monitors)
        self.assertEqual(data["assignments"], {"eDP-1": "1", "HDMI-A-1": "2"})   # sin DP-9
        self.assertEqual(data["audio"], {"eDP-1": {"muted": False, "volume": 80}})
        self.assertEqual((data["scaling"], data["speed"], data["fps"]), ({"eDP-1": "fit"}, {"eDP-1": 0.5}, 15))
        self.assertEqual(data["rotation"], {"eDP-1": {"enabled": True, "interval_minutes": 5, "mode": "random"}})

    def test_names_are_validated_and_saved_profiles_listed_and_deleted(self):
        self.scenario()
        self.assertEqual(profiles.save_profile("  Modo   trabajo ", self.monitors), "Modo trabajo")
        self.assertIn("Modo trabajo", profiles.load_profiles())
        for bad in ("", "   ", "x" * 41, None):
            with self.assertRaises(ValueError):
                profiles.clean_name(bad)
        self.assertTrue(profiles.delete_profile("Modo trabajo"))
        self.assertFalse(profiles.delete_profile("Modo trabajo"))

    def test_apply_restores_settings_assignments_and_rotation(self):
        self.scenario()
        profiles.save_profile("Trabajo", self.monitors)
        # cambiamos todo
        self.write("current.json", {"eDP-1": "3", "HDMI-A-1": "3"})
        self.write("audio.json", {"eDP-1": {"muted": True, "volume": 0}, "DP-9": {"muted": True, "volume": 1}})
        self.write("scaling.json", {"eDP-1": "fill"})
        self.write("speed.json", {"eDP-1": 2})
        self.write("playlists.json", {"eDP-1": {"enabled": False, "interval_minutes": 60, "mode": "order",
                                                "items": ["3", "2", "1"], "current_index": 0, "last_switch": 0}})
        config.set_fps(60)
        launched = []
        ok, screens, notes = profiles.apply_profile("Trabajo", self.monitors, self.ids, launched.append, now=1000)
        self.assertEqual((ok, notes), (True, []))
        self.assertEqual(launched, [[("eDP-1", "1"), ("HDMI-A-1", "2")]])
        self.assertEqual(self.read("audio.json")["eDP-1"], {"muted": False, "volume": 80})
        self.assertEqual(self.read("audio.json")["DP-9"], {"muted": True, "volume": 1})   # otras pantallas intactas
        self.assertEqual((self.read("scaling.json")["eDP-1"], self.read("speed.json")["eDP-1"]), ("fit", 0.5))
        self.assertEqual(config.load_fps(), 15)
        rotation = self.read("playlists.json")["eDP-1"]
        self.assertEqual((rotation["enabled"], rotation["interval_minutes"], rotation["mode"]), (True, 5, "random"))
        self.assertEqual(rotation["items"], ["3", "2", "1"])        # las listas actuales se conservan
        self.assertEqual((rotation["current_index"], rotation["last_switch"]), (2, 1000))  # "1" está en la posición 2

    def test_missing_wallpaper_and_missing_profile(self):
        self.scenario()
        profiles.save_profile("P", self.monitors)
        launched = []
        ok, screens, notes = profiles.apply_profile("P", self.monitors, {"1"}, launched.append)
        self.assertTrue(ok)
        self.assertEqual((screens, launched), (["eDP-1"], [[("eDP-1", "1")]]))
        self.assertIn("2", notes[0])
        ok, _, notes = profiles.apply_profile("nope", self.monitors, self.ids, launched.append)
        self.assertFalse(ok)

    def test_screens_not_connected_are_skipped(self):
        self.scenario()
        profiles.save_profile("P", self.monitors)
        launched = []
        profiles.apply_profile("P", ["eDP-1"], self.ids, launched.append)
        self.assertEqual(launched, [[("eDP-1", "1")]])

    def test_fps_setting_is_validated_and_used_by_the_engine_command(self):
        with self.assertRaises(ValueError):
            config.set_fps(45)
        config.set_fps(24)
        cmd = apply.engine_command("eDP-1", "1")
        self.assertEqual(cmd[cmd.index("--fps") + 1], "24")
        self.write("config.json", {"fps": 7})
        self.assertEqual(config.load_fps(), 30)


if __name__ == "__main__":
    unittest.main()
