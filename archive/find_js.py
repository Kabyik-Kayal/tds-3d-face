with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

import re
js_urls = re.findall(r'https?://[^\s"\'<>]+\.js', text)
print(f"Total JS URLs: {len(js_urls)}")
for u in set(js_urls):
    if 'chunks' in u:
        print('Chunk:', u)
