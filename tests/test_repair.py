import json
import os
import struct
import sys
import tempfile
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import repair  # noqa: E402


def build_pkg(path, files, header=b"PKGV0001"):
    names = list(files)
    out = bytearray(struct.pack("<I", len(header)) + header + struct.pack("<I", len(names)))
    off = 0
    for n in names:
        nb = n.encode()
        out += struct.pack("<I", len(nb)) + nb + struct.pack("<II", off, len(files[n]))
        off += len(files[n])
    for n in names:
        out += files[n]
    with open(path, "wb") as f:
        f.write(out)


class PkgTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pkg = os.path.join(self.dir, "scene.pkg")

    def test_unpack_repack_roundtrip(self):
        files = {"scene.json": b'{"objects": []}', "a/b.bin": b"\x00\x01\x02", "empty": b""}
        build_pkg(self.pkg, files)
        with open(self.pkg, "rb") as f:
            original = f.read()
        header, entries, raw = repair._unpack(self.pkg)
        self.assertEqual(header, b"PKGV0001")
        self.assertEqual(raw, files)
        repair._repack(self.pkg, header, entries, raw)
        with open(self.pkg, "rb") as f:
            self.assertEqual(f.read(), original)

    def test_repack_changed_size(self):
        build_pkg(self.pkg, {"scene.json": b"{}", "x": b"123"})
        header, entries, raw = repair._unpack(self.pkg)
        raw["scene.json"] = b'{"objects": [1, 2, 3]}'
        repair._repack(self.pkg, header, entries, raw)
        _, _, raw2 = repair._unpack(self.pkg)
        self.assertEqual(raw2, raw)


class AtomicRepackTest(unittest.TestCase):
    def test_failed_replace_keeps_original(self):
        from unittest import mock
        d = tempfile.mkdtemp()
        pkg = os.path.join(d, "scene.pkg")
        build_pkg(pkg, {"scene.json": b"{}"})
        with open(pkg, "rb") as f:
            before = f.read()
        header, entries, raw = repair._unpack(pkg)
        raw["scene.json"] = b'{"changed": true}'
        with mock.patch("os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                repair._repack(pkg, header, entries, raw)
        with open(pkg, "rb") as f:
            self.assertEqual(f.read(), before)
        self.assertEqual(os.listdir(d), ["scene.pkg"])


class RepairTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._old = repair.WORKSHOP_DIR
        repair.WORKSHOP_DIR = self.dir
        os.mkdir(os.path.join(self.dir, "1"))
        self.pkg = os.path.join(self.dir, "1", "scene.pkg")

    def tearDown(self):
        repair.WORKSHOP_DIR = self._old

    def test_fix_vector_padding(self):
        scene = {"objects": [{"text": {}, "padding": "32.00000 16.00000"}, {"text": {}, "padding": 5}]}
        self.assertEqual(repair._fix_vector_padding(scene), 1)
        self.assertEqual(scene["objects"][0]["padding"], 32.0)
        self.assertEqual(scene["objects"][1]["padding"], 5)

    def test_attempt_repair_fixes_and_backs_up(self):
        scene = {"objects": [{"text": {}, "padding": "8.0 8.0"}]}
        build_pkg(self.pkg, {"scene.json": json.dumps(scene).encode()})
        ok, msg = repair.attempt_repair("1")
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isfile(self.pkg + ".bak_original"))
        _, _, raw = repair._unpack(self.pkg)
        self.assertEqual(json.loads(raw["scene.json"])["objects"][0]["padding"], 8.0)
        ok2, _ = repair.attempt_repair("1")
        self.assertFalse(ok2)

    def test_nothing_to_repair_leaves_file_untouched(self):
        build_pkg(self.pkg, {"scene.json": b'{"objects": []}'})
        with open(self.pkg, "rb") as f:
            before = f.read()
        ok, _ = repair.attempt_repair("1")
        self.assertFalse(ok)
        with open(self.pkg, "rb") as f:
            self.assertEqual(f.read(), before)
        self.assertFalse(os.path.exists(self.pkg + ".bak_original"))

    def test_no_pkg(self):
        os.remove(self.pkg) if os.path.exists(self.pkg) else None
        ok, _ = repair.attempt_repair("1")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
