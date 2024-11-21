import os
import sys
import json
import time
import signal
import socket
import subprocess
import webbrowser
from typing import Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox, QFileDialog, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMenu
)

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
    started_successfully = pyqtSignal()
    status_update = pyqtSignal(str)

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

    def run(self):
        try:
            # Set up environment variables
            env = os.environ.copy()
            env.update({
                'APP_PORT': str(self.port),
                'APP_API_KEY': self.api_key,
                'APP_API_BASE': self.api_base,
                'APP_MODEL': self.model,
                'APP_DIRECTORY': self.directory
            })

            # Determine the correct path for the Streamlit executable
            if getattr(sys, 'frozen', False):
                base_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '..', 'vai'))
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            streamlit_exe = os.path.join(base_path, 'ai.exe' if sys.platform == 'win32' else 'ai')

            # Start the process
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            self.process = subprocess.Popen(
                [streamlit_exe],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )

            self._is_running = True
            self.started_successfully.emit()

            # Monitor the process
            while self._is_running and self.process.poll() is None:
                stdout = self.process.stdout.readline()
                if stdout:
                    self.status_update.emit(stdout.strip())
                stderr = self.process.stderr.readline()
                if stderr:
                    self.status_update.emit(f"Error: {stderr.strip()}")

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False

    def stop(self):
        if self.process:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None
        self._is_running = False

class StreamlitLauncher(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.instances: Dict[int, StreamlitThread] = {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Streamlit Multi-Instance Launcher')
        self.setFixedSize(600, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Directory selection
        self.setup_directory_section(layout)
        
        # API configuration
        self.setup_api_section(layout)
        
        # Instances table
        # self.setup_instances_table(layout)
        
        # Launch button
        self.setup_launch_button(layout)

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

        # API Key
        self.api_key_input = QLineEdit(self.config.get('api_key', ''))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(QLabel('API Key:'))
        api_layout.addWidget(self.api_key_input)

        # API Base
        self.api_base_input = QLineEdit(self.config.get('api_base', ''))
        api_layout.addWidget(QLabel('API Base:'))
        api_layout.addWidget(self.api_base_input)

        # Model
        self.model_input = QLineEdit(self.config.get('model', ''))
        api_layout.addWidget(QLabel('Model:'))
        api_layout.addWidget(self.model_input)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

    def setup_launch_button(self, layout):
        launch_button = QPushButton('Launch New Instance')
        launch_button.clicked.connect(self.launch_new_instance)
        layout.addWidget(launch_button)

    def launch_new_instance(self):
        directory = self.path_combo.currentText()
        if not directory or not os.path.exists(directory):
            return
        
        # Save directory to recent paths
        self.config.add_recent_path(directory)
        
        # Find available port and create new instance
        port = find_available_port()
        thread = StreamlitThread(
            port=port,
            directory=directory,
            api_key=self.api_key_input.text(),
            api_base=self.api_base_input.text(),
            model=self.model_input.text()
        )
        
        # Connect signals
        thread.started_successfully.connect(lambda: self.on_instance_started(port))
        thread.error_occurred.connect(lambda msg: self.on_instance_error(port, msg))
        
        # Store and start instance
        self.instances[port] = thread
        thread.start()
    

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_combo.setCurrentText(directory)
            self.config.add_recent_path(directory)

    def on_instance_started(self, port):
        webbrowser.open(f'http://localhost:{port}')

    def on_instance_error(self, port, error):
        print(f"Error on port {port}: {error}")
        self.stop_instance(port)

    def stop_instance(self, port):
        if port in self.instances:
            self.instances[port].stop()
            self.instances[port].wait()
            del self.instances[port]
            self.update_instances_display()

    def closeEvent(self, event):
        """Clean up all instances before closing"""
        for port in list(self.instances.keys()):
            self.stop_instance(port)
        event.accept()

def main():
    app = QApplication(sys.argv)
    launcher = StreamlitLauncher()
    launcher.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()