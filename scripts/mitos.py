#!/usr/bin/env python3
"""Instala "Mitos en blanco y negro" en la carpeta del Workshop (despues se aplica desde Elegir Fondo)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wpelib import mitos  # noqa: E402

if __name__ == "__main__":
    print(f"Wallpaper instalado en {mitos.install_wallpaper()}")
