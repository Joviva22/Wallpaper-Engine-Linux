import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_nikke_stage import StageBase  # noqa: E402

from wpelib import mitos  # noqa: E402


class MitosTest(StageBase):
    def test_install_creates_a_web_project_with_properties(self):
        target = mitos.install_wallpaper()
        self.assertEqual(os.path.basename(target), mitos.WALLPAPER_ID)
        for name in mitos.FILES:
            self.assertTrue(os.path.isfile(os.path.join(target, name)), name)
        with open(os.path.join(target, "project.json"), encoding="utf-8") as f:
            project = json.load(f)
        self.assertEqual((project["type"], project["file"]), ("web", "index.html"))
        props = project["general"]["properties"]
        self.assertEqual(props["scene"]["options"][0]["value"], "auto")
        self.assertEqual(sorted(p["order"] for p in props.values()), list(range(1, len(props) + 1)))

    def test_scene_options_match_the_script_scenes(self):
        with open(os.path.join(mitos.SOURCE_DIR, "mitos.js"), encoding="utf-8") as f:
            source = f.read()
        for option in mitos.SCENE_OPTIONS[1:]:
            self.assertIn(f"'{option['value']}'", source)

    def test_id_does_not_collide_with_nikke_stage(self):
        self.assertNotEqual(mitos.WALLPAPER_ID, mitos.nikke_stage.WALLPAPER_ID)


if __name__ == "__main__":
    unittest.main()
