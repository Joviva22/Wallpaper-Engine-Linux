import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("nikke_stage", os.path.join(ROOT, "scripts", "nikke-stage.py"))
stage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage)


def make_pack(code, version=b"4.0.47", extra=None):
    """Zip como los de nikke-wallpaper-packs: rutas con barras de Windows."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(f"{code}\\{code}_00.skel", b"\x00" * 8 + version + b"\x00" * 20)
        z.writestr(f"{code}\\{code}_00.atlas", "atlas")
        z.writestr(f"{code}\\{code}_00.png", b"png")
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


class StageBase(unittest.TestCase):
    def setUp(self):
        self._stdout, sys.stdout = sys.stdout, io.StringIO()
        self.tmp = tempfile.mkdtemp()
        self._env = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.tmp, "cfg")
        self.workshop = os.path.join(self.tmp, "ws")
        os.makedirs(self.workshop)
        # un wallpaper de Nikke con los reproductores Spine, como el que exige el instalador
        donor = os.path.join(self.workshop, "111")
        os.makedirs(donor)
        for name in stage.RUNTIME_FILES:
            with open(os.path.join(donor, name), "w") as f:
                f.write("// runtime")
        self._saved = (stage.workshop_dir, stage.l2d_index, stage.slotlib.download)
        stage.workshop_dir = lambda: self.workshop
        stage.l2d_index = lambda: {"c010": {"id": "c010", "name": "Rapi"},
                                   "c800": {"id": "c800", "name": "Makima"},
                                   "c800_01": {"id": "c800_01", "name": "Makima Coat Off"},
                                   "smol_rapi": {"id": "smol_rapi", "name": "Smol Rapi"}}

    def tearDown(self):
        sys.stdout = self._stdout
        stage.workshop_dir, stage.l2d_index, stage.slotlib.download = self._saved
        if self._env is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._env


class ResolveTest(StageBase):
    def test_codes_names_and_ambiguity(self):
        index = stage.l2d_index()
        self.assertEqual(stage.resolve("c010", index), "c010")
        self.assertEqual(stage.resolve("rapi", index), "c010")
        self.assertEqual(stage.resolve("Makima Coat Off", index), "c800_01")
        with self.assertRaises(SystemExit):
            stage.resolve("maki", index)  # coincide con varios
        with self.assertRaises(SystemExit):
            stage.resolve("nadie", index)


class InstallTest(StageBase):
    def test_add_installs_characters_manifest_and_project(self):
        packs = {"c010": make_pack("c010"), "c195": make_pack("c195", version=b"4.1.20")}
        stage.slotlib.download = lambda code: packs[code]
        stage.add(["c010", "c195"])

        manifest = stage.read_manifest()
        self.assertEqual(manifest["characters"]["c010"], {"name": "Rapi", "version": "4.0"})
        self.assertEqual(manifest["characters"]["c195"]["version"], "4.1")  # detectada en el .skel
        chars = os.path.join(stage.config_files(), "characters")
        self.assertTrue(os.path.isfile(os.path.join(chars, "c010", "c010_00.skel")))

        project_dir = os.path.join(self.workshop, stage.WALLPAPER_ID)
        with open(os.path.join(project_dir, "project.json"), encoding="utf-8") as f:
            project = json.load(f)
        props = project["general"]["properties"]
        self.assertEqual(project["type"], "web")
        self.assertTrue(project["general"]["supportsaudioprocessing"])
        self.assertEqual([o["value"] for o in props["char1"]["options"]], ["none", "c010", "c195"])
        self.assertEqual(props["char1"]["value"], "c010")
        self.assertEqual(props["char3"]["value"], "none")  # solo hay dos personajes instalados
        self.assertEqual(props["flip1"]["type"], "bool")
        for i in range(1, 5):
            for key in ("char", "x", "scale", "y", "flip"):
                self.assertIn(f"{key}{i}", props)
        for name in ("index.html", "stage.js", "style.css") + stage.RUNTIME_FILES:
            self.assertTrue(os.path.isfile(os.path.join(project_dir, name)), name)

    def test_remove_updates_manifest_and_files(self):
        stage.slotlib.download = lambda code: make_pack(code)
        stage.add(["c010", "c800"])
        stage.remove(["c800"])
        self.assertEqual(list(stage.read_manifest()["characters"]), ["c010"])
        self.assertFalse(os.path.exists(os.path.join(stage.config_files(), "characters", "c800")))

    def test_unsafe_or_incomplete_packs_are_rejected(self):
        bad = {
            "traversal": make_pack("c010", extra={"c010\\..\\evil.png": b"x"}),
            "wrongext": make_pack("c010", extra={"c010\\run.sh": b"#!/bin/sh"}),
            "otherdir": make_pack("c010", extra={"other\\x.png": b"x"}),
        }
        for name, data in bad.items():
            stage.slotlib.download = lambda code, data=data: data
            with self.assertRaises(SystemExit, msg=name):
                stage.add(["c010"])
        self.assertEqual(stage.read_manifest()["characters"], {})

    def test_missing_runtime_is_explained(self):
        for name in stage.RUNTIME_FILES:
            os.remove(os.path.join(self.workshop, "111", name))
        with self.assertRaises(SystemExit) as ctx:
            stage.install_wallpaper()
        self.assertIn("Nikke", str(ctx.exception))


class SkeletonVersionTest(StageBase):
    def test_versions(self):
        for code, header, expected in (("c1", b"4.1.20", "4.1"), ("c2", b"4.0.47", "4.0"), ("c3", b"3.8.99", "4.0")):
            folder = os.path.join(stage.config_files(), "characters", code)
            os.makedirs(folder)
            with open(os.path.join(folder, f"{code}_00.skel"), "wb") as f:
                f.write(b"\x01\x02\x03\x04\x05\x06\x07\x08" + header + b"\x00")
            self.assertEqual(stage.skeleton_version(code), expected)
        self.assertEqual(stage.skeleton_version("missing"), "4.0")


if __name__ == "__main__":
    unittest.main()
