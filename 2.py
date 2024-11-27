import os
import sys
import json
import time
import signal
import socket
import subprocess
import webbrowser
import psutil
import http.server
import threading
from typing import Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox, QFileDialog, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMenu
)

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, streamlit_port, *args, **kwargs):
        self.streamlit_port = streamlit_port
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        redirect_script = f'''
        <html>
        <head>
            <title>Redirecting to Streamlit...</title>
            <meta http-equiv="refresh" content="5;url=http://localhost:{self.streamlit_port}">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }}
                .loader {{
                    border: 4px solid #f3f3f3;
                    border-radius: 50%;
                    border-top: 4px solid #3498db;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .countdown {{
                    margin-top: 20px;
                    color: #666;
                }}
            </style>
            <script>
                let countdown = 5;
                function updateCountdown() {{
                    const elem = document.getElementById('countdown');
                    if (countdown > 0) {{
                        elem.textContent = `Redirecting in ${countdown} seconds...`;
                        countdown--;
                        setTimeout(updateCountdown, 1000);
                    }}
                }}
                window.onload = function() {{
                    updateCountdown();
                    setTimeout(function() {{
                        window.location.href = 'http://localhost:{self.streamlit_port}';
                    }}, 5000);
                }}
            </script>
        </head>
        <body>
            <div class="loader"></div>
            <h2>Starting Streamlit...</h2>
            <p>You will be automatically redirected when the application is ready.</p>
            <div id="countdown" class="countdown">Redirecting in 5 seconds...</div>
        </body>
        </html>
        '''
        self.wfile.write(redirect_script.encode())

class RedirectServer:
    def __init__(self, streamlit_port):
        self.streamlit_port = streamlit_port
        self.port = self._find_available_port(8000)
        self.server = None
        self.thread = None

    def _find_available_port(self, start_port):
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except socket.error:
                port += 1
        raise RuntimeError("No available ports found")

    def start(self):
        handler = lambda *args: RedirectHandler(self.streamlit_port, *args)
        self.server = http.server.HTTPServer(('localhost', self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        return self.port

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

def find_available_port(start_port=8501):
    """Find the first available port starting from start_port"""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                port += 1

def release_port(port):
    """Release the specified port by killing any process using it"""
    try:
        for proc in psutil.process_iter(['pid', 'connections']):
            try:
                connections = proc.net_connections()
                for conn in connections:
                    if conn.laddr.port == port:
                        if sys.platform == 'win32':
                            os.kill(proc.pid, signal.SIGTERM)
                        else:
                            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error releasing port {port}: {e}")

class ConfigManager:
    """Manages configuration storage and retrieval"""
    def __init__(self):
        self.base_path = self._get_base_path()
        self.config_file = os.path.join(self.base_path, 'config.json')
        self.config = self._load_config()

    def _get_base_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {
            'api_key': '',
            'api_base': 'https://integrate.api.nvidia.com/v1',
            'model': 'openai/nvidia/llama-3.1-nemotron-70b-instruct',
            'recent_paths': [],
            'instances': {}
        }

    def save(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def add_recent_path(self, path):
        recent = self.config.get('recent_paths', [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.config['recent_paths'] = recent[:10]  # Keep only 10 most recent
        self.save()

class StreamlitThread(QThread):
    """Handles running a Streamlit instance"""
    error_occurred = pyqtSignal(str)
    started_successfully = pyqtSignal(int)
    status_update = pyqtSignal(str)
    app_ready = pyqtSignal(int)

    def __init__(self, port, directory, api_key, api_base, model):
        super().__init__()
        self.port = port
        self.directory = directory
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.process = None
        self._is_running = False
        self.start_time = time.time()
        self.redirect_server = None

    def run(self):
        try:
            # Start redirect server
            self.redirect_server = RedirectServer(self.port)
            redirect_port = self.redirect_server.start()
            
            env = os.environ.copy()
            env.update({
                'APP_PORT': str(self.port),
                'APP_API_KEY': self.api_key,
                'APP_API_BASE': self.api_base,
                'APP_MODEL': self.model,
                'APP_DIRECTORY': self.directory
            })

            if getattr(sys, 'frozen', False):
                base_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '..', 'vai'))
            else:
                base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'vai')
            
            streamlit_exe = os.path.join(base_path, 'ai.exe' if sys.platform == 'win32' else 'ai')

            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            self.process = subprocess.Popen(
                [streamlit_exe],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags,
                preexec_fn=None if sys.platform == 'win32' else os.setsid
            )

            self._is_running = True
            self.started_successfully.emit(self.port)
            
            # Open browser to redirect page
            webbrowser.open(f'http://localhost:{redirect_port}', new=2)

            while self._is_running and self.process.poll() is None:
                if self.process.stdout:
                    stdout = self.process.stdout.readline()
                    if stdout:
                        self.status_update.emit(stdout.strip())
                        if "You can now view your Streamlit app in the browser" in stdout:
                            self.app_ready.emit(self.port)
                if self.process.stderr:
                    stderr = self.process.stderr.readline()
                    if stderr:
                        self.status_update.emit(f"Error: {stderr.strip()}")

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False

    def stop(self):
        if self.redirect_server:
            self.redirect_server.stop()
            
        if self.process:
            try:
                release_port(self.port)
                if sys.platform == 'win32':
                    self.process.terminate()
                    QTimer.singleShot(1000, lambda: subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)]) if self.process else None)
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process = None
            except Exception as e:
                print(f"Error stopping process: {e}")
        self._is_running = False
        self.quit()

class StreamlitLauncher(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.current_instance = None
        self.status_label = None  # New status label
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Streamlit Multi-Instance Launcher')
        self.setFixedSize(500, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.setup_directory_section(layout)
        self.setup_api_section(layout)
        self.setup_launch_button(layout)
        
        # Add status label
        self.status_label = QLabel('')
        layout.addWidget(self.status_label)

    def setup_directory_section(self, layout):
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.addItems(self.config.get('recent_paths', []))
        
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.browse_directory)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.path_combo)
        dir_layout.addWidget(browse_button)
        layout.addLayout(dir_layout)

    def setup_api_section(self, layout):
        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout()

        self.api_key_input = QLineEdit(self.config.get('api_key', ''))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(QLabel('API Key:'))
        api_layout.addWidget(self.api_key_input)

        self.api_base_input = QLineEdit(self.config.get('api_base', ''))
        api_layout.addWidget(QLabel('API Base:'))
        api_layout.addWidget(self.api_base_input)

        self.model_input = QLineEdit(self.config.get('model', ''))
        api_layout.addWidget(QLabel('Model:'))
        api_layout.addWidget(self.model_input)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

    def setup_launch_button(self, layout):
        self.launch_button = QPushButton('Launch Instance')
        self.launch_button.clicked.connect(self.toggle_instance)
        layout.addWidget(self.launch_button)

    def toggle_instance(self):
        if self.current_instance is None:
            self.launch_new_instance()
        else:
            self.stop_instance()

    def launch_new_instance(self):
        directory = self.path_combo.currentText()
        if not directory or not os.path.exists(directory):
            return
        
        self.config.add_recent_path(directory)
        port = find_available_port()
        thread = StreamlitThread(
            port=port,
            directory=directory,
            api_key=self.api_key_input.text(),
            api_base=self.api_base_input.text(),
            model=self.model_input.text()
        )
        
        thread.started_successfully.connect(lambda p: self.status_label.setText(f"Starting Streamlit on port {p}..."))
        thread.app_ready.connect(self.on_app_ready)  # Connect to new ready signal
        thread.error_occurred.connect(self.on_instance_error)
        thread.status_update.connect(lambda msg: self.status_label.setText(msg))
        
        self.current_instance = thread
        thread.start()
        self.launch_button.setText('Stop Instance')

    def on_app_ready(self, port):
        """Called when Streamlit is actually ready"""
        self.status_label.setText(f"Streamlit is ready on port {port}")
        webbrowser.open(f'http://localhost:{port}')

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_combo.setCurrentText(directory)
            self.config.add_recent_path(directory)

    def stop_instance(self):
        if self.current_instance:
            self.current_instance.stop()
            self.current_instance = None
            self.launch_button.setText('Launch Instance')
            self.status_label.setText('')

    def on_instance_error(self, error):
        self.status_label.setText(f"Error: {error}")
        self.stop_instance()
        
    def closeEvent(self, event):
        if self.current_instance:
            self.stop_instance()
        event.accept()

def main():
    app = QApplication(sys.argv)
    launcher = StreamlitLauncher()
    launcher.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()