import urllib.request
import re
import json

url = 'https://www.meshy.ai/3d-models/Alec-DouglasHome-01a16e46-d955-723d-98d0-da241487cf72?share_type=3d-models'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        with open('m:/TDS/3D-face-reconstruction/meshy_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved meshy_page.html, size:', len(html))

        # Check for .glb URLs
        glb_urls = re.findall(r'https?://[^\s"\'<>]+\.glb[^\s"\'<>]*', html)
        print('GLB URLs:', glb_urls)

        # Check for JSON embedded in __NEXT_DATA__
        next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if next_data:
            print('Found __NEXT_DATA__!')
            with open('m:/TDS/3D-face-reconstruction/meshy_next_data.json', 'w', encoding='utf-8') as f:
                f.write(next_data.group(1))
except Exception as e:
    print('Error:', e)
