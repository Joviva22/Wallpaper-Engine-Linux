"""Widgets de navegación y filtros de la ventana principal: botón de filtros y botones de la barra lateral."""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango


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
