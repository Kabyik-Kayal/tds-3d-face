with open('m:/TDS/3D-face-reconstruction/meshy_worker_chunk.js', encoding='utf-8') as f:
    text = f.read()

pos = 0
while True:
    idx = text.lower().find('glb', pos)
    if idx == -1:
        break
    print(f"\n--- 'glb' at {idx} ---")
    print(text[max(0, idx-100):min(len(text), idx+150)])
    pos = idx + 3
