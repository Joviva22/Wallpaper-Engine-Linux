"""Ventana para gestionar los personajes de Nikke Stage: buscar en el catalogo de Nikke-db,
descargar los que quieras (packs gratuitos) y quitarlos. Cada descarga se valida antes de
instalarse; el wallpaper se regenera con los personajes disponibles en cada hueco."""
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from . import nikke_stage
from .l2d_pack import PackError


class StageCharactersWindow(Gtk.Window):
    COL_INSTALLED, COL_CODE, COL_NAME = range(3)

    def __init__(self, on_done=None):
        super().__init__(title="Nikke Stage: personajes")
        self.set_default_size(620, 600)
        self.set_border_width(12)
        self.on_done = on_done
        self.busy = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(box)

        intro = Gtk.Label(
            label="Elige los personajes que quieras tener en Nikke Stage. Los packs son los gratuitos de "
                  "nikke-wallpaper-packs (contenido de fans, activos de SHIFT UP); cada uno pesa unos 3-17 MB.",
            xalign=0)
        intro.set_line_wrap(True)
        box.pack_start(intro, False, False, 0)

        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Buscar por nombre o codigo (Rapi, Makima, c010...)")
        self.search.connect("search-changed", lambda *_: self.filter.refilter())
        search_row.pack_start(self.search, True, True, 0)
        self.only_installed = Gtk.CheckButton(label="Solo instalados")
        self.only_installed.connect("toggled", lambda *_: self.filter.refilter())
        search_row.pack_start(self.only_installed, False, False, 0)
        box.pack_start(search_row, False, False, 0)

        self.store = Gtk.ListStore(bool, str, str)
        self.filter = self.store.filter_new()
        self.filter.set_visible_func(self._visible)
        self.view = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.filter))
        self.view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        toggle = Gtk.CellRendererToggle()
        self.view.append_column(Gtk.TreeViewColumn("Instalado", toggle, active=self.COL_INSTALLED))
        for title, column in (("Codigo", self.COL_CODE), ("Nombre", self.COL_NAME)):
            tree_column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=column)
            tree_column.set_sort_column_id(column)
            tree_column.set_resizable(True)
            self.view.append_column(tree_column)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.add(self.view)
        box.pack_start(scrolled, True, True, 0)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.download_btn = Gtk.Button(label="Descargar seleccionados")
        self.download_btn.get_style_context().add_class("suggested-action")
        self.download_btn.connect("clicked", self._on_download)
        self.remove_btn = Gtk.Button(label="Quitar seleccionados")
        self.remove_btn.connect("clicked", self._on_remove)
        self.reload_btn = Gtk.Button(label="Actualizar catalogo")
        self.reload_btn.connect("clicked", lambda *_: self._load_catalog())
        for button in (self.download_btn, self.remove_btn, self.reload_btn):
            buttons.pack_start(button, False, False, 0)
        box.pack_start(buttons, False, False, 0)

        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.spinner = Gtk.Spinner()
        status_row.pack_start(self.spinner, False, False, 0)
        self.status = Gtk.Label(xalign=0)
        self.status.set_line_wrap(True)
        status_row.pack_start(self.status, True, True, 0)
        box.pack_start(status_row, False, False, 0)

        self.show_all()
        self._load_catalog()

    # -- helpers ------------------------------------------------------------

    def _visible(self, model, row, _data=None):
        installed, code, name = model[row][self.COL_INSTALLED], model[row][self.COL_CODE], model[row][self.COL_NAME]
        if self.only_installed.get_active() and not installed:
            return False
        query = self.search.get_text().strip().lower()
        return not query or query in code.lower() or query in (name or "").lower()

    def _selected_codes(self):
        model, paths = self.view.get_selection().get_selected_rows()
        return [model[path][self.COL_CODE] for path in paths]

    def _set_busy(self, busy, message=None):
        self.busy = busy
        for button in (self.download_btn, self.remove_btn, self.reload_btn):
            button.set_sensitive(not busy)
        if busy:
            self.spinner.start()
        else:
            self.spinner.stop()
        if message is not None:
            self.status.set_text(message)

    def _run(self, work, finished_message):
        """Ejecuta `work(progress)` en un hilo y refresca el catalogo al terminar."""
        if self.busy:
            return
        self._set_busy(True, "Trabajando...")

        def progress(message):
            GLib.idle_add(self.status.set_text, message)

        def worker():
            error = None
            try:
                work(progress)
            except PackError as e:
                error = str(e)
            except Exception as e:  # red caida, disco lleno...
                error = f"Error inesperado: {e}"
            GLib.idle_add(self._finished, error, finished_message)

        threading.Thread(target=worker, daemon=True).start()

    def _finished(self, error, finished_message):
        self._set_busy(False, error or finished_message)
        self._fill(nikke_stage.catalog(self._index))
        if not error and self.on_done:
            self.on_done()
        return False

    # -- catalogo -----------------------------------------------------------

    _index = None

    def _fill(self, rows):
        self.store.clear()
        for code, name, installed in rows:
            self.store.append([installed, code, name])
        self.filter.refilter()

    def _load_catalog(self):
        if self.busy:
            return
        self._set_busy(True, "Cargando el catalogo de Nikke-db...")

        def worker():
            index = nikke_stage.l2d_index()
            GLib.idle_add(self._catalog_ready, index)

        threading.Thread(target=worker, daemon=True).start()

    def _catalog_ready(self, index):
        self._index = index
        rows = nikke_stage.catalog(index)
        self._fill(rows)
        if rows:
            self._set_busy(False, f"{len(rows)} personajes en el catalogo; "
                                  f"{sum(1 for r in rows if r[2])} instalados.")
        else:
            self._set_busy(False, "No se pudo cargar el catalogo (sin conexion). Puedes buscar solo los instalados.")
        return False

    # -- acciones -----------------------------------------------------------

    def _on_download(self, _button):
        codes = [c for c in self._selected_codes()]
        if not codes:
            self.status.set_text("Selecciona uno o varios personajes de la lista.")
            return
        self._run(lambda progress: nikke_stage.add(codes, progress=progress),
                  f"Instalados {len(codes)} personaje(s). Reaplica Nikke Stage para verlos y elige en "
                  f"Personalizar quien va en cada hueco.")

    def _on_remove(self, _button):
        codes = self._selected_codes()
        if not codes:
            self.status.set_text("Selecciona uno o varios personajes instalados.")
            return
        self._run(lambda progress: nikke_stage.remove(codes), f"Quitados {len(codes)} personaje(s).")
