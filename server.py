import http.server
import socketserver
import os
import cgi
import mimetypes
import argparse
from urllib.parse import urlparse, unquote, parse_qs

PORT = 8080
mimetypes.init()

# Use a global variable to store the current server base directory
SERVER_BASE_DIR = os.getcwd()

class FileServer(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        global SERVER_BASE_DIR # Declare global to modify it
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            # Added a form to change directory and link to browse files
            html_content = f"""
            <html><body>
            <h1>File Server (Serving: {SERVER_BASE_DIR})</h1>
            <form method="post" action="/upload" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="Upload to Current Dir">
            </form>
            <p><a href="/browse">Browse Current Directory</a></p>
            <hr>
            <h2>Change Server Directory</h2>
            <form method="get" action="/change_dir">
                <input type="text" name="new_dir" placeholder="Enter absolute path">
                <input type="submit" value="Change Directory">
            </form>
            </body></html>
            """
            self.wfile.write(html_content.encode())
        
        elif parsed_url.path == '/browse' or parsed_url.path.startswith('/browse/'):
            self.browse_and_serve_files(parsed_url)
        
        elif parsed_url.path == '/change_dir':
            # Handle directory change request via GET (from the form)
            query_params = parse_qs(parsed_url.query)
            new_dir_path = query_params.get('new_dir', [''])[0]
            self.change_directory(new_dir_path)
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Not found.')

    def do_POST(self):
        if self.path == '/upload':
            self.upload_file()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found.')

    def change_directory(self, new_dir_path):
        """Dynamically changes the global SERVER_BASE_DIR."""
        global SERVER_BASE_DIR
        
        if not new_dir_path:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Directory path required.')
            return

        # Sanitize and normalize the path
        abs_path = os.path.abspath(os.path.normpath(new_dir_path))

        if os.path.isdir(abs_path):
            SERVER_BASE_DIR = abs_path
            # It's good practice to also change the CWD of the process
            # when using os.path.join for relative path building later.
            try:
                os.chdir(SERVER_BASE_DIR)
            except OSError as e:
                print(f"Warning: Could not change CWD to {SERVER_BASE_DIR}: {e}")

            self.send_response(303) # See Other
            self.send_header('Location', '/') # Redirect to home page
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Specified directory does not exist or is not a directory.')

    # Remaining methods (browse_and_serve_files, serve_file, list_directory, upload_file)
    # use the global SERVER_BASE_DIR variable, so they work without further changes:

    def browse_and_serve_files(self, parsed_url):
        relative_path = unquote(parsed_url.path[len('/browse/'):])
        file_path = os.path.join(SERVER_BASE_DIR, os.path.normpath(relative_path))
        
        if not os.path.abspath(file_path).startswith(os.path.abspath(SERVER_BASE_DIR)):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Access denied.')
            return

        if os.path.isdir(file_path):
            self.list_directory(file_path)
        elif os.path.isfile(file_path):
            self.serve_file(file_path)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File or directory not found.')

    def serve_file(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Content-Disposition', f'inline; filename="{os.path.basename(file_path)}"')
        self.end_headers()
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())

    def list_directory(self, dir_path):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        response = f'<html><body><h1>Directory listing for {dir_path}</h1><ul>'.encode()
        files = os.listdir(dir_path)
        
        # Add a link to go up one level if not at the root server dir
        if os.path.abspath(dir_path) != os.path.abspath(SERVER_BASE_DIR):
            parent_dir = os.path.dirname(dir_path)
            relative_parent = os.path.relpath(parent_dir, SERVER_BASE_DIR)
            # Handle root parent edge case
            parent_link = '/browse/' + relative_parent.replace(os.sep, '/') if relative_parent != '.' else '/browse/'
            response += f'<li><a href="{parent_link}">[Parent Directory]</a></li>'.encode()

        for filename in sorted(files):
            relative_filename = os.path.relpath(os.path.join(dir_path, filename), SERVER_BASE_DIR)
            link_path = f'/browse/{relative_filename.replace(os.sep, "/")}'
            response += f'<li><a href="{link_path}">{filename}</a></li>'.encode()
        
        response += b'</ul><hr><a href="/">Go Home</a></body></html>'
        self.wfile.write(response)

    def upload_file(self):
        upload_dir = SERVER_BASE_DIR
        
        content_type = self.headers.get('Content-Type')
        if not content_type or 'multipart/form-data' not in content_type:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid Content-Type for upload.')
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
            }
        )

        if 'file' in form:
            file_item = form['file']
            if file_item.filename:
                filename = os.path.basename(file_item.filename)
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(file_item.file.read())
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f'File "{filename}" uploaded successfully! Browse files [here](/browse).'.encode())
                return

        self.send_response(400)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'No file provided or upload failed.')

# --- Server Start Logic ---

# Use argparse to handle initial command line arguments
parser = argparse.ArgumentParser(description="Simple HTTP Server with File Upload/Browse.")
parser.add_argument('-p', '--port', type=int, default=8080, help='Specify alternate port (default: 8080)')
parser.add_argument('-b', '--bind', default="", help='Specify alternate bind address (default: all interfaces)')
parser.add_argument('-d', '--directory', default=os.getcwd(), help='Specify alternative initial directory (default: current directory)')
args = parser.parse_args()

# Set the initial global variable from the command line argument
SERVER_BASE_DIR = os.path.abspath(args.directory)
PORT = args.port
BIND_ADDRESS = args.bind

# Change the initial CWD for correct relative path handling
os.chdir(SERVER_BASE_DIR)

with socketserver.TCPServer((BIND_ADDRESS, PORT), FileServer) as server:
    print(f"Serving directory {SERVER_BASE_DIR} on http://{BIND_ADDRESS or '0.0.0.0'}:{PORT}")
    server.serve_forever()
