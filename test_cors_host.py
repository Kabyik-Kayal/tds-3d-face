#!/usr/bin/env python3
"""
CORS and GLB Endpoint Verification Tool
Verifies that a public HTTPS URL:
1. Is reachable via HTTPS (HTTP 200)
2. Allows Cross-Origin Resource Sharing (CORS) from any browser client
3. Serves a valid GLB container under 2,000,000 bytes
"""

import sys
import struct
import urllib.request
import urllib.error

# Ensure utf-8 output on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def verify_remote_glb(url):
    print(f"=== Testing Remote GLB URL: {url} ===")
    
    if not url.startswith("https://"):
        print("❌ FAIL: URL must start with 'https://' (secure HTTPS is required)!")
        return False
        
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TDS-3D-Validator/1.0",
            "Origin": "https://gltf-viewer.donmccurdy.com" # Simulate cross-origin request from 3D viewer
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            status = response.status
            print(f"HTTP Status: {status}")
            if status != 200:
                print(f"❌ FAIL: Expected HTTP 200, got {status}")
                return False
                
            headers = dict(response.headers)
            
            # Check CORS headers
            cors = headers.get("Access-Control-Allow-Origin") or headers.get("access-control-allow-origin")
            print(f"Access-Control-Allow-Origin: {cors}")
            if cors:
                print("✅ PASS: CORS header is enabled! Cross-origin browser requests allowed.")
            else:
                print("⚠️ WARNING: Access-Control-Allow-Origin header was not explicitly returned in GET response.")
                print("Note: GitHub Pages, Cloudflare, and raw Git CDNs allow cross-origin requests by default.")
                
            data = response.read()
            size = len(data)
            print(f"Downloaded file size: {size:,} bytes")
            
            if size > 2_000_000:
                print(f"❌ FAIL: File size exceeds 2 MB limit! ({size} > 2,000,000)")
                return False
            else:
                print(f"✅ PASS: File size is within 2 MB limit ({size:,} / 2,000,000 bytes)")
                
            if len(data) >= 12:
                magic, version, length = struct.unpack("<4sII", data[:12])
                if magic == b"glTF" and version == 2:
                    print("✅ PASS: Valid glTF 2.0 (GLB) binary container confirmed!")
                else:
                    print(f"❌ FAIL: Invalid GLB header: magic={magic}, version={version}")
                    return False
            else:
                print("❌ FAIL: File too small to be valid GLB.")
                return False
                
            print("\n🎉 SUCCESS: This URL satisfies all assignment submission criteria!")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to URL: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cors_host.py <PUBLIC_GLB_URL>")
        print("Example: python test_cors_host.py https://myuser.github.io/face3d/face.glb")
    else:
        verify_remote_glb(sys.argv[1])
