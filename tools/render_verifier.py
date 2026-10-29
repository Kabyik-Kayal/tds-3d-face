import http.server
import socketserver
import subprocess
import threading
import os
import tempfile
import sys
import shutil
import base64
import time

PORT = 8993

def render_model(glb_filename, output_png):
    rendered_data = {}
    done_event = threading.Event()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
        def log_message(self, format, *args):
            pass
        def do_POST(self):
            if self.path == '/save':
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode('utf-8')
                if ',' in body:
                    body = body.split(',', 1)[1]
                rendered_data['png'] = base64.b64decode(body)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                done_event.set()

    httpd = socketserver.TCPServer(('', PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()

    temp_dir = tempfile.mkdtemp()
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<script>
self.ModelViewerElement = self.ModelViewerElement || {{}};
self.ModelViewerElement.meshoptDecoderLocation = 'https://cdn.jsdelivr.net/npm/meshoptimizer/meshopt_decoder.js';
</script>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
<style>body {{ margin: 0; background: #0c0e14; }} model-viewer {{ width: 800px; height: 800px; }}</style>
</head>
<body>
<model-viewer id="viewer" src="{glb_filename}" camera-orbit="0deg 80deg 3.5m" camera-target="0m 0.1m 0m" field-of-view="35deg"></model-viewer>
<script>
const viewer = document.getElementById('viewer');
viewer.addEventListener('load', () => {{
    setTimeout(async () => {{
        try {{
            const dataURL = await viewer.toDataURL('image/png');
            fetch('/save', {{ method: 'POST', body: dataURL }});
        }} catch(e) {{
            console.error('toDataURL failed', e);
        }}
    }}, 800);
}});
viewer.addEventListener('error', (e) => {{
    console.error('viewer error', e);
}});
</script>
</body>
</html>"""

    view_file = 'temp_render_view.html'
    with open(view_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    cmd = [
        edge_path,
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu-sandbox',
        '--use-gl=angle',
        '--use-angle=d3d11',
        '--enable-webgl',
        '--window-size=850,850',
        f'--user-data-dir={temp_dir}',
        f'http://localhost:{PORT}/{view_file}'
    ]
    proc = subprocess.Popen(cmd)
    done = done_event.wait(timeout=20)
    try:
        proc.kill()
    except:
        pass
    httpd.shutdown()
    if os.path.exists(view_file):
        os.remove(view_file)

    if 'png' in rendered_data and len(rendered_data['png']) > 5000:
        with open(output_png, 'wb') as f:
            f.write(rendered_data['png'])
        print(f"SUCCESS: Rendered {glb_filename} to {output_png} ({len(rendered_data['png'])} bytes)")
        return True
    else:
        print(f"FAILED: Did not capture render of {glb_filename}")
        return False

if __name__ == '__main__':
    glb = sys.argv[1] if len(sys.argv) > 1 else 'face.glb'
    out = sys.argv[2] if len(sys.argv) > 2 else 'render_output.png'
    render_model(glb, out)
