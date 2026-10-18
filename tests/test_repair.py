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


class ProjectJsonTest(unittest.TestCase):
    def combo(self, **kw):
        return {"type": "combo", "text": "x", **kw}

    def test_fix_properties(self):
        data = {"general": {"properties": {
            "noval": self.combo(index=1, options=["a", "b"]),
            "nodictval": self.combo(index=0, options=[{"label": "L", "value": 7}]),
            "bool": self.combo(value=True, options=[{"label": "on", "value": True}, {"label": "off", "value": False}]),
            "ok": self.combo(value="cover", options=[{"label": "c", "value": "cover"}]),
            "slider": {"type": "slider", "value": "50", "min": "0", "max": 100},
            "slider_f": {"type": "slider", "value": "1.5"},
            "text": {"type": "text", "value": None},
        }}}
        n = repair._fix_project_properties(data)
        p = data["general"]["properties"]
        self.assertEqual(p["noval"]["value"], "b")
        self.assertEqual(p["nodictval"]["value"], "7")
        self.assertEqual(p["nodictval"]["options"][0]["value"], "7")
        self.assertEqual(p["bool"]["value"], "true")
        self.assertEqual([o["value"] for o in p["bool"]["options"]], ["true", "false"])
        self.assertEqual(p["ok"]["value"], "cover")
        self.assertEqual((p["slider"]["value"], p["slider"]["min"], p["slider"]["max"]), (50, 0, 100))
        self.assertEqual(p["slider_f"]["value"], 1.5)
        self.assertIsNone(p["text"]["value"])
        self.assertEqual(n, 9)
        self.assertEqual(repair._fix_project_properties(data), 0)  # idempotente

    def test_garbage_is_ignored(self):
        for data in ({}, [], {"general": []}, {"general": {"properties": {"a": 5}}},
                     {"general": {"properties": {"a": {"type": "combo", "options": "x", "index": "y"}}}}):
            self.assertEqual(repair._fix_project_properties(data), 0)

    def test_attempt_repair_rewrites_project_with_backup_and_respects_flag(self):
        d = tempfile.mkdtemp()
        old = repair.WORKSHOP_DIR
        repair.WORKSHOP_DIR = d
        try:
            os.mkdir(os.path.join(d, "9"))
            path = os.path.join(d, "9", "project.json")
            original = {"type": "web", "title": "T\u00edtulo \u5c45\u4e2d",
                        "general": {"properties": {"p": self.combo(value=True, options=[])}}}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(original, f)
            ok, _ = repair.attempt_repair("9", fix_project=False)
            self.assertFalse(ok)
            ok, msg = repair.attempt_repair("9")
            self.assertTrue(ok, msg)
            with open(path, encoding="utf-8") as f:
                fixed = json.load(f)
            self.assertEqual(fixed["general"]["properties"]["p"]["value"], "true")
            self.assertEqual(fixed["title"], original["title"])
            with open(path + ".bak_original", encoding="utf-8") as f:
                self.assertEqual(json.load(f), original)
            self.assertFalse(repair.attempt_repair("9")[0])  # ya reparado
        finally:
            repair.WORKSHOP_DIR = old


class LockTest(unittest.TestCase):
    def test_concurrent_repairs_are_serialized_and_intact(self):
        import threading
        d = tempfile.mkdtemp()
        old = repair.WORKSHOP_DIR
        repair.WORKSHOP_DIR = d
        try:
            os.mkdir(os.path.join(d, "1"))
            pkg = os.path.join(d, "1", "scene.pkg")
            scene = {"objects": [{"text": {}, "padding": "8.0 8.0"}]}
            build_pkg(pkg, {"scene.json": json.dumps(scene).encode(), "x.bin": b"\x00" * 1000})
            with open(pkg, "rb") as f:
                original = f.read()
            results = []
            threads = [threading.Thread(target=lambda: results.append(repair.attempt_repair("1"))) for _ in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(30)
            self.assertEqual(sum(1 for ok, _ in results if ok), 1)  # solo uno repara
            with open(pkg + ".bak_original", "rb") as f:
                self.assertEqual(f.read(), original)  # el backup es el original intacto
            _, _, raw = repair._unpack(pkg)
            self.assertEqual(raw["x.bin"], b"\x00" * 1000)
            self.assertEqual(sorted(os.listdir(os.path.join(d, "1"))), ["scene.pkg", "scene.pkg.bak_original"])
        finally:
            repair.WORKSHOP_DIR = old


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

    def test_audio_shader_repair_is_exact_backed_up_and_idempotent(self):
        import hashlib
        from unittest import mock
        raw = b"// fixture\n" * 69 + b"#endif\n" + b"void main() {}\n"
        files = {"scene.json": b'{"objects": []}',
                 repair._AUDIO_BARS_SHADER: raw, "unrelated.bin": b"\x00\xff"}
        build_pkg(self.pkg, files)
        with open(self.pkg, "rb") as f:
            original = f.read()
        with mock.patch.object(repair, "_AUDIO_BARS_BROKEN_SHA256", hashlib.sha256(raw).hexdigest()):
            ok, msg = repair.attempt_repair("1")
            self.assertTrue(ok, msg)
            self.assertIn("barras de audio", msg)
            self.assertFalse(repair.attempt_repair("1")[0])
        with open(self.pkg + ".bak_original", "rb") as f:
            self.assertEqual(f.read(), original)
        _, _, actual = repair._unpack(self.pkg)
        self.assertEqual(actual[repair._AUDIO_BARS_SHADER], b"// fixture\n" * 69 + b"void main() {}\n")
        self.assertEqual(actual["scene.json"], files["scene.json"])
        self.assertEqual(actual["unrelated.bin"], files["unrelated.bin"])

    def test_unknown_audio_shader_is_not_changed(self):
        files = {repair._AUDIO_BARS_SHADER: b"#endif\n"}
        before = dict(files)
        self.assertFalse(repair._fix_audio_bars_shader(files))
        self.assertEqual(files, before)

    def test_backup_failure_prevents_pkg_modification(self):
        from unittest import mock
        build_pkg(self.pkg, {"scene.json": b'{"objects": [{"text": {}, "padding": "8 8"}]}'})
        with open(self.pkg, "rb") as f:
            original = f.read()
        with mock.patch.object(repair, "_backup_once", side_effect=OSError("disk full")):
            ok, msg = repair.attempt_repair("1")
        self.assertFalse(ok)
        self.assertIn("copia original", msg)
        with open(self.pkg, "rb") as f:
            self.assertEqual(f.read(), original)

    def test_fragment_fixes_keep_varyings_and_texel_sizes(self):
        import hashlib
        from unittest import mock
        names = list(repair._KNOWN_FRAGMENT_HASHES)
        files = {
            names[0]: b"varying vec2 v_TexCoord;\nvoid main() {\nv_TexCoord.y = 1.0-v_TexCoord.y;\n}",
            names[1]: b"varying vec4 v_TexCoord;\nvec2 uv = v_TexCoord + vec2(v_TexCoord.z, v_TexCoord.w);",
            names[2]: b"varying vec2 v_TexCoord;\nvec2 fragPos = v_TexCoord;",
            names[3]: b"varying vec2 v_TexCoord;\nvoid helper() {v_TexCoord.x += 1.;}\nvoid main() {vec2 waveCoord = v_TexCoord; helper();}",
        }
        digests = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        with mock.patch.object(repair, "_KNOWN_FRAGMENT_HASHES", digests):
            self.assertEqual(len(repair._fix_known_fragment_shaders(files)), 4)
            self.assertEqual(repair._fix_known_fragment_shaders(files), [])
        self.assertIn(b"varying vec2 v_TexCoord;", files[names[0]])
        self.assertIn(b"audioCoord = v_TexCoord.xy;", files[names[0]])
        self.assertIn(b"audioCoord.y = 1.0-audioCoord.y;", files[names[0]])
        self.assertIn(b"v_TexCoord.xy + vec2(v_TexCoord.z, v_TexCoord.w)", files[names[1]])
        self.assertIn(b"vec2 fragPos = v_TexCoord.xy;", files[names[2]])
        self.assertIn(b"helper() {audioCoord.x += 1.;}", files[names[3]])
        self.assertIn(b"float waveCoord = 0.0;", files[names[3]])

    def test_unknown_fragment_versions_are_untouched(self):
        files = {name: b"void main() {}" for name in repair._KNOWN_FRAGMENT_HASHES}
        before = dict(files)
        self.assertEqual(repair._fix_known_fragment_shaders(files), [])
        self.assertEqual(files, before)

    def test_no_pkg(self):
        os.remove(self.pkg) if os.path.exists(self.pkg) else None
        ok, _ = repair.attempt_repair("1")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
