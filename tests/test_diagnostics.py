import os
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import config, diagnostics  # noqa: E402


class DiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = {n: getattr(config, n) for n in ("CONF_DIR", "CURRENT_FILE", "KNOWN_BAD_FILE", "PLAYLISTS_FILE",
                                                     "PLAYLISTS_LOCK", "load_wallpapers", "load_hidden_ids",
                                                     "load_known_bad", "web_wallpapers_allowed")}
        config.CONF_DIR = self.tmp
        config.CURRENT_FILE = os.path.join(self.tmp, "current.json")
        config.KNOWN_BAD_FILE = os.path.join(self.tmp, "known_bad.json")
        config.PLAYLISTS_FILE = os.path.join(self.tmp, "playlists.json")
        config.PLAYLISTS_LOCK = os.path.join(self.tmp, "playlists.lock")
        config.load_wallpapers = lambda: [{"id": "1", "title": "Uno", "type": "Scene"}, {"id": "2", "title": "Dos", "type": "Scene"}]
        config.load_hidden_ids = lambda: set()
        config.load_known_bad = lambda: {}
        config.web_wallpapers_allowed = lambda: False

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(config, name, value)

    def write(self, name, data):
        config.atomic_write_json(os.path.join(self.tmp, name), data)

    def test_empty_config_still_produces_a_report(self):
        report = diagnostics.build_report()
        self.assertIn("Informe de Elegir Fondo", report)
        self.assertIn("== Fallos conocidos (0) ==", report)

    def test_report_lists_screens_failures_and_hides_the_home_dir(self):
        home = os.path.expanduser("~")
        self.write("current.json", {"eDP-1": "1"})
        self.write("last_good.json", {"eDP-1": "2"})
        self.write("status_eDP-1.json", {"id": "1", "state": "failed", "detail": f"crash en {home}/x/y", "token": "t"})
        self.write("known_bad.json", {"1": {"detected_at": "2026-10-18T10:00:00", "returncode": -11, "detail": f"boom {home}/z"}})
        with open(os.path.join(self.tmp, "wallpaperengine_eDP-1.log"), "w") as f:
            f.write("\n".join(f"linea {i} {home}/a" for i in range(60)))
        report = diagnostics.build_report()
        self.assertIn("eDP-1: asignado Uno (1)", report)
        self.assertIn("ultimo que funcionaba: Dos (2)", report)
        self.assertIn("ultimo estado: failed", report)
        self.assertIn("codigo -11", report)
        self.assertIn("linea 59", report)
        self.assertNotIn("linea 10 ", report)  # solo las ultimas lineas
        self.assertNotIn(home, report)
        self.assertIn("~/x/y", report)

    def test_many_known_bad_are_summarised(self):
        self.write("known_bad.json", {str(n): {"detected_at": f"2026-10-18T10:{n:02d}:00", "detail": "x"} for n in range(20)})
        report = diagnostics.build_report()
        self.assertIn("== Fallos conocidos (20) ==", report)
        self.assertIn("... y 12 mas", report)


if __name__ == "__main__":
    unittest.main()
