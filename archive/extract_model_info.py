import html
import json

with open('m:/TDS/3D-face-reconstruction/einstein_page.html', encoding='utf-8') as f:
    text = f.read()

start = text.find('id="js-dom-data-prefetched-data"><!--')
if start != -1:
    end = text.find('-->', start)
    raw_json = text[start + len('id="js-dom-data-prefetched-data"><!--') : end]
    data = json.loads(html.unescape(raw_json))
    for k, v in data.items():
        if isinstance(v, dict) and 'name' in v:
            print('Name:', v.get('name'))
            print('Vertex count:', v.get('vertexCount'))
            print('Face count:', v.get('faceCount'))
            print('Description:', v.get('description'))
            print('Tags:', [t.get('name') for t in v.get('tags', [])])
