# File-Share
You can use this tool to share file between devices.

# 🚀 Dynamic Python File Server

This is a simple yet powerful HTTP file server built in Python, leveraging the standard library modules like `http.server`, `socketserver`, and `cgi`. It provides features for **browsing files**, **uploading files** to the current served directory, and **dynamically changing the serving directory** while the server is running.

## ✨ Features

  * **File Browsing:** View a list of files and subdirectories in the served directory.
  * **File Serving:** Serve files directly from the browser with correct MIME types.
  * **File Upload:** Upload new files to the currently served directory via a simple web form.
  * **Dynamic Directory Change:** Change the root directory the server is hosting *without* restarting the server.
  * **Command-Line Configuration:** Specify the initial port, bind address, and serving directory on startup.
  * **Path Security:** Includes checks to prevent directory traversal attacks (ensures files accessed are within the server base directory).

## 📋 Prerequisites

  * Python 3.x (No external libraries required—it uses only the standard library).

## 💻 Usage

### Starting the Server

The server can be started with no arguments to serve the current directory on port `8080`.

```bash
python your_script_name.py
```

### Command-Line Options

You can customize the server by providing arguments:

| Option | Shorthand | Default | Description |
| :--- | :--- | :--- | :--- |
| `--port` | `-p` | `8080` | Specify the listening port. |
| `--bind` | `-b` | `""` (All interfaces) | Specify the interface address to bind to. |
| `--directory` | `-d` | `os.getcwd()` | Specify the initial directory to serve. |

**Example:** Serve the `/var/www` directory on port `9000`.

```bash
python your_script_name.py -d /var/www -p 9000
```

### Accessing the Server

Once started, open your web browser and navigate to the displayed address:

```
http://<bind_address>:<port>
```

-----

## 🧭 Web Interface Guide

The root page (`/`) offers three main functionalities:

1.  ### 📂 Browse Current Directory

    Click the **"Browse Current Directory"** link to view an interactive list of files and folders in the currently served directory. You can navigate through subdirectories and download files.

2.  ### ⬆️ Upload File

    Use the file input and **"Upload to Current Dir"** button to upload a file directly to the root of the directory currently being served.

3.  ### 🔄 Change Server Directory

    Enter an **absolute path** into the text field and click **"Change Directory"**. The server will immediately start serving files from the new location without a restart.

-----

## ⚙️ Implementation Details

The core of the server is the `FileServer` class, which extends `http.server.BaseHTTPRequestHandler`.

  * **Dynamic Directory:** The `SERVER_BASE_DIR` is a global variable that holds the current serving directory. It is dynamically updated by the `change_directory` method when a request is made to `/change_dir`.
  * **Request Handling:**
      * **GET requests** handle the root page, directory browsing (`/browse`), file serving, and the directory change via the form.
      * **POST requests** handle file uploads (`/upload`).
  * **Path Security:** The `browse_and_serve_files` method includes a check (`os.path.abspath(file_path).startswith(...)`) to ensure that users cannot navigate to files or directories outside the configured `SERVER_BASE_DIR`, preventing unauthorized access to other parts of the filesystem.
