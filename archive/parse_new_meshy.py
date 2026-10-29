with open('m:/TDS/3D-face-reconstruction/meshy_new_share.html', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'https://api\.meshy\.ai/misc/cdn-models/[^\s"\'<>]+model\.meshy\?sign=[a-zA-Z0-9_\-]+', text)
print('Found model.meshy URLs:', matches)

model_urls = re.findall(r'"modelUrl":"([^"]+)"', text)
print('modelUrl:', model_urls)

# Check if textured or preview
previews = re.findall(r'https://api\.meshy\.ai/misc/cdn-images/[^\s"\'<>]+preview[^\s"\'<>]*', text)
print('Previews:', previews)

# Check all metadata
task_id = '01a16e9a-db8e-7603-9676-7e03390faac9'
idx = text.find(task_id)
while idx != -1:
    snippet = text[max(0, idx-100):min(len(text), idx+500)]
    if 'modelUrl' in snippet or 'status' in snippet or 'title' in snippet:
        print("--- Metadata ---")
        print(snippet)
    idx = text.find(task_id, idx + len(task_id))
