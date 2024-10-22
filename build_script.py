import PyInstaller.__main__
import os
import sys
import json
import shutil
from pathlib import Path

# Get the absolute path to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

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
    if file.endswith(('.json', '.log')):
        if file == 'history.json':
            history_path = os.path.join(script_dir, file)
            with open(history_path, 'w') as f:
                json.dump(['/Users/steelewski/projects/bpc-vh'], f)  # Write an empty list to the file
            print(f"Cleared contents of {file}")
        data_files.append(os.path.join(script_dir, file))

print(f'data_files: {data_files}')

# Get Python installation directory
python_path = os.path.dirname(sys.executable)

# Define platform-specific Python files to include
python_files = []

if sys.platform == 'darwin':  # macOS
    framework_path = os.path.join(python_path, '..')
    binary_path = os.path.join(framework_path, 'Python')
    
    if os.path.exists(binary_path):
        python_files.append((binary_path, 'python/bin/python3'))
    
    lib_path = os.path.join(framework_path, 'Versions', f'{sys.version_info.major}.{sys.version_info.minor}', 'lib')
    if os.path.exists(lib_path):
        for file in os.listdir(lib_path):
            if file.endswith('.dylib'):
                full_path = os.path.join(lib_path, file)
                python_files.append((full_path, f'python/lib/{file}'))

elif sys.platform == 'win32':  # Windows
    python_files = [
        (os.path.join(python_path, 'python.exe'), 'python'),
        (os.path.join(python_path, 'pythonw.exe'), 'python'),
        (os.path.join(python_path, f'python{sys.version_info.major}{sys.version_info.minor}.dll'), 'python'),
        (os.path.join(python_path, 'vcruntime140.dll'), 'python'),
    ]
else:  # Linux
    python_files = [
        (sys.executable, 'python/bin/python3'),
    ]

# Get the correct stdlib path
if sys.platform == 'darwin':
    stdlib_path = os.path.join(framework_path, 'Versions', 
                             f'{sys.version_info.major}.{sys.version_info.minor}', 'lib', 
                             f'python{sys.version_info.major}.{sys.version_info.minor}')
elif sys.platform == 'win32':
    stdlib_path = os.path.join(python_path, 'Lib')
else:  # Linux
    stdlib_path = os.path.join(python_path, 'lib', 
                             f'python{sys.version_info.major}.{sys.version_info.minor}')

# Add all files from stdlib_path
for root, _, files in os.walk(stdlib_path):
    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(root, stdlib_path)
            python_files.append((full_path, os.path.join('python/Lib', rel_path)))

# Clean up previous build
dist_dir = os.path.join(script_dir, 'dist')
build_dir = os.path.join(script_dir, 'build')
for dir_path in [dist_dir, build_dir]:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
        print(f"Cleaned up {dir_path}")


script_dir = os.path.dirname(os.path.abspath(__file__))

# PyInstaller command
pyinstaller_command = [
    'entrypoint.py',
    '--name=vai',
    '--onedir',
    '--windowed',
    '--log-level=DEBUG',
    '--clean',
    f'--add-data={os.path.join(script_dir, "aider")}:aider',
    
]

# Add Python interpreter and standard library
for src, dst in python_files:
    if os.path.exists(src):
        pyinstaller_command.extend(['--add-data', f'{src}:{dst}'])

# Add your CLI script
cli_script_path = os.path.join(script_dir, "aider", "main.py")
print(f'[cli_script_path]: {cli_script_path}')
if os.path.exists(cli_script_path):
    pyinstaller_command.extend([
        '--add-data', f'{cli_script_path}:aider'
    ])

# Add GUI requirements
pyinstaller_command.extend([
    # '--hidden-import', 'PyQt6.QtCore',
    # '--hidden-import', 'PyQt6.QtGui',
    # '--hidden-import', 'PyQt6.QtWidgets',
])

# Add each dependency as a hidden import
for dep in dependencies:
    pyinstaller_command.extend(['--hidden-import', dep])

# Add data files
for file in data_files:
    pyinstaller_command.extend(['--add-data', f'{file}:.'])

print("Starting PyInstaller with command:", ' '.join(pyinstaller_command))

try:
    # Run PyInstaller
    PyInstaller.__main__.run(pyinstaller_command)
except Exception as e:
    print(f"Error during build: {e}")
    sys.exit(1)

print("Build completed successfully!")