"""El permiso de web cubre CLI, vigilante y presets sin marcar el fondo como roto."""
import os
import types
from unittest.mock import patch, Mock
from tests.test_apply import Base
from wpelib import apply, config
from wpelib.main_window import PickerWindow


class WebPermissionTest(Base):
    def project(self, wid, data):
        config.atomic_write_json(os.path.join(config.WORKSHOP_DIR, wid, 'project.json'), data)

    def test_web_blocked_by_default_without_engine_or_known_bad_changes(self):
        self.project('123', {'type': 'web', 'file': 'index.html'})
        config.atomic_write_json(config.KNOWN_BAD_FILE, {'456': {'screen': 'A'}})
        with patch('wpelib.apply._detach_and_run') as launch:
            self.assertEqual(apply.main(['eDP-1=123']), 1)
            launch.assert_not_called()
        self.assertEqual(config.load_known_bad(), {'456': {'screen': 'A'}})
        self.assertFalse(os.path.exists(self.engine_log))

    def test_direct_watchdog_cannot_bypass_permission(self):
        self.project('123', {'type': 'Web'})
        apply.restart_screen('eDP-1', '123')
        self.assertFalse(os.path.exists(self.engine_log))
        self.assertEqual(config.load_known_bad(), {})

    def test_web_allowed_after_explicit_opt_in(self):
        self.project('123', {'type': 'web'})
        config.set_web_wallpapers_allowed(True)
        with patch('wpelib.apply._detach_and_run', return_value=(True, '')) as launch:
            self.assertEqual(apply.main(['eDP-1=123']), 0)
            launch.assert_called_once_with('eDP-1', '123')

    def test_scene_and_video_do_not_need_permission(self):
        for kind in ['Scene', 'Video']:
            self.project('123', {'type': kind})
            with patch('wpelib.apply._detach_and_run', return_value=(True, '')) as launch:
                self.assertEqual(apply.main(['eDP-1=123']), 0)
                launch.assert_called_once()

    def test_web_preset_is_also_blocked(self):
        self.project('456', {'type': 'web'})
        self.project('123', {'dependency': '456', 'preset': {}})
        self.assertEqual(apply.project_type('123'), 'web')
        with patch('wpelib.apply._detach_and_run') as launch:
            self.assertEqual(apply.main(['eDP-1=123']), 1)
            launch.assert_not_called()

    def test_permission_requires_literal_true_and_can_be_revoked(self):
        config.atomic_write_json(config.CONFIG_FILE, {'steam_library': self.tmp, 'allow_web': 'true', 'steam_api_key': 'test-value'})
        self.assertFalse(config.web_wallpapers_allowed())
        config.set_web_wallpapers_allowed(True)
        self.assertTrue(config.web_wallpapers_allowed())
        self.assertEqual(config.load_json(config.CONFIG_FILE, {})['steam_api_key'], 'test-value')
        config.set_web_wallpapers_allowed(False)
        self.assertFalse(config.web_wallpapers_allowed())

    def test_gui_cancel_does_not_enable_web(self):
        self.project('123', {'type': 'web'})
        window = types.SimpleNamespace(_ask_web_permission=Mock(return_value=False), status_label=Mock())
        self.assertFalse(PickerWindow._allow_web_for(window, '123'))
        self.assertFalse(config.web_wallpapers_allowed())

    def test_gui_explicit_confirmation_enables_web(self):
        self.project('123', {'type': 'web'})
        window = types.SimpleNamespace(_ask_web_permission=Mock(return_value=True), status_label=Mock())
        self.assertTrue(PickerWindow._allow_web_for(window, '123'))
        self.assertTrue(config.web_wallpapers_allowed())
