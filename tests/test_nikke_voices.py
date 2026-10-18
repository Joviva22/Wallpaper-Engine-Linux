import io
import os
import struct
import sys
import unittest
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_nikke_stage import StageBase  # noqa: E402

from wpelib import nikke_stage, nikke_voices  # noqa: E402
from wpelib.l2d_pack import PackError  # noqa: E402


def make_zip(files, compress=True):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


class VoicesTest(StageBase):
    FILES = {"jp/": b"", "jp/c010/": b"", "jp/c010/c010_Lobby_Touch_1.wav": b"RIFF" + b"a" * 5000,
             "jp/c010/c010_Win_1.wav": b"RIFF" + b"b" * 3000, "jp/c010/notes.txt": b"x",
             "jp/c010/../evil.wav": b"zzz", "jp/c800/c800_Win_1.wav": b"RIFF"}

    def setUp(self):
        super().setUp()
        self.blob = make_zip(self.FILES)
        self.calls = []
        self._range = nikke_voices._range
        nikke_voices._range = self.fake_range

    def tearDown(self):
        nikke_voices._range = self._range
        super().tearDown()

    def fake_range(self, url, start, end, timeout=60):
        self.calls.append((start, end))
        total = len(self.blob)
        return self.blob[start:end + 1], f"bytes {start}-{min(end, total - 1)}/{total}"

    def test_lists_only_valid_voice_files_of_the_character(self):
        names = [e[0] for e in nikke_voices.files_for("jp", "c010")]
        self.assertEqual(names, ["jp/c010/c010_Lobby_Touch_1.wav", "jp/c010/c010_Win_1.wav"])

    def test_downloads_only_that_character_and_updates_the_manifest(self):
        saved = nikke_voices.download_voices("c010", "jp")
        self.assertEqual(saved, ["c010_Lobby_Touch_1.wav", "c010_Win_1.wav"])
        folder = os.path.join(nikke_voices._voices_dir(), "jp", "c010")
        with open(os.path.join(folder, "c010_Win_1.wav"), "rb") as f:
            self.assertEqual(f.read(), b"RIFF" + b"b" * 3000)
        self.assertEqual(nikke_stage.read_manifest()["voices"]["jp"]["c010"], saved)
        self.assertFalse(os.path.exists(os.path.join(nikke_voices._voices_dir(), "jp", "c800")))
        self.assertFalse(os.path.exists(os.path.join(nikke_voices._voices_dir(), "evil.wav")))

    def test_rejects_bad_language_code_and_missing_character(self):
        with self.assertRaises(PackError):
            nikke_voices.read_central_directory("xx")
        with self.assertRaises(PackError):
            nikke_voices.download_voices("../c010", "jp")
        with self.assertRaises(PackError):
            nikke_voices.download_voices("c999", "jp")

    def test_remove_deletes_files_and_manifest_entry(self):
        nikke_voices.download_voices("c010", "jp")
        nikke_voices.remove_voices("c010")
        self.assertFalse(os.path.exists(os.path.join(nikke_voices._voices_dir(), "jp", "c010")))
        self.assertNotIn("c010", nikke_stage.read_manifest()["voices"]["jp"])

    def test_oversized_entry_is_refused(self):
        entry = ("jp/c010/c010_Big.wav", 0, 1, nikke_voices.MAX_FILE_BYTES + 1, 0)
        with self.assertRaises(PackError):
            nikke_voices._fetch_entry("jp", entry)


if __name__ == "__main__":
    unittest.main()
