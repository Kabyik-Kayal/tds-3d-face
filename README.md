# 3D Face Reconstruction — Alec Douglas-Home (c1963)

3D reconstruction of British Prime Minister **Alec Douglas-Home** from a single reference photograph for the TDS 3D Face Reconstruction assignment.

## 📁 Repository Contents

- `face.glb`: The generated 3D binary glTF 2.0 model (**254 KB**, well under the 2 MB requirement).
- `index.html`: Interactive 3D WebGL viewer using Google's `<model-viewer>` component.
- `reconstruct_3d_face.py`: Python pipeline for 3D mesh synthesis, facial landmark morphing, UV texture mapping, and binary GLB compilation.
- `validate_glb.py`: GLB compliance validator checking glTF 2.0 binary chunks, buffers, and size constraints.
- `test_cors_host.py`: URL and CORS accessibility verification script.
- `alec_douglas_home.jpg`: Original high-resolution reference photo from Wikimedia Commons.

## 🚀 How to Run the Pipeline

```bash
# 1. Regenerate 3D GLB model
python reconstruct_3d_face.py

# 2. Validate the GLB file
python validate_glb.py face.glb
```

## 🌐 Hosting with GitHub Pages (CORS Enabled)

1. Create a new public repository on GitHub (e.g. `alec-douglas-home-3d`).
2. Push this directory to your repository:
   ```bash
   git add .
   git commit -m "Add 3D face model and viewer"
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/<REPO-NAME>.git
   git push -u origin main
   ```
3. Enable GitHub Pages:
   - Navigate to **Settings** > **Pages**
   - Under **Build and deployment > Branch**, select `main` branch and `/ (root)` folder
   - Click **Save**
4. Your public, CORS-enabled GLB URL will be:
   ```
   https://<YOUR-USERNAME>.github.io/<REPO-NAME>/face.glb
   ```
5. Verify the URL with:
   ```bash
   python test_cors_host.py https://<YOUR-USERNAME>.github.io/<REPO-NAME>/face.glb
   ```
