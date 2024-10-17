import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from aider.main import main as aimain


class DirectorySelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
        self.load_history()
        self.aider_processes = {}
        self.next_process_id = 0

    def initUI(self):
        main_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll_area.setWidget(content_widget)

        self.history_list = QListWidget()
        self.content_layout.addWidget(self.history_list)

        select_button = QPushButton('Select Directory')
        select_button.clicked.connect(self.select_directory)
        self.content_layout.addWidget(select_button)

        self.start_button = QPushButton('Start new vai instance')
        self.start_button.clicked.connect(self.start_cli_app)
        self.content_layout.addWidget(self.start_button)

        self.instance_layout = QVBoxLayout()
        self.content_layout.addLayout(self.instance_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('vai - Launcher')
        self.setGeometry(300, 300, 500, 500)

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

        if self.history_list.count() > 0:
            self.history_list.setCurrentRow(0)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            if directory in self.history:
                self.history.remove(directory)
            self.history.insert(0, directory)
            self.history = self.history[:10]
            self.save_history()
            self.update_history_list()

    def start_cli_app(self):
        # Use absolute path for the aider directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        aider_dir = os.path.join(app_dir, 'aider')
        main_script = os.path.join(aider_dir, 'main.py')

        selected_items = self.history_list.selectedItems()
        if selected_items:
            directory = selected_items[0].text()
        elif self.history:
            directory = self.history[0]
        else:
            directory = os.getcwd()

        # model = self.model_input.text()

        # args = f'--model {model} --map-tokens 1024'

        aimain()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DirectorySelector()
    ex.show()
    sys.exit(app.exec())
