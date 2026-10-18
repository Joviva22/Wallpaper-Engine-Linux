"""Captura de salida por intento, con memoria y logs de tamaño limitado."""
import os
import selectors
import time


def append_bounded(path, data, limit):
    """Como máximo un log activo y una copia; cada uno limitado en nuevas escrituras."""
    while data:
        size = os.path.getsize(path) if os.path.exists(path) else 0
        if size >= limit:
            os.replace(path, path + '.1')
            size = 0
        part, data = data[:limit - size], data[limit - size:]
        with open(path, 'ab') as stream:
            stream.write(part)


def capture(proc, path, limit, crash_pattern, repair_pattern, on_ready=None):
    """Lee bloques, no líneas ilimitadas. Conserva firmas aunque el log rote."""
    evidence = {'crashed': False, 'repairable': False, 'tail': ''}
    overlap = b''
    tail = b''
    started = time.monotonic()
    ready = False
    eof = False
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    try:
        while True:
            events = selector.select(0.1)
            if events:
                block = os.read(proc.stdout.fileno(), 65536)
                if not block:
                    selector.unregister(proc.stdout)
                    eof = True
                if block:
                    append_bounded(path, block, limit)
                text = (overlap + block).decode('utf-8', errors='replace')
                evidence['crashed'] |= bool(crash_pattern.search(text))
                evidence['repairable'] |= bool(repair_pattern.search(text))
                overlap = block[-256:]
                tail = (tail + block)[-4000:]
            if not ready and proc.poll() is None and time.monotonic() - started >= 0.5:
                ready = True
                if on_ready:
                    on_ready()
            # Un hijo del motor puede conservar stdout después de que el motor termine.
            if (not events or eof) and proc.poll() is not None:
                break
    finally:
        selector.close()
        proc.stdout.close()
    evidence['tail'] = tail.decode('utf-8', errors='replace')
    evidence['ready'] = ready
    return evidence
