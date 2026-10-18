"""Inventario estático de shaders: candidatos, no errores de ejecución certificados."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile

home = Path.home()
settings = json.loads((home / '.config/wallpaperengine-picker/config.json').read_text())
root = Path(settings['steam_library']) / 'steamapps/workshop/content/431960'
os.environ['HOME'] = tempfile.mkdtemp(prefix='wpe-shader-inventory-')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wpelib import repair


def shaders(path):
    # Leer solo la tabla y los shaders; no cargar texturas/vídeos en memoria.
    with path.open('rb') as f:
        size = path.stat().st_size
        def u32():
            data = f.read(4)
            if len(data) != 4:
                raise ValueError('Tabla truncada')
            return struct.unpack('<I', data)[0]
        length = u32()
        if length > 128 or not f.read(length).startswith(b'PKGV'):
            raise ValueError('Cabecera inválida')
        count = u32()
        if count > 100000:
            raise ValueError('Tabla excesiva')
        entries = []
        for _ in range(count):
            length = u32()
            if length > 16384:
                raise ValueError('Nombre excesivo')
            name = f.read(length).decode('utf-8')
            entries.append((name, u32(), u32()))
        start = f.tell()
        for name, offset, length in entries:
            if start + offset + length > size:
                raise ValueError('Entrada fuera del paquete')
            if name.endswith(('.vert', '.frag', '.h')) and length <= 2 * 1024 * 1024:
                f.seek(start + offset)
                yield name, f.read(length)


def inspect(name, raw):
    text = raw.decode('utf-8', errors='replace')
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    findings = []
    depth = 0
    for number, line in enumerate(clean.splitlines(), 1):
        directive = re.match(r'\s*#\s*(if|ifdef|ifndef|endif)\b', line)
        if directive:
            if directive[1] == 'endif':
                if depth == 0:
                    findings.append({'code': 'ORPHAN_ENDIF', 'line': number})
                else:
                    depth -= 1
            else:
                depth += 1
    if depth:
        findings.append({'code': 'UNCLOSED_IF', 'count': depth})
    uniforms = set(re.findall(r"\buniform\s+\w+\s+(\w+)\s*;", clean))
    for variable, expression in re.findall(r"\bconst\s+\w+\s+(\w+)\s*=([^;]+);", clean):
        dependencies = uniforms.intersection(re.findall(r"\b\w+\b", expression))
        if dependencies:
            findings.append({'code': 'CONST_FROM_UNIFORM', 'variable': variable, 'uniforms': sorted(dependencies)})
    if name.endswith('.frag'):
        for var in re.findall(r'\bvarying\s+\w+\s+(\w+)\s*;', clean):
            writes = re.findall(r'\b' + re.escape(var) + r'(?:\.[xyzwrgba]+)?\s*(?:[+*/-]?=(?!=)|\+\+|--)', clean)
            if writes:
                findings.append({'code': 'MUTATED_FRAGMENT_INPUT', 'variable': var, 'writes': len(writes)})
        if re.search(r'\bvarying\s+vec[34]\s+v_TexCoord\s*;', clean):
            if re.search(r'\bv_TexCoord\s*[-+]\s*(?:vec2|CAST2)\b', clean):
                findings.append({'code': 'WIDE_UV_VEC2_ARITHMETIC'})
    return findings


def main():
    groups = {}
    counts = collections.Counter()
    errors = []
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        counts['folders'] += 1
        pkg = folder / 'scene.pkg'
        if not pkg.is_file():
            continue
        counts['packages'] += 1
        try:
            for name, raw in shaders(pkg):
                counts['shader_entries'] += 1
                digest = hashlib.sha256(raw).hexdigest()
                key = name + ':' + digest
                if key not in groups:
                    groups[key] = {'shader': name, 'sha256': digest, 'ids': [], 'findings': inspect(name, raw)}
                if folder.name not in groups[key]['ids']:
                    groups[key]['ids'].append(folder.name)
        except (OSError, ValueError, struct.error) as exc:
            errors.append({'id': folder.name, 'error': str(exc)})
    candidates = [g for g in groups.values() if g['findings']]
    result = {'scope': 'Inspección estática de paquetes actuales, sin ejecutar fondos ni modificar biblioteca. Patrones requieren confirmar con motor y combos activos.',
              'counts': dict(counts), 'unique_shader_versions': len(groups), 'candidates': candidates, 'errors': errors}
    Path(__file__).with_name('shader_inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'counts': result['counts'], 'unique': len(groups), 'candidates': len(candidates), 'errors': errors}))
    for candidate in candidates:
        print(candidate['ids'], candidate['shader'], candidate['findings'])


if __name__ == '__main__':
    main()
