with open('m:/TDS/3D-face-reconstruction/meshy_decryptor.js', encoding='utf-8') as f:
    js = f.read()

# Let's find definitions of E and v
idx_MESHY = js.find('MESHY.AI')
# Look backwards 5000 characters before MESHY.AI
snippet = js[max(0, idx_MESHY - 4000):idx_MESHY + 500]
print(snippet)
