"""Dialogo 'Personalizar': expone las propiedades que el propio wallpaper
define (equivalente a la pestana Customize de Wallpaper Engine en Windows):
casillas, sliders, listas desplegables, selector de color y texto libre,
segun lo que --list-properties reporte para ese wallpaper en concreto."""
import re

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from .config import load_properties, save_properties
from .properties import list_properties, list_layer_properties

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_label(text):
    return _HTML_TAG_RE.sub("", text).strip() or "(sin nombre)"


def _parse_color(value):
    parts = value.replace(",", " ").split()
    try:
        r, g, b = (float(p) for p in parts[:3])
    except (ValueError, IndexError):
        r, g, b = 1.0, 1.0, 1.0
    rgba = Gdk.RGBA()
    rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, b, 1.0
    return rgba


class PropertiesDialog(Gtk.Dialog):
    def __init__(self, parent, wid, title, on_saved=None):
        super().__init__(title=f"Personalizar: {title}", transient_for=parent, modal=True)
        self.wid = wid
        self.on_saved = on_saved
        self.set_default_size(420, 520)

        self.all_overrides = load_properties()
        self.overrides = dict(self.all_overrides.get(wid, {}))
        self._getters = {}

        box = self.get_content_area()
        box.set_border_width(12)
        box.set_spacing(8)

        props = list_properties(wid)
        layers = list_layer_properties(wid)
        layer_keys = {layer["key"] for layer in layers}

        if not props:
            box.add(Gtk.Label(
                label="Este wallpaper no define propiedades personalizables,\n"
                      "o el motor no ha podido leerlas.",
                xalign=0.5,
            ))
        else:
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_vexpand(True)
            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            list_box.set_border_width(4)

            if layers:
                layers_title = Gtk.Label(label="CAPAS", xalign=0)
                layers_title.get_style_context().add_class("wpe-detail-section-title")
                list_box.pack_start(layers_title, False, False, 0)
                hint = Gtk.Label(
                    label="Fija una capa concreta para que se muestre siempre, en vez de "
                          "depender del raton u otra logica interna del wallpaper.",
                    xalign=0,
                )
                hint.set_line_wrap(True)
                hint.get_style_context().add_class("dim-label")
                list_box.pack_start(hint, False, False, 0)
                for layer in layers:
                    row = self._build_layer_row(layer)
                    if row:
                        list_box.pack_start(row, False, False, 0)
                list_box.pack_start(Gtk.Separator(), False, False, 6)

            for prop in props:
                if prop["type"] == "group" or prop["key"] in layer_keys:
                    continue
                row = self._build_row(prop)
                if row:
                    list_box.pack_start(row, False, False, 0)
            scrolled.add(list_box)
            box.add(scrolled)

        reset_btn = self.add_button("Restablecer valores", Gtk.ResponseType.REJECT)
        self.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        save_btn = self.add_button("Guardar y aplicar", Gtk.ResponseType.OK)
        save_btn.get_style_context().add_class("suggested-action")

        self.show_all()

    def _build_layer_row(self, layer):
        if layer["kind"] == "combo":
            return self._build_layer_combo_row(layer)
        return self._build_layer_toggle_row(layer)

    def _build_layer_toggle_row(self, layer):
        key = layer["key"]
        current = self.overrides.get(key, layer["value"])

        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_widget = Gtk.Label(label=_clean_label(layer["label"]), xalign=0)
        label_widget.set_line_wrap(True)
        row.pack_start(label_widget, False, False, 0)

        names = ", ".join(layer["layer_names"])
        subtitle = Gtk.Label(label=f"Capa(s): {names}", xalign=0)
        subtitle.set_line_wrap(True)
        subtitle.get_style_context().add_class("dim-label")
        row.pack_start(subtitle, False, False, 0)

        check = Gtk.CheckButton(label="Fijar siempre visible")
        check.set_active(str(current).strip() in ("1", "true", "True"))
        row.pack_start(check, False, False, 0)
        self._getters[key] = lambda c=check: "1" if c.get_active() else "0"

        return row

    def _build_layer_combo_row(self, layer):
        """Varias capas ligadas a las distintas opciones del MISMO combo (p.ej.
        nieve/cerezo/lluvia seleccionadas por una unica propiedad de 'estacion').
        Se presentan como radio buttons: solo una puede estar fijada a la vez,
        igual que decide el propio combo internamente."""
        key = layer["key"]
        current = str(self.overrides.get(key, layer["current_value"])).strip()

        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        label_widget = Gtk.Label(label=_clean_label(layer["label"]), xalign=0)
        label_widget.set_line_wrap(True)
        row.pack_start(label_widget, False, False, 0)

        radios = {}
        first = None
        for opt in layer["options"]:
            names = ", ".join(opt["layer_names"])
            text = f"{_clean_label(opt['option_label'])}  (capa: {names})"
            btn = Gtk.RadioButton.new_from_widget(first) if first else Gtk.RadioButton.new(None)
            if first is None:
                first = btn
            btn.set_label(text)
            btn.set_active(opt["condition"] == current)
            row.pack_start(btn, False, False, 0)
            radios[opt["condition"]] = btn

        def get_selected(radios=radios):
            for condition, btn in radios.items():
                if btn.get_active():
                    return condition
            return current

        self._getters[key] = get_selected
        return row

    def _build_row(self, prop):
        key, label = prop["key"], _clean_label(prop["label"] or prop["key"])
        current = self.overrides.get(key, prop["value"])

        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        label_widget = Gtk.Label(label=label, xalign=0)
        label_widget.set_line_wrap(True)
        row.pack_start(label_widget, False, False, 0)

        ptype = prop["type"]
        if ptype == "boolean":
            check = Gtk.CheckButton()
            check.set_active(str(current).strip() in ("1", "true", "True"))
            row.pack_start(check, False, False, 0)
            self._getters[key] = lambda c=check: "1" if c.get_active() else "0"

        elif ptype == "slider":
            try:
                lo, hi = float(prop["min"] or 0), float(prop["max"] or 1)
                step = float(prop["step"] or 0) or (hi - lo) / 100 or 0.01
                val = float(current)
            except (TypeError, ValueError):
                lo, hi, step, val = 0.0, 1.0, 0.01, 0.0
            adj = Gtk.Adjustment(value=val, lower=lo, upper=hi, step_increment=step)
            scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            scale.set_digits(3)
            scale.set_value_pos(Gtk.PositionType.RIGHT)
            row.pack_start(scale, False, False, 0)
            self._getters[key] = lambda s=scale: f"{s.get_value():.6g}"

        elif ptype == "combo":
            combo = Gtk.ComboBoxText()
            indices = [idx for idx, _ in prop["options"]]
            for idx, opt_label in prop["options"]:
                combo.append_text(opt_label)
            try:
                combo.set_active(indices.index(str(current).strip()))
            except ValueError:
                combo.set_active(0)
            row.pack_start(combo, False, False, 0)
            self._getters[key] = lambda c=combo, idx=indices: (idx[c.get_active()] if c.get_active() >= 0 and idx else "0")

        elif ptype == "color":
            color_btn = Gtk.ColorButton()
            color_btn.set_rgba(_parse_color(str(current)))
            row.pack_start(color_btn, False, False, 0)

            def get_color(btn=color_btn):
                rgba = btn.get_rgba()
                return f"{rgba.red:.6f} {rgba.green:.6f} {rgba.blue:.6f}"

            self._getters[key] = get_color

        elif ptype == "textinput":
            entry = Gtk.Entry()
            entry.set_text(str(current) if current is not None else "")
            row.pack_start(entry, False, False, 0)
            self._getters[key] = lambda e=entry: e.get_text()

        else:
            return None

        return row

    def collect_and_save(self):
        for key, getter in self._getters.items():
            self.overrides[key] = getter()
        self.all_overrides[self.wid] = self.overrides
        save_properties(self.all_overrides)
        if self.on_saved:
            self.on_saved(self.wid)

    def reset_and_save(self):
        self.all_overrides.pop(self.wid, None)
        save_properties(self.all_overrides)
        if self.on_saved:
            self.on_saved(self.wid)

    def run_and_handle(self):
        response = self.run()
        if response == Gtk.ResponseType.OK:
            self.collect_and_save()
        elif response == Gtk.ResponseType.REJECT:
            self.reset_and_save()
        self.destroy()
        return response
