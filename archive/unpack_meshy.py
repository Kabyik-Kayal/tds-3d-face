import struct

with open('m:/TDS/3D-face-reconstruction/model.meshy', 'rb') as f:
    data = f.read()

# First 64 bytes
print("Length:", len(data))
print("Bytes 0-64:", data[:64])

# Let's inspect integers in the header
# MESHY.AI is 8 bytes
version = data[8:10]
print("Version bytes:", version)

# Check next bytes
offset = 10
# Search for recognizable structures or offsets
# Let's see if there is a table of contents or file records
# Let's search for filenames in the entire file
import re
filenames = re.findall(rb'[a-zA-Z0-9_\-\.]+\.(?:obj|mtl|png|jpg|jpeg|glb|gltf|bin)', data)
print("Filenames found in file:", set(filenames))

# Look at offset 5636300 where 'PK' was found
zip_offset = data.find(b'PK\x03\x04')
print(f"ZIP offset: {zip_offset}")
if zip_offset != -1:
    import zipfile
    import io
    try:
        zf = zipfile.ZipFile(io.BytesIO(data[zip_offset:]))
        print("ZIP file contents:", zf.namelist())
        for info in zf.infolist():
            print(f"  {info.filename}: {info.file_size} bytes")
            # Extract!
            zf.extract(info, 'm:/TDS/3D-face-reconstruction/extracted_meshy')
        print("Extracted successfully from ZIP offset!")
    except Exception as e:
        print("Error extracting ZIP:", e)
