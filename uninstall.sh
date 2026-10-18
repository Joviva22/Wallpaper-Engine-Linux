#!/usr/bin/env bash
# Desinstala wallpaperengine-picker: quita los symlinks de ~/.local/bin, el lanzador del
# menu y las entradas de autostart creadas por install.sh, y detiene sus procesos.
# NO borra la configuracion (~/.config/wallpaperengine-picker), la cache, el repositorio,
# el motor parcheado (~/.local/opt/linux-wallpaperengine) ni los paquetes del sistema.
# Uso: ./uninstall.sh [--purge]   (--purge tambien borra configuracion y cache)
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
CONF_DIR="$HOME/.config/wallpaperengine-picker"
CACHE_DIR="$HOME/.cache/wallpaperengine-picker"
PURGE=0
[[ "${1:-}" == "--purge" ]] && PURGE=1

echo "Se van a quitar:"
for name in apply picker rotate tray autostart; do echo "  $BIN_DIR/wallpaperengine-$name"; done
echo "  $APPS_DIR/wallpaperengine-picker.desktop"
for name in autostart rotate tray; do echo "  $AUTOSTART_DIR/wallpaperengine-$name.desktop"; done
((PURGE)) && echo "  $CONF_DIR  y  $CACHE_DIR  (--purge)"
if [[ -t 0 ]]; then
    read -r -p "¿Continuar? [s/N] " answer
    [[ "$answer" =~ ^[sSyY]$ ]] || { echo "Cancelado."; exit 1; }
fi

# Detener procesos por PID (nada de pkill -f, que podria alcanzar a otros procesos).
for name in rotate tray picker; do
    for pid in $(pgrep -u "$USER" -x "wallpaperengine-$name" 2>/dev/null || true); do kill "$pid" 2>/dev/null || true; done
    for pid in $(pgrep -u "$USER" -f "^(bash|python3) $BIN_DIR/wallpaperengine-$name\$" 2>/dev/null || true); do
        kill "$pid" 2>/dev/null || true
    done
done
if [[ -d "$CONF_DIR" ]]; then
    for pidfile in "$CONF_DIR"/pid_*.pid; do
        [[ -f "$pidfile" ]] || continue
        pid=$(cat "$pidfile" 2>/dev/null || true)
        if [[ "$pid" =~ ^[0-9]+$ ]] && grep -aq "linux-wallpaperengine" "/proc/$pid/cmdline" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
fi

for name in apply picker rotate tray autostart; do rm -f "$BIN_DIR/wallpaperengine-$name"; done
rm -f "$APPS_DIR/wallpaperengine-picker.desktop"
for name in autostart rotate tray; do rm -f "$AUTOSTART_DIR/wallpaperengine-$name.desktop"; done

if ((PURGE)); then
    rm -rf "$CONF_DIR" "$CACHE_DIR"
fi
echo "Desinstalado."
