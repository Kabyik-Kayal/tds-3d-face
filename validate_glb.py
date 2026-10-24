import sys
import os
import struct
import json

# Ensure utf-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def validate_glb(file_path):
    print(f"=== Validating GLB: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File {file_path} does not exist!")
        return False
        
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size:,} bytes")
    
    # Requirement: no larger than 2 MB (2,000,000 bytes)
    MAX_SIZE = 2_000_000
    if file_size > MAX_SIZE:
        print(f"❌ FAIL: File size exceeds 2,000,000 bytes! ({file_size} > {MAX_SIZE})")
        return False
    else:
        print(f"✅ PASS: File size is within 2 MB limit ({file_size:,} / {MAX_SIZE:,} bytes, {file_size/MAX_SIZE*100:.1f}%)")

    with open(file_path, "rb") as f:
        data = f.read()

    if len(data) < 12:
        print("❌ FAIL: File too short to be a valid GLB container.")
        return False

    magic, version, length = struct.unpack("<4sII", data[:12])
    
    if magic != b"glTF":
        print(f"❌ FAIL: Invalid GLB magic: {magic} (expected b'glTF')")
        return False
    print(f"✅ PASS: Valid magic header: {magic.decode('ascii')}")
    
    if version != 2:
        print(f"❌ FAIL: Invalid glTF version: {version} (expected 2)")
        return False
    print(f"✅ PASS: glTF version: {version}")

    if length != file_size:
        print(f"❌ FAIL: Header length ({length}) does not match actual file size ({file_size})")
        return False
    print("✅ PASS: Header length matches file size exactly.")

    # Parse Chunks
    offset = 12
    json_data = None
    bin_data = None

    while offset < len(data):
        if offset + 8 > len(data):
            print("❌ FAIL: Corrupted chunk header at offset", offset)
            return False
            
        chunk_len, chunk_type = struct.unpack("<II", data[offset:offset+8])
        chunk_data = data[offset+8:offset+8+chunk_len]
        offset += 8 + chunk_len

        if chunk_type == 0x4E4F534A:  # "JSON"
            try:
                json_data = json.loads(chunk_data.decode("utf-8").strip())
                print("✅ PASS: Successfully parsed Chunk 0 (JSON metadata)")
            except Exception as e:
                print(f"❌ FAIL: Invalid JSON chunk: {e}")
                return False
        elif chunk_type == 0x004E4942:  # "BIN\0"
            bin_data = chunk_data
            print(f"✅ PASS: Found Chunk 1 (Binary buffer: {len(bin_data):,} bytes)")

    if json_data is None:
        print("❌ FAIL: Missing JSON chunk in GLB!")
        return False

    # Check structural glTF 2.0 properties
    asset = json_data.get("asset", {})
    print(f"glTF Asset Version: {asset.get('version')} (Generator: {asset.get('generator', 'Unknown')})")

    meshes = json_data.get("meshes", [])
    print(f"Meshes count: {len(meshes)}")
    
    materials = json_data.get("materials", [])
    textures = json_data.get("textures", [])
    images = json_data.get("images", [])
    print(f"Materials: {len(materials)}, Textures: {len(textures)}, Embedded Images: {len(images)}")

    total_vertices = 0
    total_triangles = 0

    accessors = json_data.get("accessors", [])
    for mesh in meshes:
        for prim in mesh.get("primitives", []):
            pos_acc_idx = prim.get("attributes", {}).get("POSITION")
            if pos_acc_idx is not None and pos_acc_idx < len(accessors):
                total_vertices += accessors[pos_acc_idx].get("count", 0)
            
            indices_acc_idx = prim.get("indices")
            if indices_acc_idx is not None and indices_acc_idx < len(accessors):
                total_triangles += accessors[indices_acc_idx].get("count", 0) // 3

    print(f"Total vertices: {total_vertices:,}")
    print(f"Total triangles/faces: {total_triangles:,}")

    print("\n🎉 SUMMARY: Valid GLB (glTF 2.0) Model Ready for Submission!")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "m:/TDS/3D-face-reconstruction/face.glb"
    validate_glb(target)
