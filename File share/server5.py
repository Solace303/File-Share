import http.server
import socketserver
import os
import cgi
import mimetypes
import argparse
import threading
from urllib.parse import urlparse, unquote, parse_qs

# Initialize mimetypes
mimetypes.init()

# Use a global variable for the directory
SERVER_BASE_DIR = os.getcwd()

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
        padding: 10px; border-radius: 5px; border: 1px solid #4361ee;
        background: #0f3460; color: white; margin-bottom: 10px;
        width: 100%; box-sizing: border-box;
    }
    input[type="submit"] {
        background: #4361ee; color: white; border: none; padding: 10px 20px;
        border-radius: 5px; cursor: pointer; font-weight: bold; transition: background 0.3s;
    }
    input[type="submit"]:hover { background: #3a0ca3; }
    ul { list-style: none; padding: 0; }
    li { background: #0f3460; margin: 5px 0; padding: 10px; border-radius: 5px; }
    .path-display { color: #f72585; font-family: monospace; font-size: 1.1em; }
    .thread-info { font-size: 0.8em; color: #888; text-align: right; }
</style>
"""

class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    # Allow address reuse so you don't get "Address already in use" errors frequently
    allow_reuse_address = True 

class FileServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global SERVER_BASE_DIR
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <html><head>{STYLING}</head><body>
                <h1>🚀 FILE SHARE </h1>
                <p class="thread-info">Active Connections: {threading.active_count() - 1}</p>
                <div class="card">
                    <p>Serving: <span class="path-display">{SERVER_BASE_DIR}</span></p>
                    <a href="/browse">📂 Browse Files</a>
                </div>
                <div class="card">
                    <h2>📤 Upload Files to Server </h2>
                    <form method="post" action="/upload" enctype="multipart/form-data">
                        <input type="file" name="files" multiple>
                        <input type="submit" value="Upload Now">
                    </form>
                </div>
                <div class="card">
                    <h2>⚙️ Change Server Directory </h2>
                    <form method="get" action="/change_dir">
                        <input type="text" name="new_dir" placeholder="Full path...">
                        <input type="submit" value="Update Path">
                    </form>
                </div>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif parsed_url.path == '/browse' or parsed_url.path.startswith('/browse/'):
            self.browse_and_serve_files(parsed_url)
        elif parsed_url.path == '/change_dir':
            query = parse_qs(parsed_url.query)
            self.change_directory(query.get('new_dir', [''])[0])
        else:
            self.send_error(404)

    def list_directory(self, dir_path):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        content = f"<html><head>{STYLING}</head><body><h1>📂 Directory Listing</h1><div class='card'><ul>"
        
        if os.path.abspath(dir_path) != os.path.abspath(SERVER_BASE_DIR):
            parent = os.path.dirname(dir_path)
            rel = os.path.relpath(parent, SERVER_BASE_DIR)
            link = '/browse/' + rel.replace(os.sep, '/') if rel != '.' else '/browse/'
            content += f'<li><a href="{link}">🔙 .. (Parent)</a></li>'
        
        for filename in sorted(os.listdir(dir_path)):
            rel_path = os.path.relpath(os.path.join(dir_path, filename), SERVER_BASE_DIR)
            link = f'/browse/{rel_path.replace(os.sep, "/")}'
            icon = "📁 " if os.path.isdir(os.path.join(dir_path, filename)) else "📄 "
            content += f'<li>{icon}<a href="{link}">{filename}</a></li>'
            
        content += '</ul></div><a href="/">🏠 Home</a></body></html>'
        self.wfile.write(content.encode('utf-8'))

    def do_POST(self):
        if self.path == '/upload':
            self.upload_files()
        else:
            self.send_error(404)

    def upload_files(self):
        # Increased max field size can be added here if needed for huge files
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers, 
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers.get('Content-Type')}
        )
        if 'files' in form:
            files = form['files']
            if not isinstance(files, list): files = [files]
            for f_item in files:
                if f_item.filename:
                    save_path = os.path.join(SERVER_BASE_DIR, os.path.basename(f_item.filename))
                    with open(save_path, 'wb') as f:
                        f.write(f_item.file.read())
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"<html><head>{STYLING}</head><body><div class='card'><h2>✅ Uploaded!</h2><a href='/browse'>View Files</a></div></body></html>".encode('utf-8'))
        else:
            self.send_error(400)

    def serve_file(self, file_path):
        mime, _ = mimetypes.guess_type(file_path)
        self.send_response(200)
        self.send_header('Content-Type', mime or 'application/octet-stream')
        self.end_headers()
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())

    def browse_and_serve_files(self, parsed_url):
        rel = unquote(parsed_url.path[len('/browse/'):])
        path = os.path.join(SERVER_BASE_DIR, os.path.normpath(rel))
        if not os.path.abspath(path).startswith(os.path.abspath(SERVER_BASE_DIR)):
            self.send_error(403)
            return
        if os.path.isdir(path): self.list_directory(path)
        elif os.path.isfile(path): self.serve_file(path)
        else: self.send_error(404)

    def change_directory(self, new_dir):
        global SERVER_BASE_DIR
        abs_path = os.path.abspath(new_dir)
        if os.path.isdir(abs_path):
            SERVER_BASE_DIR = abs_path
            # It's better to change the actual CWD so os.path calls stay consistent
            os.chdir(SERVER_BASE_DIR)
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404)

# --- Start ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-threaded File Server")
    parser.add_argument('-p', '--port', type=int, default=8080, help="Port to listen on")
    parser.add_argument('-b', '--bind', default="0.0.0.0", help="IP address to bind to")
    args = parser.parse_args()

    # Create server instance with the provided bind address and port
    with ThreadingServer((args.bind, args.port), FileServer) as server:
        print(f"🔥 Multi-threaded server active on http://{args.bind}:{args.port}")
        print(f"📁 Serving directory: {SERVER_BASE_DIR}")
        server.serve_forever()