import struct
import json
from PIL import Image

with open('m:/TDS/3D-face-reconstruction/LeePerrySmith.glb', 'rb') as f:
    data = f.read()
chunk_len = struct.unpack('<I', data[12:16])[0]
gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
bin_data = data[20+chunk_len+8:]

# Accessors: 1 is POSITION, 3 is TEXCOORD_0
pos_acc = gltf['accessors'][1]
uv_acc = gltf['accessors'][3]
pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
uv_bv = gltf['bufferViews'][uv_acc['bufferView']]

pos_bytes = bin_data[pos_bv['byteOffset']:pos_bv['byteOffset']+pos_bv['byteLength']]
uv_bytes = bin_data[uv_bv['byteOffset']:uv_bv['byteOffset']+uv_bv['byteLength']]

num_verts = pos_acc['count']
verts = [struct.unpack_from('<fff', pos_bytes, i*12) for i in range(num_verts)]
uvs = [struct.unpack_from('<ff', uv_bytes, i*8) for i in range(num_verts)]

# Find feature regions in UV space
# Nose tip: highest Z
nose_tip_i = max(range(num_verts), key=lambda i: verts[i][2])
print(f"Nose tip: pos={verts[nose_tip_i]}, uv={uvs[nose_tip_i]}")

# Eye centers: around y ≈ 1.3, z ≈ 1.8, x ≈ ±1.2
left_eye = min(range(num_verts), key=lambda i: (verts[i][0]-1.3)**2 + (verts[i][1]-1.3)**2 + (verts[i][2]-1.6)**2)
right_eye = min(range(num_verts), key=lambda i: (verts[i][0]+1.3)**2 + (verts[i][1]-1.3)**2 + (verts[i][2]-1.6)**2)
print(f"Left eye (mesh): pos={verts[left_eye]}, uv={uvs[left_eye]}")
print(f"Right eye (mesh): pos={verts[right_eye]}, uv={uvs[right_eye]}")

# Mouth center: y ≈ 0.5, x ≈ 0, z > 2.0
mouth_center = max([i for i in range(num_verts) if abs(verts[i][0]) < 0.2 and 0.3 < verts[i][1] < 0.7], key=lambda i: verts[i][2])
print(f"Mouth center: pos={verts[mouth_center]}, uv={uvs[mouth_center]}")

# Chin tip: y ≈ -0.5, z > 1.8, x ≈ 0
chin_tip = max([i for i in range(num_verts) if abs(verts[i][0]) < 0.2 and -0.8 < verts[i][1] < -0.2], key=lambda i: verts[i][2])
print(f"Chin tip: pos={verts[chin_tip]}, uv={uvs[chin_tip]}")

# Forehead center: y ≈ 2.2, x ≈ 0, z > 1.8
forehead = max([i for i in range(num_verts) if abs(verts[i][0]) < 0.2 and 1.8 < verts[i][1] < 2.6], key=lambda i: verts[i][2])
print(f"Forehead: pos={verts[forehead]}, uv={uvs[forehead]}")
