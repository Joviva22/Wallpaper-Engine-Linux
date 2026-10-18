#!/usr/bin/env bash
# Compila linux-wallpaperengine con los parches de patches/ y lo instala SIN root en
# ~/.local/opt/linux-wallpaperengine. wallpaperengine-apply usa ese motor si existe
# (ver config.engine_executable) y si no, el del sistema.
#
# Parches incluidos:
#   0001  wallpapers web se veian en negro (Almamu/linux-wallpaperengine#629)
#   0002  --speed para escenas y video
#   0003  luces de escena (point/lpoint/ltube como puntuales, lspot, ldirectional)
#   0004  SceneScript de textos: thisScene/engine reales, engine.userProperties, Vec2/3/4 globales
#   0005  wallpapers web: entrega de propiedades de usuario (applyUserProperties)
#   0006  wallpapers web: decodificar URLs con %XX (rutas con espacios o UTF-8)
#   0007  wallpapers web: API de audio (wallpaperRegisterAudioListener)
#   0008  wallpapers web: listeners de medios (titulo, artista, estado y posicion del reproductor MPRIS)
#
# Requisitos (Arch): git cmake sdl2 glm wayland-protocols xorg-xrandr lz4 ffmpeg mpv glfw
# glew freeglut libpulse libcups at-spi2-core nss libxcomposite libxdamage nspr.
# La primera compilacion descarga CEF (cientos de MB) y tarda un buen rato.
set -euo pipefail

REPO_DIR=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)
SRC_DIR="${LWE_SRC_DIR:-$HOME/build/linux-wallpaperengine}"
PREFIX="$HOME/.local/opt/linux-wallpaperengine"
UPSTREAM="https://github.com/Almamu/linux-wallpaperengine.git"
# Commit sobre el que se probaron los parches (r627, el del paquete AUR instalado).
BASE_COMMIT="${LWE_BASE_COMMIT:-b016d7d1}"

mkdir -p "$(dirname "$SRC_DIR")"
if [[ ! -d "$SRC_DIR/.git" ]]; then
    git clone "$UPSTREAM" "$SRC_DIR"
fi
cd "$SRC_DIR"
git fetch -q origin
git checkout -q -f "$BASE_COMMIT"
git submodule update --init --recursive
git -c protocol.file.allow=always submodule update -q
git checkout -q -- .

for patch in "$REPO_DIR"/patches/*.patch; do
    echo "Aplicando $(basename "$patch")"
    git apply "$patch"
done

cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" -Wno-dev \
    -DCMAKE_CXX_FLAGS="-ffat-lto-objects -Wno-builtin-macro-redefined" \
    -DCMAKE_C_FLAGS="-Wno-builtin-macro-redefined"
cmake --build build -j"$(nproc)"
cmake --install build

# Lanzador equivalente al del paquete AUR: fija LD_LIBRARY_PATH y el directorio de trabajo
# (el motor busca sus recursos de CEF relativos a el).
install -d "$PREFIX/bin"
cat > "$PREFIX/bin/linux-wallpaperengine" <<EOF
#!/bin/bash
export LD_LIBRARY_PATH="$PREFIX/lib:\${LD_LIBRARY_PATH:-}"
cd "$PREFIX"; exec ./linux-wallpaperengine "\$@"
EOF
chmod +x "$PREFIX/bin/linux-wallpaperengine" "$PREFIX/linux-wallpaperengine"
echo "Motor parcheado instalado en $PREFIX"
