import os
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import classify, config  # noqa: E402
from wpelib.classify import classify_project as cp  # noqa: E402


class TypeTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(classify.normalize_type(" SCENE "), "Scene")
        self.assertEqual(classify.normalize_type("video"), "Video")
        for bad in (None, 5, "", "  ", []):
            self.assertEqual(classify.normalize_type(bad), "")

    def test_declared_wins_then_inferred(self):
        self.assertEqual(cp("1", {"type": "web"})["type"], "Web")
        self.assertEqual(cp("1", {"file": "movie.MP4"})["type"], "Video")
        self.assertEqual(cp("1", {"file": "index.html"})["type"], "Web")
        self.assertEqual(cp("1", {"file": "scene.json"})["type"], "Scene")
        self.assertEqual(cp("1", {}, ["scene.pkg"])["type"], "Scene")
        self.assertEqual(cp("1", {}, ["x.txt"])["type"], "Desconocido")


class RatingTest(unittest.TestCase):
    def test_case_insensitive(self):
        self.assertEqual(cp("1", {"contentrating": "mature"})["rating"], "Mature")
        self.assertEqual(cp("1", {"contentrating": " EVERYONE "})["rating"], "Everyone")

    def test_inferred_from_sex_violence(self):
        self.assertEqual(cp("1", {"ratingsex": "adult"})["rating"], "Mature")
        self.assertEqual(cp("1", {"ratingsex": "mild"})["rating"], "Questionable")
        self.assertEqual(cp("1", {"ratingsex": "none", "ratingviolence": "included"})["rating"], "Questionable")
        self.assertEqual(cp("1", {"ratingsex": "none", "ratingviolence": "none"})["rating"], "Everyone")
        self.assertEqual(cp("1", {})["rating"], "Desconocido")

    def test_declared_beats_inferred(self):
        self.assertEqual(cp("1", {"contentrating": "Everyone", "ratingsex": "adult"})["rating"], "Everyone")


class TagsTest(unittest.TestCase):
    def test_dedupe_case_and_canonical(self):
        self.assertEqual(classify.normalize_tags(["anime", "Anime", " pixel art ", "", None, 3, "Custom"]),
                         ["Anime", "Pixel art", "Custom"])

    def test_string_and_garbage(self):
        self.assertEqual(classify.normalize_tags("game"), ["Game"])
        self.assertEqual(classify.normalize_tags({"a": 1}), [])
        self.assertEqual(classify.normalize_tags(None), [])


class RobustnessTest(unittest.TestCase):
    def test_bad_fields_do_not_raise(self):
        r = cp("42", {"title": 123, "preview": ["x"], "tags": 7, "type": 9, "contentrating": {}})
        self.assertEqual((r["title"], r["preview"], r["tags"], r["type"], r["rating"]),
                         ("42", "", [], "Desconocido", "Desconocido"))

    def test_non_dict_project(self):
        self.assertEqual(cp("9", ["not", "a", "dict"])["title"], "9")


class PresetTest(unittest.TestCase):
    PARENT = {"type": "scene", "contentrating": "Questionable", "tags": ["Pixel art"], "title": "Base"}

    def resolve(self, wid):
        return {"100": (self.PARENT, ["scene.pkg"])}.get(wid)

    def test_inherits_from_dependency(self):
        r = cp("1", {"dependency": "100", "preset": {"a": 1}, "title": "Mine"}, resolve=self.resolve)
        self.assertTrue(r["preset"])
        self.assertEqual((r["type"], r["rating"], r["tags"], r["title"]), ("Scene", "Questionable", ["Pixel art"], "Mine"))

    def test_own_values_win(self):
        r = cp("1", {"dependency": "100", "preset": {}, "contentrating": "Everyone", "tags": ["Game"]},
               resolve=self.resolve)
        self.assertEqual((r["rating"], r["tags"]), ("Everyone", ["Game"]))

    def test_missing_dependency_and_int_id(self):
        r = cp("1", {"dependency": 999, "preset": {}}, resolve=self.resolve)
        self.assertTrue(r["preset"])
        self.assertEqual(r["type"], "Desconocido")
        self.assertEqual(cp("1", {"dependency": 100, "preset": {}}, resolve=self.resolve)["type"], "Scene")

    def test_cycles_terminate(self):
        data = {"a": ({"dependency": "b", "preset": {}}, []), "b": ({"dependency": "a", "preset": {}}, [])}
        r = cp("a", data["a"][0], resolve=data.get)
        self.assertEqual(r["type"], "Desconocido")
        self.assertEqual(cp("s", {"dependency": "s", "preset": {}}, resolve=lambda w: ({}, []))["type"], "Desconocido")


class LoadWallpapersTest(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp()
        self._old = config.WORKSHOP_DIR
        config.WORKSHOP_DIR = self.ws

    def tearDown(self):
        config.WORKSHOP_DIR = self._old

    def project(self, wid, data, files=()):
        d = os.path.join(self.ws, wid)
        os.makedirs(d)
        if isinstance(data, str):
            with open(os.path.join(d, "project.json"), "w") as f:
                f.write(data)
        else:
            config.atomic_write_json(os.path.join(d, "project.json"), data)
        for f in files:
            with open(os.path.join(d, f), "w"):
                pass

    def test_bad_projects_do_not_break_catalog(self):
        self.project("1", {"title": 123, "type": "scene"})
        self.project("2", "{broken json")
        self.project("3", {"title": "ok", "type": "Video", "tags": ["anime"]}, ["preview.jpg"])
        items = {i["id"]: i for i in config.load_wallpapers()}
        self.assertEqual(set(items), {"1", "2", "3"})
        self.assertEqual(items["1"]["title"], "1")
        self.assertEqual(items["3"]["tags"], ["Anime"])
        self.assertTrue(items["3"]["preview_path"].endswith("preview.jpg"))  # sin `preview` declarado

    def test_preset_fields(self):
        self.project("100", {"title": "Base", "type": "web", "tags": ["Game"], "contentrating": "Mature"})
        self.project("101", {"dependency": "100", "preset": {}, "title": "P"})
        items = {i["id"]: i for i in config.load_wallpapers()}
        self.assertEqual((items["101"]["type"], items["101"]["rating"], items["101"]["preset"]),
                         ("Web", "Mature", True))
        self.assertFalse(items["100"]["preset"])


if __name__ == "__main__":
    unittest.main()
