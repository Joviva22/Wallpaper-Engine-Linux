"""Prueba de un wallpaper en una ventana propia, sin tocar el escritorio.

Lanza el motor en modo ventana (--window) durante unos segundos y lo cierra solo, de modo
que se puede ver como queda (o si falla, y por que) sin sustituir el fondo de ninguna
pantalla ni alterar el "ultimo fondo que funcionaba". Solo hay una prueba a la vez: lanzar
otra cierra la anterior."""
import os
import signal
import subprocess
import tempfile
import threading
import time

from . import apply, compat, config

PREVIEW_SECONDS = 30
WINDOW_GEOMETRY = "0x0x960x540"


def preview_command(wid, geometry=WINDOW_GEOMETRY, sound=False):
    return [
        config.engine_executable(), "--assets-dir", config.ASSETS_DIR, "--fps", "30",
        "--window", geometry, "--bg", os.path.join(config.WORKSHOP_DIR, wid),
        *(["--volume", "50"] if sound else ["--silent"]),
        *apply.property_args(wid),
    ]


class LivePreview:
    def __init__(self):
        self._proc = None
        self._lock = threading.Lock()
        self._generation = 0

    @property
    def running(self):
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    def stop(self):
        with self._lock:
            self._generation += 1
            proc, self._proc = self._proc, None
        self._terminate(proc)

    @staticmethod
    def _terminate(proc):
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
                proc.wait(timeout=3)
            except (subprocess.TimeoutExpired, OSError):
                pass

    def start(self, wid, on_done, seconds=PREVIEW_SECONDS, sound=False):
        """Abre la ventana de prueba. `on_done(ok, mensaje)` se llama (desde un hilo) al terminar:
        ok=True si la prueba duro lo previsto o el usuario la cerro; ok=False con el motivo si el
        motor fallo. Devuelve un mensaje de error inmediato (str) si no se pudo ni lanzar, o None."""
        reason = apply.web_block_reason(wid)
        if reason:
            return reason
        self.stop()
        log = tempfile.TemporaryFile()
        try:
            proc = subprocess.Popen(
                preview_command(wid, sound=sound), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env=apply.engine_env(wid), preexec_fn=apply.disable_core_dumps,
            )
        except OSError as exc:
            log.close()
            return f"No se pudo lanzar el motor: {exc}"
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._proc = proc

        def watch():
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
            with self._lock:
                superseded = generation != self._generation
            if proc.poll() is None:
                self._terminate(proc)
                if not superseded:
                    compat.record(wid, True, source="preview")
                    on_done(True, "Prueba terminada.")
                log.close()
                return
            returncode = proc.returncode
            log.seek(0)
            tail = log.read()[-3000:].decode("utf-8", errors="replace")
            log.close()
            if superseded:
                return  # el usuario cerro la prueba o lanzo otra: no es un fallo
            crashed = apply.returncode_is_crash(returncode) or apply.CRASH_LOG_PATTERN.search(tail)
            if crashed:
                compat.record(wid, False, tail.strip()[-600:] or f"código {returncode}", source="preview")
                on_done(False, f"El motor terminó con código {returncode}. " + tail.strip()[-600:])
            else:
                on_done(True, "La ventana de prueba se cerró.")

        threading.Thread(target=watch, daemon=True).start()
        return None
