with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

import re
img_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:png|jpg|jpeg|webp)[^\s"\'<>]*', text)
print(f"Total image URLs: {len(img_urls)}")
for u in set(img_urls):
    if 'tasks' in u or '01a16e46' in u:
        print('->', u)
