import urllib.request
import re

with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

chunks = set(re.findall(r'https://cdn\.meshy\.ai/webapp-build-assets/production/_next/static/chunks/[a-zA-Z0-9_\-\.]+\.js', text))
print(f"Total chunks to scan: {len(chunks)}")

for c in sorted(chunks):
    try:
        req = urllib.request.Request(c, headers={'User-Agent': 'Mozilla/5.0'})
        js = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        if 'MESHY' in js or 'model.meshy' in js or 'meshy' in js.lower():
            # Check if it has loader code
            for kw in ['MESHY.AI', 'model.meshy', 'MeshyLoader', 'loadMeshy', 'parseMeshy', 'decompress', 'unpack']:
                if kw in js:
                    print(f"Matched {kw} in {c}")
                    # Find snippet
                    idx = js.find(kw)
                    print(js[max(0, idx-150):min(len(js), idx+300)])
                    print("="*60)
    except Exception as e:
        pass
