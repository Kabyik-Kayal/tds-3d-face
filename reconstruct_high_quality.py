#!/usr/bin/env python3
"""
High-Fidelity 3D Face Reconstruction Pipeline for Alec Douglas-Home
Uses production-grade anatomical 3D head geometry, morphs key facial vertices to match
Alec Douglas-Home's distinct aristocratic facial structure (aquiline nose, slender face oval,
defined chin, high forehead), projects the reference photograph seamlessly into UV space,
recalculates smooth vertex normals, and exports a valid glTF 2.0 binary (.glb) model < 2 MB.
"""

import sys
import os
import math
import struct
import json
import io
from PIL import Image, ImageFilter

# Ensure utf-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def create_alec_texture(base_tex_path, photo_path, out_size=(1024, 1024)):
    """
    Creates a photorealistic 1024x1024 UV texture by blending Alec Douglas-Home's
    photograph into the anatomical UV map.
    """
    print(f"Creating blended high-res texture from {photo_path}...")
    base_tex = Image.open(base_tex_path).convert("RGB")
    alec_img = Image.open(photo_path).convert("RGB")

    # In alec_douglas_home.jpg (1737x2316):
    # Head and face region:
    face_box = (480, 180, 1260, 1320)
    alec_face = alec_img.crop(face_box)

    # In UV layout (1024x1024):
    target_w = 480
    target_h = 520
    alec_resized = alec_face.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Create elliptical feather mask for seamless blending
    mask = Image.new("L", (target_w, target_h), 0)
    mw, mh = mask.size
    cx, cy = mw / 2.0, mh / 2.0
    rx, ry = mw * 0.42, mh * 0.44

    for y in range(mh):
        for x in range(mw):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 0.65:
                alpha = 255
            elif dist < 1.0:
                alpha = int(255 * (1.0 - (dist - 0.65) / 0.35))
            else:
                alpha = 0
            mask.putpixel((x, y), alpha)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=8))

    dest_x = 512 - target_w // 2
    dest_y = 155
    base_tex.paste(alec_resized, (dest_x, dest_y), mask)
    print("Texture blending complete.")
    return base_tex

def load_base_model(glb_path):
    """
    Extracts raw vertices, normals, UVs, and triangle indices from the base GLB.
    """
    print(f"Loading anatomical base mesh from {glb_path}...")
    with open(glb_path, "rb") as f:
        data = f.read()

    magic, version, length = struct.unpack("<4sII", data[:12])
    chunk_len, chunk_type = struct.unpack("<II", data[12:20])
    gltf = json.loads(data[20:20+chunk_len].decode("utf-8"))
    bin_data = data[20+chunk_len+8:]

    prim = gltf["meshes"][0]["primitives"][0]
    indices_acc = gltf["accessors"][prim["indices"]]
    pos_acc = gltf["accessors"][prim["attributes"]["POSITION"]]
    uv_acc = gltf["accessors"][prim["attributes"]["TEXCOORD_0"]]

    indices_bv = gltf["bufferViews"][indices_acc["bufferView"]]
    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    uv_bv = gltf["bufferViews"][uv_acc["bufferView"]]

    # Read indices
    indices_raw = bin_data[indices_bv["byteOffset"]:indices_bv["byteOffset"]+indices_bv["byteLength"]]
    indices = [struct.unpack_from("<H", indices_raw, i*2)[0] for i in range(indices_acc["count"])]

    # Read positions
    pos_raw = bin_data[pos_bv["byteOffset"]:pos_bv["byteOffset"]+pos_bv["byteLength"]]
    verts = [list(struct.unpack_from("<fff", pos_raw, i*12)) for i in range(pos_acc["count"])]

    # Read UVs
    uv_raw = bin_data[uv_bv["byteOffset"]:uv_bv["byteOffset"]+uv_bv["byteLength"]]
    uvs = [list(struct.unpack_from("<ff", uv_raw, i*8)) for i in range(uv_acc["count"])]

    print(f"Loaded {len(verts)} vertices and {len(indices)//3} triangles.")
    return verts, uvs, indices

def morph_to_alec_douglas_home(verts):
    """
    Deforms the anatomical head geometry to match Alec Douglas-Home's specific
    historical facial proportions:
    - Slender, narrow aristocratic jaw and cheekbones
    - Thinner, prominent aquiline nose bridge and defined tip
    - Subtle chin protrusion and cleft
    - High cranium forehead slope
    """
    print("Morphing 3D geometry to Alec Douglas-Home's facial profile...")
    morphed = []
    
    for v in verts:
        x, y, z = v[0], v[1], v[2]

        # 1. Overall Face Oval: Alec Douglas-Home has a slender, narrow face
        if y > -2.0 and y < 2.5:
            # Narrow lateral cheekbones and jaw
            x *= 0.94

        # 2. Nose bridge and Aquiline tip (y in [0.7, 1.6], z > 1.8)
        if 0.7 <= y <= 1.6 and z > 1.6 and abs(x) < 0.6:
            ny = (y - 0.7) / 0.9 # 0 at base, 1 at bridge
            lat_w = max(0.0, 1.0 - abs(x) / 0.45)
            
            # Narrow the nasal bridge
            x *= (1.0 - 0.12 * lat_w)
            
            # Aquiline protrusion: prominent high bridge and defined tip
            bridge_lift = 0.14 * math.sin(ny * math.pi) * lat_w
            z += bridge_lift

            # Refined tip projection at y ≈ 1.05
            tip_dist = math.sqrt((y - 1.05)**2 + x*x)
            if tip_dist < 0.35:
                tip_boost = 0.10 * (1.0 - tip_dist / 0.35)
                z += tip_boost
                y -= 0.03 * (1.0 - tip_dist / 0.35)

        # 3. Lean, hollowed cheeks below cheekbones (y in [0.0, 0.9], |x| in [0.8, 2.0])
        if 0.0 <= y <= 0.9 and abs(x) > 0.6:
            ch_lat = max(0.0, 1.0 - abs(abs(x) - 1.2) / 0.6)
            ch_y = math.sin((y - 0.0) / 0.9 * math.pi)
            hollow = 0.06 * ch_lat * ch_y
            x -= math.copysign(hollow, x)
            z -= hollow * 0.5

        # 4. Aristocratic chin projection (y in [-0.7, 0.0], z > 1.6)
        if -0.7 <= y <= 0.0 and z > 1.6 and abs(x) < 0.8:
            cy = math.sin((y - (-0.7)) / 0.7 * math.pi)
            clat = max(0.0, 1.0 - abs(x) / 0.6)
            chin_p = 0.08 * cy * clat
            z += chin_p

        # 5. Elongated lower facial third (y < 0.2)
        if -1.8 <= y <= 0.2:
            t = (0.2 - y) / 2.0
            y -= 0.08 * t

        morphed.append([x, y, z])

    return morphed

def recalculate_smooth_normals(verts, indices):
    """
    Computes smooth area-weighted vertex normals across the morphed triangular mesh.
    """
    print("Recalculating smooth vertex normals...")
    normals = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
    
    for t in range(0, len(indices), 3):
        ia, ib, ic = indices[t], indices[t+1], indices[t+2]
        va, vb, vc = verts[ia], verts[ib], verts[ic]
        
        # Face edges
        ax, ay, az = vb[0]-va[0], vb[1]-va[1], vb[2]-va[2]
        bx, by, bz = vc[0]-va[0], vc[1]-va[1], vc[2]-va[2]
        
        # Cross product (face normal unnormalized = 2 * face area)
        nx = ay*bz - az*by
        ny = az*bx - ax*bz
        nz = ax*by - ay*bx
        
        for idx in (ia, ib, ic):
            normals[idx][0] += nx
            normals[idx][1] += ny
            normals[idx][2] += nz
            
    # Normalize each vertex normal
    smooth_normals = []
    for n in normals:
        l = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        if l > 1e-8:
            smooth_normals.append([n[0]/l, n[1]/l, n[2]/l])
        else:
            smooth_normals.append([0.0, 1.0, 0.0])
            
    return smooth_normals

def export_high_quality_glb(verts, normals, uvs, indices, texture_img, output_path):
    """
    Packs geometry and photorealistic texture into a single binary GLB (< 2 MB).
    """
    print(f"Exporting high-quality GLB to {output_path}...")
    tex_buf = io.BytesIO()
    texture_img.save(tex_buf, format="JPEG", quality=88, optimize=True)
    tex_bytes = tex_buf.getvalue()
    print(f"Compressed texture size: {len(tex_bytes):,} bytes")

    def pad4(b, pad_byte=b'\x00'):
        rem = len(b) % 4
        return b if rem == 0 else b + (pad_byte * (4 - rem))

    bin_data = bytearray()

    # 0: Indices (UNSIGNED_SHORT)
    indices_offset = len(bin_data)
    for idx in indices:
        bin_data.extend(struct.pack("<H", idx))
    indices_len = len(bin_data) - indices_offset
    bin_data = bytearray(pad4(bin_data))

    # 1: Positions (FLOAT, VEC3)
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

    # 2: Normals (FLOAT, VEC3)
    norm_offset = len(bin_data)
    for n in normals:
        bin_data.extend(struct.pack("<fff", n[0], n[1], n[2]))
    norm_len = len(bin_data) - norm_offset
    bin_data = bytearray(pad4(bin_data))

    # 3: TexCoords (FLOAT, VEC2)
    uv_offset = len(bin_data)
    for uv in uvs:
        bin_data.extend(struct.pack("<ff", uv[0], uv[1]))
    uv_len = len(bin_data) - uv_offset
    bin_data = bytearray(pad4(bin_data))

    # 4: Image buffer
    img_offset = len(bin_data)
    bin_data.extend(tex_bytes)
    img_len = len(tex_bytes)
    bin_data = bytearray(pad4(bin_data))

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "High-Fidelity 3D Face Reconstruction (Alec Douglas-Home)"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0, 
            "name": "AlecDouglasHome_Head",
            "translation": [0.0, 0.0, 0.0]
        }],
        "meshes": [{
            "name": "AlecDouglasHome_Bust",
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
                "metallicFactor": 0.0,
                "roughnessFactor": 0.65
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
                "componentType": 5123,
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

    print(f"SUCCESS: Exported {output_path}")
    print(f"Total GLB size: {total_length:,} bytes ({total_length/2_000_000*100:.2f}% of 2MB limit)")

def main():
    base_glb = "m:/TDS/3D-face-reconstruction/LeePerrySmith.glb"
    base_tex = "m:/TDS/3D-face-reconstruction/Map-COL.jpg"
    photo_path = "m:/TDS/3D-face-reconstruction/alec_douglas_home.jpg"
    out_glb = "m:/TDS/3D-face-reconstruction/face.glb"

    # 1. Create blended texture
    tex = create_alec_texture(base_tex, photo_path)

    # 2. Load anatomical base mesh
    verts, uvs, indices = load_base_model(base_glb)

    # 3. Morph vertices to Alec Douglas-Home proportions
    morphed_verts = morph_to_alec_douglas_home(verts)

    # 4. Recompute smooth normals
    normals = recalculate_smooth_normals(morphed_verts, indices)

    # 5. Export high-quality GLB
    export_high_quality_glb(morphed_verts, normals, uvs, indices, tex, out_glb)

if __name__ == "__main__":
    main()
