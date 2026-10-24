import struct
import json

def inspect_glb(path):
    print("=== " + path + " ===")
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack("<4sII", data[:12])
    chunk_len, chunk_type = struct.unpack("<II", data[12:20])
    gltf = json.loads(data[20:20+chunk_len].decode("utf-8"))
    print("Asset:", gltf.get("asset"))
    print("Meshes:", len(gltf.get("meshes", [])))
    for i, m in enumerate(gltf.get("meshes", [])):
        print(f" Mesh {i}: {m.get('name')}")
        for p in m.get("primitives", []):
            print("   Attrs:", list(p.get("attributes", {}).keys()))
            acc_idx = p.get("attributes", {}).get("POSITION")
            if acc_idx is not None:
                acc = gltf["accessors"][acc_idx]
                print(f"   Vertex count: {acc.get('count')}, min={acc.get('min')}, max={acc.get('max')}")
    print("Materials:", len(gltf.get("materials", [])))
    print("Textures:", len(gltf.get("textures", [])))
    print("Images:", len(gltf.get("images", [])))

inspect_glb("m:/TDS/3D-face-reconstruction/LeePerrySmith.glb")
inspect_glb("m:/TDS/3D-face-reconstruction/facecap.glb")
