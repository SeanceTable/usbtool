#!/usr/bin/env python3
"""
VirtualHere USB Manager with Web Display Server
Captures your Mac app screen and serves it via web interface with interaction
Usage: python3 script.py --program "/Applications/YourApp.app" --web-port 8080
"""

import socket
import subprocess
import threading
import time
import argparse
import sys
import os
import json
import urllib.request
import platform
import base64
import io
from datetime import datetime, timedelta
from queue import Queue
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
from PIL import Image, ImageGrab
import pyautogui

class WebDisplayHandler(BaseHTTPRequestHandler):
    """HTTP handler for web-based app display"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]
        
        if path == '/':
            self.serve_app_interface()
        elif path == '/app-screen':
            self.serve_app_screenshot()
        elif path == '/api/screenshot':
            self.serve_screenshot_api()
        elif path == '/api/click':
            self.handle_click()
        elif path == '/api/status':
            self.serve_status_api()
        elif path.startswith('/static/'):
            self.serve_static_content(path)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        path = self.path.split('?')[0]
        
        if path == '/api/click':
            self.handle_click()
        elif path == '/api/key':
            self.handle_key()
        elif path == '/api/upload':
            self.handle_upload()
        else:
            self.send_error(404)
    
    def serve_app_interface(self):
        """Serve the main web interface"""
        html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote iOS Testing Station</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: white;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.8);
            padding: 10px 20px;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
        }
        
        .title {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .status {
            display: flex;
            gap: 20px;
            align-items: center;
            font-size: 0.9rem;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #666;
        }
        
        .status-dot.connected {
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        
        .status-dot.waiting {
            background: #fbbf24;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .app-display {
            flex: 1;
            position: relative;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .app-screen {
            max-width: 100%;
            max-height: 100%;
            cursor: pointer;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            transition: transform 0.1s ease;
        }
        
        .app-screen:active {
            transform: scale(0.99);
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #333;
            border-top: 4px solid #4ade80;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }
        
        .control-btn {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #333;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }
        
        .control-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: #666;
        }
        
        .fullscreen-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.6);
            border: none;
            color: white;
            padding: 8px;
            border-radius: 4px;
            cursor: pointer;
            z-index: 1000;
        }
        
        .connection-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            z-index: 500;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">📱 iOS Testing Station</div>
            <div class="status">
                <div class="status-item">
                    <div class="status-dot" id="usbStatus"></div>
                    <span id="usbText">USB: Checking...</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" id="appStatus"></div>
                    <span id="appText">App: Loading...</span>
                </div>
                <div class="status-item">
                    <span id="sessionInfo">Session: --</span>
                </div>
            </div>
        </div>
        
        <div class="app-display">
            <img id="appScreen" class="app-screen hidden" alt="Testing App">
            
            <div id="loadingScreen" class="loading">
                <div class="spinner"></div>
                <h3>Connecting to Testing App...</h3>
                <p>Please wait while we establish connection</p>
            </div>
            
            <div id="connectionOverlay" class="connection-overlay hidden">
                <h2>🔌 Connect Your Device</h2>
                <p>Plug in your iPhone or iPad to begin testing</p>
                <div class="spinner" style="margin-top: 20px;"></div>
            </div>
            
            <button class="fullscreen-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">
                ⛶
            </button>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="refreshScreen()">🔄 Refresh</button>
            <button class="control-btn" onclick="showKeyboard()">⌨️ Keyboard</button>
            <button class="control-btn" onclick="resetConnection()">🔄 Reset</button>
        </div>
    </div>
    
    <script>
        let screenImg = document.getElementById('appScreen');
        let loadingScreen = document.getElementById('loadingScreen');
        let connectionOverlay = document.getElementById('connectionOverlay');
        let isLoaded = false;
        let updateInterval;
        let clickCooldown = false;
        
        // Initialize
        function init() {
            startScreenUpdates();
            startStatusUpdates();
            setupClickHandler();
            setupKeyboardHandler();
        }
        
        function startScreenUpdates() {
            updateInterval = setInterval(updateScreen, 500); // 2 FPS for responsiveness
            updateScreen(); // Initial load
        }
        
        function updateScreen() {
            const img = new Image();
            img.onload = function() {
                screenImg.src = this.src;
                if (!isLoaded) {
                    isLoaded = true;
                    loadingScreen.classList.add('hidden');
                    screenImg.classList.remove('hidden');
                    document.getElementById('appStatus').classList.add('connected');
                    document.getElementById('appText').textContent = 'App: Connected';
                }
            };
            img.onerror = function() {
                if (isLoaded) {
                    document.getElementById('appStatus').classList.remove('connected');
                    document.getElementById('appText').textContent = 'App: Disconnected';
                }
            };
            img.src = '/api/screenshot?' + Date.now(); // Cache busting
        }
        
        function startStatusUpdates() {
            setInterval(updateStatus, 2000);
            updateStatus();
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateUSBStatus(data.usb);
                    updateSessionInfo(data.session);
                    
                    if (data.usb.connected) {
                        connectionOverlay.classList.add('hidden');
                    } else {
                        connectionOverlay.classList.remove('hidden');
                    }
                })
                .catch(error => {
                    console.error('Status update error:', error);
                });
        }
        
        function updateUSBStatus(usb) {
            const statusDot = document.getElementById('usbStatus');
            const statusText = document.getElementById('usbText');
            
            if (usb.connected) {
                statusDot.classList.add('connected');
                statusText.textContent = `USB: ${usb.device_name}`;
            } else if (usb.queue > 0) {
                statusDot.classList.add('waiting');
                statusDot.classList.remove('connected');
                statusText.textContent = `USB: Queue (${usb.queue})`;
            } else {
                statusDot.classList.remove('connected', 'waiting');
                statusText.textContent = 'USB: Waiting...';
            }
        }
        
        function updateSessionInfo(session) {
            const sessionInfo = document.getElementById('sessionInfo');
            if (session.active) {
                const remaining = Math.max(0, session.remaining);
                sessionInfo.textContent = `Session: ${remaining}s remaining`;
            } else {
                sessionInfo.textContent = 'Session: --';
            }
        }
        
        function setupClickHandler() {
            screenImg.addEventListener('click', function(e) {
                if (clickCooldown) return;
                clickCooldown = true;
                setTimeout(() => clickCooldown = false, 200);
                
                const rect = screenImg.getBoundingClientRect();
                const scaleX = screenImg.naturalWidth / rect.width;
                const scaleY = screenImg.naturalHeight / rect.height;
                
                const x = Math.round((e.clientX - rect.left) * scaleX);
                const y = Math.round((e.clientY - rect.top) * scaleY);
                
                // Visual feedback
                screenImg.style.filter = 'brightness(1.2)';
                setTimeout(() => screenImg.style.filter = '', 100);
                
                // Send click to server
                fetch('/api/click', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({x: x, y: y})
                }).catch(error => console.error('Click error:', error));
            });
        }
        
        function setupKeyboardHandler() {
            document.addEventListener('keydown', function(e) {
                // Don't capture system shortcuts
                if (e.metaKey || e.ctrlKey || e.altKey) return;
                
                e.preventDefault();
                
                fetch('/api/key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        key: e.key,
                        code: e.code,
                        shift: e.shiftKey
                    })
                }).catch(error => console.error('Key error:', error));
            });
        }
        
        function refreshScreen() {
            updateScreen();
        }
        
        function showKeyboard() {
            // Focus on a hidden input to trigger mobile keyboard
            const input = document.createElement('input');
            input.style.opacity = '0';
            input.style.position = 'absolute';
            input.style.left = '-9999px';
            document.body.appendChild(input);
            input.focus();
            setTimeout(() => document.body.removeChild(input), 1000);
        }
        
        function resetConnection() {
            location.reload();
        }
        
        function toggleFullscreen() {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                document.documentElement.requestFullscreen();
            }
        }
        
        // Initialize when page loads
        window.addEventListener('load', init);
        
        // Handle visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                clearInterval(updateInterval);
            } else {
                startScreenUpdates();
            }
        });
    </script>
</body>
</html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_screenshot_api(self):
        """Capture and serve app screenshot"""
        try:
            # Get the app window bounds if available
            if hasattr(self.server, 'get_app_bounds'):
                bounds = self.server.get_app_bounds()
            else:
                bounds = None
            
            if bounds:
                # Capture specific app window
                screenshot = ImageGrab.grab(bbox=bounds)
            else:
                # Capture entire screen
                screenshot = ImageGrab.grab()
            
            # Resize for performance
            max_width = 1920
            if screenshot.width > max_width:
                ratio = max_width / screenshot.width
                new_height = int(screenshot.height * ratio)
                screenshot = screenshot.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='JPEG', quality=85, optimize=True)
            img_bytes = img_buffer.getvalue()
            
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', len(img_bytes))
            self.end_headers()
            self.wfile.write(img_bytes)
            
        except Exception as e:
            print(f"Screenshot error: {e}")
            self.send_error(500)
    
    def handle_click(self):
        """Handle mouse click from web interface"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                x = data.get('x', 0)
                y = data.get('y', 0)
                
                # Convert to screen coordinates if needed
                if hasattr(self.server, 'get_app_bounds'):
                    bounds = self.server.get_app_bounds()
                    if bounds:
                        x += bounds[0]
                        y += bounds[1]
                
                # Perform click
                pyautogui.click(x, y)
                print(f"Click at ({x}, {y})")
                
                response = {'success': True}
            else:
                response = {'success': False, 'error': 'No data'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Click error: {e}")
            response = {'success': False, 'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    
    def handle_key(self):
        """Handle keyboard input from web interface"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                key = data.get('key', '')
                
                # Handle special keys
                if key == 'Enter':
                    pyautogui.press('enter')
                elif key == 'Backspace':
                    pyautogui.press('backspace')
                elif key == 'Tab':
                    pyautogui.press('tab')
                elif key == 'Escape':
                    pyautogui.press('escape')
                elif len(key) == 1:
                    pyautogui.write(key)
                
                response = {'success': True}
            else:
                response = {'success': False, 'error': 'No data'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Key error: {e}")
            response = {'success': False, 'error': str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    
    def serve_status_api(self):
        """Serve status information"""
        try:
            if hasattr(self.server, 'station'):
                station = self.server.station
                
                # USB status
                usb_status = {
                    'connected': station.current_device is not None,
                    'device_name': station.current_device.get('description', 'Unknown') if station.current_device else None,
                    'queue': station.device_queue.qsize()
                }
                
                # Session status
                session_status = {
                    'active': station.session_start_time is not None,
                    'remaining': 0
                }
                
                if station.session_start_time:
                    elapsed = datetime.now() - station.session_start_time
                    session_status['remaining'] = max(0, 60 - elapsed.seconds)
                
                status = {
                    'usb': usb_status,
                    'session': session_status
                }
            else:
                status = {
                    'usb': {'connected': False, 'device_name': None, 'queue': 0},
                    'session': {'active': False, 'remaining': 0}
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            
        except Exception as e:
            print(f"Status error: {e}")
            self.send_error(500)

class WebDisplayServer(HTTPServer):
    """Custom HTTP server for web display"""
    
    def __init__(self, server_address, handler_class, station=None, program_name=None):
        super().__init__(server_address, handler_class)
        self.station = station
        self.program_name = program_name
    
    def get_app_bounds(self):
        """Get the bounds of the target application window"""
        if not self.program_name:
            return None
        
        try:
            # Use AppleScript to get window bounds
            script = f'''
            tell application "System Events"
                tell process "{self.program_name}"
                    get the position of window 1
                    get the size of window 1
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\\n')
                if len(lines) >= 2:
                    pos = lines[0].split(', ')
                    size = lines[1].split(', ')
                    
                    x = int(pos[0])
                    y = int(pos[1])
                    width = int(size[0])
                    height = int(size[1])
                    
                    return (x, y, x + width, y + height)
            
        except Exception as e:
            print(f"Error getting app bounds: {e}")
        
        return None

class VirtualHereInstaller:
    """Handles VirtualHere client download and installation"""
    
    def __init__(self):
        self.client_dir = os.path.expanduser("~/VirtualHere")
        self.client_path = os.path.join(self.client_dir, "vhclientx64")
        
        # VirtualHere download URLs
        self.download_urls = {
            "Darwin": {  # macOS
                "x86_64": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientx64",
                "arm64": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientarm64"
            },
            "Linux": {
                "x86_64": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientx86_64",
                "armv7l": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientarmhf",
                "aarch64": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientarm64"
            },
            "Windows": {
                "AMD64": "https://www.virtualhere.com/sites/default/files/usbclient/vhclientx64.exe"
            }
        }
    
    def get_platform_info(self):
        """Get current platform and architecture"""
        system = platform.system()
        machine = platform.machine()
        
        # Normalize architecture names
        if machine in ["x86_64", "AMD64"]:
            machine = "x86_64"
        elif machine in ["arm64", "aarch64"]:
            machine = "arm64"
        elif machine.startswith("arm"):
            machine = "armv7l"
            
        return system, machine
    
    def is_installed(self):
        """Check if VirtualHere client is already installed"""
        return os.path.exists(self.client_path) and os.access(self.client_path, os.X_OK)
    
    def download_client(self):
        """Download VirtualHere client for current platform"""
        system, machine = self.get_platform_info()
        
        print(f"🔍 Detected platform: {system} {machine}")
        
        # Get download URL for current platform
        if system not in self.download_urls:
            print(f"❌ Unsupported platform: {system}")
            return False
            
        platform_urls = self.download_urls[system]
        if machine not in platform_urls:
            print(f"❌ Unsupported architecture: {machine}")
            print(f"Available: {list(platform_urls.keys())}")
            return False
        
        download_url = platform_urls[machine]
        
        try:
            # Create directory
            os.makedirs(self.client_dir, exist_ok=True)
            
            print(f"📥 Downloading VirtualHere client...")
            print(f"🔗 URL: {download_url}")
            
            # Download file
            urllib.request.urlretrieve(download_url, self.client_path)
            
            # Make executable (Unix-like systems)
            if system in ["Darwin", "Linux"]:
                os.chmod(self.client_path, 0o755)
            
            print(f"✅ VirtualHere client downloaded to: {self.client_path}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def install(self):
        """Install VirtualHere client if not already present"""
        if self.is_installed():
            print(f"✅ VirtualHere client already installed: {self.client_path}")
            return True
        
        print("📦 VirtualHere client not found, downloading...")
        return self.download_client()
    
    def start_client(self, background=True):
        """Start VirtualHere client"""
        if not self.is_installed():
            print("❌ VirtualHere client not installed")
            return None
        
        try:
            print("🚀 Starting VirtualHere client...")
            
            if background:
                # Start in background
                process = subprocess.Popen([self.client_path, "-b"], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
            else:
                # Start in foreground
                process = subprocess.Popen([self.client_path])
            
            # Give it time to start
            time.sleep(2)
            
            # Check if it's running
            if process.poll() is None:
                print("✅ VirtualHere client started")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ VirtualHere client failed to start")
                if stderr:
                    print(f"Error: {stderr.decode()}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to start VirtualHere client: {e}")
            return None
    
    def stop_client(self):
        """Stop VirtualHere client"""
        try:
            # Kill VirtualHere processes
            if platform.system() == "Darwin":
                subprocess.run(["pkill", "-f", "vhclient"], capture_output=True)
            elif platform.system() == "Linux":
                subprocess.run(["pkill", "-f", "vhclient"], capture_output=True)
            elif platform.system() == "Windows":
                subprocess.run(["taskkill", "/f", "/im", "vhclientx64.exe"], capture_output=True)
            
            print("🛑 VirtualHere client stopped")
            
        except Exception as e:
            print(f"❌ Error stopping VirtualHere client: {e}")

class VirtualHereManager:
    def __init__(self, server_host="localhost", server_port=7575):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.devices = {}
        self.current_device = None
        self.device_queue = Queue()
        self.session_start_time = None
        
    def connect(self):
        """Connect to VirtualHere client"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"✅ Connected to VirtualHere at {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to VirtualHere: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from VirtualHere client"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.connected = False
            print("🔌 Disconnected from VirtualHere")
    
    def send_command(self, command):
        """Send command to VirtualHere client"""
        if not self.connected:
            return None
            
        try:
            # VirtualHere API expects commands ending with newline
            self.socket.send(f"{command}\\n".encode())
            
            # Read response
            response = b""
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
                response += data
                if b"\\n" in data:
                    break
            
            return response.decode().strip()
            
        except Exception as e:
            print(f"❌ Command error: {e}")
            return None
    
    def list_devices(self):
        """List available USB devices"""
        response = self.send_command("LIST")
        if not response:
            return []
        
        devices = []
        lines = response.split('\\n')
        
        for line in lines:
            if line.strip() and not line.startswith('VirtualHere'):
                # Parse device info
                # Format typically: "ServerName,DeviceAddress,VendorID,ProductID,Description,InUse"
                parts = line.split(',')
                if len(parts) >= 5:
                    device = {
                        'server': parts[0],
                        'address': parts[1],
                        'vendor_id': parts[2],
                        'product_id': parts[3],
                        'description': parts[4],
                        'in_use': len(parts) > 5 and parts[5] == '1',
                        'full_address': f"{parts[0]}.{parts[1]}"
                    }
                    
                    # Filter for iOS devices (Apple vendor ID: 05ac)
                    if parts[2].lower() == '05ac':
                        devices.append(device)
        
        return devices
    
    def use_device(self, device_address):
        """Connect to a USB device"""
        response = self.send_command(f"USE,{device_address}")
        success = response and "OK" in response
        
        if success:
            print(f"📱 Connected to device: {device_address}")
        else:
            print(f"❌ Failed to connect to device: {device_address}")
            
        return success
    
    def stop_using_device(self, device_address):
        """Disconnect from a USB device"""
        response = self.send_command(f"STOP USING,{device_address}")
        success = response and "OK" in response
        
        if success:
            print(f"🔌 Disconnected from device: {device_address}")
        else:
            print(f"❌ Failed to disconnect from device: {device_address}")
            
        return success

class ProgramDisplayManager:
    def __init__(self, program_path):
        self.program_path = program_path
        self.program_process = None
        self.is_displayed = False
        
    def show_program(self):
        """Show program in fullscreen"""
        try:
            print(f"🚀 Launching {os.path.basename(self.program_path)}")
            
            # Launch the program
            if self.program_path.endswith('.app'):
                self.program_process = subprocess.Popen(['open', '-a', self.program_path])
            else:
                self.program_process = subprocess.Popen([self.program_path])
            
            # Wait for launch
            time.sleep(3)
            
            # Get program name
            program_name = os.path.basename(self.program_path).replace('.app', '')
            
            # Make fullscreen and hide desktop
            applescript = f'''
            tell application "{program_name}"
                activate
                delay 1
            end tell
            
            tell application "System Events"
                tell process "{program_name}"
                    set frontmost to true
                    delay 0.5
                    try
                        keystroke "f" using {{control down, command down}}
                    on error
                        try
                            keystroke "f" using {{command down}}
                        end try
                    end try
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', applescript], 
                          capture_output=True, timeout=15)
            
            self.is_displayed = True
            print("✅ Program displayed in fullscreen")
            return True
            
        except Exception as e:
            print(f"❌ Error showing program: {e}")
            return False
    
    def hide_program(self):
        """Hide program and restore desktop"""
        if not self.is_displayed:
            return
            
        try:
            program_name = os.path.basename(self.program_path).replace('.app', '')
            
            applescript = f'''
            tell application "{program_name}"
                set miniaturized of every window to true
            end tell
            '''
            
            subprocess.run(['osascript', '-e', applescript], 
                          capture_output=True, timeout=10)
            
            self.is_displayed = False
            print("🙈 Program hidden")
            
        except Exception as e:
            print(f"❌ Error hiding program: {e}")

class USBTestingStation:
    def __init__(self, program_path, virtualhere_host="localhost", virtualhere_port=7575, 
                 web_port=8080, auto_install=True):
        self.vh_installer = VirtualHereInstaller()
        self.vh_manager = VirtualHereManager(virtualhere_host, virtualhere_port)
        self.display_manager = ProgramDisplayManager(program_path)
        self.current_device = None
        self.device_queue = Queue()
        self.session_start_time = None
        self.is_running = False
        self.auto_install = auto_install
        self.vh_process = None
        self.web_port = web_port
        self.web_server = None
        self.program_name = os.path.basename(program_path).replace('.app', '')
        
    def start(self):
        """Start the testing station"""
        print("🚀 Starting USB Testing Station with Web Interface...")
        
        # Install and start VirtualHere client if needed
        if self.auto_install:
            print("📦 Setting up VirtualHere client...")
            
            if not self.vh_installer.install():
                print("❌ Failed to install VirtualHere client")
                return False
            
            # Start VirtualHere client
            self.vh_process = self.vh_installer.start_client(background=True)
            if not self.vh_process:
                print("❌ Failed to start VirtualHere client")
                return False
            
            # Wait for client to be ready
            print("⏳ Waiting for VirtualHere client to initialize...")
            time.sleep(5)
        
        # Connect to VirtualHere
        if not self.vh_manager.connect():
            print("❌ Cannot start without VirtualHere connection")
            if self.vh_process:
                self.vh_installer.stop_client()
            return False
        
        # Show program
        if not self.display_manager.show_program():
            print("❌ Cannot start without program display")
            self.vh_manager.disconnect()
            if self.vh_process:
                self.vh_installer.stop_client()
            return False
        
        # Start web server
        if not self.start_web_server():
            print("❌ Cannot start without web server")
            self.stop()
            return False
        
        # Start monitoring
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_devices, daemon=True)
        self.monitor_thread.start()
        
        self.session_thread = threading.Thread(target=self.manage_sessions, daemon=True)
        self.session_thread.start()
        
        print("✅ Testing station started!")
        print(f"🌐 Web interface: http://localhost:{self.web_port}")
        print("👀 Users can connect via web browser to see and control your app")
        print("📱 Waiting for USB device connections...")
        
        return True
    
    def start_web_server(self):
        """Start the web server for remote display"""
        try:
            print(f"🌐 Starting web server on port {self.web_port}...")
            
            # Create web server
            self.web_server = WebDisplayServer(
                ('0.0.0.0', self.web_port), 
                WebDisplayHandler,
                station=self,
                program_name=self.program_name
            )
            
            # Start server in background thread
            self.web_server_thread = threading.Thread(
                target=self.web_server.serve_forever, 
                daemon=True
            )
            self.web_server_thread.start()
            
            print(f"✅ Web server started on http://0.0.0.0:{self.web_port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            return False
    
    def stop_web_server(self):
        """Stop the web server"""
        if self.web_server:
            try:
                self.web_server.shutdown()
                self.web_server.server_close()
                print("🌐 Web server stopped")
            except Exception as e:
                print(f"❌ Error stopping web server: {e}")
    
    def stop(self):
        """Stop the testing station"""
        print("🛑 Stopping testing station...")
        
        self.is_running = False
        
        # Disconnect current device
        if self.current_device:
            self.vh_manager.stop_using_device(self.current_device['full_address'])
        
        # Stop web server
        self.stop_web_server()
        
        # Hide program
        self.display_manager.hide_program()
        
        # Disconnect VirtualHere
        self.vh_manager.disconnect()
        
        # Stop VirtualHere client if we started it
        if self.vh_process:
            self.vh_installer.stop_client()
        
        print("✅ Testing station stopped")
    
    def monitor_devices(self):
        """Monitor for new device connections"""
        while self.is_running:
            try:
                devices = self.vh_manager.list_devices()
                
                # Find new iOS devices
                for device in devices:
                    if not device['in_use'] and device['full_address'] not in [d.get('full_address') for d in [self.current_device] if d]:
                        print(f"📱 New iOS device detected: {device['description']}")
                        
                        if not self.current_device:
                            self.connect_device(device)
                        else:
                            self.add_to_queue(device)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(10)
    
    def connect_device(self, device):
        """Connect to a device and start session"""
        if self.vh_manager.use_device(device['full_address']):
            self.current_device = device
            self.session_start_time = datetime.now()
            
            print(f"🎯 Session started: {device['description']}")
            print("⏰ 60 second session timer started")
    
    def add_to_queue(self, device):
        """Add device to queue"""
        self.device_queue.put(device)
        queue_size = self.device_queue.qsize()
        print(f"⏳ Device queued: {device['description']} (Position: {queue_size})")
    
    def manage_sessions(self):
        """Manage session timeouts and queue"""
        while self.is_running:
            try:
                # Check session timeout
                if self.current_device and self.session_start_time:
                    elapsed = datetime.now() - self.session_start_time
                    
                    if elapsed.seconds >= 60:  # 1 minute timeout
                        print(f"⏰ Session timeout: {self.current_device['description']}")
                        self.end_current_session()
                
                # Process queue
                if not self.current_device and not self.device_queue.empty():
                    next_device = self.device_queue.get()
                    print(f"📱 Processing queued device: {next_device['description']}")
                    self.connect_device(next_device)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Session management error: {e}")
                time.sleep(5)
    
    def end_current_session(self):
        """End current device session"""
        if self.current_device:
            device_addr = self.current_device['full_address']
            device_desc = self.current_device['description']
            
            self.vh_manager.stop_using_device(device_addr)
            
            print(f"🔚 Session ended: {device_desc}")
            
            self.current_device = None
            self.session_start_time = None

def main():
    parser = argparse.ArgumentParser(description='VirtualHere USB Testing Station with Web Interface')
    parser.add_argument('--program', required=True,
                       help='Path to your testing program')
    parser.add_argument('--server', default='localhost',
                       help='VirtualHere server host (default: localhost)')
    parser.add_argument('--port', type=int, default=7575,
                       help='VirtualHere server port (default: 7575)')
    parser.add_argument('--web-port', type=int, default=8080,
                       help='Web server port (default: 8080)')
    parser.add_argument('--action', choices=['start', 'stop', 'status', 'install-only'],
                       default='start',
                       help='Action to perform')
    parser.add_argument('--no-auto-install', action='store_true',
                       help='Skip automatic VirtualHere installation')
    
    args = parser.parse_args()
    
    # Check for required dependencies
    try:
        import pyautogui
        from PIL import Image, ImageGrab
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("💡 Install with: pip3 install pyautogui pillow")
        sys.exit(1)
    
    # Validate program
    if args.action != 'install-only' and not os.path.exists(args.program):
        print(f"❌ Program not found: {args.program}")
        sys.exit(1)
    
    auto_install = not args.no_auto_install
    
    if args.action == 'install-only':
        print("📦 Installing VirtualHere client only...")
        installer = VirtualHereInstaller()
        if installer.install():
            print("✅ VirtualHere client installed successfully")
            print(f"📍 Location: {installer.client_path}")
        else:
            print("❌ Failed to install VirtualHere client")
            sys.exit(1)
        return
    
    print(f"🎯 Program: {args.program}")
    print(f"🌐 VirtualHere: {args.server}:{args.port}")
    print(f"🌐 Web Interface: http://localhost:{args.web_port}")
    print(f"📦 Auto-install: {'Yes' if auto_install else 'No'}")
    
    station = USBTestingStation(
        args.program, 
        args.server, 
        args.port, 
        args.web_port,
        auto_install
    )
    
    if args.action == 'start':
        if station.start():
            try:
                print("\n" + "="*60)
                print("🎮 TESTING STATION RUNNING")
                print("="*60)
                print(f"🌐 Remote users can connect to: http://your-ip:{args.web_port}")
                print("👀 They will see and control your testing app through browser")
                print("📱 USB devices connect via VirtualHere")
                print("⌨️  Commands: Ctrl+C to stop")
                print("="*60)
                
                while station.is_running:
                    time.sleep(1)
                        
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                station.stop()

if __name__ == "__main__":
    main()
