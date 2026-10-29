with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

import re
chunks = set(re.findall(r'https://cdn\.meshy\.ai/webapp-build-assets/production/_next/static/chunks/[a-zA-Z0-9_\-\.]+\.js', text))

import urllib.request
for c in chunks:
    try:
        req = urllib.request.Request(c, headers={'User-Agent': 'Mozilla/5.0'})
        js = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        if 'fetchGeometryFromModelUrl' in js:
            print(f"Found fetchGeometryFromModelUrl in {c}!")
            idx = js.find('fetchGeometryFromModelUrl')
            print(js[max(0, idx-100):min(len(js), idx+1000)])
            with open('m:/TDS/3D-face-reconstruction/meshy_fetch_geometry.js', 'w', encoding='utf-8') as f:
                f.write(js)
            break
    except Exception as e:
        pass
