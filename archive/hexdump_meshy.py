with open('m:/TDS/3D-face-reconstruction/model.meshy', 'rb') as f:
    data = f.read(512)

import binascii
print("Hexdump of first 256 bytes:")
for i in range(0, 256, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f"{b:02x}" for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
    print(f"{i:04x}: {hex_str:<48} | {ascii_str}")
