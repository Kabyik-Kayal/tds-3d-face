import os
import shutil

root = r'm:\TDS\3D-face-reconstruction'

# Directories to create
tools_dir = os.path.join(root, 'tools')
assets_dir = os.path.join(root, 'assets')
archive_dir = os.path.join(root, 'archive')

for d in [tools_dir, assets_dir, archive_dir]:
    os.makedirs(d, exist_ok=True)

# Files to keep in ROOT (DO NOT MOVE):
keep_in_root = {
    'face.glb',
    'meshy_alec_douglas_home.glb',
    'index.html',
    'README.md',
    '.git',
    '.gitignore',
    'tools',
    'assets',
    'archive'
}

# Mapping of specific files
to_tools = {'validate_glb.py', 'test_cors_host.py', 'render_verifier.py'}
to_assets = {
    'alec_douglas_home.jpg', 'alec_portrait.jpg', 'alec_blended_texture.jpg',
    'Map-COL.jpg', 'new_preview.png', 'meshy_preview.png',
    'einstein_thumb.jpg', 'einstein_page.html', 'facecap.glb', 'LeePerrySmith.glb'
}

# Temporary files to delete
temp_patterns = ['cand', 'crop', 'render', 'opt_tex', 'orig_tex', 'base_model', 'test_', 'current_', 'ground_truth_', 'final_verified_']

for item in os.listdir(root):
    if item in keep_in_root:
        continue
    item_path = os.path.join(root, item)
    if not os.path.isfile(item_path):
        continue

    # Delete temp render artifacts
    is_temp = any(item.startswith(p) for p in temp_patterns) and (item.endswith('.png') or item.endswith('.glb') or item.endswith('.bin') or item.endswith('.gltf') or item.endswith('.webp'))
    if is_temp:
        os.remove(item_path)
        print(f"Deleted temp file: {item}")
        continue

    if item in to_tools:
        dest = os.path.join(tools_dir, item)
        shutil.move(item_path, dest)
        print(f"Moved to tools/: {item}")
    elif item in to_assets:
        dest = os.path.join(assets_dir, item)
        shutil.move(item_path, dest)
        print(f"Moved to assets/: {item}")
    else:
        dest = os.path.join(archive_dir, item)
        shutil.move(item_path, dest)
        print(f"Moved to archive/: {item}")

print("Repository organization complete!")
