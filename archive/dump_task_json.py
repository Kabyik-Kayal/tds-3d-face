with open('m:/TDS/3D-face-reconstruction/meshy_page.html', encoding='utf-8') as f:
    text = f.read()

import re

# Find occurrences of the task ID
pos = 0
task_id = '01a16e46-d955-723d-98d0-da241487cf72'
while True:
    idx = text.find(task_id, pos)
    if idx == -1:
        break
    start = max(0, idx - 200)
    end = min(len(text), idx + 400)
    print(f"\n--- Occurrence at {idx} ---")
    print(text[start:end])
    pos = idx + len(task_id)
