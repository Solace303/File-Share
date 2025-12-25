import http.server
import socketserver
import os
import cgi
import mimetypes
import argparse
from urllib.parse import urlparse, unquote, parse_qs

PORT = 8080
mimetypes.init()

# Global variable to store the current server base directory
SERVER_BASE_DIR = os.getcwd()

# CSS String for a colorful, modern UI
STYLING = """
<style>
    body { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        background-color: #1a1a2e; 
        color: #e9ecef; 
        max-width: 800px; 
        margin: 40px auto; 
        padding: 20px; 
        line-height: 1.6;
    }
    h1, h2 { color: #4cc9f0; border-bottom: 2px solid #4361ee; padding-bottom: 10px; }
    .card { 
        background: #16213e; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
        margin-bottom: 20px; 
    }
    a { color: #4cc9f0; text-decoration: none; font-weight: bold; }
    a:hover { color: #4361ee; text-decoration: underline; }
    input[type="text"], input[type="file"] {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4361ee;
        background: #0f3460;
        color: white;
        margin-bottom: 10px;
        width: 100%;
        box-sizing: border-box;
    }
    input[type="submit"] {
        background: #4361ee;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        transition: background 0.3s;
    }
    input[type="submit"]:hover { background: #3a0ca3; }
    ul { list-style: none; padding: 0; }
    li { background: #0f3460; margin: 5px 0; padding: 10px; border-radius: 5px; }
    .path-display { color: #f72585; font-family: monospace; font-size: 1.1em; }
</style>
"""

class FileServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global SERVER_BASE_DIR
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html_content = f"""
            <html>
            <head>{STYLING}</head>
            <body>
                <h1>🚀 File Server</h1>
                <div class="card">
                    <p>Current Serving Path: <span class="path-display">{SERVER_BASE_DIR}</span></p>
                    <a href="/browse">📂 Browse Current Directory</a>
                </div>

                <div class="card">
                    <h2>📤 Upload Files</h2>
                    <form method="post" action="/upload" enctype="multipart/form-data">
                        <input type="file" name="files" multiple>
                        <input type="submit" value="Upload to Current Dir">
                    </form>
                </div>

                <div class="card">
                    <h2>⚙️ Change Server Directory</h2>
                    <form method="get" action="/change_dir">
                        <input type="text" name="new_dir" placeholder="Enter absolute path (e.g. /home/user/docs)">
                        <input type="submit" value="Change Directory">
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode())
        elif parsed_url.path == '/browse' or parsed_url.path.startswith('/browse/'):
            self.browse_and_serve_files(parsed_url)
        elif parsed_url.path == '/change_dir':
            query_params = parse_qs(parsed_url.query)
            new_dir_path = query_params.get('new_dir', [''])[0]
            self.change_directory(new_dir_path)
        else:
            self.send_error(404, "Not Found")

    def list_directory(self, dir_path):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        header = f"<html><head>{STYLING}</head><body><h1>Directory listing</h1><div class='card'><ul>"
        response = header.encode()
        
        files = os.listdir(dir_path)
        if os.path.abspath(dir_path) != os.path.abspath(SERVER_BASE_DIR):
            parent_dir = os.path.dirname(dir_path)
            relative_parent = os.path.relpath(parent_dir, SERVER_BASE_DIR)
            parent_link = '/browse/' + relative_parent.replace(os.sep, '/') if relative_parent != '.' else '/browse/'
            response += f'<li><a href="{parent_link}">🔙 [Parent Directory]</a></li>'.encode()
        
        for filename in sorted(files):
            relative_filename = os.path.relpath(os.path.join(dir_path, filename), SERVER_BASE_DIR)
            link_path = f'/browse/{relative_filename.replace(os.sep, "/")}'
            icon = "📁 " if os.path.isdir(os.path.join(dir_path, filename)) else "📄 "
            response += f'<li>{icon}<a href="{link_path}">{filename}</a></li>'.encode()
            
        response += b'</ul></div><hr><a href="/"> Go Home</a></body></html>'
        self.wfile.write(response)

    # --- Keep other methods as per original implementation ---
    def do_POST(self):
        if self.path == '/upload': self.upload_files()
        else: self.send_error(404)

    def change_directory(self, new_dir_path):
        global SERVER_BASE_DIR
        if not new_dir_path:
            self.send_error(400, "Directory path required.")
            return
        abs_path = os.path.abspath(os.path.normpath(new_dir_path))
        if os.path.isdir(abs_path):
            SERVER_BASE_DIR = abs_path
            try: os.chdir(SERVER_BASE_DIR)
            except OSError: pass
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404, "Directory not found.")

    def browse_and_serve_files(self, parsed_url):
        relative_path = unquote(parsed_url.path[len('/browse/'):])
        file_path = os.path.join(SERVER_BASE_DIR, os.path.normpath(relative_path))
        if not os.path.abspath(file_path).startswith(os.path.abspath(SERVER_BASE_DIR)):
            self.send_error(403, "Access denied.")
            return
        if os.path.isdir(file_path): self.list_directory(file_path)
        elif os.path.isfile(file_path): self.serve_file(file_path)
        else: self.send_error(404)

    def serve_file(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None: mime_type = 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.end_headers()
        with open(file_path, 'rb') as f: self.wfile.write(f.read())

    def upload_files(self):
        upload_dir = SERVER_BASE_DIR
        content_type = self.headers.get('Content-Type')
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type})
        if 'files' in form:
            files = form['files']
            if not isinstance(files, list): files = [files]
            for file_item in files:
                if file_item.filename:
                    with open(os.path.join(upload_dir, os.path.basename(file_item.filename)), 'wb') as f:
                        f.write(file_item.file.read())
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<html><head>{STYLING}</head><body><div class='card'><h2>Success!</h2><a href='/browse'>Back to files</a></div></body></html>".encode())
            return
        self.send_error(400)

# --- Server Start Logic ---
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=int, default=8080)
parser.add_argument('-b', '--bind', default="")
parser.add_argument('-d', '--directory', default=os.getcwd())
args = parser.parse_args()

SERVER_BASE_DIR = os.path.abspath(args.directory)
os.chdir(SERVER_BASE_DIR)

with socketserver.TCPServer((args.bind, args.port), FileServer) as server:
    print(f"Colorful server running at http://localhost:{args.port}")
    server.serve_forever()