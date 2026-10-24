with open('m:/TDS/3D-face-reconstruction/einstein_page.html', encoding='utf-8') as f:
    text = f.read()

import re
tags = re.findall(r'"tags":\[(.*?)\]', text)
print('Tags:', tags[:2])
desc = re.findall(r'"description":"(.*?)"', text)
print('Description:', desc[:2])
vertex_count = re.findall(r'"vertexCount":(\d+)', text)
face_count = re.findall(r'"faceCount":(\d+)', text)
print('Vertices:', vertex_count, 'Faces:', face_count)
