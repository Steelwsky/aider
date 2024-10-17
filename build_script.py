import PyInstaller.__main__
import os
import json
import streamlit
import litellm

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
    if file.endswith(('.json', '.log')):  # Add other extensions as needed
        if file == 'history.json':
            # Clear the contents of history.json
            history_path = os.path.join(script_dir, file)
            with open(history_path, 'w') as f:
                json.dump(['/Users/steelewski/projects/bpc-vh'], f)  # Write an empty list to the file
            print(f"Cleared contents of {file}")
        data_files.append(os.path.join(script_dir, file))
        
streamlit_path = os.path.dirname(os.path.abspath(streamlit.__file__))
litellm_path = os.path.dirname(os.path.abspath(litellm.__file__))
litellm_path = os.path.dirname(os.path.abspath(litellm.__file__))

# PyInstaller command
pyinstaller_command = [
    'entrypoint.py',  # Replace with your main script
    '--name=vai',
    '--onedir',
    '--windowed',
    '--log-level=DEBUG',
    f'--add-data={os.path.join(script_dir, "aider")}:aider',
    f'--add-data={streamlit_path}:streamlit',
    f'--add-data={litellm_path}:litellm',
    '--collect-submodules=aider',
    '--hidden-import=streamlit',
    '--copy-metadata=streamlit',
    '--hidden-import=tiktoken_ext.openai_public', 
    '--hidden-import=tiktoken_ext',
    # f'--additional-hooks-dir={os.path.join(script_dir, "hooks")}/hook-streamlit.py'
    # '--additional-hooks-dir=./hooks hook-streamlit.py',
    '--clean',
]

# Add data files
for file in data_files:
    pyinstaller_command.extend(['--add-data', f'{file}:.'])

# Add each dependency as a hidden import
for dep in dependencies:
    pyinstaller_command.extend(['--hidden-import', dep])

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_command)