import http.server
import io
import os
import sys
import tempfile
import threading
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from wpelib import steam_api  # noqa: E402


def _png(size=(10, 10)):
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 0, 0)).save(buf, "PNG")
    return buf.getvalue()


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"x" * (steam_api.MAX_THUMB_BYTES + 10) if self.path == "/big" else _png()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class ThumbTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def test_ok(self):
        path = steam_api.download_workshop_thumb("t_ok", self.base + "/ok")
        self.assertTrue(path and os.path.isfile(path))
        self.assertEqual(Image.open(path).size, steam_api.THUMB_SIZE)

    def test_too_big_rejected_without_leftovers(self):
        self.assertIsNone(steam_api.download_workshop_thumb("t_big", self.base + "/big"))
        self.assertFalse(os.path.exists(os.path.join(steam_api.WORKSHOP_THUMB_CACHE, "t_big.png.tmp")))

    def test_non_http_scheme_rejected(self):
        self.assertIsNone(steam_api.download_workshop_thumb("t_file", "file:///etc/passwd"))


if __name__ == "__main__":
    unittest.main()
