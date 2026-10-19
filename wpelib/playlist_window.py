"""Ventana de rotacion (playlists) de wallpapers por pantalla."""
import subprocess
import threading
import time

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from .config import load_playlists, save_playlists, load_favorite_ids, APPLY_SCRIPT
from . import rotation, selection
from .ui import labeled_frame, icon_button

INTERVAL_PRESETS = [
    ("15 min", 15),
    ("30 min", 30),
    ("1 hora", 60),
    ("1 dia", 1440),
]

class PlaylistWindow(Gtk.Window):
    def __init__(self, monitors, all_items, on_saved=None):
        super().__init__(title="Rotacion de wallpapers")
        self.set_default_size(800, 560)
        self.set_border_width(12)
        self.monitors = monitors
        self.titles_by_id = {item["id"]: item["title"] for item in all_items}
        self.on_saved = on_saved
        self.playlists = load_playlists()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        top_frame = labeled_frame("Configuracion de la pantalla")
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        top_box.set_border_width(8)
        top_frame.add(top_box)

        top_box.pack_start(Gtk.Label(label="Pantalla:"), False, False, 0)
        self.monitor_combo = Gtk.ComboBoxText()
        for mon in monitors:
            self.monitor_combo.append_text(mon)
        self.monitor_combo.set_active(0)
        self.monitor_combo.connect("changed", self.on_monitor_changed)
        top_box.pack_start(self.monitor_combo, False, False, 0)

        self.enabled_check = Gtk.CheckButton(label="Activar rotacion en esta pantalla")
        top_box.pack_start(self.enabled_check, False, False, 0)

        top_box.pack_start(Gtk.Label(label="Intervalo (minutos):"), False, False, 0)
        adjustment = Gtk.Adjustment(value=30, lower=1, upper=1440, step_increment=1, page_increment=10)
        self.interval_spin = Gtk.SpinButton(adjustment=adjustment)
        top_box.pack_start(self.interval_spin, False, False, 0)

        for label, minutes in INTERVAL_PRESETS:
            preset_btn = Gtk.Button(label=label)
            preset_btn.connect("clicked", lambda _b, m=minutes: self.interval_spin.set_value(m))
            top_box.pack_start(preset_btn, False, False, 0)

        vbox.pack_start(top_frame, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.rotation_label = Gtk.Label(label="", xalign=0)
        self.rotation_label.set_line_wrap(True)
        status_box.pack_start(self.rotation_label, True, True, 0)
        prev_btn = icon_button("Anterior", "media-skip-backward-symbolic")
        prev_btn.set_tooltip_text("Aplicar ya el fondo anterior de la lista")
        prev_btn.connect("clicked", lambda _b: self.on_step_clicked(-1))
        status_box.pack_start(prev_btn, False, False, 0)
        next_btn = icon_button("Siguiente ahora", "media-skip-forward-symbolic")
        next_btn.set_tooltip_text("Aplicar ya el siguiente fondo de la lista")
        next_btn.connect("clicked", lambda _b: self.on_step_clicked(1))
        status_box.pack_start(next_btn, False, False, 0)
        vbox.pack_start(status_box, False, False, 0)

        self.warning_label = Gtk.Label(label="", xalign=0)
        self.warning_label.set_line_wrap(True)
        self.warning_label.get_style_context().add_class("error")
        vbox.pack_start(self.warning_label, False, False, 0)

        lists_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(lists_box, True, True, 0)

        avail_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        avail_vbox.pack_start(Gtk.Label(label="Disponibles"), False, False, 0)
        self.avail_search = Gtk.SearchEntry()
        self.avail_search.set_placeholder_text("Buscar...")
        self.avail_search.connect("search-changed", self.on_avail_search_changed)
        avail_vbox.pack_start(self.avail_search, False, False, 0)
        self.avail_store = Gtk.ListStore(str, str)  # titulo, id
        self.avail_filter = self.avail_store.filter_new()
        self.avail_filter.set_visible_func(self.avail_filter_func)
        self.avail_view = Gtk.TreeView(model=self.avail_filter)
        self.avail_view.append_column(Gtk.TreeViewColumn("Titulo", Gtk.CellRendererText(), text=0))
        self.avail_view.set_headers_visible(False)
        avail_scrolled = Gtk.ScrolledWindow()
        avail_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        avail_scrolled.set_shadow_type(Gtk.ShadowType.IN)
        avail_scrolled.add(self.avail_view)
        avail_vbox.pack_start(avail_scrolled, True, True, 0)
        lists_box.pack_start(avail_vbox, True, True, 0)

        mid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mid_box.set_valign(Gtk.Align.CENTER)
        add_btn = icon_button("Anadir", "go-next-symbolic")
        add_btn.connect("clicked", self.on_add_clicked)
        mid_box.pack_start(add_btn, False, False, 0)
        remove_btn = icon_button("Quitar", "go-previous-symbolic")
        remove_btn.connect("clicked", self.on_remove_clicked)
        mid_box.pack_start(remove_btn, False, False, 0)
        up_btn = icon_button("Subir", "go-up-symbolic")
        up_btn.connect("clicked", self.on_move_up)
        mid_box.pack_start(up_btn, False, False, 0)
        down_btn = icon_button("Bajar", "go-down-symbolic")
        down_btn.connect("clicked", self.on_move_down)
        mid_box.pack_start(down_btn, False, False, 0)

        mid_box.pack_start(Gtk.Separator(), False, False, 8)

        favorites_btn = icon_button("Rellenar con favoritos", "starred-symbolic")
        favorites_btn.connect("clicked", self.on_fill_from_favorites)
        mid_box.pack_start(favorites_btn, False, False, 0)

        shuffle_btn = icon_button("Aleatorizar orden", "media-playlist-shuffle-symbolic")
        shuffle_btn.connect("clicked", self.on_shuffle_clicked)
        mid_box.pack_start(shuffle_btn, False, False, 0)

        lists_box.pack_start(mid_box, False, False, 0)

        playlist_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        playlist_vbox.pack_start(Gtk.Label(label="Orden de rotacion"), False, False, 0)
        self.playlist_store = Gtk.ListStore(str, str, str)  # titulo, id, motivo por el que no rotara
        self.playlist_view = Gtk.TreeView(model=self.playlist_store)
        column = Gtk.TreeViewColumn("Titulo")
        title_cell = Gtk.CellRendererText()
        column.pack_start(title_cell, True)
        column.add_attribute(title_cell, "text", 0)
        warn_cell = Gtk.CellRendererText()
        warn_cell.set_property("foreground", "#d9822b")
        column.pack_start(warn_cell, False)
        column.add_attribute(warn_cell, "text", 2)
        self.playlist_view.append_column(column)
        self.playlist_view.set_headers_visible(False)
        playlist_scrolled = Gtk.ScrolledWindow()
        playlist_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        playlist_scrolled.set_shadow_type(Gtk.ShadowType.IN)
        playlist_scrolled.add(self.playlist_view)
        playlist_vbox.pack_start(playlist_scrolled, True, True, 0)
        lists_box.pack_start(playlist_vbox, True, True, 0)

        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vbox.pack_start(bottom_box, False, False, 0)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_halign(Gtk.Align.START)
        bottom_box.pack_start(self.status_label, True, True, 0)
        save_btn = icon_button("Guardar y aplicar", "document-save-symbolic")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_save_clicked)
        bottom_box.pack_end(save_btn, False, False, 0)

        for item in sorted(all_items, key=lambda i: i["title"].lower()):
            self.avail_store.append([item["title"], item["id"]])

        self.load_monitor_playlist(monitors[0])
        self._poll = GLib.timeout_add_seconds(2, self._refresh_status)
        self.connect("destroy", lambda *_: GLib.source_remove(self._poll))
        self._refresh_status()

    def _append_playlist(self, title, wid):
        self.playlist_store.append([title, wid, ""])

    def _refresh_problems(self):
        """Marca en la lista los fondos que la rotación se saltará y resume cuántos son."""
        ids = [row[1] for row in self.playlist_store]
        problems = selection.playlist_problems(ids)
        for row in self.playlist_store:
            row[2] = f"   ⚠ no rotará: {problems[row[1]]}" if row[1] in problems else ""
        if not ids:
            self.warning_label.set_text("")
        elif len(problems) == len(ids):
            self.warning_label.set_text("⚠ Ningún fondo de esta lista puede rotar, así que no cambiará nunca. "
                                        "Mira el motivo junto a cada uno.")
        elif problems:
            self.warning_label.set_text(f"⚠ {len(problems)} de {len(ids)} fondos se saltarán en la rotación "
                                        "(el motivo está junto a cada uno).")
        else:
            self.warning_label.set_text("")

    def _refresh_status(self):
        monitor = self.monitor_combo.get_active_text()
        if not monitor:
            return True
        info = rotation.status(monitor)
        title = lambda wid: self.titles_by_id.get(wid, wid) if wid else "-"
        if not info["items"]:
            text = "La lista está vacía."
        elif not info["enabled"]:
            text = "Rotación desactivada en esta pantalla (guarda con la casilla marcada para activarla)."
        elif info["paused"]:
            text = "Rotación en pausa (desde la bandeja)."
        elif info["next"] is None:
            text = "Rotación activada, pero ningún fondo de la lista puede rotar."
        else:
            left = info["seconds_left"] or 0
            when = "en unos segundos" if left < 60 else f"en {left // 60} min"
            text = f"Ahora: {title(info['current'])}  ·  Siguiente: {title(info['next'])}  ·  cambia {when}"
        self.rotation_label.set_text(text)
        return True

    def on_step_clicked(self, direction):
        monitor = self.monitor_combo.get_active_text()
        self.status_label.set_text("Cambiando de fondo...")

        def work():
            ok, result = rotation.step(monitor, direction)
            GLib.idle_add(done, ok, result)

        def done(ok, result):
            self.playlists = load_playlists() if ok else self.playlists
            self.status_label.set_text(f"Aplicado: {self.titles_by_id.get(result, result)}" if ok else result)
            self._refresh_status()
            return False

        self.stash_current_monitor()
        save_playlists(self.playlists)
        threading.Thread(target=work, daemon=True).start()

    def avail_filter_func(self, model, iter_, data):
        query = self.avail_search.get_text().strip().lower()
        if not query:
            return True
        return query in (model[iter_][0] or "").lower()

    def on_avail_search_changed(self, entry):
        self.avail_filter.refilter()

    def load_monitor_playlist(self, monitor):
        data = self.playlists.get(monitor, {})
        self.enabled_check.set_active(bool(data.get("enabled", False)))
        self.interval_spin.set_value(data.get("interval_minutes", 30))
        self.playlist_store.clear()
        for wid in data.get("items", []):
            self._append_playlist(self.titles_by_id.get(wid, wid), wid)
        self._refresh_problems()
        self._refresh_status()

    def stash_current_monitor(self):
        monitor = self.monitor_combo.get_active_text()
        if not monitor:
            return
        items = [row[1] for row in self.playlist_store]
        previous = self.playlists.get(monitor, {})
        self.playlists[monitor] = {
            "enabled": self.enabled_check.get_active(),
            "interval_minutes": int(self.interval_spin.get_value()),
            "items": items,
            "current_index": previous.get("current_index", 0),
            "last_switch": previous.get("last_switch", 0),
        }

    def on_monitor_changed(self, combo):
        self.stash_current_monitor()
        self.load_monitor_playlist(combo.get_active_text())

    def get_selected_row(self, view):
        model, iter_ = view.get_selection().get_selected()
        return model, iter_

    def on_add_clicked(self, button):
        model, iter_ = self.get_selected_row(self.avail_view)
        if not iter_:
            self.status_label.set_text("Selecciona un wallpaper de la lista de disponibles")
            return
        self._append_playlist(model[iter_][0], model[iter_][1])
        self._refresh_problems()

    def on_remove_clicked(self, button):
        model, iter_ = self.get_selected_row(self.playlist_view)
        if not iter_:
            self.status_label.set_text("Selecciona un wallpaper de la rotacion para quitarlo")
            return
        model.remove(iter_)
        self._refresh_problems()

    def on_move_up(self, button):
        model, iter_ = self.get_selected_row(self.playlist_view)
        if not iter_:
            return
        index = model.get_path(iter_).get_indices()[0]
        if index > 0:
            model.move_before(iter_, model.get_iter(index - 1))

    def on_move_down(self, button):
        model, iter_ = self.get_selected_row(self.playlist_view)
        if not iter_:
            return
        next_iter = model.iter_next(iter_)
        if next_iter:
            model.move_after(iter_, next_iter)

    def on_fill_from_favorites(self, button):
        favorites = load_favorite_ids()
        if not favorites:
            self.status_label.set_text("No tienes ningun wallpaper marcado como favorito todavia")
            return
        existing = {row[1] for row in self.playlist_store}
        added = 0
        for wid in favorites:
            if wid not in existing and wid in self.titles_by_id:
                self._append_playlist(self.titles_by_id.get(wid, wid), wid)
                added += 1
        self._refresh_problems()
        self.status_label.set_text(f"Anadidos {added} favoritos a la rotacion" if added else "Tus favoritos ya estaban todos en la rotacion")

    def on_shuffle_clicked(self, button):
        import random
        rows = [(row[0], row[1]) for row in self.playlist_store]
        random.shuffle(rows)
        self.playlist_store.clear()
        for title, wid in rows:
            self._append_playlist(title, wid)
        self._refresh_problems()
        self.status_label.set_text("Orden aleatorizado")

    def on_save_clicked(self, button):
        self.stash_current_monitor()
        save_playlists(self.playlists)
        monitor = self.monitor_combo.get_active_text()
        data = self.playlists.get(monitor, {})
        if data.get("enabled") and data.get("items"):
            # Se empieza por el primer fondo que de verdad puede rotar (no por uno oculto, roto o web bloqueado).
            problems = selection.playlist_problems(data["items"])
            start = next((i for i, wid in enumerate(data["items"]) if wid not in problems), None)
            if start is None:
                self.status_label.set_text(f"Guardado en {monitor}, pero ningún fondo de la lista puede rotar: no cambiará.")
            else:
                data["current_index"] = start
                data["last_switch"] = int(time.time())
                self.playlists[monitor] = data
                save_playlists(self.playlists, fresh_progress={monitor})
                subprocess.Popen([APPLY_SCRIPT, f"{monitor}={data['items'][start]}"])
                skipped = f" ({len(problems)} se saltarán)" if problems else ""
                self.status_label.set_text(f"Rotacion guardada y activada en {monitor} ({len(data['items'])} wallpapers){skipped}")
        else:
            self.status_label.set_text(f"Configuracion guardada para {monitor} (rotacion desactivada)")
        if self.on_saved:
            self.on_saved()
