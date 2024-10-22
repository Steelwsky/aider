from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QFileDialog, QLabel, QProgressBar,
                             QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, QCoreApplication
import sys
import os
from pathlib import Path
from aider.main import main as aimain


class WorkerThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    started_main = pyqtSignal()

    def __init__(self, main_function, target_dir):
        super().__init__()
        self.main_function = main_function
        self.target_dir = target_dir

    def run(self):
        try:
            print("WorkerThread: Starting main function")
            self.started_main.emit()
            
            # Wrap the main function to handle its exit
            def wrapped_main():
                try:
                    self.main_function(['--forced-path', self.target_dir])
                finally:
                    print("Main function completed, exiting application")
                    QCoreApplication.quit()
            
            # Run the wrapped main function
            wrapped_main()
            
            self.finished.emit()
        except Exception as e:
            print(f"WorkerThread error: {str(e)}")
            self.progress.emit(f"Error: {str(e)}")
            # Make sure we still exit on error
            QCoreApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        print("Initializing MainWindow")
        self.initUI()
        
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
        self.main_function = aimain
        print("UI setup complete")

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

            self.worker = WorkerThread(self.main_function, self.target_dir)
            self.worker.started_main.connect(self.close_window)
            self.worker.start()

    def close_window(self):
        """Close only the window, keeping the application running"""
        print("Closing GUI window")
        self.hide()


def main():
    print("Starting application")
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Create and show window
    window = MainWindow(app)
    window.show()
    
    print("Entering main event loop")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())