import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function computeSignature(hostname, timestamp) {
    let r = BigInt("14695981039346656037");
    let n = BigInt("1099511628211");
    let a = BigInt("0xFFFFFFFFFFFFFFFF");
    const key = "Meshy_Crypto_Key";
    const msg = hostname + ":" + timestamp;
    
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

async function main() {
    console.log("Loading mesh_loader.js...");
    const loaderModule = await import('./mesh_loader.js');
    const initLoader = loaderModule.default;
    
    const wasmPath = path.join(__dirname, 'mesh_loader.wasm');
    const wasmBinary = fs.readFileSync(wasmPath);
    
    console.log("Initializing WASM instance...");
    const instance = await initLoader({
        wasmBinary: wasmBinary,
        locateFile: (file) => file.endsWith('.wasm') ? wasmPath : file
    });
    
    console.log("Authorizing...");
    const hostname = "www.meshy.ai"; // or localhost
    const timestamp = Date.now();
    const signature = computeSignature(hostname, timestamp);
    console.log(`Hostname: ${hostname}, Timestamp: ${timestamp}, Signature: ${signature}`);
    
    const authResult = instance.authorize(hostname, timestamp, signature);
    console.log("Authorize result:", authResult);
    if (!authResult) {
        console.error("Authorization failed!");
        process.exit(1);
    }
    
    console.log("Reading model.meshy...");
    const encryptedData = fs.readFileSync(path.join(__dirname, 'model.meshy'));
    console.log(`Encrypted data size: ${encryptedData.length} bytes`);
    
    const uint8Data = new Uint8Array(encryptedData);
    console.log("Processing meshy file...");
    const result = instance.processMeshyFileForTextureEditor(uint8Data);
    
    console.log("Result success:", result.success);
    if (!result.success) {
        console.error("Failed to decrypt:", result.error);
        process.exit(1);
    }
    
    const outBuffer = Buffer.from(result.data);
    console.log(`Decrypted GLB size: ${outBuffer.length} bytes`);
    
    const outPath = path.join(__dirname, 'meshy_texture_editor.glb');
    fs.writeFileSync(outPath, outBuffer);
    console.log(`Saved decrypted GLB to ${outPath}!`);
}

main().catch(err => console.error("Error:", err));
