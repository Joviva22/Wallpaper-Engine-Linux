import os
import signal
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest

os.environ["HOME"] = tempfile.mkdtemp()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from wpelib import apply, config  # noqa: E402


def wait_for(cond, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def kill_pidfiles(conf_dir):
    """Termina los motores falsos que hayan quedado vivos (sin pkill -f, que podria
    alcanzar procesos ajenos)."""
    for name in os.listdir(conf_dir):
        if name.startswith("pid_") and name.endswith(".pid"):
            pid = apply._read_pid(os.path.join(conf_dir, name))
            if pid and apply._is_engine(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass


class Base(unittest.TestCase):
    """Aisla config en un directorio temporal y pone un 'linux-wallpaperengine' falso."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = {}
        old = config.CONF_DIR
        new = os.path.join(self.tmp, "conf")
        os.makedirs(new)
        for name in dir(config):
            val = getattr(config, name)
            if name.endswith("_FILE") and isinstance(val, str) and val.startswith(old):
                self.saved[name] = val
                setattr(config, name, new + val[len(old):])
        for name, val in (("CONF_DIR", new), ("WORKSHOP_DIR", os.path.join(self.tmp, "ws")),
                          ("ASSETS_DIR", os.path.join(self.tmp, "assets"))):
            self.saved[name] = getattr(config, name)
            setattr(config, name, val)
        os.makedirs(os.path.join(config.WORKSHOP_DIR, "123"))
        os.makedirs(os.path.join(config.WORKSHOP_DIR, "456"))

        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)
        self.engine_log = os.path.join(self.tmp, "engine_args.log")
        self.write_engine("sleep 30")
        self._path = os.environ["PATH"]
        os.environ["PATH"] = self.bindir + os.pathsep + self._path
        config._SPEED_SUPPORTED = None

    def tearDown(self):
        os.environ["PATH"] = self._path
        for name, val in self.saved.items():
            setattr(config, name, val)
        config._SPEED_SUPPORTED = None
        kill_pidfiles(config.CONF_DIR)

    def write_engine(self, body):
        path = os.path.join(self.bindir, "linux-wallpaperengine")
        with open(path, "w") as f:
            f.write(f'#!/bin/sh\nif [ "$1" = "--help" ]; then echo "Usage: x [--speed VAR]"; exit 0; fi\n'
                    f'echo "$@" >> {self.engine_log}\n{body}\n')
        os.chmod(path, 0o755)

    def known_bad(self):
        return config.load_known_bad()


class ArgsTest(Base):
    def test_defaults(self):
        cmd = apply.engine_command("eDP-1", "123")
        self.assertEqual(cmd[0], "linux-wallpaperengine")
        self.assertIn("--silent", cmd)
        self.assertNotIn("--volume", cmd)
        self.assertEqual(cmd[cmd.index("--scaling") + 1], "fill")
        self.assertEqual(cmd[cmd.index("--bg") + 1], os.path.join(config.WORKSHOP_DIR, "123"))
        self.assertNotIn("--speed", cmd)

    def test_audio_scaling_props_speed(self):
        config.save_audio({"eDP-1": {"muted": False, "volume": 70}})
        config.save_scaling({"eDP-1": "fit", "HDMI-A-1": "bogus"})
        config.save_properties({"123": {"a": "x y", "b": True, "c": 1.5, "d": 3}})
        config.save_speed({"eDP-1": 2.0})
        cmd = apply.engine_command("eDP-1", "123")
        self.assertEqual(cmd[cmd.index("--volume") + 1], "70")
        self.assertNotIn("--silent", cmd)
        self.assertEqual(cmd[cmd.index("--scaling") + 1], "fit")
        props = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--set-property"]
        self.assertEqual(props, ["a=x y", "b=true", "c=1.5", "d=3"])
        self.assertEqual(cmd[cmd.index("--speed") + 1], "2.0")
        self.assertEqual(apply.scaling_for("HDMI-A-1"), "fill")

    def test_speed_omitted_without_engine_support(self):
        config.save_speed({"eDP-1": 2.0})
        config._SPEED_SUPPORTED = False
        self.assertNotIn("--speed", apply.engine_command("eDP-1", "123"))

    def test_unmuted_false_is_not_collapsed(self):
        config.save_audio({"a": {"muted": False}, "b": {}})
        self.assertEqual(apply.audio_args("a"), ["--volume", "50"])
        self.assertEqual(apply.audio_args("b"), ["--silent"])


class ParseTest(Base):
    def test_valid(self):
        pairs, err = apply.parse_pairs(["eDP-1=123", "HDMI-A-1=456"])
        self.assertIsNone(err)
        self.assertEqual(pairs, [("eDP-1", "123"), ("HDMI-A-1", "456")])

    def test_invalid(self):
        for bad in ("nope", "=123", "eDP-1=", "eDP-1=../x", "a b=123", "eDP-1=999"):
            pairs, err = apply.parse_pairs([bad])
            self.assertIsNone(pairs, bad)
            self.assertTrue(err, bad)


class CrashClassificationTest(unittest.TestCase):
    def test_returncodes(self):
        self.assertTrue(apply.returncode_is_crash(-signal.SIGSEGV))
        self.assertTrue(apply.returncode_is_crash(139))
        self.assertTrue(apply.returncode_is_crash(-signal.SIGABRT))
        self.assertFalse(apply.returncode_is_crash(-signal.SIGTERM))
        self.assertFalse(apply.returncode_is_crash(143))
        self.assertFalse(apply.returncode_is_crash(0))
        self.assertFalse(apply.returncode_is_crash(1))

    def test_log_pattern_only_after_offset(self):
        path = os.path.join(tempfile.mkdtemp(), "l.log")
        with open(path, "w") as f:
            f.write("Segmentation fault\n")
        size = os.path.getsize(path)
        self.assertTrue(apply.log_has_crash(path, 0))
        self.assertFalse(apply.log_has_crash(path, size))
        with open(path, "a") as f:
            f.write("terminate called after throwing\n")
        self.assertTrue(apply.log_has_crash(path, size))


class WatcherTest(Base):
    def test_segfault_is_recorded_then_cleared(self):
        self.write_engine("kill -SEGV $$")
        apply.restart_screen("eDP-1", "123")
        self.assertIn("123", self.known_bad())
        self.assertEqual(self.known_bad()["123"]["screen"], "eDP-1")
        self.write_engine("exit 0")
        apply.restart_screen("eDP-1", "123")
        self.assertNotIn("123", self.known_bad())

    def test_log_pattern_crash(self):
        self.write_engine('echo "terminate called after throwing" >&2; exit 1')
        apply.restart_screen("eDP-1", "456")
        self.assertIn("456", self.known_bad())

    def test_replacement_is_not_a_crash(self):
        t = threading.Thread(target=apply.restart_screen, args=("eDP-1", "123"))
        t.start()
        self.assertTrue(wait_for(lambda: apply._read_pid(apply.pid_file("eDP-1"))))
        first = apply._read_pid(apply.pid_file("eDP-1"))
        # Segundo apply para la misma pantalla mientras el primero esta vivo.
        t2 = threading.Thread(target=apply.restart_screen, args=("eDP-1", "456"))
        t2.start()
        self.assertTrue(wait_for(lambda: apply._read_pid(apply.pid_file("eDP-1")) not in (None, first)))
        t.join(5)
        self.assertFalse(t.is_alive())
        self.assertFalse(apply._alive(first))
        self.assertEqual(self.known_bad(), {})
        second = apply._read_pid(apply.pid_file("eDP-1"))
        os.kill(second, signal.SIGTERM)
        t2.join(5)

    def test_stale_pid_of_other_process_is_not_killed(self):
        other = subprocess.Popen(["sleep", "30"])
        try:
            with open(apply.pid_file("eDP-1"), "w") as f:
                f.write(str(other.pid))
            self.write_engine("exit 0")
            apply.restart_screen("eDP-1", "123")
            self.assertIsNone(other.poll())
        finally:
            other.kill()
            other.wait()

    def test_log_rotation(self):
        with open(apply.log_file("eDP-1"), "wb") as f:
            f.write(b"x" * (apply.MAX_LOG_BYTES + 1))
        self.write_engine("exit 0")
        apply.restart_screen("eDP-1", "123")
        self.assertTrue(os.path.isfile(apply.log_file("eDP-1") + ".1"))
        self.assertLess(os.path.getsize(apply.log_file("eDP-1")), 1024)


class EndToEndTest(unittest.TestCase):
    def test_script_detaches_and_records(self):
        home = tempfile.mkdtemp()
        ws = os.path.join(home, ".local/share/Steam/steamapps/workshop/content/431960/123")
        os.makedirs(ws)
        bindir = os.path.join(home, "bin")
        os.makedirs(bindir)
        eng = os.path.join(bindir, "linux-wallpaperengine")
        with open(eng, "w") as f:
            f.write('#!/bin/sh\nif [ "$1" = "--help" ]; then exit 0; fi\nexec sleep 30\n')
        os.chmod(eng, 0o755)
        env = dict(os.environ, HOME=home, PATH=bindir + os.pathsep + os.environ["PATH"])
        script = os.path.join(ROOT, "bin", "wallpaperengine-apply")
        out = subprocess.run([script, "eDP-1=123"], env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(out.returncode, 0, out.stderr)
        conf = os.path.join(home, ".config/wallpaperengine-picker")
        pidfile = os.path.join(conf, "pid_eDP-1.pid")
        try:
            self.assertTrue(wait_for(lambda: apply._read_pid(pidfile)))
            pid = apply._read_pid(pidfile)
            self.assertTrue(apply._alive(pid))
            self.assertEqual(config.load_json(os.path.join(conf, "current.json"), {}), {"eDP-1": "123"})
            bad = subprocess.run([script, "eDP-1=../x"], env=env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
        finally:
            kill_pidfiles(conf)


if __name__ == "__main__":
    unittest.main()
