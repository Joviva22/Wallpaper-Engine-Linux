"""Ventana principal: sidebar de navegacion (biblioteca/favoritos/recientes/
animados/ocultos/workshop + monitores), cuadricula de tarjetas de wallpapers
locales con filtros combinables, y panel de detalle a la derecha con la
informacion del wallpaper seleccionado."""
import datetime
import json
import os
import subprocess
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk, Pango

from .config import (
    atomic_write_json, load_json, CONF_DIR,
    web_wallpapers_allowed, set_web_wallpapers_allowed,
    load_wallpapers, detect_monitors, load_current_assignments, load_hidden_ids,
    save_hidden_ids, load_favorite_ids, save_favorite_ids, load_recent_ids, record_recent,
    load_known_bad, load_playlists, save_playlists, load_ui_state, save_ui_state,
    unsubscribe_workshop_item, build_thumb, SORT_OPTIONS, SORT_REVERSE, APPLY_SCRIPT,
    CACHE_DIR, STEAM_LIB, load_scaling, save_scaling, SCALING_MODES, DEFAULT_SCALING,
    load_properties, save_properties, KNOWN_BAD_FILE,
    load_audio, save_audio, DEFAULT_VOLUME,
    load_speed, save_speed, SPEED_OPTIONS, DEFAULT_SPEED, engine_supports_speed,
    has_hidden_password, set_hidden_password, clear_hidden_password, verify_hidden_password,
)
from .ui import icon_button, open_in_steam, apply_css, WallpaperCard, CARD_SIZE
from .workshop_window import WorkshopBrowserWindow
from .playlist_window import PlaylistWindow
from .properties_window import PropertiesDialog
from .stage_window import StageCharactersWindow
from . import compat, diagnostics
from .live_preview import LivePreview, PREVIEW_SECONDS
from .repair import attempt_repair, attempt_repair_all

TABS = ["Todos", "Favoritos", "Recientes", "Animados", "Ocultos"]
SCALING_LABELS = {
    "fill": "Rellenar (recorta)",
    "fit": "Ajustar (sin recortar)",
    "stretch": "Estirar",
    "default": "Por defecto de la escena",
}
TAB_LABELS = {
    "Todos": "Biblioteca", "Favoritos": "Favoritos", "Recientes": "Recientes",
    "Animados": "Animados", "Ocultos": "Ocultos",
}
TAB_ICONS = {
    "Todos": "image-x-generic-symbolic", "Favoritos": "starred-symbolic",
    "Recientes": "document-open-recent-symbolic", "Animados": "media-playback-start-symbolic",
    "Ocultos": "view-conceal-symbolic",
}


class FiltersMenuButton(Gtk.MenuButton):
    """Boton unico 'Filtros' con un popover que agrupa etiquetas (deben estar
    todas presentes) y clasificacion (basta con una) en checkboxes."""

    def __init__(self, tag_options, rating_options, on_change=None, initial_ratings=None,
                 type_options=(), initial_types=None):
        super().__init__()
        self.on_change = on_change
        self.tag_checks = {}
        self.rating_checks = {}
        self.type_checks = {}

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(10)

        box.pack_start(Gtk.Label(label="Etiquetas", xalign=0), False, False, 0)
        self.tag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.pack_start(self.tag_box, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)

        box.pack_start(Gtk.Label(label="Clasificacion", xalign=0), False, False, 0)
        for opt in rating_options:
            cb = Gtk.CheckButton(label=opt)
            cb.set_active(initial_ratings is not None and opt in initial_ratings)
            cb.connect("toggled", self._on_toggled)
            box.pack_start(cb, False, False, 0)
            self.rating_checks[opt] = cb

        box.pack_start(Gtk.Separator(), False, False, 4)
        box.pack_start(Gtk.Label(label="Tipo", xalign=0), False, False, 0)
        for opt in type_options:
            cb = Gtk.CheckButton(label=opt)
            cb.set_active(initial_types is not None and opt in initial_types)
            cb.connect("toggled", self._on_toggled)
            box.pack_start(cb, False, False, 0)
            self.type_checks[opt] = cb

        popover = Gtk.Popover()
        popover.add(box)
        self.set_popover(popover)

        self.set_tag_options(tag_options)
        box.show_all()

    def set_tag_options(self, options, checked=None):
        preserve = set(checked) if checked is not None else set(self.get_selected_tags())
        for child in list(self.tag_box.get_children()):
            self.tag_box.remove(child)
        self.tag_checks = {}
        for opt in options:
            cb = Gtk.CheckButton(label=opt)
            cb.set_active(opt in preserve)
            cb.connect("toggled", self._on_toggled)
            self.tag_box.pack_start(cb, False, False, 0)
            self.tag_checks[opt] = cb
        self.tag_box.show_all()
        self._update_label()

    def _on_toggled(self, cb):
        self._update_label()
        if self.on_change:
            self.on_change()

    def get_selected_tags(self):
        return [opt for opt, cb in self.tag_checks.items() if cb.get_active()]

    def get_selected_ratings(self):
        return [opt for opt, cb in self.rating_checks.items() if cb.get_active()]

    def get_selected_types(self):
        return [opt for opt, cb in self.type_checks.items() if cb.get_active()]

    def _update_label(self):
        count = (len(self.get_selected_tags()) + len(self.get_selected_ratings())
                 + len(self.get_selected_types()))
        self.set_label(f"Filtros ({count})" if count else "Filtros")


def _nav_content(icon_name, title, subtitle=None):
    content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    content.pack_start(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON), False, False, 0)
    subtitle_label = None
    if subtitle is not None:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(Gtk.Label(label=title, xalign=0), False, False, 0)
        subtitle_label = Gtk.Label(label=subtitle, xalign=0)
        subtitle_label.set_ellipsize(Pango.EllipsizeMode.END)
        subtitle_label.set_max_width_chars(18)
        subtitle_label.get_style_context().add_class("dim-label")
        vbox.pack_start(subtitle_label, False, False, 0)
        content.pack_start(vbox, True, True, 0)
    else:
        content.pack_start(Gtk.Label(label=title, xalign=0), True, True, 0)
    return content, subtitle_label


def make_nav_radio(group, icon_name, title, subtitle=None):
    btn = Gtk.RadioButton.new_from_widget(group) if group else Gtk.RadioButton.new(None)
    btn.set_mode(False)
    btn.get_style_context().add_class("wpe-nav-item")
    content, subtitle_label = _nav_content(icon_name, title, subtitle)
    btn.add(content)
    return btn, subtitle_label


def make_nav_button(icon_name, title):
    btn = Gtk.Button()
    btn.set_relief(Gtk.ReliefStyle.NONE)
    btn.get_style_context().add_class("wpe-nav-item")
    content, _ = _nav_content(icon_name, title)
    btn.add(content)
    return btn


class PickerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Fondos de pantalla")
        self.set_default_size(1400, 860)

        self.monitors = detect_monitors() or ["DP-2"]
        self.assignments = load_current_assignments(self.monitors)
        self.scaling = load_scaling()
        self.audio = load_audio()
        self.speed = load_speed()

        ui_state = load_ui_state()
        self.target_monitor = ui_state.get("target_monitor") if ui_state.get("target_monitor") in self.monitors else self.monitors[0]
        self.current_tab = ui_state.get("tab") if ui_state.get("tab") in TABS else "Todos"
        # Si se cerro la app estando en "Ocultos" y hay contraseña configurada, no
        # restaurar directamente ahi al reabrir — seria una forma trivial de saltarse
        # la contraseña sin mas que cerrar y volver a abrir la ventana.
        if self.current_tab == "Ocultos" and has_hidden_password():
            self.current_tab = "Todos"

        self.all_items = []
        self.items_by_id = {}
        self.cards = {}
        self.hidden_ids = load_hidden_ids()
        self.favorite_ids = load_favorite_ids()
        self.recent_ids = load_recent_ids()
        self.known_bad = load_known_bad()
        self.workshop_window = None
        self.playlist_window = None
        self._detail_wid = None
        self.placeholder_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, *CARD_SIZE)
        self.placeholder_pixbuf.fill(0x2f3140ff)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root)

        root.pack_start(self._build_sidebar(), False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_border_width(14)
        root.pack_start(content, True, True, 0)

        content.pack_start(self._build_header(ui_state), False, False, 0)
        content.pack_start(self._build_monitor_row(), False, False, 0)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.flowbox.set_activate_on_single_click(False)
        self.flowbox.set_row_spacing(14)
        self.flowbox.set_column_spacing(14)
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_filter_func(self._filter_func)
        self.flowbox.set_sort_func(self._sort_func)
        self.flowbox.set_min_children_per_line(1)
        self.flowbox.set_max_children_per_line(30)
        self.flowbox.connect("selected-children-changed", self.on_selection_changed)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.add(self.flowbox)
        content.pack_start(scrolled, True, True, 0)

        content.pack_start(self._build_bottom_bar(), False, False, 0)

        self.detail_revealer = Gtk.Revealer()
        self.detail_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self.detail_revealer.set_transition_duration(180)
        self.detail_revealer.add(self._build_detail_panel())
        root.pack_start(self.detail_revealer, False, False, 0)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self._apply_seen = {mon: load_json(os.path.join(CONF_DIR, f"status_{mon}.json"), {}).get("token")
                            for mon in self.monitors}
        self.live_preview = LivePreview()
        self._apply_poll = GLib.timeout_add(1000, self._poll_apply_status)
        GLib.idle_add(self.populate)

    # -- Construccion de la interfaz ------------------------------------------

    def _build_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_size_request(210, -1)
        sidebar.set_border_width(12)
        sidebar.get_style_context().add_class("wpe-sidebar")

        self.tab_buttons = {}
        first = None
        for key in TABS:
            btn, _ = make_nav_radio(first, TAB_ICONS[key], TAB_LABELS[key])
            if first is None:
                first = btn
            btn.set_active(key == self.current_tab)
            btn.connect("toggled", self.on_tab_toggled, key)
            sidebar.pack_start(btn, False, False, 0)
            self.tab_buttons[key] = btn

        workshop_btn = make_nav_button("network-workgroup-symbolic", "Workshop")
        workshop_btn.connect("clicked", self.on_open_workshop_browser)
        sidebar.pack_start(workshop_btn, False, False, 0)

        sidebar.pack_start(Gtk.Separator(), False, False, 8)
        monitors_title = Gtk.Label(label="MONITORES", xalign=0)
        monitors_title.get_style_context().add_class("wpe-detail-section-title")
        sidebar.pack_start(monitors_title, False, False, 0)

        self.sidebar_monitor_radios = {}
        self.sidebar_monitor_subtitles = {}
        first_mon = None
        for mon in self.monitors:
            btn, subtitle_label = make_nav_radio(
                first_mon, "video-display-symbolic", mon, subtitle=self._monitor_subtitle(mon)
            )
            if first_mon is None:
                first_mon = btn
            btn.set_active(mon == self.target_monitor)
            btn.connect("toggled", self.on_monitor_nav_toggled, mon)
            sidebar.pack_start(btn, False, False, 0)
            self.sidebar_monitor_radios[mon] = btn
            self.sidebar_monitor_subtitles[mon] = subtitle_label

        sidebar.pack_start(Gtk.Box(), True, True, 0)  # empuja "Ajustes" abajo

        settings_btn = make_nav_button("preferences-system-symbolic", "Ajustes")
        settings_btn.connect("clicked", self.on_open_settings)
        sidebar.pack_start(settings_btn, False, False, 0)

        return sidebar

    def _build_header(self, ui_state):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar wallpapers... (Ctrl+F)")
        self.search_entry.get_style_context().add_class("wpe-search-big")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_filters_changed)
        header_box.pack_start(self.search_entry, True, True, 0)

        self.filters_btn = FiltersMenuButton(
            [], ["Everyone", "Questionable", "Mature", "Desconocido"],
            on_change=self.on_filters_changed,
            initial_ratings=ui_state.get("ratings", ["Everyone"]),
            type_options=["Scene", "Video", "Web"],
            initial_types=ui_state.get("types", []),
        )
        header_box.pack_start(self.filters_btn, False, False, 0)

        self.sort_combo = Gtk.ComboBoxText()
        for option in SORT_OPTIONS:
            self.sort_combo.append_text(option)
        saved_sort = ui_state.get("sort")
        sort_options_list = list(SORT_OPTIONS.keys())
        self.sort_combo.set_active(sort_options_list.index(saved_sort) if saved_sort in sort_options_list else 0)
        self.sort_combo.connect("changed", self.on_sort_changed)
        header_box.pack_start(self.sort_combo, False, False, 0)

        return header_box

    def _build_monitor_row(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label="MONITOR ACTIVO", xalign=0)
        title.get_style_context().add_class("wpe-detail-section-title")
        box.pack_start(title, False, False, 0)

        chips_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.monitor_chips = {}
        self.monitor_chip_subtitles = {}
        first = None
        for mon in self.monitors:
            chip, subtitle_label = make_nav_radio(
                first, "video-display-symbolic", mon, subtitle=self._monitor_subtitle(mon)
            )
            if first is None:
                first = chip
            chip.get_style_context().add_class("wpe-chip")
            chip.set_active(mon == self.target_monitor)
            chip.connect("toggled", self.on_monitor_chip_toggled, mon)
            chips_box.pack_start(chip, False, False, 0)
            self.monitor_chips[mon] = chip
            self.monitor_chip_subtitles[mon] = subtitle_label

        playback_btn = Gtk.MenuButton(label="Reproducción")
        playback_btn.set_tooltip_text("Escalado, audio y velocidad del monitor activo")
        popover = Gtk.Popover()
        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        controls.set_border_width(16)
        popover.add(controls)
        playback_btn.set_popover(popover)
        popover.set_relative_to(playback_btn)
        chips_box.pack_end(playback_btn, False, False, 0)

        controls.pack_start(Gtk.Label(label="Escalado:"), False, False, 0)
        self.scaling_combo = Gtk.ComboBoxText()
        for mode in SCALING_MODES:
            self.scaling_combo.append_text(SCALING_LABELS.get(mode, mode))
        current_mode = self.scaling.get(self.target_monitor, DEFAULT_SCALING)
        self.scaling_combo.set_active(SCALING_MODES.index(current_mode) if current_mode in SCALING_MODES else 0)
        self.scaling_combo.connect("changed", self.on_scaling_changed)
        controls.pack_start(self.scaling_combo, False, False, 0)

        controls.pack_start(Gtk.Label(label="Audio:"), False, False, 0)
        self.audio_toggle = Gtk.ToggleButton()
        self.audio_toggle.set_relief(Gtk.ReliefStyle.NONE)
        self.audio_toggle.connect("toggled", self.on_audio_toggled)
        controls.pack_start(self.audio_toggle, False, False, 0)

        self.volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.volume_scale.set_range(0, 100)
        self.volume_scale.set_draw_value(False)
        self.volume_scale.set_size_request(90, -1)
        self.volume_scale.set_tooltip_text("Volumen")
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        self.volume_scale.connect("button-release-event", self.on_volume_release)
        controls.pack_start(self.volume_scale, False, False, 0)

        # handler_block imprescindible aqui: set_active() dispara "toggled" de forma
        # SINCRONA en GTK si el estado cambia, y self.status_label (referenciado dentro
        # de on_audio_toggled) todavia no existe en este punto de la construccion —
        # se crea mas tarde en _build_bottom_bar(). Sin el bloqueo, arrancar la app con
        # el audio activado guardado en audio.json crasheaba con AttributeError en cada
        # inicio (visto en produccion real, journalctl confirma 4 crashes seguidos).
        audio_conf = self.audio.get(self.target_monitor, {})
        self.audio_toggle.handler_block_by_func(self.on_audio_toggled)
        self.audio_toggle.set_active(not audio_conf.get("muted", True))
        self.audio_toggle.handler_unblock_by_func(self.on_audio_toggled)
        self.volume_scale.set_value(audio_conf.get("volume", DEFAULT_VOLUME))
        self._sync_audio_widgets()

        controls.pack_start(Gtk.Label(label="Velocidad:"), False, False, 0)
        self.speed_combo = Gtk.ComboBoxText()
        for s in SPEED_OPTIONS:
            self.speed_combo.append_text(f"{s:g}x")
        current_speed = self.speed.get(self.target_monitor, DEFAULT_SPEED)
        idx = SPEED_OPTIONS.index(current_speed) if current_speed in SPEED_OPTIONS else 0
        self.speed_combo.set_active(idx)
        self.speed_combo.set_tooltip_text("Velocidad de reproducción de escenas y vídeos (requiere el motor parcheado)")
        self.speed_combo.connect("changed", self.on_speed_changed)
        if not engine_supports_speed():
            self.speed_combo.set_sensitive(False)
            self.speed_combo.set_tooltip_text(
                "Tu version de linux-wallpaperengine no soporta --speed (requiere un motor parcheado)")
        controls.pack_start(self.speed_combo, False, False, 0)

        controls.show_all()

        box.pack_start(chips_box, False, False, 0)
        return box

    def _build_bottom_bar(self):
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.status_label = Gtk.Label(label="Cargando...")
        self.status_label.set_halign(Gtk.Align.START)
        bottom_box.pack_start(self.status_label, True, True, 0)

        self.show_hidden_check = Gtk.CheckButton(label="Mostrar ocultos")
        self.show_hidden_check.connect("toggled", self.on_show_hidden_toggled)
        bottom_box.pack_start(self.show_hidden_check, False, False, 0)

        rotation_btn = icon_button("Rotacion", "media-playlist-repeat-symbolic")
        rotation_btn.connect("clicked", self.on_open_playlist_window)
        bottom_box.pack_start(rotation_btn, False, False, 0)

        self._build_bulk_actions_menu(bottom_box)

        refresh_btn = icon_button("Actualizar", "view-refresh-symbolic")
        refresh_btn.get_style_context().add_class("suggested-action")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        bottom_box.pack_end(refresh_btn, False, False, 0)

        return bottom_box

    def _build_bulk_actions_menu(self, bottom_box):
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_border_width(8)

        def add_action(label, icon_name, handler):
            btn = icon_button(label, icon_name)
            btn.set_relief(Gtk.ReliefStyle.NONE)

            def _on_click(_btn):
                popover.popdown()
                handler(_btn)

            btn.connect("clicked", _on_click)
            box.pack_start(btn, False, False, 0)

        add_action("Ocultar/Mostrar seleccionados", "list-remove-symbolic", self.on_toggle_hidden_clicked)
        add_action("Desuscribirse (seleccionados)", "user-trash-symbolic", self.on_unsubscribe_clicked)
        box.pack_start(Gtk.Separator(), False, False, 2)
        add_action("Desactivar fondos web", "dialog-password-symbolic", self._disable_web_wallpapers)
        add_action("Reparar toda la biblioteca", "applications-utilities-symbolic", self.on_repair_all_clicked)
        add_action("Diagnóstico...", "dialog-information-symbolic", self._open_diagnostics)
        box.pack_start(Gtk.Separator(), False, False, 2)
        add_action("Nikke Stage: personajes...", "avatar-default-symbolic", self._open_stage_characters)
        box.show_all()
        popover.add(box)

        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(Gtk.Image.new_from_icon_name("view-more-symbolic", Gtk.IconSize.BUTTON))
        menu_btn.set_tooltip_text("Acciones en lote sobre la seleccion")
        menu_btn.set_popover(popover)
        bottom_box.pack_start(menu_btn, False, False, 0)

    def _build_detail_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.set_size_request(300, -1)
        panel.set_border_width(14)
        panel.get_style_context().add_class("wpe-detail-panel")

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        close_btn = Gtk.Button()
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_image(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON))
        close_btn.connect("clicked", lambda *_: self.flowbox.unselect_all())
        top_row.pack_end(close_btn, False, False, 0)
        panel.pack_start(top_row, False, False, 0)

        self.detail_image = Gtk.Image()
        panel.pack_start(self.detail_image, False, False, 0)

        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.detail_title = Gtk.Label(xalign=0)
        self.detail_title.set_line_wrap(True)
        self.detail_title.get_style_context().add_class("wpe-detail-title")
        title_row.pack_start(self.detail_title, True, True, 0)
        self.detail_heart = Gtk.ToggleButton()
        self.detail_heart.set_relief(Gtk.ReliefStyle.NONE)
        self.detail_heart.get_style_context().add_class("wpe-heart")
        self.detail_heart.connect("toggled", self._on_detail_heart_toggled)
        title_row.pack_start(self.detail_heart, False, False, 0)
        panel.pack_start(title_row, False, False, 0)

        self.detail_assign_btn = icon_button("Asignar", "emblem-ok-symbolic")
        self.detail_assign_btn.get_style_context().add_class("suggested-action")
        self.detail_assign_btn.connect("clicked", self._on_detail_assign_clicked)
        panel.pack_start(self.detail_assign_btn, False, False, 0)

        preview_btn = icon_button("Vista previa", "view-fullscreen-symbolic")
        preview_btn.connect("clicked", self._on_detail_preview_clicked)
        panel.pack_start(preview_btn, False, False, 0)

        live_btn = icon_button("Probar en ventana", "media-playback-start-symbolic")
        live_btn.set_tooltip_text(f"Abre el fondo en una ventana propia durante {PREVIEW_SECONDS} s, sin tocar el escritorio")
        live_btn.connect("clicked", self._on_detail_live_preview)
        panel.pack_start(live_btn, False, False, 0)

        rotation_btn = icon_button("Anadir a rotacion", "media-playlist-repeat-symbolic")
        rotation_btn.connect("clicked", self._on_detail_add_rotation)
        panel.pack_start(rotation_btn, False, False, 0)

        customize_btn = icon_button("Personalizar", "preferences-desktop-symbolic")
        customize_btn.connect("clicked", self._on_detail_customize_clicked)
        panel.pack_start(customize_btn, False, False, 0)

        self.detail_repair_btn = icon_button("Reparar fallo conocido", "applications-utilities-symbolic")
        self.detail_repair_btn.connect("clicked", self._on_detail_repair_clicked)
        self.detail_repair_btn.set_no_show_all(True)
        self.detail_repair_btn.set_visible(False)
        panel.pack_start(self.detail_repair_btn, False, False, 0)

        self.detail_hide_btn = icon_button("Ocultar", "list-remove-symbolic")
        self.detail_hide_btn.connect("clicked", self._on_detail_hide_clicked)
        panel.pack_start(self.detail_hide_btn, False, False, 0)

        unsub_btn = icon_button("Desuscribirse", "user-trash-symbolic")
        unsub_btn.connect("clicked", self._on_detail_unsub_clicked)
        panel.pack_start(unsub_btn, False, False, 0)

        panel.pack_start(Gtk.Separator(), False, False, 6)

        info_title = Gtk.Label(label="INFORMACION", xalign=0)
        info_title.get_style_context().add_class("wpe-detail-section-title")
        panel.pack_start(info_title, False, False, 0)

        self.detail_info_grid = Gtk.Grid()
        self.detail_info_grid.set_row_spacing(4)
        self.detail_info_grid.set_column_spacing(10)
        panel.pack_start(self.detail_info_grid, False, False, 0)

        tags_title = Gtk.Label(label="ETIQUETAS", xalign=0)
        tags_title.get_style_context().add_class("wpe-detail-section-title")
        panel.pack_start(tags_title, False, False, 8)

        self.detail_tags_box = Gtk.FlowBox()
        self.detail_tags_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.detail_tags_box.set_max_children_per_line(4)
        self.detail_tags_box.set_min_children_per_line(1)
        panel.pack_start(self.detail_tags_box, False, False, 0)

        return panel

    # -- Carga y cuadricula ---------------------------------------------------

    def populate(self):
        self.known_bad = load_known_bad()
        self.compat_history = compat.load_history()
        self.all_items = load_wallpapers()
        self.items_by_id = {item["id"]: item for item in self.all_items}

        all_tags = set()
        pending_thumb_ids = []
        for item in self.all_items:
            all_tags.update(item["tags"])
            if item["thumb"] and os.path.isfile(item["thumb"]):
                try:
                    item["pixbuf"] = GdkPixbuf.Pixbuf.new_from_file(item["thumb"])
                except Exception:
                    item["pixbuf"] = self.placeholder_pixbuf
            else:
                item["pixbuf"] = self.placeholder_pixbuf
                if item.get("preview_path"):
                    pending_thumb_ids.append(item["id"])

        self.filters_btn.set_tag_options(sorted(all_tags, key=str.lower))

        for mon in self.monitors:
            self.update_monitor_label(mon)

        self.rebuild_cards()
        self._sync_speed_combo()
        self.status_label.set_text(f"{len(self.all_items)} wallpapers")

        if pending_thumb_ids:
            threading.Thread(target=self._generate_thumbs_thread, args=(pending_thumb_ids,), daemon=True).start()

        return False

    def _generate_thumbs_thread(self, ids):
        for wid in ids:
            item = self.items_by_id.get(wid)
            if not item or not item.get("preview_path"):
                continue
            thumb_path = os.path.join(CACHE_DIR, f"{wid}.png")
            if build_thumb(item["preview_path"], thumb_path):
                GLib.idle_add(self._apply_generated_thumb, wid, thumb_path)

    def _apply_generated_thumb(self, wid, thumb_path):
        item = self.items_by_id.get(wid)
        if not item:
            return False
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumb_path)
        except Exception:
            return False
        item["thumb"] = thumb_path
        item["pixbuf"] = pixbuf
        card = self.cards.get(wid)
        if card:
            card.set_pixbuf(pixbuf)
        return False

    def rebuild_cards(self):
        for child in list(self.flowbox.get_children()):
            self.flowbox.remove(child)
        self.cards = {}

        for item in self.all_items:
            card = self._build_card(item)
            self.flowbox.add(card)
            self.cards[item["id"]] = card

        self.flowbox.show_all()
        self.flowbox.invalidate_filter()
        self.flowbox.invalidate_sort()

    def _compat_for(self, wid):
        item = self.items_by_id.get(wid)
        if not item:
            return compat.UNTESTED, "", ""
        return compat.status(item, self.known_bad, self.compat_history, web_wallpapers_allowed())

    def _badge_for(self, wid):
        state, label, _ = self._compat_for(wid)
        if state in (compat.FAILED, compat.BLOCKED):
            return label
        if wid in self.hidden_ids:
            return "Oculto"
        return label

    def _update_card_badge(self, wid):
        card = self.cards.get(wid)
        if card:
            card.set_badge(self._badge_for(wid))
            card.set_tooltip_text(self._compat_for(wid)[2] or None)

    def _build_card(self, item):
        wid = item["id"]
        subtitle_parts = []
        if item.get("type") and item["type"] not in ("Desconocido", "Scene"):
            subtitle_parts.append(item["type"])
        if item.get("preset"):
            subtitle_parts.append("Preset")
        if item.get("tags"):
            subtitle_parts.append(item["tags"][0])
        subtitle = " · ".join(subtitle_parts)

        card = WallpaperCard(
            wid, item["title"], subtitle, item["pixbuf"],
            favorite=wid in self.favorite_ids, badge=self._badge_for(wid),
            assigned=(self.assignments.get(self.target_monitor) == wid),
        )
        card.on_assign = self.assign_and_apply
        card.on_preview = self.show_preview
        card.on_toggle_favorite = self.on_card_favorite_toggled
        card.on_context_menu = self.show_context_menu
        return card

    def _refresh_assigned_badges(self):
        current = self.assignments.get(self.target_monitor)
        for wid, card in self.cards.items():
            card.set_assigned(wid == current)

    # -- Filtro y orden del FlowBox ------------------------------------------

    def _passes_tab_filter(self, wid):
        item = self.items_by_id.get(wid, {})
        if self.current_tab == "Ocultos":
            return wid in self.hidden_ids
        if self.current_tab == "Favoritos":
            return wid in self.favorite_ids and wid not in self.hidden_ids
        if self.current_tab == "Recientes":
            return wid in self.recent_ids and wid not in self.hidden_ids
        if self.current_tab == "Animados":
            # "Scene" puede o no tener movimiento (Wallpaper Engine no expone un
            # flag fiable de estatico/animado); "Video" y "Web" si son siempre
            # dinamicos, asi que la pestana se limita a esos dos tipos.
            return item.get("type") in ("Video", "Web") and wid not in self.hidden_ids
        if self.show_hidden_check.get_active():
            return True
        return wid not in self.hidden_ids  # "Todos"

    def _filter_func(self, flowboxchild):
        card = flowboxchild.get_child()
        wid = card.wid
        item = self.items_by_id.get(wid)
        if not item:
            return False
        if not self._passes_tab_filter(wid):
            return False

        query = self.search_entry.get_text().strip().lower()
        if query and query not in item["title"].lower():
            return False

        selected_tags = self.filters_btn.get_selected_tags()
        if selected_tags and not all(t in item["tags"] for t in selected_tags):
            return False

        selected_ratings = self.filters_btn.get_selected_ratings()
        if selected_ratings and item["rating"] not in selected_ratings:
            return False

        selected_types = self.filters_btn.get_selected_types()
        if selected_types and item["type"] not in selected_types:
            return False

        return True

    def _sort_func(self, child_a, child_b):
        wid_a, wid_b = child_a.get_child().wid, child_b.get_child().wid

        if self.current_tab == "Recientes":
            order = {wid: i for i, wid in enumerate(self.recent_ids)}
            ia, ib = order.get(wid_a, 10**9), order.get(wid_b, 10**9)
            return -1 if ia < ib else (1 if ia > ib else 0)

        item_a, item_b = self.items_by_id.get(wid_a), self.items_by_id.get(wid_b)
        if not item_a or not item_b:
            return 0
        sort_choice = self.sort_combo.get_active_text() or "Mas reciente primero"
        key_func = SORT_OPTIONS.get(sort_choice, SORT_OPTIONS["Mas reciente primero"])
        reverse = SORT_REVERSE.get(sort_choice, False)
        ka, kb = key_func(item_a), key_func(item_b)
        cmp = -1 if ka < kb else (1 if ka > kb else 0)
        return -cmp if reverse else cmp

    def on_filters_changed(self, *args):
        self.flowbox.invalidate_filter()

    def on_sort_changed(self, combo):
        self.flowbox.invalidate_sort()
        self.save_current_ui_state()

    def on_tab_toggled(self, btn, label):
        if not btn.get_active():
            return
        if label == "Ocultos" and has_hidden_password() and not self._prompt_hidden_password():
            previous = self.current_tab
            prev_btn = self.tab_buttons.get(previous)
            if prev_btn:
                prev_btn.set_active(True)
            return
        self.current_tab = label
        self.flowbox.invalidate_filter()
        self.flowbox.invalidate_sort()
        self.save_current_ui_state()

    def on_show_hidden_toggled(self, check):
        if check.get_active() and has_hidden_password() and not self._prompt_hidden_password():
            check.handler_block_by_func(self.on_show_hidden_toggled)
            check.set_active(False)
            check.handler_unblock_by_func(self.on_show_hidden_toggled)
            return
        self.on_filters_changed()

    def _make_pin_entry(self):
        """Campo de entrada restringido a 4 digitos numericos (PIN), oculto como
        contraseña. Filtra cualquier caracter que no sea un digito al escribirlo
        (tambien al pegar), reescribiendo el contenido en el handler de "changed"
        — mas simple y robusto que interceptar "insert-text" (cuya firma exacta en
        PyGObject varia y dio TypeError al probarlo)."""
        entry = Gtk.Entry()
        entry.set_visibility(False)
        # OJO: no usar set_max_length(4) aqui — GTK trunca los caracteres BRUTOS a ese
        # limite antes de que el filtro de abajo pueda operar, asi que una letra de mas
        # (p.ej. "a1b2c3d4e5" truncado a "a1b2" por GTK) consume hueco del limite y
        # descarta digitos validos que venian despues. La longitud maxima la controla
        # solo `sanitize()`, sobre el string ya filtrado.
        entry.set_width_chars(6)
        entry.set_alignment(0.5)
        entry.set_input_purpose(Gtk.InputPurpose.DIGITS)

        def sanitize(e):
            raw = e.get_text()
            clean = "".join(c for c in raw if c.isdigit())[:4]
            if clean != raw:
                e.handler_block_by_func(sanitize)
                e.set_text(clean)
                e.set_position(-1)
                e.handler_unblock_by_func(sanitize)

        entry.connect("changed", sanitize)
        return entry

    def _prompt_hidden_password(self):
        dialog = Gtk.Dialog(title="PIN requerido", transient_for=self, modal=True)
        dialog.set_default_size(280, -1)
        box = dialog.get_content_area()
        box.set_border_width(14)
        box.set_spacing(8)
        box.add(Gtk.Label(label="Introduce el PIN de 4 digitos para ver los wallpapers ocultos:", xalign=0.5))
        entry = self._make_pin_entry()
        entry.set_activates_default(True)
        box.add(entry)
        error_label = Gtk.Label(xalign=0.5)
        error_label.get_style_context().add_class("dim-label")
        box.add(error_label)
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        ok_btn = dialog.add_button("Entrar", Gtk.ResponseType.OK)
        ok_btn.get_style_context().add_class("suggested-action")
        dialog.set_default_response(Gtk.ResponseType.OK)
        # Auto-confirmar al completar los 4 digitos, sin esperar a Enter/clic — es
        # el comportamiento habitual de un PIN.
        entry.connect("changed", lambda e: dialog.response(Gtk.ResponseType.OK) if len(e.get_text()) == 4 else None)
        dialog.show_all()

        ok = False
        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                break
            if verify_hidden_password(entry.get_text()):
                ok = True
                break
            error_label.set_markup("<span foreground='#e74c3c'>PIN incorrecto</span>")
            entry.set_text("")
            entry.grab_focus()
        dialog.destroy()
        return ok

    # -- Monitores y asignacion -----------------------------------------------

    def _monitor_subtitle(self, mon):
        wid = self.assignments.get(mon)
        item = self.items_by_id.get(wid) if wid else None
        return item["title"] if item else (wid or "?")

    def update_monitor_label(self, mon):
        text = self._monitor_subtitle(mon)
        for labels in (getattr(self, "monitor_chip_subtitles", {}), getattr(self, "sidebar_monitor_subtitles", {})):
            label_widget = labels.get(mon)
            if label_widget:
                label_widget.set_text(text)

    def on_monitor_chip_toggled(self, chip, mon):
        if chip.get_active():
            self._set_target_monitor(mon)
            radio = self.sidebar_monitor_radios.get(mon)
            if radio and not radio.get_active():
                radio.set_active(True)

    def on_monitor_nav_toggled(self, radio, mon):
        if radio.get_active():
            self._set_target_monitor(mon)
            chip = self.monitor_chips.get(mon)
            if chip and not chip.get_active():
                chip.set_active(True)

    def _set_target_monitor(self, mon):
        self.target_monitor = mon
        self._refresh_assigned_badges()
        if self._detail_wid:
            self._update_detail_panel(self._detail_wid)
        self._sync_scaling_combo()
        self._sync_audio_widgets()
        self._sync_speed_combo()
        self.save_current_ui_state()

    def _sync_scaling_combo(self):
        mode = self.scaling.get(self.target_monitor, DEFAULT_SCALING)
        idx = SCALING_MODES.index(mode) if mode in SCALING_MODES else 0
        self.scaling_combo.handler_block_by_func(self.on_scaling_changed)
        self.scaling_combo.set_active(idx)
        self.scaling_combo.handler_unblock_by_func(self.on_scaling_changed)

    def on_scaling_changed(self, combo):
        idx = combo.get_active()
        if idx < 0:
            return
        mode = SCALING_MODES[idx]
        self.scaling[self.target_monitor] = mode
        save_scaling(self.scaling)
        self._reapply_current(self.target_monitor)
        self.status_label.set_text(f"Escalado de {self.target_monitor}: {SCALING_LABELS.get(mode, mode)}")

    def _sync_speed_combo(self):
        speed = self.speed.get(self.target_monitor, DEFAULT_SPEED)
        idx = SPEED_OPTIONS.index(speed) if speed in SPEED_OPTIONS else 0
        self.speed_combo.handler_block_by_func(self.on_speed_changed)
        self.speed_combo.set_active(idx)
        self.speed_combo.handler_unblock_by_func(self.on_speed_changed)
        wid = self.assignments.get(self.target_monitor)
        kind = self.items_by_id.get(wid, {}).get("type")
        supported = engine_supports_speed() and kind in ("Scene", "Video")
        self.speed_combo.set_sensitive(supported)
        self.speed_combo.set_tooltip_text(
            "Velocidad de reproducción de escenas y vídeos" if supported else
            "La velocidad requiere un fondo de escena/vídeo y un motor con --speed")

    def on_speed_changed(self, combo):
        idx = combo.get_active()
        if idx < 0:
            return
        speed = SPEED_OPTIONS[idx]
        self.speed[self.target_monitor] = speed
        save_speed(self.speed)
        self._reapply_current(self.target_monitor)
        self.status_label.set_text(f"Velocidad de {self.target_monitor}: {speed:g}x")

    def _sync_audio_widgets(self):
        conf = self.audio.get(self.target_monitor, {})
        muted = conf.get("muted", True)
        volume = conf.get("volume", DEFAULT_VOLUME)

        self.audio_toggle.handler_block_by_func(self.on_audio_toggled)
        self.audio_toggle.set_active(not muted)
        self.audio_toggle.handler_unblock_by_func(self.on_audio_toggled)

        self.volume_scale.handler_block_by_func(self.on_volume_changed)
        self.volume_scale.set_value(volume)
        self.volume_scale.handler_unblock_by_func(self.on_volume_changed)

        self.volume_scale.set_sensitive(not muted)
        icon = "audio-volume-high-symbolic" if not muted else "audio-volume-muted-symbolic"
        self.audio_toggle.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
        self.audio_toggle.set_tooltip_text(
            f"Audio activado ({self.target_monitor})" if not muted else f"Audio silenciado ({self.target_monitor})"
        )

    def _save_audio_for_target(self, muted, volume):
        self.audio[self.target_monitor] = {"muted": muted, "volume": volume}
        save_audio(self.audio)
        self._reapply_current(self.target_monitor)

    def on_audio_toggled(self, toggle):
        muted = not toggle.get_active()
        volume = int(self.volume_scale.get_value())
        self._save_audio_for_target(muted, volume)
        self.volume_scale.set_sensitive(not muted)
        icon = "audio-volume-high-symbolic" if not muted else "audio-volume-muted-symbolic"
        self.audio_toggle.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
        self.status_label.set_text(
            f"Audio {'activado' if not muted else 'silenciado'} en {self.target_monitor}"
        )

    def on_volume_changed(self, scale):
        # Solo actualiza el valor en memoria mientras se arrastra; guardar a disco
        # y relanzar el motor se hace al soltar (on_volume_release), para no
        # reiniciar linux-wallpaperengine en cada tick del deslizador.
        if not self.audio_toggle.get_active():
            return
        conf = self.audio.setdefault(self.target_monitor, {"muted": False})
        conf["volume"] = int(scale.get_value())

    def on_volume_release(self, scale, event):
        if self.audio_toggle.get_active():
            self._save_audio_for_target(False, int(scale.get_value()))
        return False

    def _reapply_current(self, monitor):
        wid = self.assignments.get(monitor)
        if wid and self._allow_web_for(wid):
            subprocess.Popen([APPLY_SCRIPT, f"{monitor}={wid}"])

    def _ask_web_permission(self):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            text="¿Permitir wallpapers web?",
        )
        dialog.format_secondary_text(
            "Los fondos web ejecutan HTML y JavaScript de terceros. "
            "El aislamiento del motor puede ser limitado y no está verificado en esta instalación. "
            "Permítelos solo si confías en su contenido. "
            "Puedes volver a desactivarlos desde el menú de acciones."
        )
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL,
                           "Permitir wallpapers web", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        accepted = dialog.run() == Gtk.ResponseType.OK
        dialog.destroy()
        return accepted

    def _allow_web_for(self, wid):
        from .apply import project_type
        if project_type(wid) != "web" or web_wallpapers_allowed():
            return True
        if not self._ask_web_permission():
            self.status_label.set_text("Aplicación de fondo web cancelada.")
            return False
        set_web_wallpapers_allowed(True)
        return True

    def _disable_web_wallpapers(self, *_args):
        set_web_wallpapers_allowed(False)
        self.status_label.set_text("Fondos web desactivados para nuevas aplicaciones.")

    def assign_and_apply(self, wid, monitor=None):
        if not self._allow_web_for(wid):
            return
        monitor = monitor or self.target_monitor
        # Una asignacion manual desactiva cualquier rotacion activa en esa pantalla,
        # para que el demonio de rotacion no la sobrescriba mas tarde.
        playlists = load_playlists()
        if playlists.get(monitor, {}).get("enabled"):
            playlists[monitor]["enabled"] = False
            save_playlists(playlists)

        subprocess.Popen([APPLY_SCRIPT, f"{monitor}={wid}"])
        title = self.items_by_id.get(wid, {}).get("title", wid)
        self.status_label.set_text(f"Aplicando en {monitor}: {title}")

    def _refresh_compat(self):
        """Recarga el historial de compatibilidad (lo escribe el vigilante 15 s despues de aplicar) y
        actualiza solo las tarjetas cuyo estado cambio."""
        history = compat.load_history()
        known_bad = load_known_bad()
        changed = {w for w in set(history) | set(self.compat_history) if history.get(w) != self.compat_history.get(w)}
        changed |= {w for w in set(known_bad) | set(self.known_bad) if (w in known_bad) != (w in self.known_bad)}
        self.compat_history, self.known_bad = history, known_bad
        for wid in changed:
            self._update_card_badge(wid)
        if self._detail_wid in changed:
            self._update_detail_panel(self._detail_wid)

    def _poll_apply_status(self):
        self._compat_tick = getattr(self, "_compat_tick", 0) + 1
        if self._compat_tick % 5 == 0:
            self._refresh_compat()
        for monitor in self.monitors:
            state = load_json(os.path.join(CONF_DIR, f"status_{monitor}.json"), {})
            token = state.get("token")
            if not token or token == self._apply_seen.get(monitor):
                continue
            self._apply_seen[monitor] = token
            wid = state.get("id")
            self.assignments = load_current_assignments(self.monitors)
            self.update_monitor_label(monitor)
            self._refresh_assigned_badges()
            self.known_bad = load_known_bad()
            self.compat_history = compat.load_history()
            for card_wid, card in self.cards.items():
                self._update_card_badge(card_wid)
            self._sync_speed_combo()
            if state.get("state") == "rolled_back":
                failed_title = self.items_by_id.get(state.get("failed_id"), {}).get("title", state.get("failed_id"))
                good_title = self.items_by_id.get(wid, {}).get("title", wid)
                self.status_label.set_text(
                    f"{failed_title} falló en {monitor}; se restauró {good_title}. Motivo: {state.get('detail', '')[:200]}")
                self._show_rollback_dialog(monitor, failed_title, good_title, state.get("detail", ""))
            elif state.get("state") in ("failed", "blocked"):
                title = self.items_by_id.get(wid, {}).get("title", wid)
                self.status_label.set_text(f"No se pudo reproducir {title} en {monitor}: {state.get('detail', '')[:300]}")
            elif state.get("state") == "running":
                self.recent_ids = record_recent(wid)
                title = self.items_by_id.get(wid, {}).get("title", wid)
                self.status_label.set_text(f"Fondo iniciado en {monitor}: {title}")
                self.flowbox.invalidate_filter()
                self.flowbox.invalidate_sort()
        return True

    def _show_rollback_dialog(self, monitor, failed_title, good_title, detail):
        dialog = Gtk.MessageDialog(transient_for=self, modal=False, message_type=Gtk.MessageType.WARNING,
                                   text=f"«{failed_title}» no se pudo reproducir")
        dialog.format_secondary_text(
            f"Se ha restaurado el fondo anterior en {monitor}: «{good_title}».\n\nMotivo: {detail.strip()[:500] or 'el motor terminó de forma inesperada'}")
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, _r: d.destroy())
        dialog.show_all()

    def get_selected_ids(self):
        return [child.get_child().wid for child in self.flowbox.get_selected_children()]

    # -- Favoritos, ocultos, desuscribir --------------------------------------

    def on_card_favorite_toggled(self, wid, is_favorite):
        if is_favorite:
            self.favorite_ids.add(wid)
        else:
            self.favorite_ids.discard(wid)
        save_favorite_ids(self.favorite_ids)
        if self.current_tab == "Favoritos":
            self.flowbox.invalidate_filter()
        if wid == self._detail_wid:
            self.detail_heart.handler_block_by_func(self._on_detail_heart_toggled)
            self.detail_heart.set_active(is_favorite)
            self.detail_heart.handler_unblock_by_func(self._on_detail_heart_toggled)
            self._update_detail_heart_icon()

    def on_toggle_hidden_clicked(self, button):
        ids = self.get_selected_ids()
        if not ids:
            self.status_label.set_text("Selecciona uno o mas wallpapers primero")
            return
        currently_hidden = sum(1 for wid in ids if wid in self.hidden_ids)
        make_hidden = currently_hidden < len(ids)
        for wid in ids:
            self._set_hidden(wid, make_hidden)
        save_hidden_ids(self.hidden_ids)
        self.flowbox.invalidate_filter()
        action = "Ocultado(s)" if make_hidden else "Mostrado(s) de nuevo"
        self.status_label.set_text(f"{action}: {len(ids)} wallpaper(s)")

    def _set_hidden(self, wid, hidden):
        if hidden:
            self.hidden_ids.add(wid)
        else:
            self.hidden_ids.discard(wid)
        self._update_card_badge(wid)
        if wid == self._detail_wid:
            self.detail_hide_btn.set_label("Mostrar de nuevo" if hidden else "Ocultar")

    def on_unsubscribe_clicked(self, button):
        ids = self.get_selected_ids()
        if not ids:
            self.status_label.set_text("Selecciona uno o mas wallpapers primero")
            return
        self._unsubscribe_ids(ids)

    def _unsubscribe_ids(self, ids):
        titles = [self.items_by_id.get(wid, {}).get("title", wid) for wid in ids]
        used_on = sorted({mon for mon, vid in self.assignments.items() if vid in ids})
        warning = f"\n\nAviso: hay pantallas usando alguno de estos: {', '.join(used_on)}." if used_on else ""
        names = ", ".join(titles) if len(titles) <= 3 else f"{len(titles)} wallpapers"

        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            text="Desuscribirse y borrar" + (" este wallpaper" if len(ids) == 1 else f" {len(ids)} wallpapers"),
        )
        dialog.format_secondary_text(
            f"Se borrara el contenido local de: {names}.{warning}\n\n"
            "Esto NO desuscribe tu cuenta real de Steam (el login anonimo que usa la "
            "descarga no puede hacerlo). Si no quieres que Steam los vuelva a "
            "descargar mas adelante, abrelos en Steam y pulsa 'Unsubscribe' alli con tu cuenta."
        )
        dialog.add_buttons(
            "Cancelar", Gtk.ResponseType.CANCEL,
            "Solo borrar local", Gtk.ResponseType.OK,
            "Borrar y abrir en Steam", Gtk.ResponseType.APPLY,
        )
        response = dialog.run()
        dialog.destroy()

        if response not in (Gtk.ResponseType.OK, Gtk.ResponseType.APPLY):
            return

        for wid in ids:
            unsubscribe_workshop_item(wid)
            self.hidden_ids.discard(wid)
            self.favorite_ids.discard(wid)
        save_hidden_ids(self.hidden_ids)
        save_favorite_ids(self.favorite_ids)
        self.on_refresh_clicked()
        self.status_label.set_text(f"Borrado(s) localmente: {len(ids)} wallpaper(s)")

        if response == Gtk.ResponseType.APPLY:
            for wid in ids:
                open_in_steam(wid)

    # -- Panel de detalle ------------------------------------------------------

    def on_selection_changed(self, flowbox):
        ids = self.get_selected_ids()
        if len(ids) == 1:
            self._update_detail_panel(ids[0])
            self.status_label.set_text(f"{len(self.all_items)} wallpapers")
        else:
            self.detail_revealer.set_reveal_child(False)
            self._detail_wid = None
            if len(ids) > 1:
                self.status_label.set_text(f"{len(self.all_items)} wallpapers · {len(ids)} seleccionados")
            else:
                self.status_label.set_text(f"{len(self.all_items)} wallpapers")

    def _format_date(self, mtime):
        if not mtime:
            return "-"
        try:
            return datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y")
        except Exception:
            return "-"

    def _update_detail_panel(self, wid):
        item = self.items_by_id.get(wid)
        if not item:
            self.detail_revealer.set_reveal_child(False)
            return
        self._detail_wid = wid

        big = None
        if item.get("preview_path") and os.path.isfile(item["preview_path"]):
            try:
                big = GdkPixbuf.Pixbuf.new_from_file_at_scale(item["preview_path"], 272, 153, True)
            except Exception:
                big = None
        self.detail_image.set_from_pixbuf(big or item.get("pixbuf"))

        self.detail_title.set_text(item["title"])

        self.detail_heart.handler_block_by_func(self._on_detail_heart_toggled)
        self.detail_heart.set_active(wid in self.favorite_ids)
        self.detail_heart.handler_unblock_by_func(self._on_detail_heart_toggled)
        self._update_detail_heart_icon()

        self.detail_assign_btn.set_label(f"Asignar a {self.target_monitor}")
        self.detail_hide_btn.set_label("Mostrar de nuevo" if wid in self.hidden_ids else "Ocultar")
        self.detail_repair_btn.set_visible(wid in self.known_bad)

        for child in list(self.detail_info_grid.get_children()):
            self.detail_info_grid.remove(child)
        rows = [
            ("Tipo", (item.get("type") or "Desconocido") + (" (preset)" if item.get("preset") else "")),
            ("Compatibilidad", (lambda c: f"{c[1]}. {c[2]}")(self._compat_for(wid))),
            ("Categorias", ", ".join(item.get("tags", [])[:4]) or "-"),
            ("Clasificacion", item.get("rating") or "Desconocido"),
            ("Anadido", self._format_date(item.get("mtime"))),
        ]
        for i, (label, value) in enumerate(rows):
            l1 = Gtk.Label(label=label, xalign=0)
            l1.get_style_context().add_class("dim-label")
            l2 = Gtk.Label(label=value, xalign=0)
            l2.set_line_wrap(True)
            self.detail_info_grid.attach(l1, 0, i, 1, 1)
            self.detail_info_grid.attach(l2, 1, i, 1, 1)
        self.detail_info_grid.show_all()

        for child in list(self.detail_tags_box.get_children()):
            self.detail_tags_box.remove(child)
        for tag in item.get("tags", []):
            chip = Gtk.Label(label=tag)
            chip.get_style_context().add_class("wpe-tag-chip")
            self.detail_tags_box.add(chip)
        self.detail_tags_box.show_all()

        self.detail_revealer.set_reveal_child(True)

    def _update_detail_heart_icon(self):
        icon = "starred-symbolic" if self.detail_heart.get_active() else "non-starred-symbolic"
        self.detail_heart.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))

    def _on_detail_heart_toggled(self, btn):
        if not self._detail_wid:
            return
        self.on_card_favorite_toggled(self._detail_wid, btn.get_active())
        card = self.cards.get(self._detail_wid)
        if card:
            card.set_favorite(btn.get_active())
        self._update_detail_heart_icon()

    def _on_detail_assign_clicked(self, button):
        if self._detail_wid:
            self.assign_and_apply(self._detail_wid)

    def _on_detail_preview_clicked(self, button):
        if self._detail_wid:
            self.show_preview(self._detail_wid)

    def _on_detail_add_rotation(self, button):
        if self._detail_wid:
            self.add_to_rotation(self._detail_wid, self.target_monitor)

    def _on_detail_customize_clicked(self, button):
        if not self._detail_wid:
            return
        wid = self._detail_wid
        item = self.items_by_id.get(wid, {})
        dialog = PropertiesDialog(self, wid, item.get("title", wid), on_saved=self._on_properties_saved)
        dialog.run_and_handle()

    def _on_properties_saved(self, wid):
        screens = [mon for mon, vid in self.assignments.items() if vid == wid]
        for mon in screens:
            self._reapply_current(mon)
        if screens:
            self.status_label.set_text(f"Propiedades guardadas, reaplicado en: {', '.join(screens)}")
        else:
            self.status_label.set_text("Propiedades guardadas (se aplicaran la proxima vez que asignes este wallpaper)")

    def _on_detail_repair_clicked(self, button):
        if not self._detail_wid:
            return
        wid = self._detail_wid
        self.status_label.set_text("Intentando reparar...")
        while Gtk.events_pending():
            Gtk.main_iteration()

        ok, msg = attempt_repair(wid)
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO if ok else Gtk.MessageType.WARNING,
            text="Reparado" if ok else "No se pudo reparar",
        )
        dialog.format_secondary_text(msg)
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.run()
        dialog.destroy()

        if ok:
            self._remove_known_bad(wid)
            self._update_card_badge(wid)
            self.detail_repair_btn.set_visible(False)
            self.status_label.set_text(f"Reparado: {msg}")

    def _remove_known_bad(self, wid):
        if wid not in self.known_bad:
            return
        self.known_bad.pop(wid, None)
        compat.clear(wid)
        self.compat_history.pop(wid, None)
        try:
            atomic_write_json(KNOWN_BAD_FILE, self.known_bad)
        except Exception:
            pass

    def on_repair_all_clicked(self, button):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            text="Reparar toda la biblioteca",
        )
        dialog.format_secondary_text(
            "Revisa todos los wallpapers descargados en busca de la incompatibilidad "
            "conocida de 'padding' en objetos de texto (la que hacia crashear a "
            "linux-wallpaperengine) y la corrige automaticamente. Cada scene.pkg "
            "modificado se respalda antes como scene.pkg.bak_original. Puede tardar "
            "un rato si tienes muchos wallpapers descargados."
        )
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Reparar", Gtk.ResponseType.OK)
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return

        self.status_label.set_text("Reparando biblioteca... 0%")
        threading.Thread(target=self._repair_all_thread, daemon=True).start()

    def _repair_all_thread(self):
        def progress(i, total, wid):
            pct = int(100 * i / total) if total else 100
            GLib.idle_add(self.status_label.set_text, f"Reparando biblioteca... {pct}% ({i}/{total})")

        repaired, total = attempt_repair_all(progress_callback=progress)
        GLib.idle_add(self._on_repair_all_done, repaired, total)

    def _on_repair_all_done(self, repaired, total):
        for wid in repaired:
            self._remove_known_bad(wid)
            self._update_card_badge(wid)

        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
            text="Reparacion de biblioteca completada",
        )
        if repaired:
            names = ", ".join(self.items_by_id.get(w, {}).get("title", w) for w in repaired)
            dialog.format_secondary_text(f"Reparados {len(repaired)} de {total} wallpapers revisados:\n{names}")
        else:
            dialog.format_secondary_text(f"Revisados {total} wallpapers, ninguno tenia esta incompatibilidad.")
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.run()
        dialog.destroy()

        self.status_label.set_text(f"Biblioteca revisada: {len(repaired)}/{total} reparados")
        return False

    def _on_detail_hide_clicked(self, button):
        if not self._detail_wid:
            return
        wid = self._detail_wid
        self._set_hidden(wid, wid not in self.hidden_ids)
        save_hidden_ids(self.hidden_ids)
        self.flowbox.invalidate_filter()

    def _on_detail_unsub_clicked(self, button):
        if self._detail_wid:
            self._unsubscribe_ids([self._detail_wid])

    # -- Vista previa grande y menu contextual --------------------------------

    def show_preview(self, wid):
        item = self.items_by_id.get(wid)
        if not item:
            return

        dialog = Gtk.Dialog(title=item["title"], transient_for=self, modal=True)
        dialog.set_default_size(720, 500)
        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)

        pixbuf = item.get("pixbuf")
        preview_path = item.get("preview_path")
        big_pixbuf = None
        if preview_path and os.path.isfile(preview_path):
            try:
                big_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(preview_path, 680, 400, True)
            except Exception:
                big_pixbuf = None
        image = Gtk.Image.new_from_pixbuf(big_pixbuf or pixbuf)
        box.add(image)

        info_parts = [item["type"], item["rating"]] + item.get("tags", [])[:4]
        info_label = Gtk.Label(label=" · ".join(p for p in info_parts if p and p != "Desconocido"))
        info_label.get_style_context().add_class("dim-label")
        box.add(info_label)

        assign_btn = icon_button(f"Asignar a {self.target_monitor}", "emblem-ok-symbolic")
        assign_btn.get_style_context().add_class("suggested-action")
        assign_btn.connect("clicked", lambda *_: (self.assign_and_apply(wid), dialog.destroy()))
        box.add(assign_btn)

        live_btn = icon_button(f"Probar en ventana ({PREVIEW_SECONDS} s)", "media-playback-start-symbolic")
        live_btn.connect("clicked", lambda *_: (self.start_live_preview(wid), dialog.destroy()))
        box.add(live_btn)

        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def start_live_preview(self, wid):
        """Prueba el wallpaper en una ventana propia (se cierra sola); no cambia el escritorio."""
        title = self.items_by_id.get(wid, {}).get("title", wid)
        if not self._allow_web_for(wid):
            return

        def done(ok, message):
            def update():
                self._refresh_compat()
                if ok:
                    self.status_label.set_text(f"Prueba de {title}: {message}")
                else:
                    self.status_label.set_text(f"{title} falló en la prueba: {message[:300]}")
                    self._show_rollback_dialog_text(title, message)
                return False
            GLib.idle_add(update)

        error = self.live_preview.start(wid, done)
        if error:
            self.status_label.set_text(f"No se pudo probar {title}: {error}")
        else:
            self.status_label.set_text(
                f"Probando {title} en una ventana ({PREVIEW_SECONDS} s); no se cambia el escritorio. "
                f"Cierra la ventana cuando quieras.")

    def _on_detail_live_preview(self, button):
        children = self.flowbox.get_selected_children()
        if children:
            self.start_live_preview(children[0].get_child().wid)
        else:
            self.status_label.set_text("Selecciona un wallpaper primero")

    def _show_rollback_dialog_text(self, title, detail):
        dialog = Gtk.MessageDialog(transient_for=self, modal=False, message_type=Gtk.MessageType.WARNING,
                                   text=f"«{title}» falló en la prueba")
        dialog.format_secondary_text(
            f"No se ha cambiado tu escritorio.\n\nMotivo: {detail.strip()[:500] or 'el motor terminó de forma inesperada'}")
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, _r: d.destroy())
        dialog.show_all()

    def show_context_menu(self, card, event, wid):
        menu = Gtk.Menu()

        for mon in self.monitors:
            mi = Gtk.MenuItem(label=f"Asignar a {mon}")
            mi.connect("activate", lambda _mi, m=mon: self.assign_and_apply(wid, monitor=m))
            menu.append(mi)

        menu.append(Gtk.SeparatorMenuItem())

        fav_item = Gtk.CheckMenuItem(label="Favorito")
        fav_item.set_active(wid in self.favorite_ids)
        fav_item.connect("toggled", lambda mi: card.heart_btn.set_active(mi.get_active()))
        menu.append(fav_item)

        live_item = Gtk.MenuItem(label="Probar en ventana")
        live_item.connect("activate", lambda *_: self.start_live_preview(wid))
        menu.append(live_item)

        preview_item = Gtk.MenuItem(label="Vista previa")
        preview_item.connect("activate", lambda *_: self.show_preview(wid))
        menu.append(preview_item)

        menu.append(Gtk.SeparatorMenuItem())

        rotation_item = Gtk.MenuItem(label=f"Anadir a rotacion ({self.target_monitor})")
        rotation_item.connect("activate", lambda *_: self.add_to_rotation(wid, self.target_monitor))
        menu.append(rotation_item)

        hide_item = Gtk.MenuItem(label="Mostrar de nuevo" if wid in self.hidden_ids else "Ocultar")
        hide_item.connect("activate", lambda *_: self._toggle_hidden_single(wid))
        menu.append(hide_item)

        menu.append(Gtk.SeparatorMenuItem())

        unsub_item = Gtk.MenuItem(label="Desuscribirse")
        unsub_item.connect("activate", lambda *_: self._unsubscribe_ids([wid]))
        menu.append(unsub_item)

        menu.show_all()
        if event is not None:
            menu.popup_at_pointer(event)
        else:
            menu.popup_at_widget(card.menu_btn, Gdk.Gravity.SOUTH_EAST, Gdk.Gravity.NORTH_EAST, None)

    def _toggle_hidden_single(self, wid):
        self._set_hidden(wid, wid not in self.hidden_ids)
        save_hidden_ids(self.hidden_ids)
        self.flowbox.invalidate_filter()

    def add_to_rotation(self, wid, monitor):
        playlists = load_playlists()
        data = playlists.setdefault(monitor, {"enabled": False, "interval_minutes": 30, "items": [], "current_index": 0, "last_switch": 0})
        if wid not in data.get("items", []):
            data.setdefault("items", []).append(wid)
            save_playlists(playlists)
            self.status_label.set_text(f"Anadido a la rotacion de {monitor}")
        else:
            self.status_label.set_text("Ya estaba en la rotacion de esa pantalla")

    # -- Ventanas secundarias --------------------------------------------------

    def _open_diagnostics(self, _button=None):
        """Informe de estado (pantallas, fallos, rotación y registro del motor) para leer o copiar."""
        dialog = Gtk.Dialog(title="Diagnóstico", transient_for=self, modal=False)
        dialog.set_default_size(820, 560)
        box = dialog.get_content_area()
        box.set_border_width(10)
        box.set_spacing(8)
        buffer = Gtk.TextBuffer()
        view = Gtk.TextView(buffer=buffer, editable=False, monospace=True)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.add(view)
        box.pack_start(scrolled, True, True, 0)
        note = Gtk.Label(label="Sin claves ni datos privados: la carpeta personal aparece como ~.", xalign=0)
        note.get_style_context().add_class("dim-label")
        box.pack_start(note, False, False, 0)

        def refresh(*_):
            buffer.set_text(diagnostics.build_report())

        def copy(*_):
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False), -1)
            clipboard.store()
            note.set_text("Informe copiado al portapapeles.")

        def open_folder(*_):
            subprocess.Popen(["xdg-open", CONF_DIR], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        dialog.add_button("Abrir carpeta de registros", 1).connect("clicked", open_folder)
        dialog.add_button("Actualizar", 2).connect("clicked", refresh)
        dialog.add_button("Copiar informe", 3).connect("clicked", copy)
        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, r: d.destroy() if r == Gtk.ResponseType.CLOSE else None)
        refresh()
        dialog.show_all()

    def _open_stage_characters(self, _button=None):
        """Ventana para descargar y quitar los personajes del wallpaper Nikke Stage."""
        existing = getattr(self, "stage_window", None)
        if existing is not None:
            existing.present()
            return
        self.stage_window = StageCharactersWindow(on_done=self.on_refresh_clicked)
        self.stage_window.connect("destroy", lambda *_: setattr(self, "stage_window", None))

    def on_open_workshop_browser(self, button):
        if self.workshop_window is None or not self.workshop_window.get_visible():
            self.workshop_window = WorkshopBrowserWindow(on_downloaded=self.on_refresh_clicked)
            self.workshop_window.show_all()
        else:
            self.workshop_window.present()

    def on_open_playlist_window(self, button):
        if self.playlist_window is None or not self.playlist_window.get_visible():
            self.playlist_window = PlaylistWindow(self.monitors, self.all_items, on_saved=self.on_refresh_clicked)
            self.playlist_window.show_all()
        else:
            self.playlist_window.present()

    def on_open_settings(self, button):
        dialog = Gtk.Dialog(title="Ajustes", transient_for=self, modal=True)
        dialog.set_default_size(380, -1)
        box = dialog.get_content_area()
        box.set_border_width(14)
        box.set_spacing(10)

        info = Gtk.Label(xalign=0)
        info.set_line_wrap(True)
        info.set_markup(
            f"Biblioteca de Steam: {GLib.markup_escape_text(STEAM_LIB)}\n"
            f"Cache de miniaturas: {GLib.markup_escape_text(CACHE_DIR)}\n\n"
            "Para cambiar la biblioteca de Steam o la API key de Steam, edita\n"
            "<tt>~/.config/wallpaperengine-picker/config.json</tt>"
        )
        box.add(info)
        box.add(Gtk.Separator())

        pw_label = "Cambiar o quitar PIN de Ocultos..." if has_hidden_password() else "Proteger 'Ocultos' con PIN..."
        pw_btn = icon_button(pw_label, "dialog-password-symbolic")
        pw_btn.connect("clicked", lambda *_: (dialog.destroy(), self._manage_hidden_password()))
        box.add(pw_btn)

        dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _manage_hidden_password(self):
        if has_hidden_password() and not self._prompt_hidden_password():
            return  # no acerto la contraseña actual, no se toca nada

        dialog = Gtk.Dialog(title="PIN de Ocultos", transient_for=self, modal=True)
        dialog.set_default_size(300, -1)
        box = dialog.get_content_area()
        box.set_border_width(14)
        box.set_spacing(8)
        box.add(Gtk.Label(label="Nuevo PIN de 4 digitos (vacio para quitar la proteccion):", xalign=0.5))
        entry1 = self._make_pin_entry()
        box.add(entry1)
        box.add(Gtk.Label(label="Repite el PIN:", xalign=0.5))
        entry2 = self._make_pin_entry()
        entry2.set_activates_default(True)
        box.add(entry2)
        error_label = Gtk.Label(xalign=0.5)
        box.add(error_label)
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        save_btn = dialog.add_button("Guardar", Gtk.ResponseType.OK)
        save_btn.get_style_context().add_class("suggested-action")
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        while True:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                break
            pin1, pin2 = entry1.get_text(), entry2.get_text()
            if not pin1:
                clear_hidden_password()
                self.status_label.set_text("Proteccion de 'Ocultos' quitada")
                break
            if len(pin1) != 4:
                error_label.set_markup("<span foreground='#e74c3c'>El PIN debe tener 4 digitos</span>")
                continue
            if pin1 != pin2:
                error_label.set_markup("<span foreground='#e74c3c'>Los dos PIN no coinciden</span>")
                entry1.set_text("")
                entry2.set_text("")
                entry1.grab_focus()
                continue
            set_hidden_password(pin1)
            self.status_label.set_text("PIN de 'Ocultos' guardado")
            break
        dialog.destroy()

    def on_refresh_clicked(self, *args):
        self.status_label.set_text("Actualizando lista de wallpapers...")
        self.populate()

    # -- Atajos de teclado y persistencia de estado ---------------------------

    def on_key_press(self, widget, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and event.keyval in (Gdk.KEY_f, Gdk.KEY_k):
            self.search_entry.grab_focus()
            return True
        if event.keyval == Gdk.KEY_Escape and self.search_entry.get_text():
            self.search_entry.set_text("")
            return True
        if event.keyval == Gdk.KEY_Delete:
            self.on_toggle_hidden_clicked(None)
            return True
        return False

    def save_current_ui_state(self):
        save_ui_state({
            "tab": self.current_tab,
            "sort": self.sort_combo.get_active_text(),
            "ratings": self.filters_btn.get_selected_ratings(),
            "types": self.filters_btn.get_selected_types(),
            "target_monitor": self.target_monitor,
        })

    def on_destroy(self, widget):
        self.live_preview.stop()
        GLib.source_remove(self._apply_poll)
        self.save_current_ui_state()


def main():
    apply_css()
    win = PickerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
