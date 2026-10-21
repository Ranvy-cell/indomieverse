"""Convert GLB KHR_materials_pbrSpecularGlossiness materials for Three.js."""
from __future__ import annotations

import argparse
import copy
import io
import json
import struct
from pathlib import Path

from PIL import Image


OLD_EXTENSION = 'KHR_materials_pbrSpecularGlossiness'
SPECULAR_EXTENSION = 'KHR_materials_specular'


def read_glb(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b'glTF':
        raise ValueError('Input is not a GLB file')
    magic, version, total = struct.unpack_from('<4sII', raw)
    if version != 2 or total != len(raw):
        raise ValueError('Input has an invalid GLB v2 header')
    offset = 12
    doc = None
    binary = b''
    while offset < total:
        length, kind = struct.unpack_from('<I4s', raw, offset)
        offset += 8
        chunk = raw[offset:offset + length]
        if len(chunk) != length:
            raise ValueError('Truncated GLB chunk')
        offset += length
        if kind == b'JSON':
            doc = json.loads(chunk.decode('utf-8').rstrip(' \0'))
        elif kind == b'BIN\0':
            binary = chunk
    if doc is None:
        raise ValueError('GLB has no JSON chunk')
    return doc, binary


def write_glb(path: Path, doc: dict, binary: bytes) -> None:
    if doc.get('buffers'):
        doc['buffers'][0]['byteLength'] = len(binary)
    json_chunk = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    json_chunk += b' ' * ((-len(json_chunk)) % 4)
    binary += b'\0' * ((-len(binary)) % 4)
    total = 12 + 8 + len(json_chunk) + 8 + len(binary)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, total)
                     + struct.pack('<I4s', len(json_chunk), b'JSON') + json_chunk
                     + struct.pack('<I4s', len(binary), b'BIN\0') + binary)


def image_bytes(doc: dict, binary: bytes, image_index: int) -> bytes:
    image = doc['images'][image_index]
    if 'bufferView' not in image:
        raise ValueError('Only embedded GLB images are supported')
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def convert(input_path: Path, output_path: Path) -> tuple[int, int]:
    doc, binary = read_glb(input_path)
    declared_length = doc.get('buffers', [{}])[0].get('byteLength', len(binary))
    binary = binary[:declared_length]
    textures = doc.get('textures', [])
    roughness_textures: dict[tuple[int, float], int] = {}
    converted = 0

    def roughness_texture(source_texture: dict, glossiness: float) -> int:
        nonlocal binary
        texture_index = source_texture['index']
        key = (texture_index, glossiness)
        if key in roughness_textures:
            return roughness_textures[key]
        texture = textures[texture_index]
        source_image = texture.get('source')
        if source_image is None:
            raise ValueError(f'Texture {texture_index} has no embedded image source')
        with Image.open(io.BytesIO(image_bytes(doc, binary, source_image))) as opened:
            rgba = opened.convert('RGBA')
            alpha = rgba.getchannel('A')
            roughness = alpha.point(lambda value: round(255 * (1 - glossiness * value / 255)))
            payload = io.BytesIO()
            roughness.save(payload, format='PNG', compress_level=6)
        aligned = (len(binary) + 3) & ~3
        if aligned > len(binary):
            binary_extend = b'\0' * (aligned - len(binary))
        else:
            binary_extend = b''
        view_index = len(doc.setdefault('bufferViews', []))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': aligned,
                                   'byteLength': len(payload.getvalue())})
        image_index = len(doc.setdefault('images', []))
        doc['images'].append({'name': f'{doc["images"][source_image].get("name", f"image_{source_image}")}_roughness',
                              'mimeType': 'image/png', 'bufferView': view_index})
        new_texture = copy.deepcopy(texture)
        new_texture['source'] = image_index
        new_texture.pop('extensions', None)
        new_texture['name'] = f'{texture.get("name", f"texture_{texture_index}")}_roughness'
        roughness_index = len(textures)
        textures.append(new_texture)
        binary += binary_extend + payload.getvalue()
        roughness_textures[key] = roughness_index
        return roughness_index

    for material in doc.get('materials', []):
        extensions = material.get('extensions', {})
        source = extensions.pop(OLD_EXTENSION, None)
        if source is None:
            continue
        converted += 1
        pbr = material.setdefault('pbrMetallicRoughness', {})
        pbr['baseColorFactor'] = copy.deepcopy(source.get('diffuseFactor', [1, 1, 1, 1]))
        if 'diffuseTexture' in source:
            pbr['baseColorTexture'] = copy.deepcopy(source['diffuseTexture'])
        pbr['metallicFactor'] = 0
        glossiness = max(0.0, min(1.0, float(source.get('glossinessFactor', 1))))
        gloss_texture = source.get('specularGlossinessTexture')
        if gloss_texture:
            pbr['roughnessFactor'] = 1
            pbr['metallicRoughnessTexture'] = copy.deepcopy(gloss_texture)
            pbr['metallicRoughnessTexture']['index'] = roughness_texture(gloss_texture, glossiness)
        else:
            pbr['roughnessFactor'] = 1 - glossiness
            pbr.pop('metallicRoughnessTexture', None)

        specular = {'specularFactor': 1,
                    'specularColorFactor': copy.deepcopy(source.get('specularFactor', [1, 1, 1]))}
        if gloss_texture:
            specular['specularColorTexture'] = copy.deepcopy(gloss_texture)
        extensions[SPECULAR_EXTENSION] = specular
        if not extensions:
            material.pop('extensions', None)

    for key in ('extensionsUsed', 'extensionsRequired'):
        values = [value for value in doc.get(key, []) if value != OLD_EXTENSION]
        if key == 'extensionsUsed' and converted:
            values.append(SPECULAR_EXTENSION)
        if values:
            doc[key] = list(dict.fromkeys(values))
        else:
            doc.pop(key, None)

    if converted == 0:
        raise ValueError(f'No {OLD_EXTENSION} materials found in {input_path}')
    write_glb(output_path, doc, binary)
    return converted, len(roughness_textures)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    materials, maps = convert(args.input, args.output)
    print(f'Converted {materials} materials; generated {maps} lossless roughness maps.')
    print(f'Wrote {args.output} ({args.output.stat().st_size:,} bytes).')


if __name__ == '__main__':
    main()
