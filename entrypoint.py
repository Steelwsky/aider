import sys
import os
import subprocess
import webbrowser
import signal
import time
import socket
import json
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFileDialog,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


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


def load_recent_paths():
    """Load recent paths from JSON file"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        recent_paths_file = os.path.join(base_path, 'recent_paths.json')
        if os.path.exists(recent_paths_file):
            with open(recent_paths_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_error(f"Failed to load recent paths: {str(e)}")
    return []


def save_recent_paths(paths):
    """Save recent paths to JSON file"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        recent_paths_file = os.path.join(base_path, 'recent_paths.json')
        with open(recent_paths_file, 'w') as f:
            json.dump(paths, f)
    except Exception as e:
        log_error(f"Failed to save recent paths: {str(e)}")


def log_error(message):
    """Helper function to log errors"""
    print(f"ERROR: {message}", file=sys.stderr)
    if getattr(sys, 'frozen', False):
        log_path = os.path.join(os.path.dirname(sys.executable), 'launcher_error.log')
        with open(log_path, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")


class ConfigManager:
    def __init__(self):
        self.config_path = self._get_config_path()
        self._config: Dict[str, Any] = self._load_config()

    def _get_config_path(self) -> str:
        """Determine the correct path for args.json based on whether app is frozen"""
        if getattr(sys, 'frozen', False):
            launcher_path = os.path.dirname(sys.executable)
            add_path = "_internal"
            base_path = os.path.abspath(os.path.join(launcher_path, '..', 'vai'))
            return os.path.join(base_path, add_path, 'args.json')
        else:
            # For development environment
            base_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, 'args.json')

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from args.json"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return {}

    def save_config(self) -> bool:
        """Save current configuration to args.json"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the config"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a value in the config and save it"""
        self._config[key] = value
        return self.save_config()

    def update(self, new_values: Dict[str, Any]) -> bool:
        """Update multiple config values at once"""
        self._config.update(new_values)
        return self.save_config()

    @property
    def config(self) -> Dict[str, Any]:
        """Get the entire config dictionary"""
        return self._config.copy()


class StreamlitThread(QThread):
    error_occurred = pyqtSignal(str)
    started_successfully = pyqtSignal()
    status_update = pyqtSignal(str)

    def __init__(self, arguments=None):
        super().__init__()
        self.process = None
        self._is_running = False
        self.config_manager = ConfigManager()
    
    def run(self):
        try:
            if getattr(sys, 'frozen', False):
                launcher_path = os.path.dirname(sys.executable)
                base_path = os.path.abspath(os.path.join(launcher_path, '..', 'vai'))
            else:
                # For development environment
                base_path = os.path.abspath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__))))

            self.status_update.emit(f"Base path: {base_path}")
            streamlit_exe = os.path.join(
                base_path, 'ai.exe' if sys.platform == 'win32' else 'ai')
            # Start the packaged Streamlit process
            cmd = [streamlit_exe]
            self.status_update.emit(f"Starting process with command: {cmd}")

            try:
                if sys.platform != 'win32':
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        preexec_fn=os.setsid
                    )
                else:
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
            except Exception as e:
                error_msg = f"Failed to start Streamlit process: {str(e)}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self._is_running = True
            self.status_update.emit("Process started, waiting for initialization...")

            # Wait for a brief moment to let Streamlit start
            time.sleep(2)

            # Check if process is still running and get any error output
            if self.process.poll() is not None:
                error_output = self.process.stderr.read()
                error_msg = f"Process ended immediately. Exit code: {self.process.returncode}. Error output: {error_output}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self.status_update.emit("Process is running, emitting success signal")
            self.started_successfully.emit()

            # Keep running until stopped
            while self._is_running and self.process.poll() is None:
                time.sleep(0.1)

            if self._is_running and self.process.poll() is not None:
                error = self.process.stderr.read()
                error_msg = f"Streamlit process ended unexpectedly: {error}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)

        except Exception as e:
            if self._is_running:
                error_msg = f"Unexpected error: {str(e)}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
        finally:
            self._is_running = False

    def _kill_streamlit_on_port(self, port):
        """Kill any existing Streamlit process on the specified port"""
        if sys.platform == 'win32':
            try:
                # Find and kill process using the port on Windows
                cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| find "{port}" ^| find "LISTENING"\') do taskkill /F /PID %a'
                subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            except Exception as e:
                log_error(f"Error killing process on port {port}: {str(e)}")
        else:
            try:
                # Find and kill process using the port on Unix
                cmd = f"lsof -ti:{port} | xargs kill -9"
                subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            except Exception as e:
                log_error(f"Error killing process on port {port}: {str(e)}")
    
    def _kill_python_processes(self):
        """Kill all related Python processes"""
        if self.process and self.process.pid:
            try:
                if sys.platform == 'win32':
                    # Kill process tree on Windows
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], 
                                 stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                else:
                    # Kill process group on Unix
                    try:
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                        time.sleep(0.5)
                        
                        # If process still exists, force kill
                        if self.process.poll() is None:
                            os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        # If process group not found, try direct process termination
                        self.process.terminate()
                        time.sleep(0.5)
                        if self.process.poll() is None:
                            self.process.kill()
                
                # Wait for process to finish
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                    
            except Exception as e:
                log_error(f"Error killing Python processes: {str(e)}")
                
    def stop(self):
        """Stop all processes and clean up resources"""
        self._is_running = False
        
        if self.process:
            try:
                # Kill Python processes first
                self._kill_python_processes()
                
                # Then clean up any remaining port usage
                self._kill_process_on_port()
                
            except Exception as e:
                log_error(f"Error in stop process: {str(e)}")
            finally:
                self.process = None


class StreamlitLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.streamlit_thread = None
        self.current_port = None
        self.current_directory = None
        self.recent_paths = load_recent_paths()
        self.streamlit_args = {}
        self.config_manager = ConfigManager()
        self.initUI()

    def mask_api_key(self, api_key):
        if not api_key:
            return ''
        return '*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else api_key

    def create_api_key_section(self) -> QHBoxLayout:
        """Create and return the API key input section"""
        api_key_layout = QHBoxLayout()

        api_key_label = QLabel('API Key:')
        api_key_label.setFixedWidth(60)

        self.api_key_input = QLineEdit()
        self.api_key_input.setFixedHeight(24)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        saved_api_key = self.config_manager.get('api_key', '')
        self.api_key_input.setText(saved_api_key)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)

        self.toggle_view_button = QPushButton('👁️')
        self.toggle_view_button.setFixedSize(30, 20)
        self.toggle_view_button.clicked.connect(self.toggle_api_key_visibility)
        self.toggle_view_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.toggle_view_button)
        # api_key_layout.addSpacing(10)

        return api_key_layout

    def create_api_base_section(self) -> QHBoxLayout:
        """Create and return the API base URL input section"""
        api_base_layout = QHBoxLayout()

        api_base_label = QLabel('API Base:')
        api_base_label.setFixedWidth(60)

        self.api_base_input = QLineEdit()
        self.api_base_input.setFixedHeight(24)
        saved_api_base = self.config_manager.get('api_base', 'https://integrate.api.nvidia.com/v1')
        self.api_base_input.setText(saved_api_base)
        self.api_base_input.setPlaceholderText('https://api.openai.com/v1')
        self.api_base_input.textChanged.connect(self.on_api_base_changed)

        api_base_layout.addWidget(api_base_label)
        api_base_layout.addWidget(self.api_base_input)

        return api_base_layout

    def create_model_section(self) -> QHBoxLayout:
        """Create and return the model selection section"""
        model_layout = QHBoxLayout()

        model_label = QLabel('Model:')
        model_label.setFixedWidth(60)

        self.model_input = QLineEdit()
        self.model_input.setFixedHeight(24)
        saved_model = self.config_manager.get('model', 'nvidia/llama-3.1-nemotron-70b-instruct')
        self.model_input.setText(saved_model)
        self.model_input.setPlaceholderText('gpt-4-turbo-preview')
        self.model_input.textChanged.connect(self.on_model_changed)

        self.model_dropdown = QPushButton('▼')
        self.model_dropdown.setFixedSize(30, 20)
        self.model_dropdown.clicked.connect(self.show_model_menu)
        self.model_dropdown.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        model_layout.addWidget(self.model_dropdown)

        return model_layout

    def create_api_config_section(self) -> QVBoxLayout:
        """Create and return the complete API configuration section"""
        api_config_layout = QVBoxLayout()

        # Add all API-related sections
        api_config_layout.addLayout(self.create_api_key_section())
        api_config_layout.addSpacing(4)

        api_config_layout.addLayout(self.create_api_base_section())
        api_config_layout.addSpacing(4)

        api_config_layout.addLayout(self.create_model_section())
        api_config_layout.addSpacing(4)

        # Add some spacing after the API config section
        api_config_layout.addSpacing(20)

        return api_config_layout

    def initUI(self):
        self.setWindowTitle('Streamlit App Launcher')
        self.setFixedSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_label = QLabel('Streamlit Application Launcher')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; margin-bottom: 20px;')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Directory selection combo box
        self.path_combo = QComboBox()
        self.path_combo.setStyleSheet('padding: 5px; margin-bottom: 10px;')
        self.path_combo.addItems(self.recent_paths)
        self.path_combo.setEditable(True)
        self.path_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        layout.addWidget(self.path_combo)

        # Directory browse button
        directory_layout = QHBoxLayout()
        self.browse_button = QPushButton('Browse Directory')
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.browse_button.clicked.connect(self.browse_directory)
        directory_layout.addWidget(self.browse_button)
        layout.addLayout(directory_layout)

        layout.addLayout(self.create_api_config_section())

        # Launch button
        self.launch_button = QPushButton('Launch Streamlit App')
        self.launch_button.setFixedSize(200, 50)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.launch_button.clicked.connect(self.toggle_streamlit)
        layout.addWidget(self.launch_button)

        # Status labels
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet('color: #666; margin-top: 10px;')
        layout.addWidget(self.status_label)

        self.port_label = QLabel('')
        self.port_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.port_label.setStyleSheet('color: #666; margin-top: 5px;')
        layout.addWidget(self.port_label)

        self.debug_label = QLabel('')
        self.debug_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.debug_label.setStyleSheet('color: #666; margin-top: 10px; font-size: 10px;')
        self.debug_label.setWordWrap(True)
        layout.addWidget(self.debug_label)

        # Center window
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.is_running = False

    def on_api_key_changed(self, new_key: str):
        """Handle API key changes and save to config"""
        self.config_manager.set('api_key', new_key)
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            masked_key = self.mask_api_key(new_key)
            self.api_key_input.setPlaceholderText(masked_key)

    def mask_api_key(self, api_key: str) -> str:
        """Mask all but the last 4 characters of the API key"""
        if not api_key:
            return ''
        return '*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else api_key

    def toggle_api_key_visibility(self):
        """Toggle between showing and hiding the API key"""
        current_key = self.config_manager.get('api_key', '')
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.api_key_input.setText(current_key)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_key_input.setText(current_key)

    def on_api_base_changed(self, new_base: str):
        """Handle API base URL changes"""
        self.config_manager.set('api_base', new_base)

    def on_model_changed(self, new_model: str):
        """Handle model name changes"""
        self.config_manager.set('model', new_model)

    def show_model_menu(self):
        """Show quick selection menu for common models"""
        menu = QMenu(self)
        models = [
            'nvidia/llama-3.1-nemotron-70b-instruct',
            'gpt-4-0125-preview',
            'gpt-4-1106-preview',
            'gpt-4',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-0125'
        ]

        for model in models:
            action = menu.addAction(model)
            action.triggered.connect(lambda checked, m=model: self.model_input.setText(m))

        # Show menu below the dropdown button
        menu.exec(self.model_dropdown.mapToGlobal(self.model_dropdown.rect().bottomLeft()))

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.current_directory = directory
            if directory not in self.recent_paths:
                self.recent_paths.insert(0, directory)
                if len(self.recent_paths) > 10:  # Keep only last 10 paths
                    self.recent_paths.pop()
                save_recent_paths(self.recent_paths)
                self.path_combo.clear()
                self.path_combo.addItems(self.recent_paths)
            self.path_combo.setCurrentText(directory)

    def toggle_streamlit(self):
        if not self.is_running:
            self.start_streamlit()
        else:
            self.stop_streamlit()

    def start_streamlit(self):
        try:
            self.debug_label.setText('')

            # Get selected directory
            selected_directory = self.path_combo.currentText()
            if not selected_directory or not os.path.exists(selected_directory):
                self.status_label.setText('Please select a valid directory')
                self.status_label.setStyleSheet('color: #d32f2f;')
                return

            # Find available port
            self.current_port = find_available_port()
            self.port_label.setText(f'Using port: {self.current_port}')

            self.config_manager.set("directory", selected_directory)
            self.config_manager.set("port", str(self.current_port))

            self.streamlit_thread = StreamlitThread()
            self.streamlit_thread.started_successfully.connect(self.on_streamlit_started)
            self.streamlit_thread.error_occurred.connect(self.on_streamlit_error)
            self.streamlit_thread.status_update.connect(self.on_status_update)
            self.streamlit_thread.start()

            self.status_label.setText('Starting Streamlit...')
            self.status_label.setStyleSheet('color: #1e88e5;')
            self.launch_button.setText('Stop Streamlit App')
            self.launch_button.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c62828;
                }
                QPushButton:pressed {
                    background-color: #b71c1c;
                }
            """)
            self.is_running = True

        except Exception as e:
            error_msg = f"Error in start_streamlit: {str(e)}"
            log_error(error_msg)
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet('color: #d32f2f;')

    def stop_streamlit(self):
        if self.streamlit_thread:
            self.streamlit_thread.stop()
            self.streamlit_thread.wait()
            self.streamlit_thread = None

        self.launch_button.setText('Launch Streamlit App')
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        self.status_label.setText('Streamlit stopped')
        self.status_label.setStyleSheet('color: #666;')
        self.port_label.setText('')
        self.is_running = False

    def on_streamlit_started(self):
        self.status_label.setText('Streamlit is running')
        self.status_label.setStyleSheet('color: #2e7d32;')
        webbrowser.open(f'http://localhost:{self.current_port}')

    def on_streamlit_error(self, error_message):
        self.status_label.setText(f'Error: {error_message}')
        self.status_label.setStyleSheet('color: #d32f2f;')
        self.stop_streamlit()

    def closeEvent(self, event):
        self.stop_streamlit()
        event.accept()

    def on_status_update(self, message):
        current_text = self.debug_label.text()
        self.debug_label.setText(f"{current_text}\n{message}" if current_text else message)


def main():
    app = QApplication(sys.argv)
    launcher = StreamlitLauncher()
    launcher.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
