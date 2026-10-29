import struct
import json
import math
import io
from PIL import Image

def build_optimized_face():
    print("Loading raw textured Meshy model...")
    with open('m:/TDS/3D-face-reconstruction/meshy_alec_douglas_home.glb', 'rb') as f:
        data = f.read()

    chunk_len = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
    bin_data = data[20+chunk_len+8:]

    node0 = gltf['nodes'][0]
    scale = node0.get('scale', [1.0, 1.0, 1.0])
    trans = node0.get('translation', [0.0, 0.0, 0.0])

    prim = gltf['meshes'][0]['primitives'][0]
    pos_acc = gltf['accessors'][prim['attributes']['POSITION']]
    norm_acc = gltf['accessors'][prim['attributes']['NORMAL']]
    uv_acc = gltf['accessors'][prim['attributes']['TEXCOORD_0']]
    idx_acc = gltf['accessors'][prim['indices']]

    pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
    norm_bv = gltf['bufferViews'][norm_acc['bufferView']]
    uv_bv = gltf['bufferViews'][uv_acc['bufferView']]
    idx_bv = gltf['bufferViews'][idx_acc['bufferView']]

    pos_bytes = bin_data[pos_bv['byteOffset']:pos_bv['byteOffset']+pos_bv['byteLength']]
    norm_bytes = bin_data[norm_bv['byteOffset']:norm_bv['byteOffset']+norm_bv['byteLength']]
    uv_bytes = bin_data[uv_bv['byteOffset']:uv_bv['byteOffset']+uv_bv['byteLength']]
    idx_bytes = bin_data[idx_bv['byteOffset']:idx_bv['byteOffset']+idx_bv['byteLength']]

    num_verts = pos_acc['count']
    num_indices = idx_acc['count']
    print(f"Original vertices: {num_verts:,}, triangles: {num_indices//3:,}")

    # Cluster vertices with cell_size=200
    CELL_SIZE = 220
    cell_to_idx = {}
    verts = []
    normals = []
    uvs = []
    vert_map = [0] * num_verts

    # Extract texture transform scale and offset if present
    tex_transform = gltf['materials'][0]['pbrMetallicRoughness']['baseColorTexture'].get('extensions', {}).get('KHR_texture_transform', {})
    t_scale = tex_transform.get('scale', [1.0, 1.0])
    t_offset = tex_transform.get('offset', [0.0, 0.0])

    for i in range(num_verts):
        qx, qy, qz = struct.unpack_from('<HHH', pos_bytes, i*6)
        cell = (qx // CELL_SIZE, qy // CELL_SIZE, qz // CELL_SIZE)
        if cell not in cell_to_idx:
            idx = len(verts)
            cell_to_idx[cell] = idx
            
            wx = qx * scale[0] + trans[0]
            wy = qy * scale[1] + trans[1]
            wz = qz * scale[2] + trans[2]
            verts.append([wx, wy, wz])

            nx, ny, nz = struct.unpack_from('<bbb', norm_bytes, i*3)
            normals.append([nx/127.0, ny/127.0, nz/127.0])

            # UV coordinates (uint16 normalized or quantized)
            qu, qv = struct.unpack_from('<HH', uv_bytes, i*4)
            # Standard glTF normalized uint16: float = uint16 / 65535.0
            u = (qu / 65535.0) * t_scale[0] + t_offset[0]
            v = (qv / 65535.0) * t_scale[1] + t_offset[1]
            # Wrap to [0, 1]
            u = u % 1.0
            v = v % 1.0
            uvs.append([u, v])

            vert_map[i] = idx
        else:
            vert_map[i] = cell_to_idx[cell]

    print(f"Clustered vertices: {len(verts):,}")

    # Filter 2-manifold triangles
    indices = []
    edge_count = {}
    for t in range(0, num_indices, 3):
        i0, i1, i2 = struct.unpack_from('<III', idx_bytes, t*4)
        m0, m1, m2 = vert_map[i0], vert_map[i1], vert_map[i2]
        if m0 != m1 and m1 != m2 and m2 != m0:
            e0 = tuple(sorted((m0, m1)))
            e1 = tuple(sorted((m1, m2)))
            e2 = tuple(sorted((m2, m0)))
            if edge_count.get(e0, 0) < 2 and edge_count.get(e1, 0) < 2 and edge_count.get(e2, 0) < 2:
                edge_count[e0] = edge_count.get(e0, 0) + 1
                edge_count[e1] = edge_count.get(e1, 0) + 1
                edge_count[e2] = edge_count.get(e2, 0) + 1
                indices.extend([m0, m1, m2])

    print(f"Filtered triangles: {len(indices)//3:,}")

    # Extract BaseColor image from glTF
    img0_bv = gltf['bufferViews'][gltf['images'][0]['bufferView']]
    img0_bytes = bin_data[img0_bv['byteOffset']:img0_bv['byteOffset']+img0_bv['byteLength']]
    print(f"Base color image size: {len(img0_bytes):,} bytes")

    # Compress base color image to JPEG (or keep WebP if < 800 KB)
    tex_im = Image.open(io.BytesIO(img0_bytes)).convert("RGB")
    tex_buf = io.BytesIO()
    tex_im.save(tex_buf, format="JPEG", quality=85, optimize=True)
    comp_tex_bytes = tex_buf.getvalue()
    print(f"Optimized texture size: {len(comp_tex_bytes):,} bytes")

    # Build GLB
    def pad4(b, pad_byte=b'\x00'):
        rem = len(b) % 4
        return b if rem == 0 else b + (pad_byte * (4 - rem))

    bin_out = bytearray()

    # Indices (uint16)
    idx_off = len(bin_out)
    for idx in indices:
        bin_out.extend(struct.pack("<H", idx))
    idx_len = len(bin_out) - idx_off
    bin_out = bytearray(pad4(bin_out))

    # Positions
    pos_off = len(bin_out)
    min_pos = [float('inf')]*3
    max_pos = [float('-inf')]*3
    for v in verts:
        bin_out.extend(struct.pack("<fff", v[0], v[1], v[2]))
        for k in range(3):
            if v[k] < min_pos[k]: min_pos[k] = v[k]
            if v[k] > max_pos[k]: max_pos[k] = v[k]
    pos_len = len(bin_out) - pos_off
    bin_out = bytearray(pad4(bin_out))

    # Normals
    norm_off = len(bin_out)
    for n in normals:
        bin_out.extend(struct.pack("<fff", n[0], n[1], n[2]))
    norm_len = len(bin_out) - norm_off
    bin_out = bytearray(pad4(bin_out))

    # UVs
    uv_off = len(bin_out)
    for uv in uvs:
        bin_out.extend(struct.pack("<ff", uv[0], uv[1]))
    uv_len = len(bin_out) - uv_off
    bin_out = bytearray(pad4(bin_out))

    # Image
    img_off = len(bin_out)
    bin_out.extend(comp_tex_bytes)
    img_len = len(comp_tex_bytes)
    bin_out = bytearray(pad4(bin_out))

    new_gltf = {
        "asset": {"version": "2.0", "generator": "Meshy 7.1 Textured Face Model"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "AlecDouglasHome_Head"}],
        "meshes": [{
            "name": "HeadMesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 1,
                    "NORMAL": 2,
                    "TEXCOORD_0": 3
                },
                "indices": 0,
                "material": 0
            }]
        }],
        "materials": [{
            "name": "TexturedSkin",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.05,
                "roughnessFactor": 0.60
            },
            "doubleSided": True
        }],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": 4, "mimeType": "image/jpeg"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5123, "count": len(indices), "type": "SCALAR"},
            {"bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(verts), "type": "VEC3", "max": max_pos, "min": min_pos},
            {"bufferView": 2, "byteOffset": 0, "componentType": 5126, "count": len(normals), "type": "VEC3"},
            {"bufferView": 3, "byteOffset": 0, "componentType": 5126, "count": len(uvs), "type": "VEC2"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": idx_off, "byteLength": idx_len, "target": 34963},
            {"buffer": 0, "byteOffset": pos_off, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": norm_off, "byteLength": norm_len, "target": 34962},
            {"buffer": 0, "byteOffset": uv_off, "byteLength": uv_len, "target": 34962},
            {"buffer": 0, "byteOffset": img_off, "byteLength": img_len}
        ],
        "buffers": [{"byteLength": len(bin_out)}]
    }

    json_str = json.dumps(new_gltf, separators=(',', ':'))
    json_bytes = pad4(json_str.encode('utf-8'), b' ')

    total_len = 12 + (8 + len(json_bytes)) + (8 + len(bin_out))
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    c0 = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    c1 = struct.pack("<II", len(bin_out), 0x004E4942)

    out_path = 'm:/TDS/3D-face-reconstruction/face.glb'
    with open(out_path, "wb") as f:
        f.write(header)
        f.write(c0)
        f.write(json_bytes)
        f.write(c1)
        f.write(bin_out)

    print(f"Exported {out_path}: {total_len:,} bytes ({total_len/2_000_000*100:.2f}% of 2MB limit)")

build_optimized_face()
