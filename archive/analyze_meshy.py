with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

import re
storage_urls = re.findall(r'https?://[^\s"\'<>]*(?:assets|model|storage|meshy|amazonaws)[^\s"\'<>]*', text)
print(f"Total storage URLs found: {len(storage_urls)}")
for u in set(storage_urls):
    u_clean = u.rstrip('\\').rstrip('"').rstrip(';')
    if any(ext in u_clean.lower() for ext in ['.glb', '.obj', '.fbx', '.bin', 'model', 'task', '01a16e46', 'preview']):
        print('->', u_clean)
