import sys
import os
import subprocess
import webbrowser
import signal
import time
import socket
import json
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFileDialog,
    QComboBox,
    QHBoxLayout
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


class StreamlitThread(QThread):
    error_occurred = pyqtSignal(str)
    started_successfully = pyqtSignal()
    status_update = pyqtSignal(str)

    def __init__(self, arguments=None):
        super().__init__()
        self.process = None
        self._is_running = False
        self.arguments = arguments or {}

    def run(self):
        try:
            if getattr(sys, 'frozen', False):
                launcher_path = os.path.dirname(sys.executable)
                # Navigate from launcher directory to vai directory
                base_path = os.path.abspath(os.path.join(launcher_path, '..', 'vai'))
            else:
                # For development environment
                base_path = os.path.abspath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'vai'
                ))

            self.status_update.emit(f"Base path: {base_path}")

            streamlit_exe = os.path.join(
                base_path, 'ai.exe' if sys.platform == 'win32' else 'ai')
            self.status_update.emit(f"Looking for Streamlit at: {streamlit_exe}")

            if not os.path.exists(streamlit_exe):
                error_msg = f"Streamlit executable not found at: {streamlit_exe}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

            # Create a temporary file to store arguments
            args_file = os.path.join(launcher_path, '_internal', 'args.json')
            self.status_update.emit(f"Creating args file at: {args_file}")

            try:
                with open(args_file, 'w') as f:
                    json.dump(self.arguments, f)
            except Exception as e:
                error_msg = f"Failed to write args file: {str(e)}"
                log_error(error_msg)
                self.error_occurred.emit(error_msg)
                return

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
            # Clean up the arguments file
            try:
                if os.path.exists(args_file):
                    os.remove(args_file)
            except Exception as e:
                log_error(f"Failed to remove args file: {str(e)}")

    def stop(self):
        self._is_running = False
        if self.process:
            try:
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    except ProcessLookupError:
                        self.process.terminate()

                    time.sleep(0.5)

                    if self.process.poll() is None:
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        except ProcessLookupError:
                            self.process.kill()

                self.process.wait(timeout=2)

            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
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
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Streamlit App Launcher')
        self.setFixedSize(600, 400)

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

            # Update arguments with directory and port
            self.streamlit_args.update({
                "directory": selected_directory,
                "port": self.current_port
            })

            self.streamlit_thread = StreamlitThread(arguments=self.streamlit_args)
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
