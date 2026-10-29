with open('m:/TDS/3D-face-reconstruction/meshy_worker_chunk.js', encoding='utf-8') as f:
    text = f.read()

idx = text.find('format:"glb"')
if idx != -1:
    print(text[max(0, idx-400):min(len(text), idx+200)])
