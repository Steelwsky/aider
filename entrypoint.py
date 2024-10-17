import sys
import json
import os
import subprocess
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from aider.main import main as aimain
# from aider.main import main

logging.basicConfig(filename='vai_launcher.log', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AiInstance(QThread):
    finished = pyqtSignal(int)

    def __init__(self, process_id, directory, model, args):
        super().__init__()
        self.process_id = process_id
        self.directory = directory
        self.model = model
        self.args = args
        self.running = True

    # def run(self):
    #     cmd = [sys.executable, "-m", "aider.main", "--model", self.model] + self.args.split()
    #     self.process = subprocess.Popen(cmd, cwd=self.directory)
    #     self.process.wait()
    #     self.finished.emit(self.process_id)

    # def run(self):
    #     try:
    #         # Now you can directly call the function from aider.main
    #         logger.info(f"Starting AiInstance {self.process_id} for model: {self.model}")
    #         while self.running:
    #             main(self.args)
    #             # Add additional logic here if needed for reentrancy

    #         logger.info(f"AiInstance {self.process_id} finished successfully")

    #     except Exception as e:
    #         logger.error(f"Error in AiInstance {self.process_id}: {e}")
    #     finally:
    #         self.finished.emit(self.process_id)

        
    def run(self):
        
        # aimain(argv=['--forced-path', self.directory])
        
        if hasattr(sys, '_MEIPASS'):
            # When running inside a PyInstaller bundle
            aider_main_path = os.path.join(sys._MEIPASS, 'aider', 'main.py')
            python_path = os.path.join(sys._MEIPASS, 'Python')
        else:
            # Running in development (outside of PyInstaller)
            aider_main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aider', 'main.py')
            python_path = sys.executable
            # python_path = '/Users/steelewski/projects/aider-forked/dist/vai/_internal/_internal/Python'
        
        # aider_main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aider', 'main.py')
        
        cmd = [python_path, aider_main_path, '--forced-path', self.directory, "--model", self.model] + self.args.split()
        logger.info(f"Starting AiInstance {self.process_id} with command: {' '.join(cmd)}")
        try:
            # self.process = subprocess.Popen(cmd, cwd=self.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f'******cmd is: {cmd}')
            self.process = subprocess.Popen(cmd)
            self.process.wait()
            logger.info(f"AiInstance {self.process_id} finished with return code: {self.process.returncode}")
        except Exception as e:
            logger.error(f"Error in AiInstance {self.process_id}: {str(e)}", exc_info=True)
        finally:
            self.finished.emit(self.process_id)

    def stop(self):
        if self.process:
            logger.info(f"Stopping AiInstance {self.process_id}")
            self.process.terminate()

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
        selected_items = self.history_list.selectedItems()
        if selected_items:
            directory = selected_items[0].text()
        elif self.history:
            directory = self.history[0]
        else:
            directory = os.getcwd()

        model = 'openai/mistralai/Codestral-22B-v0.1'
        args = '--map-tokens 1024'
        
        process_id = self.next_process_id
        self.next_process_id += 1
        
        instance_widget = QWidget()
        instance_layout = QHBoxLayout(instance_widget)
        
        label = QLabel(f"Instance {process_id} ({os.path.basename(directory)})")
        status_label = QLabel("Running")
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(lambda: self.stop_instance(process_id))
        
        instance_layout.addWidget(label)
        instance_layout.addWidget(status_label)
        instance_layout.addWidget(stop_button)
        
        self.instance_layout.addWidget(instance_widget)
        
        aimain(argv=['--forced-path', directory])
        
        # process = AiInstance(process_id, directory, model, args)
        # process.finished.connect(self.on_aider_finished)
        # process.start()
        
        # self.aider_processes[process_id] = {
        #     'process': process,
        #     'widget': instance_widget,
        #     'status_label': status_label,
        #     'stop_button': stop_button
        # }

    def on_aider_finished(self, process_id):
        logger.info(f"AiInstance {process_id} finished")
        self.remove_instance(process_id, "Finished")

    def stop_instance(self, process_id):
        if process_id in self.aider_processes:
            logger.info(f"Stopping AiInstance {process_id}")
            instance = self.aider_processes[process_id]
            instance['process'].stop()
            self.remove_instance(process_id, "Stopped")

    def remove_instance(self, process_id, status):
        if process_id in self.aider_processes:
            logger.info(f"Removing AiInstance {process_id} with status: {status}")
            instance = self.aider_processes[process_id]
            instance['widget'].setParent(None)
            instance['widget'].deleteLater()
            del self.aider_processes[process_id]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DirectorySelector()
    ex.show()
    sys.exit(app.exec())
 