import struct
import json
import math
import time

print("Loading meshy_alec_douglas_home.glb...")
t0 = time.time()
with open('m:/TDS/3D-face-reconstruction/meshy_alec_douglas_home.glb', 'rb') as f:
    data = f.read()

magic, version, length = struct.unpack('<4sII', data[:12])
chunk_len = struct.unpack('<I', data[12:16])[0]
gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
bin_data = data[20+chunk_len+8:]

prim = gltf['meshes'][0]['primitives'][0]
pos_acc = gltf['accessors'][prim['attributes']['POSITION']]
norm_acc = gltf['accessors'][prim['attributes']['NORMAL']]
idx_acc = gltf['accessors'][prim['indices']]

pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
norm_bv = gltf['bufferViews'][norm_acc['bufferView']]
idx_bv = gltf['bufferViews'][idx_acc['bufferView']]

pos_bytes = bin_data[pos_bv['byteOffset']:pos_bv['byteOffset']+pos_bv['byteLength']]
norm_bytes = bin_data[norm_bv['byteOffset']:norm_bv['byteOffset']+norm_bv['byteLength']]
idx_bytes = bin_data[idx_bv['byteOffset']:idx_bv['byteOffset']+idx_bv['byteLength']]

num_verts = pos_acc['count']
num_indices = idx_acc['count']

print(f"Loaded in {time.time()-t0:.2f}s: {num_verts:,} vertices, {num_indices//3:,} triangles")

# Node transform
node0 = gltf['nodes'][0]
scale = node0.get('scale', [1.0, 1.0, 1.0])
trans = node0.get('translation', [0.0, 0.0, 0.0])

# Quantized uint16 positions -> World float coordinates
# x_world = x_quant * scale[0] + trans[0]
print(f"Scale: {scale}, Translation: {trans}")

# Let's perform spatial grid clustering
# We want around 30,000 vertices
# Bounding box is [0, 15959] x [0, 16383] x [0, 12132]
# If cell size is ~120 units: 16000 / 120 ≈ 130 cells per axis
CELL_SIZE = 120

cell_to_new_idx = {}
new_verts = []
new_normals = []
vert_map = [0] * num_verts

print("Clustering vertices...")
t1 = time.time()
for i in range(num_verts):
    qx, qy, qz = struct.unpack_from('<HHH', pos_bytes, i*6)
    cell = (qx // CELL_SIZE, qy // CELL_SIZE, qz // CELL_SIZE)
    if cell not in cell_to_new_idx:
        new_idx = len(new_verts)
        cell_to_new_idx[cell] = new_idx
        # Convert to world float coordinates
        wx = qx * scale[0] + trans[0]
        wy = qy * scale[1] + trans[1]
        wz = qz * scale[2] + trans[2]
        new_verts.append((wx, wy, wz))
        
        # Read normal (int8 normalized)
        nx, ny, nz = struct.unpack_from('<bbb', norm_bytes, i*3)
        new_normals.append((nx/127.0, ny/127.0, nz/127.0))
        vert_map[i] = new_idx
    else:
        vert_map[i] = cell_to_new_idx[cell]

print(f"Clustered to {len(new_verts):,} vertices in {time.time()-t1:.2f}s")

# Remap triangles and eliminate degenerate faces
print("Remapping triangles...")
new_indices = []
seen_triangles = set()

for t in range(0, num_indices, 3):
    i0, i1, i2 = struct.unpack_from('<III', idx_bytes, t*4)
    m0, m1, m2 = vert_map[i0], vert_map[i1], vert_map[i2]
    if m0 != m1 and m1 != m2 and m2 != m0:
        tri = tuple(sorted((m0, m1, m2)))
        if tri not in seen_triangles:
            seen_triangles.add(tri)
            new_indices.extend([m0, m1, m2])

print(f"Remaining triangles: {len(new_indices)//3:,}")
