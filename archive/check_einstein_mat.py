with open('m:/TDS/3D-face-reconstruction/einstein_page.html', encoding='utf-8') as f:
    text = f.read()

import re
# Look for materials or textures in the page
mats = re.findall(r'"textures":\[(.*?)\]', text)
print("Textures in Einstein:", mats[:2])
# Check thumbnails / images of Einstein model
imgs = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|png|jpeg)[^\s"\'<>]*', text)
for u in imgs:
    if 'thumbnail' in u or 'media' in u:
        print('Thumbnail:', u)
        break
