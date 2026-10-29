with open('m:/TDS/3D-face-reconstruction/meshy_worker_chunk.js', encoding='utf-8') as f:
    text = f.read()

idx = text.find('format:"glb"')
scope_start = max(0, idx - 1500)
print(text[scope_start:idx])
