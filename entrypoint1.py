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
    QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer


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


class DefaultConfigManager:
    def __init__(self):
        self.config_path = self._get_config_path()
        self._config = self._load_config()
        self._ensure_defaults()

    def _get_config_path(self) -> str:
        """Determine the correct path for config.json"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            add_path = ['..', 'launcher']
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            add_path = ['..',]
        return os.path.join(base_path, *add_path, 'config.json')

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading default config: {str(e)}")
            return {}

    def _ensure_defaults(self):
        """Ensure all default values exist in config"""
        defaults = {
            "default_api_key": "",
            "default_api_base": "https://integrate.api.nvidia.com/v1",
            "default_model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "recent_api_keys": [],
            "recent_api_bases": [],
            "recent_models": []
        }

        changed = False
        for key, default_value in defaults.items():
            if key not in self._config:
                self._config[key] = default_value
                changed = True

        if changed:
            self.save_config()

    def save_config(self) -> bool:
        """Save current configuration to config.json"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving default config: {str(e)}")
            return False

    def get_default(self, key: str, default: Any = None) -> Any:
        """Get a default value from the config"""
        return self._config.get(key, default)

    def set_default(self, key: str, value: Any) -> bool:
        """Set a default value in the config"""
        self._config[key] = value
        return self.save_config()

    def add_recent(self, key: str, value: str, max_items: int = 5):
        """Add an item to a recent items list"""
        recent_key = f"recent_{key}s"
        if recent_key in self._config:
            # Remove if exists and add to front
            if value in self._config[recent_key]:
                self._config[recent_key].remove(value)
            self._config[recent_key].insert(0, value)
            # Keep only max_items
            self._config[recent_key] = self._config[recent_key][:max_items]
            self.save_config()

    def get_recent(self, key: str) -> list[str]:
        """Get recent items list"""
        recent_key = f"recent_{key}s"
        return self._config.get(recent_key, [])


class ConfigManager:
    def __init__(self):
        self.config_path = self._get_config_path()
        self._config: Dict[str, Dict[str, Any]] = self._load_config()

    def _get_config_path(self) -> str:
        """Determine the correct path for args.json based on whether app is frozen"""
        if getattr(sys, 'frozen', False):
            launcher_path = os.path.dirname(sys.executable)
            add_path = "_internal"
            base_path = os.path.abspath(os.path.join(launcher_path, '..', 'vai'))
            return os.path.join(base_path, add_path, 'args.json')
        else:
            base_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, 'args.json')

    def _load_config(self) -> Dict[str, Dict[str, Any]]:
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
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False

    def get_instance_config(self, port: str) -> Dict[str, Any]:
        """Get configuration for a specific instance"""
        return self._config.get(str(port), {})

    def set_instance_config(self, port: str, config: Dict[str, Any]) -> bool:
        """Set configuration for a specific instance"""
        self._config[str(port)] = config
        return self.save_config()

    def remove_instance_config(self, port: str) -> bool:
        """Remove configuration for a specific instance"""
        if str(port) in self._config:
            del self._config[str(port)]
            return self.save_config()
        return False


class StreamlitInstance:
    def __init__(self, port: int, directory: str, thread: 'StreamlitThread'):
        self.port = port
        self.directory = directory
        self.thread = thread
        self.start_time = time.time()

    @property
    def runtime(self) -> str:
        """Get runtime duration as formatted string"""
        duration = int(time.time() - self.start_time)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class StreamlitThread(QThread):
    error_occurred = pyqtSignal(str)
    started_successfully = pyqtSignal()
    status_update = pyqtSignal(str)

    def __init__(self, port=None, arguments=None):
        super().__init__()
        self.process = None
        self._is_running = False
        self.port = port
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

            # Get instance-specific configuration
            instance_config = self.config_manager.get_instance_config(str(self.port))

            # Create environment variables with instance configuration
            env = os.environ.copy()
            env['APP_PORT'] = str(self.port)
            env['APP_API_KEY'] = instance_config.get('api_key', '')
            env['APP_API_BASE'] = instance_config.get('api_base', '')
            env['APP_MODEL'] = instance_config.get('model', '')
            env['APP_DIRECTORY'] = instance_config.get('directory', '')

            # Start the packaged Streamlit process
            cmd = [streamlit_exe]
            self.status_update.emit(f"Starting process with command: {cmd} on port {self.port}")

            try:
                if sys.platform != 'win32':
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        preexec_fn=os.setsid,
                        env=env
                    )
                else:
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                        env=env
                    )
            except Exception as e:
                error_msg = f"Failed to start Streamlit process on port {self.port}: {str(e)}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self._is_running = True
            self.status_update.emit(
                f"Process started on port {self.port}, waiting for initialization...")

            # Wait for a brief moment to let Streamlit start
            time.sleep(2)

            # Check if process is still running and get any error output
            if self.process.poll() is not None:
                error_output = self.process.stderr.read()
                error_msg = f"Process on port {self.port} ended immediately. Exit code: {self.process.returncode}. Error output: {error_output}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            self.status_update.emit(
                f"Process is running on port {self.port}, emitting success signal")
            self.started_successfully.emit()

            # Keep running until stopped
            while self._is_running and self.process.poll() is None:
                # Check for any output from the process
                stdout_line = self.process.stdout.readline()
                if stdout_line:
                    self.status_update.emit(f"Port {self.port}: {stdout_line.strip()}")
                stderr_line = self.process.stderr.readline()
                if stderr_line:
                    self.status_update.emit(f"Port {self.port} Error: {stderr_line.strip()}")
                time.sleep(0.1)

            if self._is_running and self.process.poll() is not None:
                error = self.process.stderr.read()
                error_msg = f"Streamlit process on port {self.port} ended unexpectedly: {error}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)

        except Exception as e:
            if self._is_running:
                error_msg = f"Unexpected error on port {self.port}: {str(e)}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
        finally:
            self._is_running = False

    def _kill_process_on_specific_port(self, port):
        """Kill process using the specific port"""
        try:
            if sys.platform == 'win32':
                # Windows: find and kill specific process on port
                cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| find "{port}" ^| find "LISTENING"\') do taskkill /F /PID %a'
                subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            else:
                # Unix: kill specific process on port
                cmd = f"lsof -ti:{port} | xargs -r kill -9"
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
                log_error(f"Error killing Python processes on port {self.port}: {str(e)}")

    def stop(self):
        """Stop the specific process and clean up its port"""
        self._is_running = False

        if self.process:
            try:
                port = self.port

                # Kill the specific process
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        time.sleep(0.5)

                        if self.process.poll() is None:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        self.process.terminate()
                        if self.process.poll() is None:
                            self.process.kill()

                # Wait for process to finish
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass

                # Clean up the specific port if it exists in config
                if port:
                    self._kill_process_on_specific_port(port)

            except Exception as e:
                log_error(f"Error in stop process: {str(e)}")
            finally:
                self.process = None


class StreamlitLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recent_paths = load_recent_paths() or []
        self.instances: Dict[int, StreamlitInstance] = {}
        self.config_manager = ConfigManager()
        self.default_config = DefaultConfigManager()
        self.initUI()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_instances_display)
        self.update_timer.start(1000)

    def mask_api_key(self, api_key):
        if not api_key:
            return ''
        return '*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else api_key

    def create_api_key_section(self) -> QHBoxLayout:
        """Create and return the API key input section with recent values dropdown"""
        api_key_layout = QHBoxLayout()

        api_key_label = QLabel('API Key:')
        api_key_label.setFixedWidth(60)

        self.api_key_input = QLineEdit()
        self.api_key_input.setFixedHeight(24)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Load default API key
        default_api_key = self.default_config.get_default('default_api_key', '')
        self.api_key_input.setText(default_api_key)

        self.api_key_input.textChanged.connect(self.on_api_key_changed)

        # Recent API keys dropdown
        self.api_key_dropdown = QPushButton('▼')
        self.api_key_dropdown.setFixedSize(30, 20)
        self.api_key_dropdown.clicked.connect(self.show_recent_api_keys)
        self.api_key_dropdown.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        self.toggle_view_button = QPushButton('👁️')
        self.toggle_view_button.setFixedSize(30, 20)
        self.toggle_view_button.clicked.connect(self.toggle_api_key_visibility)

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.api_key_dropdown)
        api_key_layout.addWidget(self.toggle_view_button)

        return api_key_layout

    def create_api_base_section(self) -> QHBoxLayout:
        """Create and return the API base URL input section with recent values"""
        api_base_layout = QHBoxLayout()

        api_base_label = QLabel('API Base:')
        api_base_label.setFixedWidth(60)

        self.api_base_input = QLineEdit()
        self.api_base_input.setFixedHeight(24)

        # Load default API base
        default_api_base = self.default_config.get_default('default_api_base',
                                                           'https://integrate.api.nvidia.com/v1')
        self.api_base_input.setText(default_api_base)

        self.api_base_input.textChanged.connect(self.on_api_base_changed)

        # Recent API bases dropdown
        self.api_base_dropdown = QPushButton('▼')
        self.api_base_dropdown.setFixedSize(30, 20)
        self.api_base_dropdown.clicked.connect(self.show_recent_api_bases)
        self.api_base_dropdown.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        api_base_layout.addWidget(api_base_label)
        api_base_layout.addWidget(self.api_base_input)
        api_base_layout.addWidget(self.api_base_dropdown)

        return api_base_layout

    def create_model_section(self) -> QHBoxLayout:
        """Create and return the model selection section with recent values"""
        model_layout = QHBoxLayout()

        model_label = QLabel('Model:')
        model_label.setFixedWidth(60)

        self.model_input = QLineEdit()
        self.model_input.setFixedHeight(24)

        # Load default model
        default_model = self.default_config.get_default('default_model',
                                                        'nvidia/llama-3.1-nemotron-70b-instruct')
        self.model_input.setText(default_model)

        self.model_input.textChanged.connect(self.on_model_changed)

        self.model_dropdown = QPushButton('▼')
        self.model_dropdown.setFixedSize(30, 20)
        self.model_dropdown.clicked.connect(self.show_model_menu)

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        model_layout.addWidget(self.model_dropdown)

        return model_layout

    def create_api_config_section(self) -> QVBoxLayout:
        """Create and return the complete API configuration section"""
        api_config_layout = QVBoxLayout()

    def create_api_config_section(self) -> QVBoxLayout:
        """Create and return the complete API configuration section"""
        api_config_layout = QVBoxLayout()

        api_config_layout.addLayout(self.create_api_key_section())
        api_config_layout.addSpacing(4)

        api_config_layout.addLayout(self.create_api_base_section())
        api_config_layout.addSpacing(4)

        api_config_layout.addLayout(self.create_model_section())
        api_config_layout.addSpacing(4)

        api_config_layout.addSpacing(20)

        return api_config_layout

    def show_recent_api_keys(self):
        """Show menu with recent API keys"""
        menu = QMenu(self)
        recent_keys = self.default_config.get_recent('api_key')

        for key in recent_keys:
            masked_key = self.mask_api_key(key)
            action = menu.addAction(masked_key)
            action.triggered.connect(lambda checked, k=key: self.api_key_input.setText(k))

        # Add option to set current as default
        menu.addSeparator()
        set_default_action = menu.addAction("Set Current as Default")
        set_default_action.triggered.connect(lambda: self.set_current_as_default('api_key'))

        menu.exec(self.api_key_dropdown.mapToGlobal(
            self.api_key_dropdown.rect().bottomLeft()))

    def show_recent_api_bases(self):
        """Show menu with recent API base URLs"""
        menu = QMenu(self)
        recent_bases = self.default_config.get_recent('api_base')

        for base in recent_bases:
            action = menu.addAction(base)
            action.triggered.connect(lambda checked, b=base: self.api_base_input.setText(b))

        # Add option to set current as default
        menu.addSeparator()
        set_default_action = menu.addAction("Set Current as Default")
        set_default_action.triggered.connect(lambda: self.set_current_as_default('api_base'))

        menu.exec(self.api_base_dropdown.mapToGlobal(
            self.api_base_dropdown.rect().bottomLeft()))

    def show_model_menu(self):
        """Show menu with recent and predefined models"""
        menu = QMenu(self)

        # Add recent models
        recent_models = self.default_config.get_recent('model')
        for model in recent_models:
            action = menu.addAction(model)
            action.triggered.connect(lambda checked, m=model: self.model_input.setText(m))

        # Add separator and predefined models
        if recent_models:
            menu.addSeparator()

        predefined_models = [
            'nvidia/llama-3.1-nemotron-70b-instruct',
            'gpt-4-0125-preview',
            'gpt-4-1106-preview',
            'gpt-4',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-0125'
        ]

        for model in predefined_models:
            action = menu.addAction(model)
            action.triggered.connect(lambda checked, m=model: self.model_input.setText(m))

        # Add option to set current as default
        menu.addSeparator()
        set_default_action = menu.addAction("Set Current as Default")
        set_default_action.triggered.connect(lambda: self.set_current_as_default('model'))

        menu.exec(self.model_dropdown.mapToGlobal(
            self.model_dropdown.rect().bottomLeft()))

    def set_current_as_default(self, field: str):
        """Set current value as default for the specified field"""
        if field == 'api_key':
            value = self.api_key_input.text()
            self.default_config.set_default('default_api_key', value)
        elif field == 'api_base':
            value = self.api_base_input.text()
            self.default_config.set_default('default_api_base', value)
        elif field == 'model':
            value = self.model_input.text()
            self.default_config.set_default('default_model', value)

    def on_api_key_changed(self, new_key: str):
        """Handle API key changes"""
        if new_key:
            self.default_config.add_recent('api_key', new_key)

    def on_api_base_changed(self, new_base: str):
        """Handle API base URL changes"""
        if new_base:
            self.default_config.add_recent('api_base', new_base)

    def on_model_changed(self, new_model: str):
        """Handle model name changes"""
        if new_model:
            self.default_config.add_recent('model', new_model)

    def initUI(self):
        self.setWindowTitle('Streamlit App Launcher')
        self.setFixedSize(600, 700)

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

        self.instances_group = QGroupBox("Running Instances")
        instances_layout = QVBoxLayout()
        self.instances_list = QTableWidget()
        self.instances_list.setColumnCount(4)
        self.instances_list.setHorizontalHeaderLabels(["Port", "Directory", "Runtime", "Action"])
        self.instances_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        instances_layout.addWidget(self.instances_list)
        self.instances_group.setLayout(instances_layout)
        layout.addWidget(self.instances_group)

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

    def start_new_instance(self):
        try:
            selected_directory = self.path_combo.currentText()
            if not selected_directory or not os.path.exists(selected_directory):
                self.status_label.setText('Please select a valid directory')
                self.status_label.setStyleSheet('color: #d32f2f;')
                return

            new_port = find_available_port()

            # Save instance configuration
            instance_config = {
                "directory": selected_directory,
                "port": str(new_port),
                "model": self.model_input.text(),
                "api_key": self.api_key_input.text(),
                "api_base": self.api_base_input.text()
            }
            self.config_manager.set_instance_config(str(new_port), instance_config)

            # Start new instance
            thread = StreamlitThread(port=str(new_port))
            thread.started_successfully.connect(lambda: self.on_instance_started(new_port))
            thread.error_occurred.connect(lambda msg: self.on_instance_error(new_port, msg))
            thread.status_update.connect(self.on_status_update)
            thread.start()

            # Add to instances dictionary
            self.instances[new_port] = StreamlitInstance(new_port, selected_directory, thread)
            self.update_instances_display()

            self.status_label.setText(f'Starting new instance on port {new_port}...')
            self.status_label.setStyleSheet('color: #1e88e5;')

        except Exception as e:
            error_msg = f"Error starting new instance: {str(e)}"
            log_error(error_msg)
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet('color: #d32f2f;')

    def update_instances_display(self):
        """Update the instances table display"""
        self.instances_list.setRowCount(len(self.instances))
        for i, (port, instance) in enumerate(self.instances.items()):
            # Port
            port_item = QTableWidgetItem(str(port))
            self.instances_list.setItem(i, 0, port_item)

            # Directory
            dir_item = QTableWidgetItem(instance.directory)
            self.instances_list.setItem(i, 1, dir_item)

            # Runtime
            runtime_item = QTableWidgetItem(instance.runtime)
            self.instances_list.setItem(i, 2, runtime_item)

            # Stop button
            if not hasattr(self, f'stop_button_{port}'):
                stop_button = QPushButton('Stop')
                stop_button.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        border-radius: 3px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #c62828;
                    }
                """)
                stop_button.clicked.connect(lambda checked, p=port: self.stop_instance(p))
                setattr(self, f'stop_button_{port}', stop_button)

            self.instances_list.setCellWidget(i, 3, getattr(self, f'stop_button_{port}'))

    def stop_instance(self, port: int):
        """Stop a specific instance"""
        if port in self.instances:
            instance = self.instances[port]
            instance.thread.stop()
            instance.thread.wait()
            self.config_manager.remove_instance_config(str(port))
            del self.instances[port]
            delattr(self, f'stop_button_{port}')
            self.update_instances_display()
            self.status_label.setText(f'Instance on port {port} stopped')
            self.status_label.setStyleSheet('color: #666;')

    def on_instance_started(self, port: int):
        """Handle successful instance start"""
        self.status_label.setText(f'Instance on port {port} is running')
        self.status_label.setStyleSheet('color: #2e7d32;')
        webbrowser.open(f'http://localhost:{port}')

    def on_instance_error(self, port: int, error_message: str):
        """Handle instance error"""
        self.status_label.setText(f'Error on port {port}: {error_message}')
        self.status_label.setStyleSheet('color: #d32f2f;')
        self.stop_instance(port)

    def closeEvent(self, event):
        """Stop all instances when closing the launcher"""
        for port in list(self.instances.keys()):
            self.stop_instance(port)
        event.accept()

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

            instance_config = {
                "directory": selected_directory,
                "port": str(self.current_port),
                "model": self.model_input.text(),
                "api_key": self.api_key_input.text(),
                "api_base": self.api_base_input.text()
            }
            self.config_manager.set_instance_config(str(self.current_port), instance_config)
            self.streamlit_thread = StreamlitThread(port=self.current_port)
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
            # Remove the instance configuration when stopping
            if hasattr(self, 'current_port'):
                self.config_manager.remove_instance_config(str(self.current_port))

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
