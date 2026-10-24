#!/usr/bin/env python3
"""
Meshy-Derived High-Quality 3D Face Pipeline for Alec Douglas-Home
Takes the exact AI 3D reconstructed geometry from Meshy 7.1,
downsamples it to production-grade real-time density (~20k vertices),
applies seamless photographic UV mapping from Alec Douglas-Home's photo,
recalculates smooth vertex normals, and exports a valid GLB under 2 MB.
"""

import os
import sys
import math
import struct
import json
import io
from PIL import Image, ImageFilter

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def create_photographic_texture(photo_path, out_size=(1024, 1024)):
    print(f"Creating 1024x1024 photographic texture from {photo_path}...")
    orig = Image.open(photo_path).convert("RGB")
    ow, oh = orig.size
    
    # Precise facial crop from reference photo
    # Face center is at x=870, y=700 in original (1737x2316)
    face_box = (450, 120, 1290, 1450)
    face_crop = orig.crop(face_box)
    
    tw, th = out_size
    # Base background: neutral dark skin/hair tone matching Alec Douglas-Home
    tex = Image.new("RGB", (tw, th), (40, 36, 34))
    
    # Place photo in front UV region (u: 0.22 to 0.78, v: 0.12 to 0.88)
    target_w = int(tw * 0.56)
    target_h = int(th * 0.76)
    face_resized = face_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    paste_x = int(tw * 0.22)
    paste_y = int(th * 0.12)
    
    # Create soft alpha mask for seamless bilateral blending
    mask = Image.new("L", (target_w, target_h), 255)
    edge_blend = int(target_w * 0.12)
    for x in range(edge_blend):
        alpha = int(255 * (x / edge_blend))
        for y in range(target_h):
            mask.putpixel((x, y), alpha)
            mask.putpixel((target_w - 1 - x, y), alpha)
            
    # Feather top and bottom edges
    top_blend = int(target_h * 0.08)
    for y in range(top_blend):
        alpha_y = y / top_blend
        for x in range(target_w):
            cur = mask.getpixel((x, y))
            mask.putpixel((x, y), int(cur * alpha_y))
            cur_b = mask.getpixel((x, target_h - 1 - y))
            mask.putpixel((x, target_h - 1 - y), int(cur_b * alpha_y))
            
    tex.paste(face_resized, (paste_x, paste_y), mask)
    print("Texture generated successfully.")
    return tex

def process_meshy_geometry(meshy_glb_path, cell_size=180):
    print(f"Loading Meshy geometry from {meshy_glb_path}...")
    with open(meshy_glb_path, 'rb') as f:
        data = f.read()

    chunk_len = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
    bin_data = data[20+chunk_len+8:]

    node0 = gltf['nodes'][0]
    scale = node0.get('scale', [1.0, 1.0, 1.0])
    trans = node0.get('translation', [0.0, 0.0, 0.0])

    prim = gltf['meshes'][0]['primitives'][0]
    pos_acc = gltf['accessors'][prim['attributes']['POSITION']]
    idx_acc = gltf['accessors'][prim['indices']]

    pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
    idx_bv = gltf['bufferViews'][idx_acc['bufferView']]

    pos_bytes = bin_data[pos_bv['byteOffset']:pos_bv['byteOffset']+pos_bv['byteLength']]
    idx_bytes = bin_data[idx_bv['byteOffset']:idx_bv['byteOffset']+idx_bv['byteLength']]

    num_verts = pos_acc['count']
    num_indices = idx_acc['count']
    print(f"Original: {num_verts:,} vertices, {num_indices//3:,} triangles")

    # Spatial clustering
    cell_to_idx = {}
    verts = []
    vert_map = [0] * num_verts

    min_y = float('inf')
    max_y = float('-inf')

    for i in range(num_verts):
        qx, qy, qz = struct.unpack_from('<HHH', pos_bytes, i*6)
        cell = (qx // cell_size, qy // cell_size, qz // cell_size)
        if cell not in cell_to_idx:
            idx = len(verts)
            cell_to_idx[cell] = idx
            wx = qx * scale[0] + trans[0]
            wy = qy * scale[1] + trans[1]
            wz = qz * scale[2] + trans[2]
            verts.append([wx, wy, wz])
            vert_map[i] = idx
            if wy < min_y: min_y = wy
            if wy > max_y: max_y = wy
        else:
            vert_map[i] = cell_to_idx[cell]

    print(f"Clustered: {len(verts):,} vertices")

    # Remap indices with 2-manifold surface filtering
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

    print(f"Cleaned 2-manifold triangles: {len(indices)//3:,}")

    # Compute smooth vertex normals
    print("Computing smooth vertex normals...")
    normals = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
    for t in range(0, len(indices), 3):
        ia, ib, ic = indices[t], indices[t+1], indices[t+2]
        va, vb, vc = verts[ia], verts[ib], verts[ic]
        ax, ay, az = vb[0]-va[0], vb[1]-va[1], vb[2]-va[2]
        bx, by, bz = vc[0]-va[0], vc[1]-va[1], vc[2]-va[2]
        nx = ay*bz - az*by
        ny = az*bx - ax*bz
        nz = ax*by - ay*bx
        for idx in (ia, ib, ic):
            normals[idx][0] += nx
            normals[idx][1] += ny
            normals[idx][2] += nz

    smooth_normals = []
    for n in normals:
        l = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        if l > 1e-8:
            smooth_normals.append([n[0]/l, n[1]/l, n[2]/l])
        else:
            smooth_normals.append([0.0, 1.0, 0.0])

    # Compute UV mapping
    # Cylindrical unwrap around Y axis + photographic mapping
    print("Calculating UV texture coordinates...")
    uvs = []
    y_range = max(1e-5, max_y - min_y)
    
    for v in verts:
        x, y, z = v[0], v[1], v[2]
        # Angle theta: 0 is front face (+Z), +pi/2 is left (+X), -pi/2 is right (-X)
        theta = math.atan2(x, z) # theta in [-pi, pi]
        
        # Normalize u: 0.5 is front center
        u = 0.5 - (theta / (2.0 * math.pi))
        u = max(0.0, min(1.0, u))
        
        # Normalize v: 0.0 top of head, 1.0 bottom of neck
        v_coord = 1.0 - ((y - min_y) / y_range)
        v_coord = max(0.0, min(1.0, v_coord))
        uvs.append([u, v_coord])

    return verts, smooth_normals, uvs, indices

def export_final_glb(verts, normals, uvs, indices, texture_img, output_path):
    print(f"Exporting final GLB to {output_path}...")
    tex_buf = io.BytesIO()
    texture_img.save(tex_buf, format="JPEG", quality=88, optimize=True)
    tex_bytes = tex_buf.getvalue()
    print(f"Compressed texture size: {len(tex_bytes):,} bytes")

    def pad4(b, pad_byte=b'\x00'):
        rem = len(b) % 4
        return b if rem == 0 else b + (pad_byte * (4 - rem))

    bin_data = bytearray()

    # Determine index type: uint16 if max_index < 65536, else uint32
    max_idx = max(indices) if indices else 0
    use_uint16 = (max_idx < 65535)

    indices_offset = len(bin_data)
    if use_uint16:
        for idx in indices:
            bin_data.extend(struct.pack("<H", idx))
        idx_comp_type = 5123 # UNSIGNED_SHORT
    else:
        for idx in indices:
            bin_data.extend(struct.pack("<I", idx))
        idx_comp_type = 5125 # UNSIGNED_INT
    indices_len = len(bin_data) - indices_offset
    bin_data = bytearray(pad4(bin_data))

    # Positions
    pos_offset = len(bin_data)
    min_pos = [float('inf')]*3
    max_pos = [float('-inf')]*3
    for v in verts:
        bin_data.extend(struct.pack("<fff", v[0], v[1], v[2]))
        for k in range(3):
            if v[k] < min_pos[k]: min_pos[k] = v[k]
            if v[k] > max_pos[k]: max_pos[k] = v[k]
    pos_len = len(bin_data) - pos_offset
    bin_data = bytearray(pad4(bin_data))

    # Normals
    norm_offset = len(bin_data)
    for n in normals:
        bin_data.extend(struct.pack("<fff", n[0], n[1], n[2]))
    norm_len = len(bin_data) - norm_offset
    bin_data = bytearray(pad4(bin_data))

    # UVs
    uv_offset = len(bin_data)
    for uv in uvs:
        bin_data.extend(struct.pack("<ff", uv[0], uv[1]))
    uv_len = len(bin_data) - uv_offset
    bin_data = bytearray(pad4(bin_data))

    # Embedded Image
    img_offset = len(bin_data)
    bin_data.extend(tex_bytes)
    img_len = len(tex_bytes)
    bin_data = bytearray(pad4(bin_data))

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "Meshy 7.1 Reconstructed 3D Face (Alec Douglas-Home)"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0, 
            "name": "AlecDouglasHome_Head"
        }],
        "meshes": [{
            "name": "AlecDouglasHome_Mesh",
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
            "name": "SkinMaterial",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.05,
                "roughnessFactor": 0.60
            },
            "doubleSided": False
        }],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": 4, "mimeType": "image/jpeg"}],
        "samplers": [{
            "magFilter": 9729,
            "minFilter": 9987,
            "wrapS": 10497,
            "wrapT": 10497
        }],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": idx_comp_type,
                "count": len(indices),
                "type": "SCALAR"
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(verts),
                "type": "VEC3",
                "max": max_pos,
                "min": min_pos
            },
            {
                "bufferView": 2,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(normals),
                "type": "VEC3"
            },
            {
                "bufferView": 3,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(uvs),
                "type": "VEC2"
            }
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": indices_offset, "byteLength": indices_len, "target": 34963},
            {"buffer": 0, "byteOffset": pos_offset, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": norm_offset, "byteLength": norm_len, "target": 34962},
            {"buffer": 0, "byteOffset": uv_offset, "byteLength": uv_len, "target": 34962},
            {"buffer": 0, "byteOffset": img_offset, "byteLength": img_len}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    json_str = json.dumps(gltf, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    json_padded = pad4(json_bytes, b' ')

    total_length = 12 + (8 + len(json_padded)) + (8 + len(bin_data))
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    chunk0_header = struct.pack("<II", len(json_padded), 0x4E4F534A)
    chunk1_header = struct.pack("<II", len(bin_data), 0x004E4942)

    with open(output_path, "wb") as f:
        f.write(header)
        f.write(chunk0_header)
        f.write(json_padded)
        f.write(chunk1_header)
        f.write(bin_data)

    print(f"Successfully generated: {output_path}")
    print(f"Total file size: {total_length:,} bytes ({total_length/2_000_000*100:.2f}% of 2MB limit)")

def main():
    meshy_glb = "m:/TDS/3D-face-reconstruction/meshy_alec_douglas_home.glb"
    photo = "m:/TDS/3D-face-reconstruction/alec_douglas_home.jpg"
    out_glb = "m:/TDS/3D-face-reconstruction/face.glb"

    tex = create_photographic_texture(photo)
    verts, normals, uvs, indices = process_meshy_geometry(meshy_glb, cell_size=200)
    export_final_glb(verts, normals, uvs, indices, tex, out_glb)

if __name__ == "__main__":
    main()
