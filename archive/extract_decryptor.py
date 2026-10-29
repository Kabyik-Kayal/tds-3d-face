import urllib.request

url = "https://cdn.meshy.ai/webapp-build-assets/production/_next/static/chunks/1stm5w-xitq02.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
js = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
print(f"Downloaded {len(js)} bytes of 1stm5w-xitq02.js")

with open('m:/TDS/3D-face-reconstruction/meshy_decryptor.js', 'w', encoding='utf-8') as f:
    f.write(js)

idx = js.find('MESHY.AI')
print(f"Found 'MESHY.AI' at offset {idx}")
# Print the surrounding 2000 characters
print("="*60)
print(js[max(0, idx-200):min(len(js), idx+2500)])
print("="*60)
