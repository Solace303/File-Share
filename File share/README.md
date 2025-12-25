This README is designed to showcase your project professionally on GitHub, highlighting the **Async** capabilities, the **Modern UI**, and the **Bash integration** we built.

---

# 🚀 Async Colorful File Server

A lightweight, multi-threaded Python HTTP server designed for seamless file sharing and management. This server features a modern, colorful dark-mode UI and is optimized for concurrent connections, making it ideal for cloud-to-server communication and multi-user environments.

## ✨ Features

* **⚡ Fully Asynchronous:** Built using `ThreadingMixIn` to handle multiple uploads, downloads, and requests simultaneously without blocking.
* **🎨 Modern UI:** A custom CSS-injected interface featuring a vibrant dark-mode palette, responsive "cards," and intuitive icons.
* **📂 Directory Browsing:** Navigate through your local filesystem directly from the web browser.
* **📤 File Uploads:** Supports multiple file uploads at once to the current server directory.
* **⚙️ Dynamic Root Change:** Change the server's base directory on the fly via the web interface.
* **📶 Network Optimized:** Includes a Bash script for automatic IP detection (wlan0) to make the server instantly accessible over local networks.

---

## 🛠️ Installation & Setup

### 1. Prerequisites

Ensure you have Python 3.x installed on your system.

### 2. File Structure

Place both files in the same directory:

* `server5.py` (The Python Logic)
* `run_server.sh` (The Bash script)

### 3. Make the script executable

```bash
chmod +x run_server.sh

```

---

## 🚀 Usage

### Running via Bash (Recommended)

This method automatically detects your `wlan0` IP address and binds the server to it:

```bash
./start.sh

```

### Running via Python Directly

You can also specify custom ports or bind addresses manually:

```bash
python3 server5.py --bind 192.168.1.5 --port 8080

```

---

## 📂 Project Architecture

The server uses a **Thread-per-Request** model. This ensures that:

1. **User A** can upload a large video file.
2. **User B** can browse the directory at the same time.
3. **Cloud processes** can ping the server for status updates without latency.

---

## 🎨 Configuration (CSS Styling)

The look and feel of the server is controlled by the `STYLING` constant within `server5.py`. You can easily modify the colors:

* **Background:** `#1a1a2e`
* **Cards:** `#16213e`
* **Accents:** `#4cc9f0` (Blue), `#f72585` (Pink)

---

## 📝 Technical Details

| Component | Description |
| --- | --- |
| **Language** | Python 3.x |
| **Library** | `http.server`, `socketserver` |
| **Concurrency** | `socketserver.ThreadingMixIn` |
| **Encoding** | UTF-8 (Full Emoji Support) |
| **Protocol** | HTTP/1.1 |

---

## 🛡️ License

This project is open-source and available under the MIT License.

---

Would you like me to add a **"How to Contribute"** section or a **"Security Warning"** about exposing this server to the public internet?
