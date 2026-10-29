import struct
import json

# Let's count edge manifoldness in the cleaned triangles
with open('m:/TDS/3D-face-reconstruction/meshy_alec_douglas_home.glb', 'rb') as f:
    data = f.read()

chunk_len = struct.unpack('<I', data[12:16])[0]
gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
bin_data = data[20+chunk_len+8:]

prim = gltf['meshes'][0]['primitives'][0]
pos_bv = gltf['bufferViews'][gltf['accessors'][prim['attributes']['POSITION']]['bufferView']]
idx_bv = gltf['bufferViews'][gltf['accessors'][prim['indices']]['bufferView']]

pos_bytes = bin_data[pos_bv['byteOffset']:pos_bv['byteOffset']+pos_bv['byteLength']]
idx_bytes = bin_data[idx_bv['byteOffset']:idx_bv['byteOffset']+idx_bv['byteLength']]

num_verts = gltf['accessors'][prim['attributes']['POSITION']]['count']
num_indices = gltf['accessors'][prim['indices']]['count']

cell_size = 200
cell_to_idx = {}
vert_map = [0] * num_verts

for i in range(num_verts):
    qx, qy, qz = struct.unpack_from('<HHH', pos_bytes, i*6)
    cell = (qx // cell_size, qy // cell_size, qz // cell_size)
    if cell not in cell_to_idx:
        cell_to_idx[cell] = len(cell_to_idx)
    vert_map[i] = cell_to_idx[cell]

print(f"Unique clustered vertices: {len(cell_to_idx):,}")

# Filter triangles by 2-manifold edge constraint
edge_count = {}
filtered_indices = []

for t in range(0, num_indices, 3):
    i0, i1, i2 = struct.unpack_from('<III', idx_bytes, t*4)
    m0, m1, m2 = vert_map[i0], vert_map[i1], vert_map[i2]
    if m0 != m1 and m1 != m2 and m2 != m0:
        e0 = tuple(sorted((m0, m1)))
        e1 = tuple(sorted((m1, m2)))
        e2 = tuple(sorted((m2, m0)))
        # In a 2-manifold mesh, an edge is shared by at most 2 triangles
        if edge_count.get(e0, 0) < 2 and edge_count.get(e1, 0) < 2 and edge_count.get(e2, 0) < 2:
            edge_count[e0] = edge_count.get(e0, 0) + 1
            edge_count[e1] = edge_count.get(e1, 0) + 1
            edge_count[e2] = edge_count.get(e2, 0) + 1
            filtered_indices.extend([m0, m1, m2])

print(f"2-manifold filtered triangles: {len(filtered_indices)//3:,}")
index_bytes = len(filtered_indices) * 2 # uint16
print(f"Index buffer size: {index_bytes:,} bytes ({index_bytes / 1024:.1f} KB)")
