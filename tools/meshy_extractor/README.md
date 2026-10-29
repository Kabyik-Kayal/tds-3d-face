# Meshy AI 3D Model Extractor & Decryption Protocol

This directory contains the standalone tool and documentation for extracting raw, uncompressed, full-resolution 3D models (`.glb`) from any public Meshy AI share link (e.g. `https://www.meshy.ai/s/...`).

---

## 🔍 How Meshy AI Share Links Work

When viewing a 3D model on Meshy AI without a subscription, direct GLB downloads are blocked in the web UI. Instead, the model is streamed to the browser using an encrypted proprietary container format with a `.meshy` extension.

### The Delivery Pipeline

1. **Next.js SSR Hydration**:
   - When a shared URL like `https://www.meshy.ai/s/39mTE9` is loaded, the HTML contains a server-rendered React state containing task metadata and a signed CDN URL:
     ```text
     https://api.meshy.ai/misc/cdn-models/.../tasks/<TASK_ID>/output/model.meshy?sign=<TIMESTAMP>-<HMAC>
     ```
2. **Encrypted Payload (`model.meshy`)**:
   - The `.meshy` file is an encrypted binary blob containing the full glTF 2.0 geometry, embedded WebP texture maps, and PBR materials.
3. **WebAssembly Decrypter Engine**:
   - The browser loads `mesh_loader.js` and `mesh_loader.wasm`.
   - Before decrypting, the WASM engine requires an **authorization token** computed via a client-side hashing routine using the internal key `"Meshy_Crypto_Key"`.
4. **Client-Side Authorization Signature**:
   - The signature is calculated by combining the hostname (`"www.meshy.ai"`) and the current millisecond timestamp (`Date.now()`).
   - The algorithm is a 64-bit FNV-1a hash variant coupled with a 64-bit Murmur3 avalanche finalizer:
     ```javascript
     function computeSignature(hostname, timestamp) {
         let r = BigInt("14695981039346656037");
         const n = BigInt("1099511628211");
         const a = BigInt("0xFFFFFFFFFFFFFFFF");
         const key = "Meshy_Crypto_Key";
         const msg = `${hostname}:${timestamp}`;
         
         for (let i = 0; i < key.length; i++) {
             r ^= BigInt(key.charCodeAt(i));
             r = (r * n) & a;
         }
         for (let i = 0; i < msg.length; i++) {
             r ^= BigInt(msg.charCodeAt(i));
             r = (r * n) & a;
         }
         r ^= r >> BigInt(33);
         r = (r * BigInt("0xff51afd7ed558ccd")) & a;
         r ^= r >> BigInt(33);
         r = (r * BigInt("0xc4ceb9fe1a85ec53")) & a;
         r ^= r >> BigInt(33);
         return r.toString(16).padStart(16, "0");
     }
     ```
5. **Decryption Execution**:
   - The engine is unlocked via:
     ```javascript
     instance.authorize("www.meshy.ai", timestamp, signature);
     ```
   - Once authorized, calling `instance.processMeshyFile(uint8EncryptedBuffer)` decrypts the container in memory and returns a standard, unencrypted `.glb` file.

---

## 🚀 One-Command CLI Usage

To extract and decrypt the raw 3D model from any Meshy AI share link:

```bash
node tools/meshy_extractor/extract_meshy.mjs https://www.meshy.ai/s/39mTE9 -o raw_model.glb
```

### Decrypting a Local `.meshy` File

If you have already downloaded an encrypted `model.meshy` file:

```bash
node tools/meshy_extractor/extract_meshy.mjs model.meshy -o decrypted.glb
```
