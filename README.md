# 3D Face Reconstruction — Alec Douglas-Home (c1963)

3D reconstruction of British Prime Minister **Alec Douglas-Home** from the assigned photograph for the TDS 3D Face Reconstruction assignment.

## 🔗 Live URLs

- **Primary Submission GLB URL**: [`https://www.kabyik.dev/tds-3d-face/face.glb`](https://www.kabyik.dev/tds-3d-face/face.glb)
- **Fallback GitHub Raw CDN URL**: [`https://raw.githubusercontent.com/Kabyik-Kayal/tds-3d-face/master/face.glb`](https://raw.githubusercontent.com/Kabyik-Kayal/tds-3d-face/master/face.glb)
- **Interactive 3D Web Viewer**: [`https://www.kabyik.dev/tds-3d-face/`](https://www.kabyik.dev/tds-3d-face/)

All endpoints serve `Access-Control-Allow-Origin: *` (CORS enabled) with HTTP 200.

---

## 📁 Repository Structure

```text
tds-3d-face/
├── face.glb                     # Official submission model (< 2 MB requirement, 1.88 MB)
├── meshy_alec_douglas_home.glb  # Full-resolution raw AI model (45.6 MB reference)
├── index.html                   # Interactive 3D WebGL viewer (Google Model Viewer)
├── README.md                    # Project documentation
├── tools/                       # Testing, validation, and rendering verification tools
│   ├── validate_glb.py          # Validates glTF 2.0 specs and < 2,000,000 bytes limit
│   ├── test_cors_host.py        # Verifies remote HTTPS & CORS headers
│   └── render_verifier.py       # Headless Chromium/WebGL automated visual renderer
├── assets/                      # Reference photographs and baseline texture maps
│   ├── alec_douglas_home.jpg    # Wikimedia reference photograph
│   └── ...
└── archive/                     # Intermediate research, scraping, and pipeline scripts
```

---

## 📊 Model Specifications (`face.glb`)

| Property | Value |
| :--- | :--- |
| **Format** | Binary glTF 2.0 (`.glb`) |
| **File Size** | **1,881,876 bytes** (~1.88 MB, strictly within the 2,000,000 bytes limit) |
| **Vertices** | 107,461 |
| **Triangles** | 149,990 |
| **Textures** | 2048 × 2048 WebP (BaseColor, Normal Map, Metallic-Roughness) |
| **CORS Status** | Enabled (`Access-Control-Allow-Origin: *`) |

---

## 🛠️ Verification Commands

```bash
# Validate local GLB file compliance (< 2 MB, valid glTF 2.0 container)
python tools/validate_glb.py face.glb

# Test remote CORS headers and public download
python tools/test_cors_host.py https://www.kabyik.dev/tds-3d-face/face.glb

# Headless visual verification (captures exact WebGL render to PNG)
python tools/render_verifier.py face.glb verified_render.png
```
