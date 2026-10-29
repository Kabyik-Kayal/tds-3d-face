import struct
import json

path = 'm:/TDS/3D-face-reconstruction/meshy_texture_editor.glb'
with open(path, 'rb') as f:
    data = f.read()

magic, version, length = struct.unpack('<4sII', data[:12])
chunk_len, chunk_type = struct.unpack('<II', data[12:20])
gltf = json.loads(data[20:20+chunk_len].decode('utf-8'))
bin_data = data[20+chunk_len+8:]

# Apply the same scale and translation as meshy_alec_douglas_home.glb
gltf['nodes'][0]['scale'] = [0.000116170289, 0.000116170289, 0.000116170289]
gltf['nodes'][0]['translation'] = [-0.927729964, -0.951825678, -0.704652309]

# Pack back
def pad4(b, pad_byte=b'\x00'):
    rem = len(b) % 4
    return b if rem == 0 else b + (pad_byte * (4 - rem))

json_str = json.dumps(gltf, separators=(',', ':'))
json_bytes = pad4(json_str.encode('utf-8'), b' ')

total_len = 12 + (8 + len(json_bytes)) + (8 + len(bin_data))
header = struct.pack('<4sII', b'glTF', 2, total_len)
c0 = struct.pack('<II', len(json_bytes), 0x4E4F534A)
c1 = struct.pack('<II', len(bin_data), 0x004E4942)

with open(path, 'wb') as f:
    f.write(header)
    f.write(c0)
    f.write(json_bytes)
    f.write(c1)
    f.write(bin_data)

print(f"Updated {path} with proper scaling: {total_len:,} bytes")
