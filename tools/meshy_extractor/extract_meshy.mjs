import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Computes the 64-bit authorization hash signature expected by Meshy's WebAssembly decrypter.
 * Algorithm: 64-bit FNV-1a variant with Murmur3-style 64-bit mixing finalizer.
 */
function computeSignature(hostname, timestamp) {
    let r = BigInt("14695981039346656037");
    const n = BigInt("1099511628211");
    const a = BigInt("0xFFFFFFFFFFFFFFFF");
    const key = "Meshy_Crypto_Key";
    const msg = `${hostname}:${timestamp}`;
    
    // Hash key bytes
    for (let i = 0; i < key.length; i++) {
        r ^= BigInt(key.charCodeAt(i));
        r = (r * n) & a;
    }
    // Hash message bytes
    for (let i = 0; i < msg.length; i++) {
        r ^= BigInt(msg.charCodeAt(i));
        r = (r * n) & a;
    }
    // Murmur3 64-bit avalanche mixing
    r ^= r >> BigInt(33);
    r = (r * BigInt("0xff51afd7ed558ccd")) & a;
    r ^= r >> BigInt(33);
    r = (r * BigInt("0xc4ceb9fe1a85ec53")) & a;
    r ^= r >> BigInt(33);

    return r.toString(16).padStart(16, "0");
}

/**
 * Decrypts a binary .meshy buffer into a standard glTF 2.0 (.glb) buffer.
 */
async function decryptMeshyBuffer(encryptedBuffer) {
    const wasmPath = path.join(__dirname, 'mesh_loader.wasm');
    const jsPath = path.join(__dirname, 'mesh_loader.js');

    if (!fs.existsSync(wasmPath) || !fs.existsSync(jsPath)) {
        throw new Error(`WASM loader files missing in ${__dirname}`);
    }

    const loaderModule = await import('./mesh_loader.js');
    const initLoader = loaderModule.default;
    const wasmBinary = fs.readFileSync(wasmPath);

    const instance = await initLoader({
        wasmBinary: wasmBinary,
        locateFile: (file) => file.endsWith('.wasm') ? wasmPath : file
    });

    const hostname = "www.meshy.ai";
    const timestamp = Date.now();
    const signature = computeSignature(hostname, timestamp);

    const authorized = instance.authorize(hostname, timestamp, signature);
    if (!authorized) {
        throw new Error("Failed to authorize WASM decrypter module");
    }

    const uint8Input = new Uint8Array(encryptedBuffer);
    const result = instance.processMeshyFile(uint8Input);

    if (!result || !result.success) {
        throw new Error(result?.error || "Decryption failed in WASM processMeshyFile");
    }

    return Buffer.from(result.data);
}

/**
 * Main CLI handler
 */
async function main() {
    const args = process.argv.slice(2);
    if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
        console.log(`
Meshy AI 3D Model Extractor & Decrypter
======================================
Extracts and decrypts raw full-resolution 3D models (.glb) from Meshy shared links or encrypted .meshy files.

Usage:
  node extract_meshy.mjs <share-url-or-file> [-o output.glb]

Examples:
  node extract_meshy.mjs https://www.meshy.ai/s/39mTE9 -o model.glb
  node extract_meshy.mjs encrypted_model.meshy -o decrypted.glb
`);
        process.exit(0);
    }

    const input = args[0];
    let outIdx = args.indexOf('-o');
    let outputPath = (outIdx !== -1 && args[outIdx + 1]) ? args[outIdx + 1] : 'decrypted_model.glb';

    let encryptedBuffer;

    if (input.startsWith('http://') || input.startsWith('https://')) {
        console.log(`[1/3] Fetching Meshy share page: ${input}...`);
        const resp = await fetch(input, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        const html = await resp.text();

        // Extract signed model.meshy URL from Next.js SSR payload
        const match = html.match(/https:\/\/api\.meshy\.ai\/misc\/cdn-models\/[^\s"\'<>]+\.meshy\?sign=[a-zA-Z0-9_\-]+/);
        if (!match) {
            throw new Error("Could not find encrypted model URL in shared page HTML");
        }
        const modelUrl = match[0];
        console.log(`[2/3] Found encrypted model payload: ${modelUrl}`);
        console.log("Downloading encrypted .meshy container...");
        const modelResp = await fetch(modelUrl);
        encryptedBuffer = Buffer.from(await modelResp.arrayBuffer());
    } else {
        console.log(`[1/3] Reading local encrypted file: ${input}...`);
        encryptedBuffer = fs.readFileSync(input);
    }

    console.log(`[2/3] Decrypting ${encryptedBuffer.length} bytes via WebAssembly crypto engine...`);
    const glbBuffer = await decryptMeshyBuffer(encryptedBuffer);

    console.log(`[3/3] Saving decrypted glTF 2.0 binary model (${glbBuffer.length} bytes) to: ${outputPath}`);
    fs.writeFileSync(outputPath, glbBuffer);
    console.log("Done! Extracted model is ready for 3D inspection.");
}

main().catch(err => {
    console.error("Extraction Error:", err.message);
    process.exit(1);
});
