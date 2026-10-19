"""Pruebas de humo de la interfaz: construye la ventana principal y abre cada diálogo auxiliar.

Se saltan si no hay pantalla (CI sin display). Usan un HOME temporal: no tocan tu configuración."""
import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ["HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

HAS_DISPLAY = Gtk.init_check()[0] if isinstance(Gtk.init_check(), tuple) else bool(Gtk.init_check())

if HAS_DISPLAY:
    from wpelib import dialogs, main_window  # noqa: E402


def open_dialog(call):
    """Ejecuta `call()` sin mostrar nada en pantalla y devuelve los diálogos que creó."""
    before = set(Gtk.Window.list_toplevels())
    with mock.patch.object(Gtk.Widget, "show_all"):
        call()
    return [w for w in Gtk.Window.list_toplevels() if w not in before]


def descendants(widget):
    yield widget
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            yield from descendants(child)


@unittest.skipUnless(HAS_DISPLAY, "sin pantalla")
class DialogsSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = main_window.PickerWindow()

    @classmethod
    def tearDownClass(cls):
        cls.window.destroy()

    def test_main_window_exposes_monitor_widgets_and_fps(self):
        self.assertTrue(self.window.monitors)
        self.assertEqual(self.window.fps_combo.get_active_id(), "30")
        self.assertEqual(set(self.window.monitor_chips), set(self.window.monitors))

    def test_non_modal_dialogs_open_and_show_their_texts(self):
        for opener, expected in ((dialogs.open_profiles, "Perfil"), (dialogs.open_repairs, "reparado"),
                                 (dialogs.open_diagnostics, "Informe de Elegir Fondo")):
            dialogs_opened = open_dialog(lambda: opener(self.window))
            self.assertEqual(len(dialogs_opened), 1, opener.__name__)
            dialog = dialogs_opened[0]
            texts = []
            for widget in descendants(dialog):
                if isinstance(widget, Gtk.Label):
                    texts.append(widget.get_text())
                elif isinstance(widget, Gtk.TextView):
                    buffer = widget.get_buffer()
                    texts.append(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False))
            self.assertTrue(any(expected.lower() in t.lower() for t in texts), (opener.__name__, texts[:5]))
            dialog.destroy()

    def test_pin_entry_only_accepts_four_digits(self):
        entry = dialogs.make_pin_entry(self.window)
        entry.set_text("a1b2c3d4e5")
        self.assertEqual(entry.get_text(), "1234")
        self.assertTrue(entry.get_visibility() is False)

    def test_cleanup_dialog_cancelled_changes_nothing(self):
        with mock.patch.object(Gtk.Dialog, "run", return_value=Gtk.ResponseType.CANCEL), \
                mock.patch.object(Gtk.Widget, "show_all"), \
                mock.patch.object(dialogs.cleanup, "clean") as clean:
            dialogs.open_cleanup(self.window)
        clean.assert_not_called()

    def test_failure_dialogs_do_not_crash(self):
        for call in (lambda: dialogs.show_rollback(self.window, "eDP-1", "Nuevo", "Anterior", "motivo"),
                     lambda: dialogs.show_preview_failure(self.window, "Fondo", "boom")):
            opened = open_dialog(call)
            self.assertEqual(len(opened), 1)
            opened[0].destroy()

    def test_monitor_hot_plug_rebuilds_selectors_and_keeps_playback_menu(self):
        window = self.window
        original = list(window.monitors)
        with mock.patch.object(main_window.subprocess, "Popen"):
            window._on_monitors_changed(original + ["DP-9"], ["DP-9"], [])
            self.assertEqual(set(window.monitor_chips), set(original + ["DP-9"]))
            window._on_monitors_changed(original, [], ["DP-9"])
        self.assertEqual(set(window.sidebar_monitor_radios), set(original))
        window._sync_scaling_combo()   # el menú "Reproducción" sigue vivo tras reconstruir


if __name__ == "__main__":
    unittest.main()
