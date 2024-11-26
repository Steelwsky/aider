import os
import sys
import json
import time
import signal
import socket
import subprocess
import webbrowser
import psutil
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog, QGroupBox, QLineEdit
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
            'recent_paths': []
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
            env = os.environ.copy()
            env.update({
                'APP_PORT': str(self.port),
                'APP_API_KEY': self.api_key,
                'APP_API_BASE': self.api_base,
                'APP_MODEL': self.model,
                'APP_DIRECTORY': self.directory
            })

            if getattr(sys, 'frozen', False):
                base_path = os.path.abspath(os.path.join(
                    os.path.dirname(sys.executable), '..', 'vai'))
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
            self.started_successfully.emit()

            while self._is_running and self.process.poll() is None:
                if self.process.stdout:
                    stdout = self.process.stdout.readline()
                    if stdout:
                        self.status_update.emit(stdout.strip())
                if self.process.stderr:
                    stderr = self.process.stderr.readline()
                    if stderr:
                        self.status_update.emit(f"Error: {stderr.strip()}")

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False

    def stop(self):
        if self.process:
            try:
                release_port(self.port)
                if sys.platform == 'win32':
                    self.process.terminate()
                    QTimer.singleShot(1000, lambda: subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(self.process.pid)]) if self.process else None)
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
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Streamlit Multi-Instance Launcher')
        self.setFixedSize(600, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.setup_directory_section(layout)
        self.setup_api_section(layout)
        self.setup_launch_button(layout)

        self.status_label = QLabel()
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
        self.config.set('api_key', self.api_key_input.text())
        self.config.set('api_base', self.api_base_input.text())
        self.config.set('model', self.model_input.text())

        port = find_available_port()
        thread = StreamlitThread(
            port=port,
            directory=directory,
            api_key=self.api_key_input.text(),
            api_base=self.api_base_input.text(),
            model=self.model_input.text()
        )

        thread.started_successfully.connect(lambda: self.on_instance_started(port))
        thread.error_occurred.connect(self.on_instance_error)

        self.current_instance = thread
        thread.start()

        self.status_label.setText("Starting...")

        self.launch_button.setEnabled(False)
        self.launch_button.setText('Stop Instance')

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_combo.setCurrentText(directory)
            self.config.add_recent_path(directory)

    def on_instance_started(self, port):
        QTimer.singleShot(6000, lambda: (
            webbrowser.open(f'http://localhost:{port}'),
            self.status_label.clear(),
            self.launch_button.setEnabled(True),
            self.launch_button.setText('Stop Instance')
        ))

    def stop_instance(self):
        if self.current_instance:
            self.current_instance.stop()
            self.current_instance = None
            self.launch_button.setText('Launch Instance')
            self.status_label.clear()

    def on_instance_error(self, error):
        print(f"Error: {error}")
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
