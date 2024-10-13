import PyInstaller.__main__
import os
import json

# Get the absolute path to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Function to read requirements.txt
def get_requirements():
    req_file = os.path.join(script_dir, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return []

# Get dependencies from requirements.txt
dependencies = get_requirements()

# Collect data files from the root directory
data_files = []
for file in os.listdir(script_dir):
    if file.endswith(('.json')):  # Add other extensions as needed
        if file == 'history.json':
            # Clear the contents of history.json
            history_path = os.path.join(script_dir, file)
            with open(history_path, 'w') as f:
                json.dump([], f)  # Write an empty list to the file
            print(f"Cleared contents of {file}")
        data_files.append(os.path.join(script_dir, file))

# PyInstaller command
pyinstaller_command = [
    'entrypoint.py',  # Replace with your main script
    '--name=vai',
    '--onedir',
    '--windowed',
    f'--add-data={os.path.join(script_dir, "aider")}:aider',
    '--collect-submodules=aider',
]

# Add data files
for file in data_files:
    pyinstaller_command.extend(['--add-data', f'{file}:.'])

# Add each dependency as a hidden import
for dep in dependencies:
    pyinstaller_command.extend(['--hidden-import', dep])

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_command)