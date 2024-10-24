from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QFileDialog, QLabel, QProgressBar,
                             QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, QCoreApplication, Qt, QTimer
import sys
import os
import signal
import subprocess
import webbrowser
import json
import socket
import tempfile
import multiprocessing


def get_gui_path():
    """Get the correct path to st_gui.py"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'aider', 'gui.py')
    else:
        # Running in normal Python environment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'aider', 'gui.py')


def find_available_port(start_port=8501, max_port=8600):
    """Find the next available port starting from start_port"""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                # Try to bind to the port
                sock.bind(('localhost', port))
                return port
            except socket.error:
                continue
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")


def get_active_ports():
    """Get list of currently active Streamlit ports"""
    try:
        if os.path.exists('active_ports.json'):
            with open('active_ports.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def add_active_port(port):
    """Add port to active ports list"""
    ports = get_active_ports()
    if port not in ports:
        ports.append(port)
        with open('active_ports.json', 'w') as f:
            json.dump(ports, f)


def remove_active_port(port):
    """Remove port from active ports list"""
    ports = get_active_ports()
    if port in ports:
        ports.remove(port)
        with open('active_ports.json', 'w') as f:
            json.dump(ports, f)


class StreamlitProcess(multiprocessing.Process):
    def __init__(self, target_dir, port):
        super().__init__()
        self.target_dir = target_dir
        self.port = port
        self.daemon = True
        
    def run(self):
        try:
            os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
            os.environ['STREAMLIT_SERVER_PORT'] = str(self.port)
            
            gui_path = get_gui_path()
            print(f"Starting Streamlit with GUI path: {gui_path} on port {self.port}")
            
            # Add this port to active ports
            add_active_port(self.port)
            
            cmd = [
                sys.executable,
                "-m", "streamlit",
                "run",
                gui_path,
                "--server.port", str(self.port),
                "--server.runOnSave=false",
                "--server.fileWatcherType=none",
                "--client.toolbarMode=viewer",
                "--",
                "--forced-path",
                self.target_dir
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            # Create a unique log file for this instance
            log_file_name = f'streamlit_{self.port}.log'
            with open(log_file_name, 'w') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
            
            # Write process info including port
            process_info = {
                'pid': process.pid,
                'port': self.port
            }
            with open(f'streamlit_process_{self.port}.json', 'w') as f:
                json.dump(process_info, f)
            
            # Open browser after a short delay
            QTimer.singleShot(3000, lambda: webbrowser.open(f'http://localhost:{self.port}'))
            
            process.wait()
            
        except Exception as e:
            print(f"Error in StreamlitProcess: {e}")
            with open(f'streamlit_error_{self.port}.log', 'w') as f:
                f.write(str(e))
        finally:
            # Cleanup process files and port
            self.cleanup()

    def cleanup(self):
        """Clean up process-specific files and port"""
        try:
            process_file = f'streamlit_process_{self.port}.json'
            if os.path.exists(process_file):
                os.remove(process_file)
            remove_active_port(self.port)
        except Exception as e:
            print(f"Cleanup error: {e}")

class WorkerThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    started_main = pyqtSignal()
    
    def __init__(self, target_dir):
        super().__init__()
        self.target_dir = target_dir
        self.streamlit_process = None
        self.port = None

    def run(self):
        try:
            print("WorkerThread: Starting Streamlit process")
            self.started_main.emit()
            
            # Find available port
            self.port = find_available_port()
            print(f"Using port: {self.port}")
            
            # Create and start Streamlit process with assigned port
            self.streamlit_process = StreamlitProcess(self.target_dir, self.port)
            self.streamlit_process.start()
            
            # Wait for the process to complete
            self.streamlit_process.join()
            
        except Exception as e:
            print(f"WorkerThread error: {str(e)}")
            self.progress.emit(f"Error: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        print("Cleaning up resources...")
        try:
            if self.port:
                process_file = f'streamlit_process_{self.port}.json'
                if os.path.exists(process_file):
                    with open(process_file, 'r') as f:
                        process_info = json.load(f)
                    try:
                        os.kill(process_info['pid'], signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    os.remove(process_file)
                remove_active_port(self.port)
        except Exception as e:
            print(f"Cleanup error: {e}")


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        print("Initializing MainWindow")
        self.initial_cwd = os.getcwd()
        self.initUI()

    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'worker'):
            self.worker.cleanup()
        os.chdir(self.initial_cwd)
        event.accept()

    def run_process(self):
        if not self.target_dir:
            QMessageBox.warning(self, "Warning", "Please select a directory first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to process the directory:\n{self.target_dir}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("Starting processing")
            self.run_button.setEnabled(False)
            self.progress_label.setText("Processing...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            self.worker = WorkerThread(self.target_dir)
            self.worker.started_main.connect(self.close_window)
            self.worker.start()

    def shutdown_application(self):
        """Handle complete application shutdown"""
        print("Shutting down application...")
        QTimer.singleShot(500, lambda: os._exit(0))  # Force quit after cleanup

    def select_target_directory(self):
        print("Opening directory selection dialog")
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Process",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.target_dir = dir_path
            self.target_dir_label.setText(f"Selected: {dir_path}")
            self.run_button.setEnabled(True)
            print(f"Selected directory: {dir_path}")

    def close_window(self):
        """Close only the window, keeping the application running"""
        print("Closing GUI window")
        self.hide()

    def initUI(self):
        print("Setting up UI components")
        self.setWindowTitle("Directory Processor")
        self.setMinimumSize(600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add title/description
        title_label = QLabel("Directory Processing Tool")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        description = QLabel("This tool processes the contents of a selected directory.\n"
                             "Please select the directory you want to process.")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Target Directory Selection
        layout.addWidget(QLabel("\nTarget Directory:"))
        self.target_dir_label = QLabel("No directory selected")
        self.target_dir_label.setStyleSheet(
            "padding: 5px; background-color: #a9a9a9; border-radius: 3px;")
        layout.addWidget(self.target_dir_label)

        select_target_button = QPushButton("Select Directory to Process")
        select_target_button.clicked.connect(self.select_target_directory)
        layout.addWidget(select_target_button)

        layout.addSpacing(20)

        self.run_button = QPushButton("Start Processing")
        self.run_button.clicked.connect(self.run_process)
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet("padding: 10px;")
        layout.addWidget(self.run_button)

        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        self.target_dir = None
        print("UI setup complete")


def main():
    print("Starting application")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Executable path: {sys.executable}")

    # Initialize empty active ports file if it doesn't exist
    if not os.path.exists('active_ports.json'):
        with open('active_ports.json', 'w') as f:
            json.dump([], f)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow(app)
    window.show()

    print("Entering main event loop")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
