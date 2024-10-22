from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QFileDialog, QLabel, QProgressBar,
                             QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import os
from pathlib import Path
import importlib.util
import threading
from aider.main import main as aimain


class WorkerThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self, main_function, target_dir):
        super().__init__()
        self.main_function = main_function
        self.target_dir = target_dir

    def run(self):
        try:
            self.main_function(['--forced-path', self.target_dir])
            self.finished.emit()
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")


def get_application_path():
    """Get the correct application path whether running as script or bundled app"""
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        return sys._MEIPASS
    else:
        # Running in normal Python environment
        return os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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

        # Add some spacing
        layout.addSpacing(20)

        # Run button
        self.run_button = QPushButton("Start Processing")
        self.run_button.clicked.connect(self.run_process)
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet("padding: 10px;")
        layout.addWidget(self.run_button)

        # Progress indication
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Add stretching space at the bottom
        layout.addStretch()

        # Initialize variables
        self.target_dir = None
        self.main_function = None

        # Load the main function
        self._load_main_function()

    def _load_main_function(self):
        try:
            # Get the directory where the executable is located
            # if getattr(sys, 'frozen', False):
            #     # If running as compiled executable
            #     application_path = sys._MEIPASS
            # else:
            # If running as script
            application_path = get_application_path()

            print(f'application_path: {application_path}')
            # Construct path to main.py (assuming it's in myproj/ai/main.py)
            main_path = Path(application_path) / "aider" / "main.py"

            if main_path.exists():
                spec = importlib.util.spec_from_file_location("main", str(main_path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.main_function = module.main
            else:
                QMessageBox.critical(
                    self, "Error", "Could not find main.py in the expected location.")
                sys.exit(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load main function: {str(e)}")
            sys.exit(1)

    def select_target_directory(self):
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

    def run_process(self):
        if not self.target_dir:
            QMessageBox.warning(self, "Warning", "Please select a directory first.")
            return

        if not self.main_function:
            QMessageBox.critical(self, "Error", "Main function not properly loaded.")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to process the directory:\n{self.target_dir}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.run_button.setEnabled(False)
            self.progress_label.setText("Processing...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Infinite progress bar

            # thread = threading.Thread(target=aimain, args=[f'--forced-path {self.target_dir}',])
            # thread = threading.Thread(target=aimain, args=[self.target_dir,])
            # thread.start()
            # thread.join()

            # Create and start worker thread
            self.worker = WorkerThread(self.main_function, self.target_dir)
            self.worker.finished.connect(self.process_finished)
            self.worker.progress.connect(self.update_progress)
            self.worker.start()

    def process_finished(self):
        self.progress_label.setText("Process completed successfully!")
        self.progress_bar.setVisible(False)
        self.run_button.setEnabled(True)

        QMessageBox.information(
            self,
            "Success",
            f"Directory processing complete:\n{self.target_dir}"
        )

    def update_progress(self, message):
        self.progress_label.setText(message)


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
