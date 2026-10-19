import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wpelib import config  # noqa: E402


class MonitorTest(unittest.TestCase):
    def test_changes_keep_order_and_ignore_unchanged(self):
        self.assertEqual(config.monitor_changes(["A", "B"], ["A", "B"]), ([], []))
        self.assertEqual(config.monitor_changes(["A"], ["A", "B", "C"]), (["B", "C"], []))
        self.assertEqual(config.monitor_changes(["A", "B"], ["B"]), ([], ["A"]))
        self.assertEqual(config.monitor_changes(["A", "B"], ["C", "A"]), (["C"], ["B"]))

    def test_detect_monitors_parses_xrandr_and_tolerates_failure(self):
        out = "Monitors: 2\n 0: +*eDP-1 1920/344x1200/215+0+0  eDP-1\n 1: +HDMI-A-1 1920/527x1080/296+1920+0  HDMI-A-1\n"
        with mock.patch.object(config.subprocess, "check_output", return_value=out):
            self.assertEqual(config.detect_monitors(), ["eDP-1", "HDMI-A-1"])
        with mock.patch.object(config.subprocess, "check_output", side_effect=OSError):
            self.assertEqual(config.detect_monitors(), [])


if __name__ == "__main__":
    unittest.main()
