import urllib.request
import json

# Test model.meshy URL
meshy_url = "https://api.meshy.ai/misc/cdn-models/73e2c8ea-382f-489b-9d45-bf7843a319c1/tasks/01a16e46-d955-723d-98d0-da241487cf72/output/model.meshy?sign=1792972800-0d5b6a727e6ab3f57a56b2065e2d3bfe"
print("Testing model.meshy URL...")
req = urllib.request.Request(meshy_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        print(f"model.meshy downloaded: {len(data)} bytes, Content-Type: {resp.headers.get('Content-Type')}")
        with open('m:/TDS/3D-face-reconstruction/model.meshy', 'wb') as f:
            f.write(data)
        # Check first bytes (magic)
        print("First 16 bytes:", data[:16])
except Exception as e:
    print("Error model.meshy:", e)

# Test ?download=glb
dl_url = "https://www.meshy.ai/3d-models/Alec-DouglasHome-01a16e46-d955-723d-98d0-da241487cf72?download=glb"
print("\nTesting ?download=glb...")
req2 = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req2) as resp:
        data2 = resp.read()
        print(f"download=glb response: {len(data2)} bytes, Content-Type: {resp.headers.get('Content-Type')}")
        print("First 32 bytes:", data2[:32])
except Exception as e:
    print("Error ?download=glb:", e)
