import urllib.request
import re

with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

# Find all script src in HTML
scripts = re.findall(r'<script[^>]+src="([^">]+)"', text)
print(f"Total script tags in HTML: {len(scripts)}")

for s in scripts:
    if 'chunks' in s:
        try:
            req = urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0'})
            js = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
            if 'model.meshy' in js or 'MESHY.AI' in js or '.meshy' in js:
                print(f"Found in {s}!")
                # Find context
                idx = js.find('.meshy')
                print(js[max(0, idx-100):min(len(js), idx+200)])
        except Exception as e:
            pass
