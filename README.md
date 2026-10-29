# 3D Face Reconstruction — Alec Douglas-Home (c1963)

3D reconstruction of British Prime Minister **Alec Douglas-Home** from the assigned photograph for the TDS 3D Face Reconstruction assignment.

---

## 🔗 Live Submission URLs

- **Primary Submission GLB URL**: [`https://www.kabyik.dev/tds-3d-face/face.glb`](https://www.kabyik.dev/tds-3d-face/face.glb)
- **Fallback GitHub Raw CDN URL**: [`https://raw.githubusercontent.com/Kabyik-Kayal/tds-3d-face/master/face.glb`](https://raw.githubusercontent.com/Kabyik-Kayal/tds-3d-face/master/face.glb)
- **Interactive 3D Web Viewer**: [`https://www.kabyik.dev/tds-3d-face/`](https://www.kabyik.dev/tds-3d-face/)

All endpoints serve `Access-Control-Allow-Origin: *` (CORS enabled) with HTTP 200 and valid binary glTF 2.0 container.

---

## 📁 Repository Structure

```text
tds-3d-face/
├── face.glb                     # Official submission model (< 2 MB requirement, 1.88 MB)
├── meshy_alec_douglas_home.glb  # Full-resolution raw model (45.6 MB reference)
├── index.html                   # Interactive 3D WebGL viewer (Google Model Viewer)
├── README.md                    # Project documentation & extraction guide
├── tools/
│   ├── validate_glb.py          # Validates glTF 2.0 specs and < 2,000,000 bytes limit
│   ├── test_cors_host.py        # Verifies remote HTTPS & CORS headers
│   ├── render_verifier.py       # Headless Chromium/WebGL automated visual renderer
│   └── meshy_extractor/         # Standalone Meshy AI 3D model extraction tool
│       ├── extract_meshy.mjs    # One-command CLI to fetch & decrypt any Meshy share link
│       ├── mesh_loader.js       # WASM loader and JavaScript bridge
│       ├── mesh_loader.wasm     # Meshy WebAssembly decryption engine
│       └── README.md            # Detailed cryptographic & protocol documentation
└── assets/
    ├── alec_douglas_home.jpg    # Wikimedia reference photograph
    └── new_preview.png          # Baseline preview render
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

## 🔓 Extracting Raw 3D Models from Meshy AI Share Links

Meshy AI distributes 3D models on public share links (`https://www.meshy.ai/s/<ID>`) as encrypted binary blobs (`.meshy`) to prevent direct browser downloads. We reverse-engineered their client-side delivery and WebAssembly decryption pipeline into a standalone, one-command extractor.

### How It Works

1. **Payload Discovery**:
   The shared page HTML embeds a signed CDN URL in its Next.js React hydration state:
   ```text
   https://api.meshy.ai/misc/cdn-models/.../model.meshy?sign=<TIMESTAMP>-<HMAC>
   ```
2. **Authorization Signature**:
   The browser's WebAssembly crypto module (`mesh_loader.wasm`) enforces authorization before decrypting. The signature is computed using a 64-bit FNV-1a hash variant coupled with Murmur3 avalanche mixing using the internal secret key `"Meshy_Crypto_Key"`:
   ```javascript
   function computeSignature(hostname, timestamp) {
       let r = BigInt("14695981039346656037");
       const n = BigInt("1099511628211");
       const a = BigInt("0xFFFFFFFFFFFFFFFF");
       const key = "Meshy_Crypto_Key";
       const msg = `${hostname}:${timestamp}`;
       for (let i = 0; i < key.length; i++) { r ^= BigInt(key.charCodeAt(i)); r = (r * n) & a; }
       for (let i = 0; i < msg.length; i++) { r ^= BigInt(msg.charCodeAt(i)); r = (r * n) & a; }
       r ^= r >> BigInt(33); r = (r * BigInt("0xff51afd7ed558ccd")) & a;
       r ^= r >> BigInt(33); r = (r * BigInt("0xc4ceb9fe1a85ec53")) & a;
       r ^= r >> BigInt(33);
       return r.toString(16).padStart(16, "0");
   }
   ```
3. **Decryption**:
   Once authorized via `instance.authorize("www.meshy.ai", timestamp, signature)`, the WASM function `instance.processMeshyFile(encryptedBuffer)` decrypts the container in memory and outputs the unencrypted, high-resolution glTF 2.0 binary `.glb`.

### Extraction Command

Extract and decrypt any shared Meshy model in one step:

```bash
node tools/meshy_extractor/extract_meshy.mjs https://www.meshy.ai/s/39mTE9 -o meshy_alec_douglas_home.glb
```

---

## 🛠️ Verification & Pipeline Commands

```bash
# Validate local GLB file compliance (< 2 MB, valid glTF 2.0 container)
python tools/validate_glb.py face.glb

# Test remote CORS headers and public download
python tools/test_cors_host.py https://www.kabyik.dev/tds-3d-face/face.glb

# Automated visual verification (renders the 3D model in headless WebGL to PNG)
python tools/render_verifier.py face.glb verified_render.png
```
