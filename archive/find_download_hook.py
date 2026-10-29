with open('m:/TDS/3D-face-reconstruction/meshy_worker_chunk.js', encoding='utf-8') as f:
    text = f.read()

idx = text.find('useDownloadTaskV2')
print("Found useDownloadTaskV2:", idx)
if idx != -1:
    print(text[max(0, idx-200):min(len(text), idx+600)])
