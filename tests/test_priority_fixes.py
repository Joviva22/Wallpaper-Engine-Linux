"""Regresiones de fallos de arranque, logs, selección y rotación."""
import json
import os
import signal
import tempfile
import threading
import unittest
from unittest.mock import patch

from tests.test_apply import Base, wait_for
from wpelib import apply, config, rotation, selection


class EngineFailuresTest(Base):
    def test_plain_exit_one_keeps_failure_and_detail(self):
        apply.record_result('eDP-1', '123', True)
        self.write_engine('echo "Combo property must have a value" >&2; exit 1')
        apply.restart_screen('eDP-1', '123', allow_repair=False)
        failure = self.known_bad()['123']
        self.assertEqual(failure['returncode'], 1)
        self.assertIn('Combo property', failure['detail'])
        state = config.load_json(apply._path('status_eDP-1.json'), {})
        self.assertEqual(state['state'], 'failed')

    def test_missing_executable_records_failure_and_does_not_assign(self):
        config.atomic_write_json(config.CURRENT_FILE, {'eDP-1': '456'})
        os.remove(os.path.join(self.bindir, 'linux-wallpaperengine'))
        with patch('wpelib.apply.engine_command', return_value=['/nonexistent/wpe-test-engine']):
            replies = []
            apply.restart_screen('eDP-1', '123', on_started=lambda *args: replies.append(args))
        self.assertIn('123', self.known_bad())
        self.assertFalse(replies[0][0])
        self.assertEqual(config.load_json(config.CURRENT_FILE, {})['eDP-1'], '456')

    def test_failed_start_does_not_save_requested_assignment(self):
        config.atomic_write_json(config.CURRENT_FILE, {'eDP-1': '456'})
        self.write_engine('echo "invalid property" >&2; exit 1')
        replies = []
        apply.restart_screen('eDP-1', '123', on_started=lambda *args: replies.append(args))
        self.assertFalse(replies[0][0])
        self.assertEqual(config.load_json(config.CURRENT_FILE, {})['eDP-1'], '456')

    def test_logs_rotate_while_alive_and_keep_early_crash_evidence(self):
        self.write_engine('echo "terminate called after throwing"; head -c 25000 /dev/zero; sleep 1; exit 0')
        with patch.object(apply, 'MAX_LOG_BYTES', 1024):
            worker = threading.Thread(target=apply.restart_screen, args=('eDP-1', '123'),
                                      kwargs={'allow_repair': False})
            worker.start()
            try:
                path = apply.log_file('eDP-1')
                self.assertTrue(wait_for(lambda: os.path.exists(path + '.1')))
                self.assertLessEqual(os.path.getsize(path), 1024)
                self.assertLessEqual(os.path.getsize(path + '.1'), 1024)
            finally:
                worker.join(5)
            self.assertFalse(worker.is_alive())
        self.assertIn('123', self.known_bad())

    def test_no_core_dumps_for_real_child(self):
        dest = os.path.join(self.tmp, 'core-limit')
        self.write_engine(f'ulimit -c > "{dest}"; exit 0')
        apply.restart_screen('eDP-1', '123')
        with open(dest) as stream:
            self.assertEqual(stream.read().strip(), '0')

    def test_cli_returns_failure_without_overwriting_assignment(self):
        config.atomic_write_json(config.CURRENT_FILE, {'eDP-1': '456'})
        self.write_engine('echo "invalid combo"; exit 1')
        self.assertEqual(apply.main(['eDP-1=123']), 1)
        self.assertEqual(config.load_json(config.CURRENT_FILE, {})['eDP-1'], '456')

    def test_repair_does_not_replace_newer_selection(self):
        self.write_engine('echo "type_error.302"; exit 1')
        def repair(*args):
            with open(apply.pid_file('eDP-1'), 'w') as stream:
                stream.write('987654321')
            return True
        with patch('wpelib.apply.try_auto_repair', side_effect=repair):
            apply.restart_screen('eDP-1', '123')
        with open(self.engine_log) as stream:
            self.assertEqual(len(stream.readlines()), 1)

    def test_speed_uses_selected_engine_and_rejects_invalid_values(self):
        with patch.object(config, 'engine_executable', return_value='/tmp/patched-wallpaperengine'), \
             patch.object(config, 'engine_supports_speed', return_value=True):
            config.save_speed({'eDP-1': 2.0})
            cmd = apply.engine_command('eDP-1', '123')
            self.assertEqual(cmd[0], '/tmp/patched-wallpaperengine')
            self.assertEqual(cmd[cmd.index('--speed') + 1], '2.0')
            for value in [float('nan'), float('inf'), -2, 0, 5, True]:
                config.save_speed({'eDP-1': value})
                self.assertEqual(apply.speed_args('eDP-1'), [])

    def test_closed_stdout_does_not_prevent_start_confirmation(self):
        self.write_engine('exec 1>&- 2>&-; sleep 1; exit 0')
        replies = []
        apply.restart_screen('eDP-1', '123', on_started=lambda *args: replies.append(args))
        self.assertTrue(replies[0][0])
        self.assertEqual(config.load_json(config.CURRENT_FILE, {})['eDP-1'], '123')


class SelectionTest(unittest.TestCase):
    def test_random_and_rotation_exclude_hidden_bad_web_and_presets(self):
        items = [
            {'id': '1', 'type': 'Scene'}, {'id': '2', 'type': 'Video'},
            {'id': '3', 'type': 'Scene'}, {'id': '4', 'type': 'Web'},
            {'id': '5', 'type': 'Desconocido'},
            {'id': '6', 'type': 'Scene', 'preset': True, 'dependency': '1'},
            {'id': '7', 'type': 'Scene', 'dependency': '3'},
            {'id': '8', 'type': 'Video'},
        ]
        with patch.object(config, 'load_wallpapers', return_value=items), \
             patch.object(config, 'load_hidden_ids', return_value={'1'}), \
             patch.object(config, 'load_known_bad', return_value={'3': {}}):
            self.assertEqual(selection.eligible_ids(), {'2', '8'})


class RotationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        folder = self.temp.name
        self.patches = [patch.object(config, 'CONF_DIR', folder),
                        patch.object(config, 'PLAYLISTS_FILE', os.path.join(folder, 'playlists.json')),
                        patch.object(config, 'PLAYLISTS_LOCK', os.path.join(folder, 'playlists.lock')),
                        patch('wpelib.rotation.eligible_ids', return_value={'1', '4'})]
        for p in self.patches: p.start()
        self.entry = {'enabled': True, 'items': ['1', '2', '3', '4'],
                      'current_index': 0, 'last_switch': 0, 'interval_minutes': 1}
        config.atomic_write_json(config.PLAYLISTS_FILE, {'A': self.entry})

    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.temp.cleanup()

    def test_skips_ineligible_entries_and_saves_original_index(self):
        calls = []
        rotation.tick(now=1000, apply_fn=lambda *args: calls.append(args) or True)
        self.assertEqual(calls, [('A', '4')])
        result = config.load_playlists()['A']
        self.assertEqual((result['current_index'], result['last_switch']), (3, 1000))

    def test_failed_apply_does_not_advance(self):
        rotation.tick(now=1000, apply_fn=lambda *args: False)
        self.assertEqual(config.load_playlists()['A'], self.entry)

    def test_no_eligible_entries_does_not_apply_or_advance(self):
        with patch('wpelib.rotation.eligible_ids', return_value=set()):
            apply_fn = unittest.mock.Mock()
            rotation.tick(now=1000, apply_fn=apply_fn)
            apply_fn.assert_not_called()
        self.assertEqual(config.load_playlists()['A'], self.entry)

    def test_paused_rotation_does_not_apply(self):
        with open(os.path.join(config.CONF_DIR, 'rotation_paused'), 'w'): pass
        apply_fn = unittest.mock.Mock()
        rotation.tick(now=1000, apply_fn=apply_fn)
        apply_fn.assert_not_called()

    def test_disabled_rotation_does_not_apply(self):
        self.entry['enabled'] = False
        config.atomic_write_json(config.PLAYLISTS_FILE, {'A': self.entry})
        apply_fn = unittest.mock.Mock()
        rotation.tick(now=1000, apply_fn=apply_fn)
        apply_fn.assert_not_called()
