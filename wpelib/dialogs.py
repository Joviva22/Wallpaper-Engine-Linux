"""Diálogos auxiliares de la ventana principal (perfiles, reparaciones, limpieza, diagnóstico, avisos).

Cada función recibe la ventana principal (`window`) y usa su estado público; así `main_window.py`
se queda con la cuadrícula, el panel de detalle y la lógica de aplicar, y estos diálogos se pueden
leer y probar por separado."""
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, Pango

from . import cleanup, diagnostics, profiles
from .config import (
    CONF_DIR, clear_hidden_password, has_hidden_password, load_audio, load_fps, load_scaling, load_speed,
    set_hidden_password, verify_hidden_password,
)
from .repair import list_repairs, undo_repair


def open_profiles(window, _button=None):
    """Perfiles ("Trabajo", "Juego"...): guardan y recuperan fondos, audio, escalado, rotación y fps."""
    dialog = Gtk.Dialog(title="Perfiles de escritorio", transient_for=window, modal=False)
    dialog.set_default_size(520, 420)
    box = dialog.get_content_area()
    box.set_border_width(10)
    box.set_spacing(8)
    intro = Gtk.Label(
        label="Un perfil guarda, para tus pantallas, el fondo de cada una, el audio, el escalado, la velocidad, "
              "la rotación (activa, intervalo y orden) y los fps. Las listas de rotación no se tocan.", xalign=0)
    intro.set_line_wrap(True)
    box.pack_start(intro, False, False, 0)
    store = Gtk.ListStore(str, str)
    view = Gtk.TreeView(model=store)
    view.set_headers_visible(False)
    view.append_column(Gtk.TreeViewColumn("Perfil", Gtk.CellRendererText(), text=0))
    view.append_column(Gtk.TreeViewColumn("Contenido", Gtk.CellRendererText(foreground="#888888"), text=1))
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_shadow_type(Gtk.ShadowType.IN)
    scrolled.set_vexpand(True)
    scrolled.add(view)
    box.pack_start(scrolled, True, True, 0)
    note = Gtk.Label(xalign=0)
    note.set_line_wrap(True)
    box.pack_start(note, False, False, 0)

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    entry = Gtk.Entry()
    entry.set_placeholder_text("Nombre del perfil (Trabajo, Juego, Batería...)")
    row.pack_start(entry, True, True, 0)
    save_btn = Gtk.Button(label="Guardar el estado actual")
    row.pack_start(save_btn, False, False, 0)
    box.pack_start(row, False, False, 0)

    def selected():
        model, it = view.get_selection().get_selected()
        return model[it][0] if it else None

    def refresh():
        store.clear()
        for name, data in sorted(profiles.load_profiles().items()):
            shots = len(data.get("assignments", {}))
            store.append([name, f"{shots} pantalla(s) · {data.get('fps', '?')} fps"])

    def save(*_):
        try:
            name = profiles.save_profile(entry.get_text(), window.monitors)
        except ValueError as error:
            note.set_text(str(error))
            return
        note.set_text(f"Perfil «{name}» guardado con el estado actual.")
        refresh()

    def apply_selected(*_):
        name = selected()
        if not name:
            note.set_text("Selecciona un perfil de la lista.")
            return
        ok, screens, notes = profiles.apply_profile(name, window.monitors, set(window.items_by_id))
        if not ok:
            note.set_text(notes[0])
            return
        window.fps_combo.set_active_id(str(load_fps()))
        window.scaling = load_scaling()
        window.audio = load_audio()
        window.speed = load_speed()
        window._sync_scaling_combo()
        window._sync_audio_widgets()
        window._sync_speed_combo()
        text = f"Perfil «{name}» aplicado" + (f" en {', '.join(screens)}" if screens else "") + "."
        if notes:
            text += " " + " ".join(notes)
        note.set_text(text)
        window.status_label.set_text(text)

    def delete(*_):
        name = selected()
        if name and profiles.delete_profile(name):
            note.set_text(f"Perfil «{name}» borrado.")
            refresh()

    save_btn.connect("clicked", save)
    entry.connect("activate", save)
    view.connect("row-activated", apply_selected)
    dialog.add_button("Borrar", 3).connect("clicked", delete)
    dialog.add_button("Aplicar el perfil", 2).connect("clicked", apply_selected)
    dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
    dialog.connect("response", lambda d, r: d.destroy() if r == Gtk.ResponseType.CLOSE else None)
    refresh()
    dialog.show_all()


def open_repairs(window, _button=None):
    """Lista los wallpapers reparados por la app y permite devolver cada uno a su estado original."""
    dialog = Gtk.Dialog(title="Reparaciones", transient_for=window, modal=False)
    dialog.set_default_size(760, 480)
    box = dialog.get_content_area()
    box.set_border_width(10)
    box.set_spacing(8)
    intro = Gtk.Label(
        label="Wallpapers que la app ha reparado (guarda una copia del original). Al deshacer, se restaura el "
              "original y ese wallpaper no se volverá a reparar solo; puedes repararlo a mano cuando quieras.",
        xalign=0)
    intro.set_line_wrap(True)
    box.pack_start(intro, False, False, 0)
    store = Gtk.ListStore(str, str, str, str, str)  # id, titulo, fecha, archivos, resumen
    view = Gtk.TreeView(model=store)
    for number, title in enumerate(("Wallpaper", "Fecha", "Archivos", "Qué se cambió"), 1):
        column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END), text=number)
        column.set_resizable(True)
        column.set_expand(number in (1, 4))
        view.append_column(column)
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_shadow_type(Gtk.ShadowType.IN)
    scrolled.add(view)
    box.pack_start(scrolled, True, True, 0)
    note = Gtk.Label(xalign=0)
    box.pack_start(note, False, False, 0)

    def refresh():
        store.clear()
        for entry in list_repairs():
            when = entry["at"][:16].replace("T", " ")
            title = window.items_by_id.get(entry["id"], {}).get("title", entry["id"])
            store.append([entry["id"], title, when, ", ".join(entry["files"]),
                          entry["summary"].replace("Reparado: ", "") or "(reparación anterior al registro)"])
        note.set_text("" if len(store) else "No hay reparaciones que deshacer.")

    def undo(*_):
        model, paths = view.get_selection().get_selected_rows()
        wids = [model[p][0] for p in paths]
        if not wids:
            note.set_text("Selecciona un wallpaper de la lista.")
            return
        results = [undo_repair(w) for w in wids]
        failed = [msg for ok, msg in results if not ok]
        note.set_text(failed[0] if failed else f"Restaurado el original de {len(wids)} wallpaper(s).")
        window.status_label.set_text(note.get_text())
        refresh()

    view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    undo_btn = dialog.add_button("Deshacer la reparación seleccionada", 1)
    undo_btn.connect("clicked", undo)
    dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
    dialog.connect("response", lambda d, r: d.destroy() if r == Gtk.ResponseType.CLOSE else None)
    refresh()
    dialog.show_all()


def open_cleanup(window, _button=None):
    """Muestra cuánto ocupa lo que la app puede regenerar y borra lo que elijas."""
    categories = cleanup.scan()
    dialog = Gtk.Dialog(title="Limpiar espacio", transient_for=window, modal=True)
    dialog.set_default_size(560, -1)
    box = dialog.get_content_area()
    box.set_border_width(12)
    box.set_spacing(8)
    intro = Gtk.Label(
        label="Solo se borra lo que la app vuelve a generar. No se tocan tus wallpapers, las copias de "
              "reparaciones, los personajes y voces de Nikke Stage ni tu configuración.", xalign=0)
    intro.set_line_wrap(True)
    box.pack_start(intro, False, False, 0)
    checks = []
    total = Gtk.Label(xalign=0)

    def update_total(*_):
        chosen = sum(c.size for c, check in checks if check.get_active())
        total.set_text(f"Se liberarán {cleanup.human(chosen)}")
        clean_btn.set_sensitive(any(check.get_active() for _c, check in checks))

    if not categories:
        box.pack_start(Gtk.Label(label="No hay nada que limpiar."), False, False, 0)
    for cat in categories:
        amount = cleanup.human(cat.size) if cat.size else f"{len(cat.paths)} archivos"
        check = Gtk.CheckButton(label=f"{cat.label} — {amount}")
        check.set_active(cat.default and not cat.blocked)
        check.set_sensitive(not cat.blocked)
        check.connect("toggled", update_total)
        note = Gtk.Label(label=cat.blocked or cat.note, xalign=0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("dim-label")
        note.set_margin_start(26)
        box.pack_start(check, False, False, 0)
        box.pack_start(note, False, False, 0)
        checks.append((cat, check))
    box.pack_start(total, False, False, 4)
    dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
    clean_btn = dialog.add_button("Limpiar", Gtk.ResponseType.OK)
    clean_btn.get_style_context().add_class("suggested-action")
    update_total()
    dialog.show_all()
    response = dialog.run()
    chosen = [c for c, check in checks if check.get_active()]
    dialog.destroy()
    if response != Gtk.ResponseType.OK or not chosen:
        return
    freed, errors = cleanup.clean(chosen)
    window.status_label.set_text(f"Limpieza hecha: {cleanup.human(freed)} liberados"
                               + (f" ({len(errors)} avisos: {errors[0][:120]})" if errors else ""))


def open_diagnostics(window, _button=None):
    """Informe de estado (pantallas, fallos, rotación y registro del motor) para leer o copiar."""
    dialog = Gtk.Dialog(title="Diagnóstico", transient_for=window, modal=False)
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


def show_rollback(window, monitor, failed_title, good_title, detail):
    dialog = Gtk.MessageDialog(transient_for=window, modal=False, message_type=Gtk.MessageType.WARNING,
                               text=f"«{failed_title}» no se pudo reproducir")
    dialog.format_secondary_text(
        f"Se ha restaurado el fondo anterior en {monitor}: «{good_title}».\n\nMotivo: {detail.strip()[:500] or 'el motor terminó de forma inesperada'}")
    dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
    dialog.connect("response", lambda d, _r: d.destroy())
    dialog.show_all()


def show_preview_failure(window, title, detail):
    dialog = Gtk.MessageDialog(transient_for=window, modal=False, message_type=Gtk.MessageType.WARNING,
                               text=f"«{title}» falló en la prueba")
    dialog.format_secondary_text(
        f"No se ha cambiado tu escritorio.\n\nMotivo: {detail.strip()[:500] or 'el motor terminó de forma inesperada'}")
    dialog.add_button("Cerrar", Gtk.ResponseType.CLOSE)
    dialog.connect("response", lambda d, _r: d.destroy())
    dialog.show_all()


def make_pin_entry(window):
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


def prompt_pin(window):
    dialog = Gtk.Dialog(title="PIN requerido", transient_for=window, modal=True)
    dialog.set_default_size(280, -1)
    box = dialog.get_content_area()
    box.set_border_width(14)
    box.set_spacing(8)
    box.add(Gtk.Label(label="Introduce el PIN de 4 digitos para ver los wallpapers ocultos:", xalign=0.5))
    entry = make_pin_entry(window)
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


def manage_pin(window):
    if has_hidden_password() and not prompt_pin(window):
        return  # no acerto la contraseña actual, no se toca nada

    dialog = Gtk.Dialog(title="PIN de Ocultos", transient_for=window, modal=True)
    dialog.set_default_size(300, -1)
    box = dialog.get_content_area()
    box.set_border_width(14)
    box.set_spacing(8)
    box.add(Gtk.Label(label="Nuevo PIN de 4 digitos (vacio para quitar la proteccion):", xalign=0.5))
    entry1 = make_pin_entry(window)
    box.add(entry1)
    box.add(Gtk.Label(label="Repite el PIN:", xalign=0.5))
    entry2 = make_pin_entry(window)
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
            window.status_label.set_text("Proteccion de 'Ocultos' quitada")
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
        window.status_label.set_text("PIN de 'Ocultos' guardado")
        break
    dialog.destroy()
