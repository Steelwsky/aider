import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class DirectorySelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.history_file = 'directory_history.json'
        self.load_history()

    def initUI(self):
        layout = QVBoxLayout()

        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        select_button = QPushButton('Select Directory')
        select_button.clicked.connect(self.select_directory)
        layout.addWidget(select_button)

        # Add model input field
        model_layout = QHBoxLayout()
        model_label = QLabel('Model:')
        self.model_input = QLineEdit('openai/mistralai/Codestral-22B-v0.1')
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)

        start_button = QPushButton('Start CLI Application')
        start_button.clicked.connect(self.start_cli_app)
        layout.addWidget(start_button)

        self.setLayout(layout)
        self.setWindowTitle('Directory Selector')
        self.setGeometry(300, 300, 400, 300)

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
        self.update_history_list()

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f)

    def update_history_list(self):
        self.history_list.clear()
        for directory in self.history:
            self.history_list.addItem(directory)
        
        # Preselect the first item if the list is not empty
        if self.history_list.count() > 0:
            self.history_list.setCurrentRow(0)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            if directory in self.history:
                self.history.remove(directory)
            self.history.insert(0, directory)
            self.history = self.history[:10]  # Keep only the 10 most recent directories
            self.save_history()
            self.update_history_list()

    def start_cli_app(self):
        selected_items = self.history_list.selectedItems()
        if selected_items:
            directory = selected_items[0].text()
        elif self.history:
            directory = self.history[0]
        else:
            directory = os.getcwd()

        # Get the model from the input field
        model = self.model_input.text()

        # Replace 'your_cli_app.py' with the actual name of your CLI application
        cli_app = 'your_cli_app.py'

        if sys.platform.startswith('win'):
            subprocess.Popen(f'start cmd /k "cd /d {directory} && python {cli_app} --model {model}"', shell=True)
        elif sys.platform == 'darwin':  # macOS
            applescript = f'''
            tell application "Terminal"
                do script "cd {directory} && python {cli_app} --model {model}"
                activate
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript])
        else:  # Linux and other Unix-like systems
            subprocess.Popen(['x-terminal-emulator', '-e', f'python {cli_app} --model {model}'], cwd=directory)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DirectorySelector()
    ex.show()
    sys.exit(app.exec())